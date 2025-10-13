# Python
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import pandas as pd

from data.db.db_model import User, Role
from security.auth_service import Auth
from services.service_user import UserService


@dataclass
class UserForm:
    serial: str
    username: str
    password: str
    email: str
    role: str


class UserManagementController:
    def __init__(self,):
        # If your DBService requires a config path, adjust here
        self._service =  UserService()
        self.selected_user=None

    @staticmethod
    def role_choices() -> List[str]:
        try:
            return [r.value for r in Role]
        except Exception:
            return [str(r) for r in Role]

    async def list_users_df(self) -> pd.DataFrame:
        users = await self._service.get_all_users()
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

    async def validate(self, form: UserForm, *, is_update: bool) -> Tuple[bool, str]:
        req = ["serial", "username", "password", "email", "role"]
        for f in req:
            if not getattr(form, f, "").strip():
                return False, f"Field '{f}' is required."
        if "@" not in form.email or "." not in form.email.split("@")[-1]:
            return False, "Invalid email address."
        exists = await self._service.serial_exists(form.serial.strip())
        mail_unique = await self._service.user_mail_exist(form.email)
        user_name_exist = await self._service.get_user_by_username(form.username)
        if is_update:
            if form.serial.strip() != (self.selected_user.serial or "") and exists:
                return False, f"Serial '{form.serial}' already exists."

            if form.email.strip() !=(self.selected_user.email or "") and mail_unique:
                return (
                    False,
                    f"User with email '{form.email}' already exists."
                )
            if form.username.strip() !=(self.selected_user.username or "") and user_name_exist:
                return (
                    False,
                    f"User with username '{form.username}' already exists."
                )
        else:
            if exists:
                return False, f"Serial '{form.serial}' already exists."
            if mail_unique:
                return (
                    False,
                    f"User with email '{form.email}' already exists."
                )
            if user_name_exist:
                return (
                    False,
                    f"User with username '{form.username}' already exists."
                )

        return True, "OK"

    def set_selected_user(self, user:UserForm):
        self.selected_user=user


    async def create_user(self, form: UserForm) -> Optional[User]:
        user = User()
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        user.is_active = True
        return await self._service.add_user(user)

    async def update_user(self, user_id: int, form: UserForm) -> bool:
        user = User()
        user.id = user_id
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        updated = await self._service.update_user(user_id, user)
        return bool(updated)

    async def delete_user_by_serial(self, serial: str) -> bool:
        return await self._service.delete_user_by_serial(serial)