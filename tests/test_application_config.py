"""Unit tests for ApplicationConfig."""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.config.settings_data import SettingsData
from warriorfit.logic.singleton import Singleton


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "db": {
        "host": "localhost",
        "port": 5432,
        "database": "warriorfit_db",
        "username": "wf_user",
        "password": "secret",
    },
    "path": {"pdf_path": "/tmp/wf_pdf"},
    "unit": {"name": "Alpha"},
    "mail": {
        "host": "smtp.example.com",
        "port": 587,
        "username": "mail_user",
        "password": "mail_pass",
        "use_tls": True,
        "use_ssl": False,
        "sender": "WarriorFit",
        "sender_email": "noreply@example.com",
    },
    "hr": {"url": "https://hr.example.com/api", "api_key": "hr-key-123"},
    "version": {"status": "stable"},
}

MINIMAL_VERSION = {"version": "2.0.0", "date": "2026-03-23"}


def _clear_singleton():
    """Remove ApplicationConfig from the Singleton registry so each test gets a fresh instance."""
    from warriorfit.config.appliccation_config import ApplicationConfig
    Singleton._instances.pop(ApplicationConfig, None)


def _make_config(env: str = "development", extra_env: dict | None = None):
    """
    Instantiate ApplicationConfig with all I/O mocked.
    Returns the instance.
    """
    _clear_singleton()
    from warriorfit.config.appliccation_config import ApplicationConfig

    env_vars = {"APP_ENV": env}
    if extra_env:
        env_vars.update(extra_env)

    yaml_data = {
        "config": yaml.dump(MINIMAL_CONFIG),
        "version": yaml.dump(MINIMAL_VERSION),
    }

    def fake_open(path, *args, **kwargs):
        path_str = str(path)
        if "version" in path_str:
            content = yaml_data["version"]
        else:
            content = yaml_data["config"]
        return mock_open(read_data=content)()

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch("builtins.open", side_effect=fake_open),
        patch("warriorfit.config.appliccation_config.create_async_engine", return_value=MagicMock()),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        instance = ApplicationConfig()

    return instance


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------

def test_singleton_returns_same_instance():
    cfg1 = _make_config()
    from warriorfit.config.appliccation_config import ApplicationConfig
    cfg2 = ApplicationConfig()   # no args — returns cached instance
    assert cfg1 is cfg2


# ---------------------------------------------------------------------------
# settings_data is populated correctly
# ---------------------------------------------------------------------------

def test_settings_data_db_fields():
    cfg = _make_config()
    sd = cfg.settings_data
    assert sd.db_host == "localhost"
    assert sd.db_port == 5432
    assert sd.db_database == "warriorfit_db"
    assert sd.db_username == "wf_user"
    assert sd.db_password == "secret"


def test_settings_data_unit():
    cfg = _make_config()
    assert cfg.settings_data.own_unit == "Alpha"


def test_settings_data_hr():
    cfg = _make_config()
    assert cfg.settings_data.hr_url == "https://hr.example.com/api"
    assert cfg.settings_data.hr_api_key == "hr-key-123"


def test_settings_data_mail_server():
    cfg = _make_config()
    mail = cfg.settings_data.mail_server
    assert isinstance(mail, SmtpConfig)
    assert mail.host == "smtp.example.com"
    assert mail.use_tls is True


# ---------------------------------------------------------------------------
# Properties delegate to settings_data
# ---------------------------------------------------------------------------

def test_property_hr_url():
    cfg = _make_config()
    assert cfg.hr_url == "https://hr.example.com/api"


def test_property_hr_api_key():
    cfg = _make_config()
    assert cfg.hr_api_key == "hr-key-123"


def test_property_own_unit():
    cfg = _make_config()
    assert cfg.own_unit == "Alpha"


def test_property_mail_server():
    cfg = _make_config()
    assert cfg.mail_server.host == "smtp.example.com"


def test_property_pdf_output_path():
    cfg = _make_config()
    assert cfg.pdf_output_path == "/tmp/wf_pdf"


# ---------------------------------------------------------------------------
# Version tuple
# ---------------------------------------------------------------------------

def test_version_is_tuple_of_three():
    cfg = _make_config()
    assert isinstance(cfg.version, tuple)
    assert len(cfg.version) == 3


def test_version_values():
    cfg = _make_config()
    # version = (status, version_number, date)
    assert cfg.version[0] == "stable"
    assert cfg.version[1] == "2.0.0"
    assert cfg.version[2] == "2026-03-23"


# ---------------------------------------------------------------------------
# config property returns the engine
# ---------------------------------------------------------------------------

def test_config_property_returns_engine():
    cfg = _make_config()
    assert cfg.config is not None


# ---------------------------------------------------------------------------
# Environment-based config path selection
# ---------------------------------------------------------------------------

