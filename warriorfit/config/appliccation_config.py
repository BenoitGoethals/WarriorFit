from pathlib import Path
from typing import Any
import yaml
from sqlalchemy.ext.asyncio import create_async_engine
import os
from warriorfit.config.settings_data import SettingsData
from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.logic.singleton import Singleton


class ApplicationConfig(metaclass=Singleton):
    """
    Singleton class to manage application configuration.
    """

    def __init__(self, config_path: str = "warriorfit/config/config.yml"):
        """
        Initialize the application configuration.

        :param config_path: Path to the configuration file.
        """
        ENV = os.getenv('APP_ENV', 'development')

        if ENV == 'production':
           config_path = "warriorfit/config/config_prod.yml"
        elif ENV == 'development':
            config_path = "warriorfit/config/config_dev.yml"
        elif ENV == 'test':
            config_path = "warriorfit/config/config_test.yml"

        self.config_path = self._get_project_root() / config_path
        self._settings_data = None
        self.__config_db = None


        self.__version = None
        self.load_config()

    @property
    def config(self):
        if not self.__config_db:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__config_db

    @property
    def settings_data(self):
        return self._settings_data

    @property
    def version(self) -> tuple[str, str]:
        return self.__version

    @property
    def pdf_output_path(self):
        if not self._settings_data.pdf_path:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.pdf_path

    @property
    def hr_url(self) -> str:
        if not self._settings_data.hr_url:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.hr_url

    @property
    def own_unit(self) -> str:
        if not self._settings_data.own_unit:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.own_unit

    @property
    def mail_server(self) -> SmtpConfig:
        if not self._settings_data.mail_server:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._settings_data.mail_server

    @staticmethod
    def _get_project_root() -> Path:
        """
        Get the project root directory by searching for marker files.
        """
        current_path = Path(__file__).resolve().parent
        while current_path != current_path.root:
            if any((current_path / marker).exists() for marker in ["pyproject.toml", "requirements.txt", ".env"]):
                return current_path
            current_path = current_path.parent
        return Path(__file__).resolve().parent

    def load_config(self):
        """
        Load the application configuration from the YAML file.
        """
        config = self._load_yaml_file()
        if not config:
            raise ValueError(f"Configuration file is empty or not found: {self.config_path}")
        
        self._settings_data = SettingsData(db_host=config['db']['host'], db_port=config['db']['port'],
                            db_database=config['db']['database'], db_username=config['db']['username'],
                            db_password=config['db']['password'],pdf_path=self._ensure_directory(config["path"]["pdf_path"])
                            ,own_unit=config["unit"]["name"],mail_server=SmtpConfig(**config["mail"]),
                                           hr_url=config["hr"]["url"]
                                           )
   
        self.__version = (config["version"]["number"], config["version"]["status"])


        self.__config_db = self._setup_database_connection()

    def _load_yaml_file(self) -> Any:
        """
        Load YAML data from the configuration file.
        """
        try:
            with open(self.config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {error}")

    @staticmethod
    def _ensure_directory(path: str) -> str:
        """
        Ensure the directory exists, creating it if necessary.
        """
        directory = Path(path)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
        return str(directory)


    def _setup_database_connection(self):
        """
        Set up the database connection using SQLAlchemy.
        """
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
        )

    def save_config(self, config: SettingsData):
        """
        Save the updated configuration back to the YAML file.
        """
        config_dict = {
            'db': {
                'database': config.db_database,
                'host': config.db_host,
                'password': config.db_password,
                'port': config.db_port,
                'username': config.db_username
            },
            'hr': {
                'url': config.hr_url
            },
            'mail': {
                'host': config.mail_server.host,
                'password': config.mail_server.password,
                'port': config.mail_server.port,
                'sender': config.mail_server.sender,
                'sender_email': config.mail_server.sender_email,
                'use_ssl': config.mail_server.use_ssl,
                'use_tls': config.mail_server.use_tls,
                'username': config.mail_server.username
            },
            'path': {
                'pdf_path': config.pdf_path
            },
            'unit': {
                'name': config.own_unit
            },
            'version': {
                'number': self.version[0],
                'status': self.version[1]
            }
        }
        with open(self.config_path, "w") as file:
            yaml.dump(config_dict, file, default_flow_style=False, sort_keys=False)
