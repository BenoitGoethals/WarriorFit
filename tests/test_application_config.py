"""Unit tests for ApplicationConfig."""

import io
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from warriorfit.config.settings_data import SettingsData
from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.logic.singleton import Singleton

# ---------------------------------------------------------------------------
# Test data
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_singleton():
    """Ensure every test starts with a fresh ApplicationConfig instance."""
    from warriorfit.config.appliccation_config import ApplicationConfig

    Singleton._instances.pop(ApplicationConfig, None)
    yield
    Singleton._instances.pop(ApplicationConfig, None)


@pytest.fixture()
def app_config():
    """
    Fully mocked ApplicationConfig instance (development env).
    YAML loading and the DB engine are replaced with mocks; builtins.open is untouched
    so that tests calling save_config() can write real files.
    """
    from warriorfit.config.appliccation_config import ApplicationConfig

    with (
        patch.dict(os.environ, {"APP_ENV": "development"}, clear=False),
        patch.object(ApplicationConfig, "_load_yaml_file", return_value=MINIMAL_CONFIG),
        patch.object(
            ApplicationConfig, "_load_version_yaml_file", return_value=MINIMAL_VERSION
        ),
        patch(
            "warriorfit.config.appliccation_config.create_async_engine",
            return_value=MagicMock(),
        ),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        yield ApplicationConfig()


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------


def test_singleton_returns_same_instance(app_config):
    from warriorfit.config.appliccation_config import ApplicationConfig

    second = ApplicationConfig()
    assert app_config is second


# ---------------------------------------------------------------------------
# settings_data is populated correctly
# ---------------------------------------------------------------------------


def test_settings_data_db_host(app_config):
    assert app_config.settings_data.db_host == "localhost"


def test_settings_data_db_port(app_config):
    assert app_config.settings_data.db_port == 5432


def test_settings_data_db_database(app_config):
    assert app_config.settings_data.db_database == "warriorfit_db"


def test_settings_data_db_credentials(app_config):
    assert app_config.settings_data.db_username == "wf_user"
    assert app_config.settings_data.db_password == "secret"


def test_settings_data_unit(app_config):
    assert app_config.settings_data.own_unit == "Alpha"


def test_settings_data_hr_url(app_config):
    assert app_config.settings_data.hr_url == "https://hr.example.com/api"


def test_settings_data_hr_api_key(app_config):
    assert app_config.settings_data.hr_api_key == "hr-key-123"


def test_settings_data_mail_server_type(app_config):
    assert isinstance(app_config.settings_data.mail_server, SmtpConfig)


def test_settings_data_mail_server_host(app_config):
    assert app_config.settings_data.mail_server.host == "smtp.example.com"


def test_settings_data_mail_server_tls(app_config):
    assert app_config.settings_data.mail_server.use_tls is True


# ---------------------------------------------------------------------------
# Properties delegate to settings_data
# ---------------------------------------------------------------------------


def test_property_hr_url(app_config):
    assert app_config.hr_url == "https://hr.example.com/api"


def test_property_hr_api_key(app_config):
    assert app_config.hr_api_key == "hr-key-123"


def test_property_own_unit(app_config):
    assert app_config.own_unit == "Alpha"


def test_property_mail_server(app_config):
    assert app_config.mail_server.host == "smtp.example.com"


def test_property_pdf_output_path(app_config):
    assert app_config.pdf_output_path == "/tmp/wf_pdf"


# ---------------------------------------------------------------------------
# Version tuple
# ---------------------------------------------------------------------------


def test_version_is_tuple_of_three(app_config):
    assert isinstance(app_config.version, tuple)
    assert len(app_config.version) == 3


def test_version_status(app_config):
    status, *_ = app_config.version
    assert status == "stable"


def test_version_number(app_config):
    _, version_num, *_ = app_config.version
    assert version_num == "2.0.0"


def test_version_date(app_config):
    *_, date = app_config.version
    assert date == "2026-03-23"


# ---------------------------------------------------------------------------
# config property returns the DB engine
# ---------------------------------------------------------------------------


def test_config_property_returns_engine(app_config):
    assert app_config.config is not None


# ---------------------------------------------------------------------------
# Environment-based config path selection
# ---------------------------------------------------------------------------


def test_development_env_uses_dev_config():
    from warriorfit.config.appliccation_config import ApplicationConfig

    with (
        patch.dict(os.environ, {"APP_ENV": "development"}, clear=False),
        patch.object(ApplicationConfig, "_load_yaml_file", return_value=MINIMAL_CONFIG),
        patch.object(
            ApplicationConfig, "_load_version_yaml_file", return_value=MINIMAL_VERSION
        ),
        patch(
            "warriorfit.config.appliccation_config.create_async_engine",
            return_value=MagicMock(),
        ),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        cfg = ApplicationConfig()

    assert "config_dev.yml" in str(cfg.config_path)


def test_production_env_missing_secret_key_raises():
    from warriorfit.config.appliccation_config import ApplicationConfig

    env = {k: v for k, v in os.environ.items() if k != "WF_SECRET_KEY"}
    env["APP_ENV"] = "production"

    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(KeyError):
            ApplicationConfig()


def test_production_env_with_secret_key_and_config_override(tmp_path):
    from warriorfit.config.appliccation_config import ApplicationConfig

    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump(MINIMAL_CONFIG), encoding="utf-8")
    version_file = tmp_path / "version.yaml"
    version_file.write_text(yaml.dump(MINIMAL_VERSION), encoding="utf-8")

    _real_open = io.open

    def fake_open(path, *args, **kwargs):
        target = version_file if "version" in str(path) else config_file
        return _real_open(target, *args, **kwargs)

    with (
        patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "WF_SECRET_KEY": "supersecret",
                "APP_CONFIG_PATH": str(config_file),
            },
            clear=False,
        ),
        patch("builtins.open", side_effect=fake_open),
        patch(
            "warriorfit.config.appliccation_config.create_async_engine",
            return_value=MagicMock(),
        ),
        patch.object(ApplicationConfig, "_ensure_directory", side_effect=lambda p: p),
    ):
        cfg = ApplicationConfig()

    assert cfg.settings_data.db_host == "localhost"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# _ensure_directory
