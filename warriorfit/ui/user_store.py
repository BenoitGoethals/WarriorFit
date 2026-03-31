from typing import Optional

from warriorfit.data.model.db_model import User
from warriorfit.logic.singleton import Singleton


class UserStore(metaclass=Singleton):
    __user: Optional[User] = None

    @classmethod
    def set_user(cls, user: Optional[User]) -> None:
        cls.__user = user

    @classmethod
    def get_user(cls) -> Optional[User]:
        return cls.__user

    @classmethod
    def logout(cls) -> None:
        cls.__user = None
