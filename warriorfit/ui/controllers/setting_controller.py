# Python
from __future__ import annotations

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.config.settings_data import SettingsData


class SettingsController:
    """
    Handles the loading and saving of application settings.

    This class is responsible for managing the application's configuration settings,
    specifically loading settings from a configuration file or resource and saving
    updated settings. It interacts with an ``ApplicationConfig`` instance to perform
    these operations, and processes various configuration sections such as database,
    paths, units, and display settings.

    """

    def __init__(self, config: ApplicationConfig = None) -> None:
        self._config = config if config is not None else ApplicationConfig()

    def load(self) -> SettingsData:
        """
        Loads configuration settings and maps them to a `SettingsData` object.

        This method reads configuration settings from the application configuration file
        via `self._config` and processes the data to populate a `SettingsData` object.
        It extracts specific fields related to database parameters, file paths,
        unit details, and display preferences.

        :raises KeyError: If an expected key is missing in the configuration dictionary.
        :raises ValueError: If type conversion of a value, like string to integer or
            boolean, fails.

        :return: An instance of `SettingsData` populated with settings data.
        :rtype: SettingsData
        """
        self._config.load_config()
        return self._config.settings_data  # type: ignore[return-value]

    def save(self, data: SettingsData) -> tuple[bool, str]:
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
            self._config.save_config(data)
            self._config.load_config()
            return True, "Configuration saved successfully."
        except (OSError, ValueError, KeyError) as e:
            return False, f"Failed to save configuration: {e}"