def test_development_env_uses_dev_config(tmp_path):
    _clear_singleton()
    from warriorfit.config.appliccation_config import ApplicationConfig

    captured_paths = []

    def fake_open(path, *args, **kwargs):
        captured_paths.append(str(path))
        if "version" in str(path):
            return mock_open(read_data=yaml.dump(MINIMAL_VERSION))()
        return mock_open(read_data=yaml.dump(MINIMAL_CONFIG))()

    with (
        patch.dict(os.environ, {"APP_ENV": "development"}, clear=False),
        patch("builtins.open", side_effect=fake_open),
        patch("warriorfit.config.appliccation_config.create_async_engine", return_value=MagicMock()),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        ApplicationConfig()

    assert any("config_dev.yml" in p for p in captured_paths)


def test_production_env_requires_secret_key():
    _clear_singleton()
    from warriorfit.config.appliccation_config import ApplicationConfig

    env = {"APP_ENV": "production"}
    # Remove WF_SECRET_KEY if present
    env_clean = {k: v for k, v in os.environ.items() if k != "WF_SECRET_KEY"}
    env_clean["APP_ENV"] = "production"

    with patch.dict(os.environ, env_clean, clear=True):
        with pytest.raises((KeyError, ValueError)):
            ApplicationConfig()


def test_production_env_with_secret_key_and_config_override(tmp_path):
    import io
    _clear_singleton()
    from warriorfit.config.appliccation_config import ApplicationConfig

    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump(MINIMAL_CONFIG), encoding="utf-8")
    version_file = tmp_path / "version.yaml"
    version_file.write_text(yaml.dump(MINIMAL_VERSION), encoding="utf-8")

    _real_open = io.open

    def fake_open(path, *args, **kwargs):
        if "version" in str(path):
            return _real_open(version_file, *args, **kwargs)
        return _real_open(config_file, *args, **kwargs)

    with (
        patch.dict(os.environ, {
            "APP_ENV": "production",
            "WF_SECRET_KEY": "supersecret",
            "APP_CONFIG_PATH": str(config_file),
        }, clear=False),
        patch("builtins.open", side_effect=fake_open),
        patch("warriorfit.config.appliccation_config.create_async_engine", return_value=MagicMock()),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        cfg = ApplicationConfig()

    assert cfg.settings_data.db_host == "localhost"


# ---------------------------------------------------------------------------
# _ensure_directory creates missing directories
# ---------------------------------------------------------------------------

def test_ensure_directory_creates_path(tmp_path):
    from warriorfit.config.appliccation_config import ApplicationConfig
    new_dir = tmp_path / "sub" / "dir"
    assert not new_dir.exists()
    result = ApplicationConfig._ensure_directory(str(new_dir))
    assert Path(result).exists()


def test_ensure_directory_existing_path(tmp_path):
    from warriorfit.config.appliccation_config import ApplicationConfig
    result = ApplicationConfig._ensure_directory(str(tmp_path))
    assert Path(result).exists()


# ---------------------------------------------------------------------------
# save_config writes correct YAML
# ---------------------------------------------------------------------------

def test_save_config_writes_yaml(tmp_path):
    cfg = _make_config()

    output_file = tmp_path / "saved_config.yml"
    cfg.config_path = output_file

    new_settings = SettingsData(
        db_host="db.new",
        db_port=5433,
        db_database="new_db",
        db_username="new_user",
        db_password="new_pass",
        pdf_path="/tmp/new_pdf",
        own_unit="Bravo",
        mail_server=SmtpConfig(
            host="mail.new",
            port=465,
            username="u",
            password="p",
            use_tls=False,
            use_ssl=True,
            sender="NW",
            sender_email="nw@example.com",
        ),
        hr_url="https://hr.new/api",
        hr_api_key="new-key",
    )

    cfg.save_config(new_settings)

    saved = yaml.safe_load(output_file.read_text(encoding="utf-8"))
    assert saved["db"]["host"] == "db.new"
    assert saved["db"]["database"] == "new_db"
    assert saved["unit"]["name"] == "Bravo"
    assert saved["hr"]["url"] == "https://hr.new/api"
    assert saved["mail"]["host"] == "mail.new"
    assert saved["path"]["pdf_path"] == "/tmp/new_pdf"


# ---------------------------------------------------------------------------
# SettingsData helpers (tested here for completeness)
# ---------------------------------------------------------------------------

def test_settings_data_has_database_config_true():
    sd = SettingsData(db_host="h", db_database="d", db_username="u", db_password="p")
    assert sd.has_database_config() is True


def test_settings_data_has_database_config_false():
    sd = SettingsData(db_host="", db_database="d", db_username="u", db_password="p")
    assert sd.has_database_config() is False


def test_settings_data_has_hr_config_true():
    sd = SettingsData(hr_url="https://hr.example.com", hr_api_key="key")
    assert sd.has_hr_config() is True


def test_settings_data_has_hr_config_false():
    sd = SettingsData(hr_url="", hr_api_key="key")
    assert sd.has_hr_config() is False
