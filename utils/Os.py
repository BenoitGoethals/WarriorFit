from pathlib import Path
from typing import Any
from pythonping import ping

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
    def is_alive(host):
        response = ping(host, count=2, timeout=1)
        return response.success()
