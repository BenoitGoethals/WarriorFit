from typing import Any, Dict, List

import pandas as pd

from warriorfit.data.model.db_model import User
from warriorfit.services.service_user import UserService


class AuditLogEventsController:
    """
    Manages audit log events and provides functionality to retrieve audit logs in
    a structured format.

    This class interacts with user-related services to fetch audit log data and
    user information asynchronously. It is designed to correlate and present audit
    events in a tabular format for analysis and reporting.

    """

    def __init__(
        self,
        user_service: UserService = None,
    ) -> None:
        self._service = user_service if user_service is not None else UserService()

    async def list_audit_logs_df(self) -> pd.DataFrame:
        """
        Generates a DataFrame containing audit logs with details about users' actions,
        including user, action, details, IP address, and creation timestamp. This
        method retrieves audit logs and user data asynchronously, then matches user
        records to logs to compile a comprehensive DataFrame.

        :return: A pandas DataFrame containing audit logs, with columns for
                 user, action, details, IP address, and creation time. If no logs
                 are available, an empty DataFrame is returned with predefined
                 column headers.
        :rtype: pd.DataFrame
        """
        logs: List[Any] = await self._service.get_audit_logs()
        users: List[User] = await self._service.get_all_users()

        if not logs:
            return pd.DataFrame(columns=["User", "Action", "Details", "IP", "Created"])
        rows: List[Dict[str, Any]] = []
        for log_entry in logs:
            user = next(
                (user for user in users if user.id == getattr(log_entry, "user_id", None)), None
            )
            if user is not None:
                rows.append(
                    {
                        "User": user.username,
                        "Action": getattr(log_entry, "action", ""),
                        "Details": getattr(log_entry, "details", ""),
                        "IP": getattr(log_entry, "ip_address", ""),
                        "Created": getattr(log_entry, "created_at", ""),
                    }
                )

        return pd.DataFrame(rows).sort_values(by="Created", ascending=False)
