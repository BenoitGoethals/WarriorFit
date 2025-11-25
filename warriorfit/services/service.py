import logging
from abc import ABC
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.db.user_repository import UserRepository
from warriorfit.services.military_service import MilitaryService
from warriorfit.ui.user_store import UserStore
from warriorfit.utils.Os import Os


class Service(ABC):
    NO_ENTITY_FOUND_MSG = "No {entity} found."

    def __init__(self, file_name: str = None):
        self._user_repo = UserRepository()
        self._be_mil_service = MilitaryService()

        self._logger = logging.getLogger(__name__)
        async_engine = ApplicationConfig().config
        if async_engine is None:
            self._logger.error(
                "Database configuration not found. Please check your configuration file."
            )
            raise ValueError(
                "Database configuration not found. Please check your configuration file."
            )
        self.SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )

    async def add_audit_log(self, details, action):
        user_id = getattr(UserStore.get_user(), "id", None)
        return await self._user_repo.create_audit_log(
            user_id=user_id,
            details=details,
            ip_address=Os.what_is_my_ip(),
            action=action,
        )

    async def get_audit_logs(self):
        return await self._user_repo.get_audit_logs()
