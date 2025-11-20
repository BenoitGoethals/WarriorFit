from typing import List, Dict, Any
import pandas as pd

from data.db.db_model import User
from services.service_user import UserService


class AuditLogEventsController:
    def __init__(self) -> None:
        self._service = UserService()

    async def list_audit_logs_df(self) -> pd.DataFrame:
        logs: List[Any] = await self._service.get_audit_logs()
        users:List[User] = await self._service.get_all_users()
        
        if not logs:
            return pd.DataFrame(columns=["User", "Action", "Details", "IP", "Created"])
        rows: List[Dict[str, Any]] = []
        for l in logs:
            user = next((user for user in users if user.id == getattr(l, "user_id", None)), None)
            rows.append(
                {
                    "User": user.username,
                    "Action": getattr(l, "action", ""),
                    "Details": getattr(l, "details", ""),
                    "IP": getattr(l, "ip_address", ""),
                    "Created": getattr(l, "created_at", ""),
                }
            )
       
        return pd.DataFrame(rows).sort_values(by="Created", ascending=False)


