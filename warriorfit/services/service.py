import logging
from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.repositories.user_repository import UserRepository
from warriorfit.services.military_service import MilitaryService
from warriorfit.ui.user_store import UserStore


class Service(ABC):
    """
    Service class to manage interactions with repositories and external services.

    This class provides an interface to manage audit logging, interact with
    repositories, and handle configuration of database sessions. It serves as
    a utility for higher-level application operations.

    :ivar NO_ENTITY_FOUND_MSG: Default message when no relevant entity is found.
    :type NO_ENTITY_FOUND_MSG: str
    """

    NO_ENTITY_FOUND_MSG = "No {entity} found."

    def __init__(
        self,
        user_repository: UserRepository = None,
        military_service: MilitaryService = None,
        config: ApplicationConfig = None,
    ):
        if config is None:
            config = ApplicationConfig()
        self._user_repo = (
            user_repository if user_repository is not None else UserRepository()
        )
        self._be_mil_service = (
            military_service if military_service is not None else MilitaryService()
        )

        self._logger = logging.getLogger(__name__)
        async_engine = config.config
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

    async def add_audit_log(self, details, action, ip_address: str = None):
        """
        Add an entry to the audit log with the provided details and action.

        :param details: Additional information related to the action.
        :type details: str
        :param action: The action performed by the user that is to be logged.
        :type action: str
        :param ip_address: Client IP address. If not provided, defaults to None.
        :type ip_address: str, optional
        :return: A coroutine that resolves once the audit log has been created.
        :rtype: Coroutine
        """
        user_id = getattr(UserStore.get_user(), "id", None)
        return await self._user_repo.create_audit_log(
            user_id=user_id,  # type: ignore[arg-type]
            details=details,
            ip_address=ip_address,
            action=action,
        )

    async def get_audit_logs(self):
        """
        Retrieves audit logs asynchronously.

        This method fetches audit logs from the associated user repository. It is
        designed to work with asynchronous programming.

        :return: A coroutine that resolves to the audit logs fetched from the user
            repository.
        :rtype: Any
        """
        return await self._user_repo.get_audit_logs()
