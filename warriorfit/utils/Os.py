from pathlib import Path
from typing import Any
from pythonping import ping
import socket


class Os:

    @staticmethod
    def get_project_root() -> Path | None | Any:
        """
        Returns the project root as a Path object. The project root is determined
        by searching for markers like 'pyproject.toml', 'requirements.txt', or '.env'.
        If none of these markers are found, None is returned.
        """
        current_dir = Path(__file__).resolve()
        while (
            current_dir != current_dir.root
        ):  # Repeat until reaching the root directory
            if any(
                (current_dir / marker).exists()
                for marker in ["pyproject.toml", "requirements.txt", ".env"]
            ):
                return current_dir
            current_dir = current_dir.parent  # Move one directory up
        return None

    @staticmethod
    def is_alive(host)-> bool:
        try:
            response = ping(host, count=2, timeout=1)
        except (socket.gaierror, RuntimeError):
            return False

        return response.success()
    
    
    @staticmethod
    def what_is_my_ip() -> str:
        """
        Returns the local IP address of the machine.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            raise Exception(f"Failed to get IP address: {str(e)}")



