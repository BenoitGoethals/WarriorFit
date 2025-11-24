from pathlib import Path
from typing import Any
import yaml
from sqlalchemy.ext.asyncio import create_async_engine

from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.logic.singleton import Singleton


class ApplicationConfig(metaclass=Singleton):
    __config= None
    __pdf_path=None
    __own_unit=None
    __mail_server=None


    def __init__(self, config_path:str="warriorfit/config/config.yml"):
        """
        Initializes the application configuration with a specified path.

        :param config_path: Optional path to the configuration file.
        """

        self.config_path:Path = self.__get_project_root().joinpath(Path(config_path))
        self.load_config()


    @property
    def config(self):
        """
        Returns the loaded application configuration.

        :return: The application configuration dictionary.
        """

        if self.__config is None:
            raise ValueError("Configuration not loaded. Please call load_config() first.")
        return self.__config

    @property
    def pdf_output_path(self):

        if self.__pdf_path is None:
            raise ValueError("Configuration not loaded. Please call load_config() first.")
        return self.__pdf_path


    @property
    def own_unit(self)->str:

        if self.__own_unit is None:
            raise ValueError("Configuration not loaded. Please call load_config() first.")
        return self.__own_unit

    @property
    def mail_server(self)->SmtpConfig:
        if self.__mail_server is None:
            raise ValueError("Configuration not loaded. Please call load_config() first.")
        return self.__mail_server

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

    def load_config(self):
        """
        Loads the application configuration from the specified path.
        """
        # Placeholder for loading logic
        print(f"Loading configuration from {self.config_path}")
        config=self.__load_yaml_file()
        if not config:
            raise ValueError(f"Configuration file is empty or not found: {self.config_path}")
        self.__pdf_path = config["path"]["pdf_path"]
        self.__own_unit = config["unit"]["name"]
        self.__mail_server= SmtpConfig(host=config["mail"]["host"],
                                       port=config["mail"]["port"],
                                       username=config["mail"]["username"],
                                       password=config["mail"]["password"],
                                       use_tls=config["mail"]["use_tls"],
                                       use_ssl=config["mail"]["use_ssl"],
                                       sender_email=config["mail"]["sender_email"] )
        self.__config = self.__setup_connection_from_yaml(config=config)
        return config

    def __load_yaml_file(self)->Any:
        """Helper method to load YAML data from a given file."""
        try:
            print(self.config_path.absolute())
            with open(self.config_path.absolute(), "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path.absolute()}")
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {self.config_path}, Error: {error}")


    def __setup_connection_from_yaml(self,config):

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

    def save_config(self, config):
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)




