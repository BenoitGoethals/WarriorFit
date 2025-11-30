from pathlib import Path
from typing import Any
import yaml
from sqlalchemy.ext.asyncio import create_async_engine
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
        self.config_path = self._get_project_root() / config_path
        self.__config = None
        self.__pdf_path = None
        self.__own_unit = None
        self.__mail_server = None
        self.__hr_url = None
        self.__version = None
        self.load_config()

    @property
    def config(self):
        if not self.__config:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__config

    @property
    def version(self) -> tuple[str, str]:
        return self.__version

    @property
    def pdf_output_path(self):
        if not self.__pdf_path:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__pdf_path

    @property
    def hr_url(self) -> str:
        if not self.__hr_url:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__hr_url

    @property
    def own_unit(self) -> str:
        if not self.__own_unit:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__own_unit

    @property
    def mail_server(self) -> SmtpConfig:
        if not self.__mail_server:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self.__mail_server

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

        self.__pdf_path = self._ensure_directory(config["path"]["pdf_path"])
        self.__own_unit = config["unit"]["name"]
        self.__version = (config["version"]["number"], config["version"]["status"])
        self.__hr_url = config["hr"]["url"]
        self.__mail_server = SmtpConfig(**config["mail"])
        self.__config = self._setup_database_connection(config)

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

    @staticmethod
    def _setup_database_connection(config: dict):
        """
        Set up the database connection using SQLAlchemy.
        """
        return create_async_engine(
            url=f"postgresql+asyncpg://{config['db']['username']}:{config['db']['password']}@"
                f"{config['db']['host']}:{config['db']['port']}/{config['db']['database']}",
            echo=False,
            future=True,
            pool_size=20,
            max_overflow=30,
            pool_recycle=3600,
            pool_timeout=30,
        )

    def save_config(self, config: dict):
        """
        Save the updated configuration back to the YAML file.
        """
        with open(self.config_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False)
