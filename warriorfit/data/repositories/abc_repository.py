import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import AuditLog



class ABCRepository:
    """
    Handles database operations for the application, providing functionality for
    checking database connectivity, fetching and logging entities, managing audit
    logs, and performing other utility operations. The class ensures interaction
    with an asynchronous SQLAlchemy session maker and handles errors gracefully.

    :ivar SessionLocal: SQLAlchemy asynchronous session maker bound to the database
                        engine for managing transactions and queries.
    :type SessionLocal: sqlalchemy.ext.asyncio.async_sessionmaker
    """
    def __init__(self):

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



    async def check_if_db_is_operational(self) -> bool:
        """
        Checks if the database is operational by performing a lightweight query.

        :return: True if the database is operational, otherwise False.
        :rtype: bool
        """
        test_query = select(1)  # Lightweight query to check DB connection
        try:
            async with self.SessionLocal() as session:
                await session.execute(test_query)  # Execute the test query
                self._logger.info("Database is operational.")
                return True
        except SQLAlchemyError as e:
            self._logger.error("Database connection error: %s", e)
            return False


    async def fetch_and_log(self, query, log_entity_name: str):
        """
        Fetches entities from the database using the given query and logs necessary
        information. Ensures error handling for SQLAlchemy-specific errors as well
        as unexpected exceptions. It logs a message if no entities are found and
        returns the fetched results if successful.

        :param query: SQLAlchemy query to be executed for fetching the entities.
        :type query: sqlalchemy.sql.selectable.Select
        :param log_entity_name: Name of the entity to be logged for clarity in error
                                or information messages.
        :type log_entity_name: str
        :return: A list of unique scalar results if entities are found, or None
                 otherwise.
        :rtype: list[Any] | None
        """
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(query)
                res = result.scalars().all()
                if not res:
                    return None
                return res
        except SQLAlchemyError as e:
            self._logger.error("SQLAlchemy error fetching %s: %s", log_entity_name, e)
            return None

        # Security

    async def create_audit_log(
            self,
            user_id: int,
            action: str,
            details: dict|str = None,
            ip_address: str = None,
    ):
        """
        Creates an audit log entry in the database. The function records the provided data
        such as user identifier, action performed, optional details, and the IP address.
        This operation is performed asynchronously, ensuring the audit log is both added
        and refreshed in the database session.
    
        :param user_id: Identifier of the user associated with the action
        :param action: Description of the action performed by the user
        :param details: Optional dictionary containing additional details about the action
        :param ip_address: Optional string containing the IP address associated with the action
        :return: The created audit log entry
        """


        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            created_at=datetime.now(),
        )

        async with self.SessionLocal() as session:
            try:
                session.add(audit_log)
                await session.commit()
                await session.refresh(audit_log)
                return audit_log

            except SQLAlchemyError as e:
                await session.rollback()
                self._logger.error("Failed to create audit log: %s", e)
                return None

    async def get_all_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[AuditLog]:
        """
        Returns all AuditLog entries ordered by created_at desc.
        Optional pagination via limit/offset.
        """
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(stmt)
                logs = result.scalars().all()
                return list(logs)
        except SQLAlchemyError as e:
                self._logger.error("get_all_audit_logs failed: %s", e)
                return []

    async def get_audit_logs(self) -> list[AuditLog]:
        """
        Fetches and returns a list of audit logs from the database. The method performs
        an asynchronous database query to retrieve all available audit log entries. If
        an error occurs during the operation, the method logs it and returns an empty list.

        :raises Exception: If an error occurs during the database operation,
                           it logs the error internally.

        :return: A list of AuditLog objects if the query is successful,
                 otherwise an empty list.
        :rtype: list[AuditLog]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = select(AuditLog)
                    results = await self.fetch_and_log(query, "audit_logs")
                    return results if results else []
        except SQLAlchemyError as e:
            self._logger.error("Error fetching audit logs: %s", e)
            return []

    async def running_year(self) -> tuple[datetime, datetime]:
        now_year = datetime.now().year
        start = datetime(now_year, 1, 1)
        end = datetime(now_year, 12, 31, 23, 59, 59)
        return end, start
