"""
User database service class for managing user-related database operations.
"""

from warriorfit.logic.singleton import Singleton
from warriorfit.services.service import Service


class UserService(Service, metaclass=Singleton):
    """
    User database service class for managing user-related database operations.
    """

    def __init__(self):
        super().__init__()

    async def check_user(self, username_login, password_login):
        user = await self._user_repo.get_user_by_username(username_login)
        if user.is_active:
            return user
        return None


    async def get_user_by_username(self, username_login):
        return await self._user_repo.get_user_by_username(username_login)

    async def get_all_users(self):
        return await self._user_repo.get_all_users()

    async def serial_exists(self, param):
        return await self._user_repo.serial_exists(param)

    async def user_mail_exist(self, email):
        return await self._user_repo.user_mail_exist(email)

    async def add_user(self, user):
        user = await self._user_repo.add_user(user)
        if user:
            await self.add_audit_log(
                details=f"User {user.username} added", action="add"
            )
        return user

    async def update_user(self, user_id, user):
        user = await self._user_repo.update_user(user_id, user)
        if user:
            await self.add_audit_log(
                details=f"User {user.username} updated", action="update"
            )
        return user

    async def delete_user_by_serial(self, serial):
        is_deleted = await self._user_repo.delete_user_by_serial(serial)
        if is_deleted:
            await self.add_audit_log(details=f"User {serial} deleted", action="delete")
        return is_deleted

    async def get_user_by_id(self, id):
        return await self._user_repo.get_user_by_id(id)
