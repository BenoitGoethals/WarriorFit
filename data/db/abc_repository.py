import logging
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from config.appliccation_config import ApplicationConfig
from data.db.db_model import AuditLog
from services.be_mil_service import BEMILService
from utils.Os import Os


class ABCRepository:

    def __init__(self):
        # Configure logging

        self.setup_logger()
        self._be_mil_service = BEMILService()

        logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
        self.__logger = logging.getLogger(__name__)
        async_engine = ApplicationConfig().config
        if async_engine is None:
            self.__logger.error(
                "Database configuration not found. Please check your configuration file."
            )
            raise ValueError(
                "Database configuration not found. Please check your configuration file."
            )
        self.SessionLocal = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )


    @staticmethod
    def setup_logger():
        """
        Sets up logging by adding a console handler and file handler.
        Both handlers will log messages at the informational level and above.
        """
        # Create logger
        logger = logging.getLogger()  # Root logger
        logger.setLevel(logging.INFO)  # Set global logging level
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

        # Create a formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Ensure logs directory exists
        project_root = Os.get_project_root()
        if project_root:
            log_dir = project_root / "logs"
            log_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist

            # File handler -> Logs to a file
            file_handler = logging.FileHandler(
                log_dir / "application_db.log", mode="a"
            )  # Append mode
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            # Add file handler to the root logger
            if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
                logger.addHandler(file_handler)

        # Console handler -> Logs to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Add console handler to the root logger
        if not any(
                isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
                for h in logger.handlers
        ):
            logger.addHandler(console_handler)


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
                self.__logger.info("Database is operational.")
                return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database connection error: {e}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error while checking database: {e}")
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
                res = result.unique().scalars().all()
                if not res:
                    self.__logger.info(
                        "No entities found. Please check your database and try again."
                    )
                    return None
                return res
        except SQLAlchemyError as e:
            self.__logger.error(f"SQLAlchemy error fetching {log_entity_name}: {e}")
            return None
        except Exception as e:
            self.__logger.error(f"Unexpected error fetching {log_entity_name}: {e}")
            return None

        # Security

    async def create_audit_log(
            self,
            user_id: int,
            action: str,
            details: dict = None,
            ip_address: str = None,

    ):

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )

        async with self.SessionLocal() as session:
            try:
                async with session.begin():
                    session.add(audit_log)
                    await session.commit()
                    await session.refresh(audit_log)

                return audit_log

            except Exception as e:

                self.__logger.error(f"Failed to deactivate subscriptions: {e}")

    async def get_all_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[AuditLog]:
        """
        Returns all AuditLog entries ordered by created_at desc.
        Optional pagination via limit/offset.
        """
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)

        async with self.SessionLocal() as session:
            try:
                result = await session.execute(stmt)
                logs = result.scalars().all()
                return list(logs)
            except Exception as e:
                self.__logger.error(f"get_all_audit_logs failed: {e}")
                return []