# ---------------------------------------------------------------------------


def test_ensure_directory_creates_missing_path(tmp_path):
    from warriorfit.config.appliccation_config import ApplicationConfig

    new_dir = tmp_path / "sub" / "dir"
    assert not new_dir.exists()
    result = ApplicationConfig._ensure_directory(str(new_dir))
    assert Path(result).exists()


def test_ensure_directory_is_idempotent_on_existing_path(tmp_path):
    from warriorfit.config.appliccation_config import ApplicationConfig

    result = ApplicationConfig._ensure_directory(str(tmp_path))
    assert Path(result).exists()


# ---------------------------------------------------------------------------
# save_config writes correct YAML
# ---------------------------------------------------------------------------


def test_save_config_writes_yaml(app_config, tmp_path):
    output_file = tmp_path / "saved_config.yml"
    app_config.config_path = output_file

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

    app_config.save_config(new_settings)

    saved = yaml.safe_load(output_file.read_text(encoding="utf-8"))
    assert saved["db"]["host"] == "db.new"
    assert saved["db"]["database"] == "new_db"
    assert saved["unit"]["name"] == "Bravo"
    assert saved["hr"]["url"] == "https://hr.new/api"
    assert saved["mail"]["host"] == "mail.new"
    assert saved["path"]["pdf_path"] == "/tmp/new_pdf"


# ---------------------------------------------------------------------------
# SettingsData helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "host,db,user,pwd,expected",
    [
        ("h", "d", "u", "p", True),
        ("", "d", "u", "p", False),
        ("h", "", "u", "p", False),
        ("h", "d", "", "p", False),
        ("h", "d", "u", "", False),
    ],
)
def test_settings_data_has_database_config(host, db, user, pwd, expected):
    sd = SettingsData(db_host=host, db_database=db, db_username=user, db_password=pwd)
    assert sd.has_database_config() is expected


@pytest.mark.parametrize(
    "url,api_key,expected",
    [
        ("https://hr.example.com", "key", True),
        ("", "key", False),
        ("https://hr.example.com", "", False),
    ],
)
def test_settings_data_has_hr_config(url, api_key, expected):
    sd = SettingsData(hr_url=url, hr_api_key=api_key)
    assert sd.has_hr_config() is expected
