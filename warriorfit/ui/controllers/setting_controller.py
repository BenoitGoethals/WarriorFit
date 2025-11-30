# Python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from warriorfit.config.appliccation_config import ApplicationConfig


@dataclass
class SettingsData:
    db_host: str = ""
    db_port: int = 5432
    db_database: str = ""
    db_username: str = ""
    db_password: str = ""
    pdf_path: str = ""
    own_unit: str = ""
    darkmode: bool = False


class SettingsController:
    """
    Handles the loading and saving of application settings.

    This class is responsible for managing the application's configuration settings,
    specifically loading settings from a configuration file or resource and saving
    updated settings. It interacts with an ``ApplicationConfig`` instance to perform
    these operations, and processes various configuration sections such as database,
    paths, units, and display settings.

    :ivar app_cfg: An instance of the ApplicationConfig class used to read and write
        configuration files.
    :type app_cfg: ApplicationConfig
    """

    def __init__(self) -> None:
        self.app_cfg = ApplicationConfig()

    def load(self) -> SettingsData:
        """
        Loads configuration settings and maps them to a `SettingsData` object.

        This method reads configuration settings from the application configuration file
        via `self.app_cfg` and processes the data to populate a `SettingsData` object.
        It extracts specific fields related to database parameters, file paths,
        unit details, and display preferences.

        :raises KeyError: If an expected key is missing in the configuration dictionary.
        :raises ValueError: If type conversion of a value, like string to integer or
            boolean, fails.

        :return: An instance of `SettingsData` populated with settings data.
        :rtype: SettingsData
        """
        cfg = self.app_cfg.load_config() or {}

        db = cfg.get("db", {})
        path = cfg.get("path", {})
        unit = cfg.get("unit", {})
        display = cfg.get("display", {})

        return SettingsData(
            db_host=db.get("host", "") or "",
            db_port=int(db.get("port", 5432) or 5432),
            db_database=db.get("database", "") or "",
            db_username=db.get("username", "") or "",
            db_password=db.get("password", "") or "",
            pdf_path=path.get("pdf_path", "") or "",
            own_unit=unit.get("name", "") or "",
            darkmode=bool(display.get("darkmode", False)),
        )

    def save(self, data: SettingsData) -> Tuple[bool, str]:
        """
        Saves the given configuration data to the application configuration.

        :param data: SettingsData object containing the configuration details to be saved.
        :type data: SettingsData
        :returns: A tuple where the first element is a boolean indicating the success of
                  the operation, and the second element is a string providing a success
                  message or an error description.
        :rtype: Tuple[bool, str]
        """
        try:
            cfg: Dict[str, Any] = self.app_cfg.load_config() or {}
            cfg["db"] = {
                "host": data.db_host,
                "port": int(data.db_port or 5432),
                "database": data.db_database,
                "username": data.db_username,
                "password": data.db_password,
            }
            cfg.setdefault("path", {})
            cfg["path"]["pdf_path"] = data.pdf_path

            cfg.setdefault("unit", {})
            cfg["unit"]["name"] = data.own_unit

            cfg.setdefault("display", {})
            cfg["display"]["darkmode"] = bool(data.darkmode)

            self.app_cfg.save_config(cfg)
            return True, "Configuration saved successfully."
        except Exception as e:
            return False, f"Failed to save configuration: {e}"