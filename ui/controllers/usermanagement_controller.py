# Python
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import pandas as pd

from data.db.db_model import User, Role
from security.auth_service import Auth
from services.db_service import DBService



@dataclass
class UserForm:
    serial: str
    username: str
    password: str
    email: str
    role: str


class UserManagementController:
    def __init__(self, db: Optional[DBService] = None):
        # If your DBService requires a config path, adjust here
        self.db = db or DBService()

    @staticmethod
    def role_choices() -> List[str]:
        try:
            return [r.value for r in Role]
        except Exception:
            return [str(r) for r in Role]

    async def list_users_df(self) -> pd.DataFrame:
        users = await self.db.get_all_users()
        return pd.DataFrame([
            {
                "Serial": u.serial_number,
                "ID": u.id,
                "Username": u.username,
                "Email": u.email,
                "Role": str(u.role),
                "Active": bool(u.is_active),
                "Password": u.password_hash,
                "Created": getattr(u.created_at, "date", lambda: "")(),
            }
            for u in users
        ])

    async def validate(self, form: UserForm, *, is_update: bool, current_serial: Optional[str] = None) -> Tuple[bool, str]:
        req = ["serial", "username", "password", "email", "role"]
        for f in req:
            if not getattr(form, f, "").strip():
                return False, f"Field '{f}' is required."
        if "@" not in form.email or "." not in form.email.split("@")[-1]:
            return False, "Invalid email address."
        exists = await self.db.serial_exists(form.serial.strip())
        mail_unique = await self.db.user_mail_exist(form.email)
        if is_update:
            if form.serial.strip() != (current_serial or "") and exists:
                return False, f"Serial '{form.serial}' already exists."

            if form.email.strip() !=(form.email or "") and mail_unique:
                return (
                    False,
                    f"User with email '{form.email}' already exists."
                )
        else:
            if exists:
                return False, f"Serial '{form.serial}' already exists."
            if mail_unique:
                return (
                    False,
                    f"User with email '{form.email}' already exists."
                )


        return True, "OK"

    async def create_user(self, form: UserForm) -> Optional[User]:
        user = User()
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        user.is_active = True
        return await self.db.add_user(user)

    async def update_user(self, user_id: int, form: UserForm) -> bool:
        user = User()
        user.id = user_id
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        updated = await self.db.update_user(user_id, user)
        return bool(updated)

    async def delete_user_by_serial(self, serial: str) -> bool:
        return await self.db.delete_user_by_serial(serial)