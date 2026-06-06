import logging
import os
import ssl
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from warriorfit.config.settings_data import SettingsData
from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.logic.singleton import Singleton


class ApplicationConfig(metaclass=Singleton):
    """
    Manages the application's configuration, including loading, saving, and settings management.

    This class is responsible for the initialization and management of the application's configuration,
    including database settings, paths, and other application-specific parameters. It supports environment-specific
    configuration files and ensures directory structures are created if they do not exist.

    :ivar config_path: The path to the primary configuration file.
    :type config_path: Path
    :ivar config_path_version: The path to the version-specific configuration file.
    :type config_path_version: Path
    :ivar config: The loaded configuration database connection object. Accessing it requires `load_config()` to be called first.
    :type config: Any
    :ivar settings_data: The loaded application-specific settings data object.
    :type settings_data: SettingsData
    :ivar version: A tuple containing the version status, version number, and release date of the application.
    :type version: tuple[str, str, str]
    :ivar pdf_output_path: The directory path for PDF file outputs, as defined in the configuration.
    :type pdf_output_path: str
    :ivar hr_url: The URL for the human resources API, as defined in the configuration.
    :type hr_url: str
    :ivar hr_api_key: The API key for accessing the human resources API.
    :type hr_api_key: str
    :ivar own_unit: The name of the organization's unit, as defined in the configuration.
    :type own_unit: str
    :ivar mail_server: The SMTP configuration for email communication.
    :type mail_server: SmtpConfig
    """

    def __init__(self, config_path: str = "warriorfit/config/config.yml") -> None:
        """
        Initialize the application configuration.

        :param config_path: Path to the configuration file.
        """
        env = os.getenv("APP_ENV", "development")
        resolved_path: str | Path = config_path

        if env in ("production", "test"):
            secret_key = os.environ["WF_SECRET_KEY"]
            os.environ["SHINY_DEV_MODE"] = "false"
            if secret_key is None or secret_key == "":
                logging.error("WF_SECRET_KEY environment variable is not set")
                raise ValueError("WF_SECRET_KEY environment variable is not set")
            # Allow explicit override (e.g. local scripts targeting a specific DB)
            config_override = os.getenv("APP_CONFIG_PATH")
            if config_override:
                resolved_path = Path(config_override)
            else:
                # Running in Docker container — config must be mounted at /etc/WarriorFit/config.yml
                resolved_path = Path("/etc/WarriorFit/config.yml")
        elif env == "development":
            resolved_path = "warriorfit/config/config_dev.yml"

        self.config_path: Path = self._get_project_root() / resolved_path
        self.config_path_version: Path = self._get_project_root() / "version.yaml"
        self._settings_data: SettingsData | None = None
        self.__config_db: AsyncEngine | None = None

        self.__version: tuple[str, str, str] | None = None
        self.__gdpr: dict[str, int] = {
            "fitness_retention_days": 1825,
            "audit_retention_days": 365,
            "hr_message_retention_days": 90,
        }
        # Broker outbox tunables; values can be overridden in the YAML's `broker:` block.
        self.__broker: dict[str, int] = {
            "poll_interval_s": 5,
            "batch_size": 5,
            "max_attempts": 10,
            "base_backoff_s": 5,
            "max_backoff_s": 600,
        }
        self.__broker_alert_email: str = ""
        self.load_config()

    @property
    def config(self) -> AsyncEngine:
        if not self.__config_db:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__config_db

    @property
    def settings_data(self) -> SettingsData | None:
        return self._settings_data

    @property
    def version(self) -> tuple[str, str, str] | None:
        return self.__version

    @property
    def pdf_output_path(self) -> str:
        assert self._settings_data is not None
        if not self._settings_data.pdf_path:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.pdf_path

    @property
    def hr_url(self) -> str:
        assert self._settings_data is not None
        if not self._settings_data.hr_url:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.hr_url

    @property
    def hr_api_key(self) -> str:
        assert self._settings_data is not None
        if not self._settings_data.hr_api_key:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.hr_api_key

    @property
    def own_unit(self) -> str:
        assert self._settings_data is not None
        if not self._settings_data.own_unit:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.own_unit

    @property
    def gdpr_retention(self) -> dict[str, int]:
        return dict(self.__gdpr)

    # ---- Broker tunables (read by warriorfit/mom/broker.py) ----
    @property
    def broker_poll_interval_s(self) -> int:
        return int(self.__broker["poll_interval_s"])

    @property
    def broker_batch_size(self) -> int:
        return int(self.__broker["batch_size"])

    @property
    def broker_max_attempts(self) -> int:
        return int(self.__broker["max_attempts"])

    @property
    def broker_base_backoff_s(self) -> int:
        return int(self.__broker["base_backoff_s"])

    @property
    def broker_max_backoff_s(self) -> int:
        return int(self.__broker["max_backoff_s"])

    @property
    def broker_alert_email(self) -> str:
        return self.__broker_alert_email

    @property
    def mail_server(self) -> SmtpConfig:
        assert self._settings_data is not None
        if not self._settings_data.mail_server:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.mail_server

    @staticmethod
    def _get_project_root() -> Path:
        """
        Get the project root directory by searching for marker files.
        """
        current_path = Path(__file__).resolve().parent
        while current_path != Path(current_path.root):
            if any(
                (current_path / marker).exists()
                for marker in ["pyproject.toml", "requirements.txt", ".env"]
            ):
                return current_path
            current_path = current_path.parent
        return Path(__file__).resolve().parent

    def load_config(self) -> None:
        """
        Load the application configuration from the YAML file.
        """
        config = self._load_yaml_file()
        version_config = self._load_version_yaml_file()
        if not config:
            raise ValueError(f"Configuration file is empty or not found: {self.config_path}")

        self._settings_data = SettingsData(
            db_host=config["db"]["host"],
            db_port=config["db"]["port"],
            db_database=config["db"]["database"],
            db_username=config["db"]["username"],
            db_password=config["db"]["password"],
            db_ssl=config["db"].get("ssl", "prefer"),
            db_ssl_root_cert=config["db"].get("ssl_root_cert", ""),
            pdf_path=self._ensure_directory(config["path"]["pdf_path"]),
            own_unit=config["unit"]["name"],
            mail_server=SmtpConfig(**config["mail"]),
            hr_url=config["hr"]["url"],
            hr_api_key=config["hr"].get("api_key", ""),
        )

        self.__version = (
            config["version"]["status"],
            version_config["version"],
            version_config["date"],
        )

        gdpr_cfg = config.get("gdpr") or {}
        for key in self.__gdpr:
            if key in gdpr_cfg:
                self.__gdpr[key] = int(gdpr_cfg[key])

        broker_cfg = config.get("broker") or {}
        for key in self.__broker:
            if key in broker_cfg:
                self.__broker[key] = int(broker_cfg[key])
        self.__broker_alert_email = str(broker_cfg.get("alert_email") or "")

        self.__config_db = self._setup_database_connection()

    def _load_yaml_file(self) -> Any:
        """
        Load YAML data from the configuration file.
        """
        try:
            with open(self.config_path, encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}") from None
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {error}") from error

    def _load_version_yaml_file(self) -> Any:
        """
        Load YAML data from the configuration file.
        """
        try:
            with open(self.config_path_version, encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"version file not found: {self.config_path}") from None
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {error}") from error

    @staticmethod
    def _ensure_directory(path: str) -> str:
        """
        Ensure the directory exists, creating it if necessary.
        """
        directory = Path(path)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
        return str(directory)

    def _setup_database_connection(self) -> AsyncEngine:
        """
        Set up the database connection using SQLAlchemy.
        """
        assert self._settings_data is not None
        connect_args: dict[str, Any] = {}
        ssl_arg = self._build_db_ssl(self._settings_data)
        if ssl_arg is not None:
            connect_args["ssl"] = ssl_arg
        return create_async_engine(
            url=f"postgresql+asyncpg://{self._settings_data.db_username}:{self._settings_data.db_password}@"
            f"{self._settings_data.db_host}:{self._settings_data.db_port}/{self._settings_data.db_database}",
            echo=False,
            future=True,
            pool_size=20,
            max_overflow=30,
            pool_recycle=3600,
            pool_timeout=30,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

    @staticmethod
    def _build_db_ssl(settings: SettingsData) -> Any:
        mode = (settings.db_ssl or "prefer").lower()
        if mode == "disable":
            return False
        if mode in {"verify-ca", "verify-full"}:
            cafile = settings.db_ssl_root_cert or None
            if cafile and not Path(cafile).is_file():
                raise FileNotFoundError(
                    f"db.ssl_root_cert points to '{cafile}', but no such file exists. "
                    f"Mount the CA certificate into the container or clear db.ssl_root_cert "
                    f"to use the system trust store."
                )
            ctx = ssl.create_default_context(cafile=cafile)
            if mode == "verify-ca":
                ctx.check_hostname = False
            return ctx
        if mode in {"allow", "prefer", "require"}:
            return mode
        raise ValueError(f"Unsupported db.ssl mode: {settings.db_ssl}")

    def save_config(self, config: SettingsData) -> None:
        """
        Save the updated configuration back to the YAML file.
        """
        assert config.mail_server is not None
        config_dict = {
            "db": {
                "database": config.db_database,
                "host": config.db_host,
                "password": config.db_password,
                "port": config.db_port,
                "username": config.db_username,
                "ssl": config.db_ssl,
                "ssl_root_cert": config.db_ssl_root_cert,
            },
            "hr": {"url": config.hr_url, "api_key": config.hr_api_key},
            "mail": {
                "host": config.mail_server.host,
                "password": config.mail_server.password,
                "port": config.mail_server.port,
                "sender": config.mail_server.sender,
                "sender_email": config.mail_server.sender_email,
                "use_ssl": config.mail_server.use_ssl,
                "use_tls": config.mail_server.use_tls,
                "username": config.mail_server.username,
            },
            "path": {"pdf_path": config.pdf_path},
            "unit": {"name": config.own_unit},
            "version": (
                {"number": self.__version[0], "status": self.__version[1]} if self.__version else {}
            ),
        }
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(config_dict, file, default_flow_style=False, sort_keys=False)
