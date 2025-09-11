import logging
import platform
import shutil
from pathlib import Path


class Configuration:
    """
    Handles configuration-related operations such as validating configuration file presence,
    creating necessary directories, and copying default configuration files. The class is
    platform-sensitive and caters to both Windows and Linux environments. It logs messages
    at various levels to track operations and errors.

    :ivar __logger: Logger instance used for logging information and errors specific to
        configuration operations.
    :type __logger: logging.Logger
    """

    __logger = logging.getLogger(__name__)

    @classmethod
    def configuration_files_check(cls):
        """
        Checks and ensures the necessary configuration files and directories are present.
        Performs operations for creating and copying missing configuration files based
        on the detected operating system.

        :return: None
        :rtype: None
        """
        system_name = platform.system()
        if not system_name:
            cls.__logger.error(f"Unsupported platform: {system_name}")
            return
        cls.log_message(f"Running on {system_name}", "info")

        base_path, config_path, src_path = cls.get_paths(system_name)
        if not base_path.exists():
            if not cls.create_directories(base_path):
                cls.log_message(
                    "Error creating directories. Please check the permissions.",
                    "error",
                )
                return
            else:
                cls.copy_configuration_file(src_path, config_path)

    @classmethod
    def get_paths(cls, system_name):
        """
        Determines and retrieves file paths based on the provided operating system name.

        This class method returns three specific paths: the base path where the application
        data is located, the path to the configuration file relative to the base path, and
        a source path for the configuration file. The method supports two operating systems:
        Windows and Linux. If the system name is unrecognized, it returns None for all paths.

        :param system_name: Name of the operating system, used to determine the file paths.
        :type system_name: str
        :return: A tuple of three paths: the base path, the configuration file path, and
            the source configuration file path. If the operating system name is unrecognized,
            all paths will be None.
        :rtype: tuple[Optional[Path], Optional[Path], Optional[Path]]
        """
        if system_name == "Windows":
            base_path = Path("C:\\ProgramData\\fitnesstests")
        elif system_name == "Linux":
            base_path = Path.home() / "configurations"
        else:
            return None, None, None

        config_path = base_path / "configurations" / "config.yml"
        src_path = Path("src/configurations/config.yml")
        return base_path, config_path, src_path

    @classmethod
    def log_message(cls, message, level):
        """
        Logs a message at a specified log level using the class's logger.

        This class method provides a way to log messages at specified log levels, such as
        'info' or 'error', using the internal logger of the class. It forwards the message
        to the appropriate logging method based on the given level.

        :param message: The message that needs to be logged.
        :type message: str
        :param level: The severity level at which the message will be logged. Supported
            values include 'info' and 'error'.
        :type level: str
        :return: None
        :rtype: None
        """
        if level == "info":
            cls.__logger.info(message)
        elif level == "error":
            cls.__logger.error(message)

    @classmethod
    def create_directories(cls, base_path):
        """
        Creates necessary directories under the specified base path, including `configurations`,
        `photos`, and `pdf` folders. If directories already exist, it will not create duplicates.
        Logs an error message in case of failures during the directory creation process.

        :param base_path: The base path under which the directories will be created.
        :type base_path: pathlib.Path
        :return: True if all directories were created successfully or already exist,
                 False if an error occurred during the process.
        :rtype: bool
        """
        try:
            Path(base_path / "configurations").mkdir(parents=True, exist_ok=True)
            Path(base_path / "pdf").mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            cls.log_message(f"Error creating directories at {base_path}: {e}", "error")
            return False

    @classmethod
    def copy_configuration_file(cls, src_path, dest_path):
        """
        Copies a configuration file from the source path to the destination path. This method ensures the configuration file
        is transferred securely while logging relevant information or errors for tracing. In case of a failure like the
        source file being missing or encountering an unexpected error during the copy process, an appropriate message
        is logged. The process uses `shutil.copy` for file copying.

        :param src_path: Path to the source configuration file.
        :type src_path: str
        :param dest_path: Path to the destination where the configuration file should be copied.
        :type dest_path: str
        :return: None
        :rtype: None
        :raises FileNotFoundError: If the source configuration file is not found.
        :raises Exception: If any unexpected error occurs during the file copy.
        """
        try:
            shutil.copy(src_path, dest_path)
            cls.log_message(
                f"Configuration file copied from {src_path} to {dest_path}",
                "info",
            )
        except FileNotFoundError:
            cls.log_message(
                f"Source configuration file not found at {src_path}. Please check the source path.",
                "error",
            )
        except Exception as e:
            cls.log_message(
                f"Unexpected error while copying configuration file: {e}",
                "error",
            )
