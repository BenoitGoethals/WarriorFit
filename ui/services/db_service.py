import logging
from datetime import datetime
from typing import List, Optional, Any, Coroutine

from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import User, Role, TestSession
import bcrypt
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import joinedload  # add selectin_polymorphic
from sqlalchemy.orm import selectinload, selectin_polymorphic

from ui.config.appliccation_config import ApplicationConfig
from logic.singleton import Singleton
from data.db.db_model import (
    AuditLog,
    User,
    TestSession,
    FitnessTest,
    PhefTest,
    FunctionalTest,
    CombatTestParatrooper,
    CombatSwimmingTest,
)
from utils.Os import Os


class DBService(metaclass=Singleton):
    NO_ENTITY_FOUND_MSG = "No {entity} found."

    def __init__(self, file_name: str = None):
        """
        Initializes the database session manager with the provided configuration.

        The constructor ensures that the database can be configured properly using the specified
        configuration file. It sets up logging for the SQLAlchemy engine to suppress unnecessary
        logging at the error level. The async session maker is configured to interact with the
        database. If the database configuration cannot be loaded, the initialization process will
        raise an exception and provide an appropriate error message.

        :param file_name: Name of the configuration file to load. If not specified,
            defaults will be applied to locate the configuration.
        :type file_name: str or None
        :raises ValueError: If the database configuration is missing or cannot be loaded
        """
        # Configure logging
        self.setup_logger()

        logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
        self.__logger = logging.getLogger(__name__)
        async_engine = ApplicationConfig(file_name).config
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

    async def add_user(self, user: User) -> Optional[User]:

        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(user)
                await session.refresh(user)
                return user
        except IntegrityError as e:
            self.__logger.error(
                f"Integrity error adding user {user.username}: {str(e)}"
            )
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error adding user {user.username}: {str(e)}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Fetches a user from the database by their username.

        :param username: The username of the user to fetch.
        :type username: str
        :return: User object if found, otherwise None.
        :rtype: Optional[User]
        """
        query = select(User).where(User.username == username)
        results = await self.fetch_and_log(query, "user")
        return results[0] if results else None

    async def get_all_users(self) -> List[User]:
        """
        Fetches all users from the database.

        :return: A list of User objects.
        :rtype: List[User]
        """
        query = select(User)
        results = await self.fetch_and_log(query, "users")
        return results if results else []

    async def update_user(self, id: int, user: User) -> User | None:
        """
        Updates an existing user in the database.

        :param id: The ID of the user to update.
        :type id: int
        :param user: The User object containing updated information.
        :type user: User
        :return: The updated User object if successful, otherwise None.
        :rtype: Optional[User]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_user = await session.get(User, id)
                    if not existing_user:
                        self.__logger.error(f"User with ID {id} not found.")
                        return None

                    # Update fields
                    existing_user.username = user.username
                    existing_user.password_hash = user.password_hash
                    existing_user.email = user.email
                    existing_user.role = user.role

                    await session.flush()  # Ensure changes are applied
                    await session.refresh(existing_user)  # Refresh to get updated data
                    return existing_user

        except IntegrityError as e:
            self.__logger.error(f"Integrity error updating user {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error updating user {id}: {str(e)}")
            return None

    # Security

    async def create_audit_log(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None,
    ):

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
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

    async def delete_all_users(self):
        """
        Deletes all users from the database.

        :return: None
        """
        query = delete(User)
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    await session.execute(query)
                    await session.commit()
            self.__logger.info("All users deleted successfully.")
        except SQLAlchemyError as e:
            self.__logger.error(f"Error deleting all users: {e}")
        except Exception as e:
            self.__logger.error(f"Unexpected error deleting all users: {e}")

    async def check_user(self, user_name: str, plain_password: str) -> bool:
        """
        Securely checks if the provided username and password match an entry in the database.

        :param user_name: The username to verify.
        :param plain_password: The plain-text password to verify.
        :return: True if the username and password are valid; otherwise, False.
        """
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.username == user_name)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self.__logger.info(f"User '{user_name}' not found.")
                    return False
                password_matches = bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    user.password_hash.encode("utf-8"),
                )
                if not password_matches:
                    self.__logger.info("Password mismatch.")
                    return False
                self.__logger.info(f"User '{user_name}' authenticated successfully.")
                return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error in check_user: {e}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error in check_user: {e}")
            return False

    async def cleanup(self):
        pass

    async def add_test_session(self, test_session: TestSession) -> Optional[Any]:
        """
        Adds a test session to the database.

        :param test_session: The test session object to be added.
        :type test_session: Any
        :return: The added test session object if successful, otherwise None.
        :rtype: Optional[Any]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(test_session)
                await session.refresh(test_session)
                return test_session
        except IntegrityError as e:
            self.__logger.error(f"Integrity error adding test session: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error adding test session: {str(e)}")
            return None

    async def get_all_fitness_tests_from_test_session(
        self, test_session_id: int
    ) -> Optional[List[FitnessTest]]:
        """
        Fetches all fitness tests associated with a specific test session.

        :param test_session_id: The ID of the test session.
        :type test_session_id: int
        :return: A list of FitnessTest objects if found, otherwise None.
        :rtype: Optional[List[FitnessTest]]
        """
        async with self.SessionLocal() as session:
            async with session.begin():
                query = (
                    select(FitnessTest)
                    .join(TestSession.fitness_tests)
                    .where(TestSession.id == test_session_id)
                    .execution_options(populate_existing=True)
                )
                results = await session.execute(query)
                tests = results.scalars().all()
                # Explicitly load relationships if needed
                for test in tests:
                    await session.refresh(test)
                return list(tests) if tests else None

    async def update_test_session(self, test_session: TestSession):
        """
        Updates an existing test session in the database.

        :param test_session: The test session object to be updated.
        :type test_session: TestSession
        :return: The updated test session object if successful, otherwise None.
        :rtype: Optional[TestSession]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    merged_session = await session.merge(test_session)
                    await session.flush()
                    await session.refresh(merged_session)
                    # Make a copy of the data before session closes
                    return merged_session
        except IntegrityError as e:
            self.__logger.error(f"Integrity error updating test session: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error updating test session: {str(e)}")
            return None

    async def add_fitness_test_to_TestSession(
        self, test_session_id: int, fitness_test: FitnessTest
    ) -> type[TestSession] | None:
        """
        Adds a fitness test to an existing test session in the database.

        :param test_session_id: The ID of the test session to which the fitness test will be added.
        :type test_session_id: int
        :param fitness_test: The fitness test object to be added.
        :type fitness_test: FitnessTest
        :return: The updated TestSession object if successful, otherwise None.
        :rtype: Optional[TestSession]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    # First add the fitness test
                    session.add(fitness_test)
                    await session.flush()  # Ensure fitness_test has an ID

                    # Then get the test session with relationships loaded
                    test_session = await session.get(
                        TestSession,
                        test_session_id,
                        options=[joinedload(TestSession.fitness_tests)],
                    )

                    if not test_session:
                        self.__logger.error(
                            f"Test session with ID {test_session_id} not found."
                        )
                        return None

                    test_session.fitness_tests.append(fitness_test)
                    await session.flush()

                    # Refresh inside the transaction
                    await session.refresh(test_session)
                    return test_session

        except IntegrityError as e:
            self.__logger.error(f"Integrity error adding fitness test: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error adding fitness test: {str(e)}")
            return None

    async def get_all_test_sessions(self)-> List[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        query = select(TestSession)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_type_fitnessTest(self,typetest:TypeFitnessTest) -> List[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        query = select(TestSession).where(TestSession.type_test==typetest)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def delete_all_test_sessions(self):
        query = delete(TestSession)
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    await session.execute(query)
                    await session.commit()
            self.__logger.info("All TestSession deleted successfully.")
        except SQLAlchemyError as e:
            self.__logger.error(f"Error deleting all TestSession: {e}")
        except Exception as e:
            self.__logger.error(f"Unexpected error deleting all TestSession: {e}")

    async def get_all_fitness_tests_that_passed_from_year(
        self, year: int
    ) -> Optional[List[FitnessTest]]:
        """
        Retrieves all passed fitness tests from test sessions for a specific year.

        :param year: The year to filter test sessions by
        :type year: int
        :return: List of passed FitnessTest objects if found, otherwise None
        :rtype: Optional[List[FitnessTest]]
        """
        return await self.get_all_fitness_tests_that_passed_or_not_from_year(year, True)

    async def get_all_fitness_tests_that_not_passed_from_year(
        self, year: int
    ) -> Optional[List[FitnessTest]]:
        """
        Retrieves all not passed fitness tests from test sessions for a specific year.

        :param year: The year to filter test sessions by
        :type year: int
        :return: List of not passed FitnessTest objects if found, otherwise None
        :rtype: Optional[List[FitnessTest]]
        """
        return await self.get_all_fitness_tests_that_passed_or_not_from_year(
            year, False
        )

    async def get_all_fitness_tests_that_passed_or_not_from_year(
        self, year: int, passed: bool
    ) -> Optional[List[FitnessTest]]:
        """
        Retrieves all passed fitness tests from test sessions for a specific year.

        :param year: The year to filter test sessions by
        :type year: int
        :return: List of passed FitnessTest objects if found, otherwise None
        :rtype: Optional[List[FitnessTest]]
        """
        try:
            async with self.SessionLocal() as session:
                query = (
                    select(FitnessTest)
                    .join(TestSession.fitness_tests)
                    .where(
                        TestSession.datetime_start.between(
                            datetime(year, 1, 1), datetime(year, 12, 31, 23, 59, 59)
                        ),
                        FitnessTest.passed == passed,
                    )
                )
                result = await session.execute(query)
                tests = result.scalars().all()
                return list(tests) if tests else None
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error fetching passed fitness tests for year {year}: {str(e)}"
            )
            return None
        except Exception as e:
            self.__logger.error(
                f"Unexpected error fetching passed fitness tests for year {year}: {str(e)}"
            )
            return None

    async def delete_user(self, id):
        """
        Deletes a user by ID from the database.

        :param id: The ID of the user to delete.
        :type id: int
        :return: True if the user was deleted successfully, otherwise False.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(User).where(User.id == id)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self.__logger.error(f"No user found with ID {id}.")
                        return False
                    await session.commit()
            self.__logger.info(f"User with ID {id} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error deleting user with ID {id}: {str(e)}")
            return False
        except Exception as e:
            self.__logger.error(
                f"Unexpected error deleting user with ID {id}: {str(e)}"
            )
            return False

    async def get_upcoming_test_sessions(self, count: int = 5) -> List[TestSession]:
        """
        Fetches upcoming test sessions from the database ordered by start date.
        Only returns sessions that start in the future or today.

        :param count: Number of upcoming test sessions to return (default: 5)
        :type count: int
        :return: A list of upcoming test session objects ordered by start date
        :rtype: List[TestSession]
        """
        try:
            current_datetime = datetime.now()
            query = (
                select(TestSession)
                .where(TestSession.datetime_start >= current_datetime)
                .order_by(TestSession.datetime_start)
                .limit(count)
            )
            results = await self.fetch_and_log(query, "upcoming test sessions")
            return results if results else []

        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error fetching upcoming test sessions: {str(e)}"
            )
            return []
        except Exception as e:
            self.__logger.error(
                f"Unexpected error fetching upcoming test sessions: {str(e)}"
            )
            return []

    async def get_test_session_by_id(self, session_id: int) -> Optional[TestSession]:
        """
        Retrieves a test session by its ID.

        :param session_id: The ID of the test session to retrieve
        :type session_id: int
        :return: TestSession object if found, otherwise None
        :rtype: Optional[TestSession]
        """
        try:
            async with self.SessionLocal() as session:
                query = (
                    select(TestSession)
                    .where(TestSession.id == session_id)
                    .options(
                        # Load the collection via select-in and include subclass columns
                        selectinload(TestSession.fitness_tests).selectin_polymorphic(
                            [
                                PhefTest,
                                FunctionalTest,
                                CombatTestParatrooper,
                                CombatSwimmingTest,
                            ]
                        )
                    )
                )
                result = await session.execute(query)
                # When using eager load on a collection, the result must be uniqued
                test_session = result.unique().scalar_one_or_none()
                return test_session
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error retrieving test session {session_id}: {str(e)}"
            )
            return None

    async def delete_test_session(self, session_id: int) -> bool:
        """
        Deletes a test session by its ID.

        :param session_id: The ID of the test session to delete
        :type session_id: int
        :return: True if deletion was successful, False otherwise
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(TestSession).where(TestSession.id == session_id)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self.__logger.error(
                            f"No test session found with ID {session_id}"
                        )
                        return False
                    return True
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error deleting test session {session_id}: {str(e)}"
            )
            return False

    async def get_all_fitness_tests(self) -> list[FitnessTest]:
        """
        Fetches all fitness tests.

        :return: A list of FitnessTest objects (base or subtype instances).
        """
        query = select(FitnessTest)
        results = await self.fetch_and_log(query, "fitness tests")
        return results if results else []

    async def get_all_fitness_tests_full(self) -> list[FitnessTest]:
        """
        Fetches all fitness tests with:
        - Polymorphic loading of concrete subtypes
        - Related TestSession objects

        :return: A list of FitnessTest objects with related data.
        """
        try:
            async with self.SessionLocal() as session:
                # Load related sessions and ensure polymorphic subtypes are populated
                query = select(FitnessTest).options(
                    joinedload(FitnessTest.test_sessions),
                    selectin_polymorphic(FitnessTest),
                )
                result = await session.execute(query)
                tests = result.unique().scalars().all()
                return list(tests) if tests else []
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error fetching all fitness tests (full): {str(e)}"
            )
            return []
        except Exception as e:
            self.__logger.error(
                f"Unexpected error fetching all fitness tests (full): {str(e)}"
            )
            return []

    async def get_all_phef(self, session_id: int) -> List[PhefTest]:
        """
        Fetch all PhefTest entities with their related TestSession objects.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    query = (
                        select(TestSession)
                        .where(TestSession.id == session_id)
                        .options(selectinload(TestSession.fitness_tests))
                    )
                    result = await session.execute(query)
                    test_session = result.unique().scalar_one_or_none()

                    if test_session:
                        # Create a list of PhefTests while the session is still active
                        phef_tests = [
                            test for test in test_session.fitness_tests
                            if isinstance(test, PhefTest)
                        ]
                        # Ensure all necessary data is loaded
                        for test in phef_tests:
                            await session.refresh(test)
                        return phef_tests
                    return []
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error fetching PHEF tests: {str(e)}")
            return []

    async def get_all_combat_test(self, session_id: int) -> List[CombatTestParatrooper]:
        """
        Fetch all PhefTest entities with their related TestSession objects.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    query = (
                        select(TestSession)
                        .where(TestSession.id == session_id)
                        .options(selectinload(TestSession.fitness_tests))
                    )
                    result = await session.execute(query)
                    test_session = result.unique().scalar_one_or_none()

                    if test_session:
                        # Create a list of PhefTests while the session is still active
                        tests = [
                            test for test in test_session.fitness_tests
                            if isinstance(test, CombatTestParatrooper)
                        ]
                        # Ensure all necessary data is loaded
                        for test in tests:
                            await session.refresh(test)
                        return tests
                    return []
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error fetching Combat tests: {str(e)}")
            return []

    async def delete_fitness_test_from_test_session(
        self, test_session_id: int, fitness_test_id: int
    ) -> bool:
        """
        Deletes a specific FitnessTest from a TestSession by removing the association and deleting the FitnessTest.

        :param test_session_id: The ID of the TestSession.
        :param fitness_test_id: The ID of the FitnessTest to be deleted.
        :return: True if deletion succeeded, False otherwise.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    # Load the TestSession with related fitness_tests
                    test_session = await session.get(
                        TestSession,
                        test_session_id,
                        options=[joinedload(TestSession.fitness_tests)],
                    )
                    if not test_session:
                        self.__logger.error(
                            f"TestSession with ID {test_session_id} not found."
                        )
                        return False

                    fitness_test = await session.get(FitnessTest, fitness_test_id)
                    if not fitness_test:
                        self.__logger.error(
                            f"FitnessTest with ID {fitness_test_id} not found."
                        )
                        return False

                    if fitness_test in test_session.fitness_tests:
                        test_session.fitness_tests.remove(fitness_test)
                        await session.flush()
                    else:
                        self.__logger.error(
                            f"FitnessTest {fitness_test_id} not in TestSession {test_session_id}"
                        )
                        return False

                    # Delete the FitnessTest itself
                    await session.delete(fitness_test)
                    await session.flush()
                    await session.refresh(test_session)
                    return True
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error deleting FitnessTest {fitness_test_id} from TestSession {test_session_id}: {str(e)}"
            )
            return False
        except Exception as e:
            self.__logger.error(
                f"Unexpected error deleting FitnessTest {fitness_test_id} from TestSession {test_session_id}: {str(e)}"
            )
            return False

    async def update_fitness_test(
        self, fitness_test_id: int, updated_fitness_test: FitnessTest
    ) -> type[FitnessTest] | None:
        """
        Updates an existing FitnessTest, handling polymorphic subclasses.

        :param fitness_test_id: ID of the FitnessTest to update.
        :param updated_fitness_test: FitnessTest or its subclass instance with updated data.
        :return: The updated FitnessTest if successful, otherwise None.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    # Load with polymorphic identity (all columns)
                    fitness_test = await session.get(
                        FitnessTest,
                        fitness_test_id,
                        options=[
                            selectin_polymorphic(
                                FitnessTest,
                                [
                                    PhefTest,
                                    FunctionalTest,
                                    CombatTestParatrooper,
                                    CombatSwimmingTest,
                                ],
                            )
                        ],
                    )
                    if not fitness_test:
                        self.__logger.error(
                            f"FitnessTest with ID {fitness_test_id} not found."
                        )
                        return None

                    # Copy all matching attributes, including polymorphic fields
                    for key in updated_fitness_test.__mapper__.columns.keys():
                        if key != "id":
                            setattr(
                                fitness_test, key, getattr(updated_fitness_test, key)
                            )

                    await session.flush()
                    await session.refresh(fitness_test)
                    return fitness_test
        except IntegrityError as e:
            self.__logger.error(
                f"Integrity error updating FitnessTest {fitness_test_id}: {str(e)}"
            )
            return None
        except SQLAlchemyError as e:
            self.__logger.error(
                f"Database error updating FitnessTest {fitness_test_id}: {str(e)}"
            )
            return None
        except Exception as e:
            self.__logger.error(
                f"Unexpected error updating FitnessTest {fitness_test_id}: {str(e)}"
            )
            return None

    async def serial_exists(self,serial:str) -> bool:
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.serial_number == serial)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self.__logger.info(f"User '{serial}' not found.")
                    return False
                return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error in check_user: {e}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error in check_user: {e}")
            return False

    async def delete_user_by_serial(self, selected_serial):
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(User).where(User.serial_number == selected_serial)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                       self.__logger.error(f"No user found with serial {selected_serial}.")
                       return False
                    return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error deleting user with serial {selected_serial}: {str(e)}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error deleting user with serial {selected_serial}: {str(e)}")
            return False

    async def update_user_by_serial(self, user):


        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_user = (await session.execute(
                        select(User).where(User.serial_number == user.serial_number)
                    )).scalar_one_or_none()
                    if not existing_user:
                        self.__logger.error(f"User with serial number {user.serial_number} not found.")
                        return None

                    # Update fields

                    existing_user.username = user.username
                    existing_user.password_hash = user.password_hash
                    existing_user.email = user.email
                    existing_user.role = user.role
                    existing_user.serial_number = user.serial_number

                    await session.flush()  # Ensure changes are applied
                    await session.refresh(existing_user)  # Refresh to get updated data
                    return existing_user

        except IntegrityError as e:
            self.__logger.error(f"Integrity error updating user {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error updating user {id}: {str(e)}")
            return None

    async def get_all_pti(self)->list[User]:
        query = select(User).where(User.role ==Role.PTI)
        results = await self.fetch_and_log(query, "users")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test_from_a_test_session(self, type_test,session_id:int)->list[FitnessTest]:
        query = select(TestSession).where(TestSession.type_test==type_test ).where(TestSession.id==session_id)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []


