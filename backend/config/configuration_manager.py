import logging
import platform
import sys
from pathlib import Path

import asyncpg.connection
import yaml
from sqlalchemy.ext.asyncio import create_async_engine

from backend.core.singleton import Singleton


class ConfigurationManager(metaclass=Singleton):

    def __init__(self, name: str = None):
        self.__config_path = Path()
        self.__app_config = None
        self.__logger = logging.getLogger(__name__)
        self.__config_db = None
        self.__pdf_path = None
        self.load(name)
        self.__login_use = None
        self.__logger.info("ConfigurationManager initialized successfully.")

    @staticmethod
    def __get_project_root() -> Path:
        current_path = Path(__file__).resolve().parent
        while current_path != current_path.root:
            if any(
                (current_path / marker_file).exists()
                for marker_file in [
                    "pyproject.toml",
                    "requirements.txt",
                    ".env",
                ]
            ):
                return current_path
            current_path = current_path.parent

        # Fallback to the parent of the current file
        return Path(__file__).resolve().parent

    def load(self, file_name: str = None):
        try:
            system_name = platform.system()
            if file_name is not None:
                self.__config_path = Path.joinpath(
                    self.__get_project_root(),
                    "src",
                    "configurations",
                    file_name,
                )
            elif system_name == "Windows":
                logging.info("Running on Windows")
                path = Path("C:\\ProgramData\\fitnesstests")
                self.__config_path = Path.joinpath(path, "configurations", "config.yml")
                if not path.exists() or not self.__config_path.exists():
                    self.__logger.error(
                        f"Configuration file not found in expected Windows locations.{
                            path.absolute()}"
                    )
            elif system_name == "Linux":
                logging.info("Running on Linux")
                self.__config_path = Path.joinpath(
                    Path.home(), "configurations", "config.yml"
                )
                if not self.__config_path.exists():
                    self.__logger.error(
                        f"Configuration file not found in expected Linux location.{
                            self.__config_path.absolute()}"
                    )
            else:
                self.__logger.error(f"Unsupported platform: {system_name}")

            if self.__config_path is None:
                sys.exit("Configuration file not found")
            config = self.__load_configuration()
            logging.info("Application configuration loaded successfully.")
            self.__config_db = self.__setup_connection_from_yaml(config)
            self.__pdf_path = config["path"]["pdf_path"]
            return self

        except Exception as error:
            logging.error(
                f"Unexpected error occurred while loading configuration: {error}"
            )
            sys.exit("Error occurred while loading configuration")

    @staticmethod
    def __setup_connection_from_yaml(config) -> asyncpg.connection:

        return create_async_engine(
            url=f"postgresql+asyncpg://{
                config['db']['username']}:{
                config['db']['password']}@{
                config['db']['host']}:{
                config['db']['port']}/{
                    config['db']['database']}",
            echo=True,  # Set to False for production to reduce excessive logging overhead
            future=True,
            pool_size=20,  # Increase pool size for handling more concurrent requests
            max_overflow=30,  # Allow more connection overflow
            pool_recycle=3600,  # Recycle less often if connections are stable
            pool_timeout=30,  # Increase timeout for waiting connections
        )

    @property
    def config_db(self) -> asyncpg.connection:
        return self.__config_db

    @property
    def config_pdf(self) -> asyncpg.connection:
        return self.__pdf_path

    @staticmethod
    def __load_yaml_file(file_path: Path):
        """Helper method to load YAML data from a given file."""
        try:
            print(file_path.absolute())
            with open(file_path.absolute(), "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {file_path}, Error: {error}")

    def __load_configuration(self):
        """Loads the configuration data."""
        return self.__load_yaml_file(self.__config_path)

    def get_config_value(self, key, default=None):
        config = self.__load_configuration()
        return config.get(key, default)

    @property
    def login_use(self):
        return self.__login_use

    @login_use.setter
    def login_use(self, value):
        self.__login_use = value
