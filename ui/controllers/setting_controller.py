# Python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from config.appliccation_config import ApplicationConfig


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
    Encapsulates loading and saving of application configuration.
    """

    def __init__(self) -> None:
        self.app_cfg = ApplicationConfig()

    def load(self) -> SettingsData:
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