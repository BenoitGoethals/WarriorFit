"""
User database service class for managing user-related database operations.
"""
from appdirs import user_log_dir

from data.db.user_repository import UserRepository
from logic.singleton import Singleton
from services.service import Service
from utils.Os import Os


class UserService(Service,metaclass=Singleton):
    """
    User database service class for managing user-related database operations.
    """
    def __init__(self):
        super().__init__()

        self._user_repo = UserRepository()


    async def check_user(self, username_login, password_login):
        return await self._user_repo.check_user(username_login, password_login)

    async def get_user_by_username(self, username_login):
        return await self._user_repo.get_user_by_username(username_login)

    async def get_all_users(self):
        return await self._user_repo.get_all_users()

    async def serial_exists(self, param):
        return await self._user_repo.serial_exists(param)

    async def user_mail_exist(self, email):
        return await self._user_repo.user_mail_exist(email)

    async def add_user(self, user):
        return await self._user_repo.add_user(user)

    async def update_user(self, user_id, user):
        return await self._user_repo.update_user(user_id, user)

    async def delete_user_by_serial(self, serial):
        return await self._user_repo.delete_user_by_serial(serial)

    async def add_audit_log(self,user_id,details,action):
        return await self._user_repo.create_audit_log(user_id=user_id,details=details,ip_address=Os.what_is_my_ip(),action=action)






