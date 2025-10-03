from pathlib import Path
from typing import Any
import asyncpg
import yaml
from sqlalchemy.ext.asyncio import create_async_engine
from logic.singleton import Singleton


class ApplicationConfig(metaclass=Singleton):
    __config= None

    @property
    def config(self):
        """
        Returns the loaded application configuration.

        :return: The application configuration dictionary.
        """
        if self.__config is None:
            raise ValueError("Configuration not loaded. Please call load_config() first.")
        return self.__config


    def __init__(self, config_path:str="ui/config/config.yml"):
        """
        Initializes the application configuration with a specified path.

        :param config_path: Optional path to the configuration file.
        """
        self.config_path:Path = Path(config_path)
        self.load_config()

    def load_config(self):
        """
        Loads the application configuration from the specified path.
        """
        # Placeholder for loading logic
        print(f"Loading configuration from {self.config_path}")
        config=self.__load_yaml_file()
        if not config:
            raise ValueError(f"Configuration file is empty or not found: {self.config_path}")
        self.__config = self.__setup_connection_from_yaml(config=config)
        return config

    def __load_yaml_file(self)->Any:
        """Helper method to load YAML data from a given file."""
        try:
            print(self.config_path.absolute())
            with open(self.config_path.absolute(), "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing YAML file: {self.config_path}, Error: {error}")


    def __setup_connection_from_yaml(self,config) -> asyncpg.connection:

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



