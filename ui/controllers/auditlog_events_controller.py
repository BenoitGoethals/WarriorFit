from typing import List, Dict, Any
import pandas as pd

from services.service_user import UserService


class AuditLogEventsController:
    def __init__(self) -> None:
        self._service = UserService()

    async def list_audit_logs_df(self) -> pd.DataFrame:
        logs: List[Any] = await self._service.get_audit_logs()
        if not logs:
            return pd.DataFrame(columns=["ID", "User", "Action", "Details", "IP", "Created"])
        rows: List[Dict[str, Any]] = []
        for l in logs:
            user = await self._service.get_user_by_id(getattr(l, "user_id", None))
            rows.append(
                {
                    "ID": getattr(l, "id", None),
                    "User": user.username if user else "",
                    "Action": getattr(l, "action", ""),
                    "Details": getattr(l, "details", ""),
                    "IP": getattr(l, "ip_address", ""),
                    "Created": getattr(l, "created_at", ""),
                }
            )

        return pd.DataFrame(rows)


