import socket
from pathlib import Path

from pythonping import ping


class Os:
    @staticmethod
    def get_project_root() -> Path | None:
        """
        Returns the project root as a Path object. The project root is determined
        by searching for markers like 'pyproject.toml', 'requirements.txt', or '.env'.
        If none of these markers are found, None is returned.
        """
        current_dir = Path(__file__).resolve().parent
        while current_dir != current_dir.parent:
            if any(
                (current_dir / marker).exists()
                for marker in ["pyproject.toml", "requirements.txt", ".env"]
            ):
                return current_dir
            current_dir = current_dir.parent
        return None

    @staticmethod
    def is_alive(host: str) -> bool:
        """
        Checks the reachability of a given host by sending ICMP ping requests.

        This method attempts to ping the specified host using a timeout and a
        fixed number of ping attempts. If the host responds successfully to
        the ping requests, the method returns True. Otherwise, it will return
        False. This is a static utility method, making it suitable for quick
        checks without initializing a class instance.

        :param host: The hostname or IP address of the target to check for reachability.
        :type host: str
        :return: True if the host responds successfully to the ping request,
            False otherwise.
        :rtype: bool
        """
        try:
            response = ping(host, count=2, timeout=1)
        except (socket.gaierror, RuntimeError):
            return False

        return bool(response.success())

    @staticmethod
    def what_is_my_ip() -> str:
        """
        Returns the local IP address of the machine.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip: str = s.getsockname()[0]
            s.close()
            return ip
        except (OSError, socket.error) as e:
            raise OSError(f"Failed to get IP address: {str(e)}")
