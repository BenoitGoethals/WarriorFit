from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, selectin_polymorphic, selectinload

from warriorfit.core.role import Role
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    MfftEvalTest,
    PhefTest,
    TestSession,
    User,
)
from warriorfit.data.repositories.abc_repository import ABCRepository

# Concrete polymorphic subtypes of FitnessTest, used wherever a query needs to
# eager-load subclass columns via selectin(_polymorphic).
_FITNESS_TEST_SUBTYPES = [
    PhefTest,
    FunctionalTest,
    CombatTestParatrooper,
    CombatSwimmingTest,
    MfftEvalTest,
]

_T = TypeVar("_T", bound=FitnessTest)


class FitnessTestRepository(ABCRepository):
    def __init__(self, config=None):
        super().__init__(config=config)

    async def _get_subtype_tests_from_session(
        self, test_type: type[_T], session_id: int, current_year: bool
    ) -> list[_T]:
        """Load a single test session and return its fitness tests of ``test_type``.

        Shared implementation behind ``get_all_phef``/``get_all_combat_test``/etc.
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                query = (
                    select(TestSession)
                    .where(TestSession.id == session_id)
                    .options(selectinload(TestSession.fitness_tests))
                )
                if current_year:
                    end, start = await self.running_year()
                    query = query.where(TestSession.datetime_start.between(start, end))
                result = await session.execute(query)
                test_session = result.unique().scalar_one_or_none()
                if not test_session:
                    return []
                tests = [t for t in test_session.fitness_tests if isinstance(t, test_type)]
                # Ensure subclass columns are loaded while the session is open.
                for test in tests:
                    await session.refresh(test)
                return tests
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching %s tests: %s", test_type.__name__, str(e))
            return []

    async def _get_subtype_tests_from_mil(
        self, test_type: type[_T], serial: str, current_year: bool
    ) -> list[_T]:
        """Return all ``test_type`` tests for a service member (serial number).

        Shared implementation behind ``get_all_phef_from_mil``/etc.
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                query = select(test_type).where(FitnessTest.serial_number == serial)
                if current_year:
                    end, start = await self.running_year()
                    query = query.join(FitnessTest.test_sessions).where(  # type: ignore[attr-defined]
                        TestSession.datetime_start.between(start, end)
                    )
                result = await session.execute(query)
                tests = result.scalars().all()
                return list(tests) if tests else []
        except (SQLAlchemyError, Exception) as e:
            self._logger.error(
                "Error fetching %s tests for service member %s: %s",
                test_type.__name__,
                serial,
                str(e),
            )
            return []

    async def add_test_session(self, test_session: TestSession) -> Any | None:
        """
        Adds a test session to the database.

        :param test_session: The test session object to be added.
        :type test_session: Any
        :return: The added test session object if successful, otherwise None.
        :rtype: Optional[Any]
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                session.add(test_session)
                # Flush so the INSERT runs and the instance becomes persistent;
                # otherwise refresh() trips on a pending instance.
                await session.flush()
                await session.refresh(test_session)
                return test_session
        except IntegrityError as e:
            self._logger.error("Integrity error adding test session: %s", str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error adding test session: %s", str(e))
            return None

    async def get_all_fitness_tests_from_test_session(
        self, test_session_id: int
    ) -> list[FitnessTest] | None:
        """
        Fetches all fitness tests associated with a specific test session.

        :param test_session_id: The ID of the test session.
        :type test_session_id: int
        :return: A list of FitnessTest objects if found, otherwise None.
        :rtype: Optional[List[FitnessTest]]
        """
        async with self.SessionLocal() as session, session.begin():
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

    async def update_test_session(self, test_session: TestSession) -> TestSession | None:
        """
        Updates an existing test session in the database.

        :param test_session: The test session object to be updated.
        :type test_session: TestSession
        :return: The updated test session object if successful, otherwise None.
        :rtype: Optional[TestSession]
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                merged_session = await session.merge(test_session)
                await session.flush()
                await session.refresh(merged_session)
                # Make a copy of the data before session closes
                return merged_session
        except IntegrityError as e:
            self._logger.error("Integrity error updating test session: %s", str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error updating test session: %s", str(e))
            return None

    async def add_fitness_test_to_TestSession(
        self, test_session_id: int, fitness_test: FitnessTest
    ) -> TestSession | None:
        """
        Adds a fitness test to an existing test session in the database.

        :param test_session_id: The ID of the test session to which the fitness test will be added.S
        :type test_session_id: int
        :param fitness_test: The fitness test object to be added.
        :type fitness_test: FitnessTest
        :return: The updated TestSession object if successful, otherwise None.
        :rtype: Optional[TestSession]
        """
        try:
            async with self.SessionLocal() as session, session.begin():
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
                    self._logger.error("Test session with ID %d not found.", test_session_id)
                    return None

                test_session.fitness_tests.append(fitness_test)
                await session.flush()

                # Refresh inside the transaction
                await session.refresh(test_session)
                return test_session

        except IntegrityError as e:
            self._logger.error("Integrity error adding fitness test: %s", str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error adding fitness test: %s", str(e))
            return None

    async def get_all_test_sessions(self, this_year: bool = True) -> list[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = select(TestSession).where(TestSession.datetime_start.between(start, end))
        else:
            query = select(TestSession)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_for_a_pti(
        self, serial_number_pti, this_year: bool = True
    ) -> list[TestSession]:
        """
        Fetches all test sessions from the database for a particular PTI..

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = (
                select(TestSession)
                .where(TestSession.serial_number_pti == serial_number_pti)
                .where(TestSession.datetime_start.between(start, end))
            )
        else:
            query = select(TestSession)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test(
        self, typetest: TypeFitnessTest, this_year: bool = True
    ) -> list[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = (
                select(TestSession)
                .where(TestSession.type_test == typetest)
                .where(TestSession.datetime_start.between(start, end))
            )
        else:
            query = select(TestSession).where(TestSession.type_test == typetest)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test_for_service_men(
        self, serial: str, typetest: TypeFitnessTest, this_year: bool = True
    ) -> list[TestSession]:
        """
        Fetches all test sessions of a specific type for a given service member.
        #S
        :param serial: The serial number of the service member
        :param typetest: The type of fitness test to filter by
        :param this_year: If True, only returns sessions from the current year
        :return: A list of matching TestSession objects
        :rtype: List[TestSession]
        """
        try:
            query = (
                select(TestSession)
                .join(TestSession.fitness_tests)
                .where(TestSession.type_test == typetest)
                .where(FitnessTest.serial_number == serial)
                .options(
                    selectinload(TestSession.fitness_tests).selectin_polymorphic(
                        _FITNESS_TEST_SUBTYPES
                    )
                )
            )
            if this_year:
                end, start = await self.running_year()
                query = query.where(TestSession.datetime_start.between(start, end))

            results = await self.fetch_and_log(query, f"test sessions for service member {serial}")
            return results if results else []

        except SQLAlchemyError as e:
            self._logger.error(
                "Database error fetching test sessions for service member %s: %s",
                serial,
                str(e),
            )
            return []

    async def get_all_test_sessions_type_fitnessTest_full(
        self, typetest: TypeFitnessTest, this_year: bool = True
    ) -> list[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        query = (
            select(TestSession)
            .where(TestSession.type_test == typetest)
            .options(
                # Load the collection via select-in and include subclass columns
                selectinload(TestSession.fitness_tests).selectin_polymorphic(_FITNESS_TEST_SUBTYPES)
            )
        )
        if this_year:
            end, start = await self.running_year()
            query = query.where(TestSession.datetime_start.between(start, end))
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def delete_all_test_sessions(self):
        """
        Deletes all records from the TestSession table.

        This method executes a deletion query on the TestSession table, removes
        all records, and commits the transaction. It handles potential exceptions
        arising from database operations and logs the respective outcomes.

        :raises SQLAlchemyError: If an SQLAlchemy-related exception occurs during
                                 query execution or commit.
        :raises Exception: If an unexpected error occurs.
        """
        query = delete(TestSession)
        try:
            async with self.SessionLocal() as session, session.begin():
                await session.execute(query)
                await session.commit()
            self._logger.info("All TestSession deleted successfully.")
        except SQLAlchemyError as e:
            self._logger.error("Error deleting all TestSession: %s", e)

    async def get_all_fitness_tests_that_passed_from_year(
        self, year: int
    ) -> list[FitnessTest] | None:
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
    ) -> list[FitnessTest] | None:
        """
        Retrieves all not passed fitness tests from test sessions for a specific year.

        :param year: The year to filter test sessions by
        :type year: int
        :return: List of not passed FitnessTest objects if found, otherwise None
        :rtype: Optional[List[FitnessTest]]
        """
        return await self.get_all_fitness_tests_that_passed_or_not_from_year(year, False)

    async def get_all_fitness_tests_that_passed_or_not_from_year(
        self, year: int, passed: bool
    ) -> list[FitnessTest] | None:
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
                    )
                )
                result = await session.execute(query)
                tests = result.scalars().all()
                return list(tests) if tests else None
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error fetching passed fitness tests for year %d: %s",
                year,
                str(e),
            )
            return None

    async def get_upcoming_test_sessions(self, count: int = 5) -> list[TestSession]:
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
            results = await self.fetch_and_log(query, "test sessions")
            return results if results else []

        except SQLAlchemyError as e:
            self._logger.error("Database error fetching upcoming test sessions: %s", str(e))
            return []

    async def get_test_session_by_id(self, session_id: int) -> TestSession | None:
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
                            _FITNESS_TEST_SUBTYPES
                        )
                    )
                )
                result = await session.execute(query)
                # When using eager load on a collection, the result must be uniqued
                test_session = result.unique().scalar_one_or_none()
                return test_session
        except SQLAlchemyError as e:
            self._logger.error("Database error retrieving test session %d: %s", session_id, str(e))
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
            async with self.SessionLocal() as session, session.begin():
                query = delete(TestSession).where(TestSession.id == session_id)
                result = await session.execute(query)
                if result.rowcount == 0:
                    self._logger.error("No test session found with ID %d", session_id)
                    return False
                return True
        except SQLAlchemyError as e:
            self._logger.error("Database error deleting test session %d: %s", session_id, str(e))
            return False

    async def get_all_fitness_tests(self, current_year=True) -> list[FitnessTest]:
        """
        Fetches all fitness tests.

        :return: A list of FitnessTest objects (base or subtype instances).
        """

        if current_year:
            end, start = await self.running_year()
            query = (
                select(FitnessTest)
                .join(FitnessTest.test_sessions)  # type: ignore[attr-defined]
                .where(TestSession.datetime_start.between(start, end))
            )
        else:
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
                end, start = await self.running_year()
                query = (
                    select(FitnessTest)
                    .where(TestSession.datetime_start.between(start, end))
                    .options(
                        selectin_polymorphic(FitnessTest, _FITNESS_TEST_SUBTYPES),
                        selectinload(FitnessTest.test_sessions),  # type: ignore[attr-defined]
                    )
                )
                result = await session.execute(query)

                tests = result.unique().scalars().all()
                return list(tests) if tests else []
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching all fitness tests (full): %s", str(e))
            return []

    async def get_all_fitness_tests_full_this_year(self) -> list[FitnessTest]:
        """
        Fetches all fitness tests with:
        - Polymorphic loading of concrete subtypes
        - Related TestSession objects

        :return: A list of FitnessTest objects with related data.
        """
        # Identical to get_all_fitness_tests_full (both scope to the running year).
        return await self.get_all_fitness_tests_full()

    async def get_all_phef(self, session_id: int, current_year=True) -> list[PhefTest]:
        """
        Fetches all PHEF (Physical Health Evaluation Framework) tests associated with a
        specific test session. The method can be filtered to retrieve tests only
        from the current running year. If the session contains related fitness
        tests that are of type `PhefTest`, they are returned as a list.

        :param session_id: The unique identifier of the test session.
        :type session_id: int
        :param current_year: A flag indicating whether to filter tests from the
            current running year (default is True).
        :type current_year: bool, optional
        :return: A list of PHEF tests (`PhefTest`) associated with the specified test session.
                 If no related tests are found or in case of an error, an empty list is returned.
        :rtype: list[PhefTest]
        """
        return await self._get_subtype_tests_from_session(PhefTest, session_id, current_year)

    async def get_all_combat_test(
        self, session_id: int, current_year=True
    ) -> list[CombatTestParatrooper]:
        """
        Fetches all CombatTestParatrooper instances related to a test session.

        This coroutine retrieves all fitness tests of type CombatTestParatrooper associated
        with the specified test session. If `current_year` is True, it only considers sessions
        that occur within the current running year.

        :param session_id: The unique identifier of the test session.
        :type session_id: int
        :param current_year: A flag indicating whether to restrict the query to the current year
            or not. Defaults to True.
        :type current_year: bool
        :return: A list of CombatTestParatrooper instances linked to the test session.
        :rtype: list[CombatTestParatrooper]
        :raises SQLAlchemyError: If a database-related error occurs during the operation.
        """
        return await self._get_subtype_tests_from_session(
            CombatTestParatrooper, session_id, current_year
        )

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
            async with self.SessionLocal() as session, session.begin():
                # Load the TestSession with related fitness_tests
                test_session = await session.get(
                    TestSession,
                    test_session_id,
                    options=[joinedload(TestSession.fitness_tests)],
                )
                if not test_session:
                    self._logger.error("TestSession with ID %d not found.", test_session_id)
                    return False

                fitness_test = await session.get(FitnessTest, fitness_test_id)
                if not fitness_test:
                    self._logger.error("FitnessTest with ID %d not found.", fitness_test_id)
                    return False

                if fitness_test in test_session.fitness_tests:
                    test_session.fitness_tests.remove(fitness_test)
                    await session.flush()
                else:
                    self._logger.error(
                        "FitnessTest %d not in TestSession %d",
                        fitness_test_id,
                        test_session_id,
                    )
                    return False

                # Delete the FitnessTest itself
                await session.delete(fitness_test)
                await session.flush()
                await session.refresh(test_session)
                return True
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error deleting FitnessTest %d from TestSession %d: %s",
                fitness_test_id,
                test_session_id,
                str(e),
            )
            return False

    async def update_fitness_test(
        self, fitness_test_id: int, updated_fitness_test: FitnessTest
    ) -> FitnessTest | None:
        """
        Updates an existing FitnessTest, handling polymorphic subclasses.

        :param fitness_test_id: ID of the FitnessTest to update.
        :param updated_fitness_test: FitnessTest or its subclass instance with updated data.
        :return: The updated FitnessTest if successful, otherwise None.
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                # Load with polymorphic identity (all columns)
                fitness_test = await session.get(
                    FitnessTest,
                    fitness_test_id,
                    options=[selectin_polymorphic(FitnessTest, _FITNESS_TEST_SUBTYPES)],
                )
                if not fitness_test:
                    self._logger.error("FitnessTest with ID %d not found.", fitness_test_id)
                    return None

                # Copy all matching attributes, including polymorphic fields.
                # column.key is the mapped attribute name (str); iterating the
                # ColumnCollection directly would yield Column objects instead.
                for column in updated_fitness_test.__mapper__.columns:
                    if column.key != "id":
                        setattr(fitness_test, column.key, getattr(updated_fitness_test, column.key))

                await session.flush()
                await session.refresh(fitness_test)
                return fitness_test
        except IntegrityError as e:
            self._logger.error(
                "Integrity error updating FitnessTest %d: %s", fitness_test_id, str(e)
            )
            return None
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error updating FitnessTest %d: %s", fitness_test_id, str(e)
            )
            return None

    async def get_all_pti(self) -> list[User]:
        """
        Fetches all users with the role of PTI (Professional Technical Instructor)
        from the database. The method constructs a database query targeting users
        with the PTI role, executes the query asynchronously, and retrieves the
        results. If no users are found, it returns an empty list.

        :raises DatabaseError: Indicates a failure to execute the query or issues
            with the database connection.

        :return: A list of `User` objects with the role of PTI. If no such users
            exist, returns an empty list.
        :rtype: list[User]
        """
        query = select(User).where(User.role == Role.PTI)
        results = await self.fetch_and_log(query, "users")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test_from_a_test_session(
        self, type_test, session_id: int
    ) -> list[FitnessTest]:
        query = (
            select(TestSession)
            .where(TestSession.type_test == type_test)
            .where(TestSession.id == session_id)
        )
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_functional_test(
        self, session_id: int, current_year=True
    ) -> list[FunctionalTest]:
        """
        Fetches all functional tests associated with a given session ID. By default, it fetches tests
        for the current year, unless specified otherwise.

        :param session_id: The unique identifier for the test session.
        :type session_id: int
        :param current_year: A flag indicating whether to filter for the current year's tests
            (default is True). If False, retrieves tests regardless of the year.
        :type current_year: bool
        :return: A list of FunctionalTest objects associated with the specified session ID. If no
            tests are found, an empty list is returned.
        :rtype: list[FunctionalTest]
        :raises SQLAlchemyError: If a database error occurs while fetching the tests.
        """
        return await self._get_subtype_tests_from_session(FunctionalTest, session_id, current_year)

    async def get_all_combat_swimming_test(
        self, session_id: int, current_year=True
    ) -> list[CombatSwimmingTest]:
        """
        Retrieves all combat swimming test records associated with a given session ID. The records can
        be filtered based on whether they belong to the current running year or not. The function
        leverages asynchronous mechanisms to interact with the database and ensures proper management of
        database sessions and transactions. In case no records match the criteria or an error occurs
        during the process, an empty list will be returned.

        :param session_id: The identifier of the test session to query.
        :type session_id: int or str
        :param current_year: A flag indicating whether to filter test sessions for the current year.
        :type current_year: bool, optional
        :return: A list of CombatSwimmingTest instances matching the criteria. Returns an empty list if
            no matching records are found or an error occurs.
        :rtype: list[CombatSwimmingTest]
        """
        return await self._get_subtype_tests_from_session(
            CombatSwimmingTest, session_id, current_year
        )

    async def get_all_phef_from_mil(self, serial, current_year) -> list[PhefTest]:
        """
        Fetch all PHEF tests for a given serial from the database.

        This asynchronous method retrieves PHEF (Pulmonary Health Evaluation Form) tests
        based on the provided serial and the optional current_year flag. If current_year
        is True, it fetches tests within the current year using the `running_year` method
        to calculate the start and end dates. Otherwise, it retrieves all tests matching
        the specific serial number. The method handles both successful retrieval and
        error scenarios, logging any issues encountered during execution.

        :param serial: The serial number to filter PHEF tests.
        :type serial: str
        :param current_year: Flag to indicate whether to filter tests for the current year.
        :type current_year: bool
        :return: A list of PhefTest objects matching the filter criteria or an empty list
            if no matches are found.
        :rtype: List[PhefTest]
        """
        return await self._get_subtype_tests_from_mil(PhefTest, serial, current_year)

    async def get_all_combat_from_mil(
        self, service_number, current_year
    ) -> list[CombatTestParatrooper]:
        """
        Fetch all combat test records tied to a specific service number from the database for
        a given military unit. When the current year is provided, the query is restricted
        to tests conducted during that year. If the year is not provided, all available records
        related to the service number are retrieved. The function also handles any database
        or processing errors gracefully by logging the issue and returning an empty result set.

        :param service_number: The unique identifier for the military service number.
        :type service_number: str

        :param current_year: A flag indicating whether to limit results to the current year.
        :type current_year: bool

        :return: A list of ``CombatTestParatrooper`` instances representing the retrieved tests.
        :rtype: List[CombatTestParatrooper]
        """
        return await self._get_subtype_tests_from_mil(
            CombatTestParatrooper, service_number, current_year
        )

    async def get_all_swim_from_mil(self, service_number, current_year) -> list[CombatSwimmingTest]:
        """
        Fetches all combat swimming tests for a given military service number.

        This asynchronous method retrieves all CombatSwimmingTest entries associated with
        the provided service number. A specific year can also be filtered by providing the
        current year parameter; in this case, the method calculates the start and end of
        the year to limit the query results accordingly.

        :param service_number: Military service number used to retrieve the swimming tests.
        :type service_number: str
        :param current_year: Determines whether to filter tests for the current year. If True,
                             the method filters tests to the present year's timeframe.
        :type current_year: bool
        :return: A list of CombatSwimmingTest objects for the provided service number. If no
                 tests are found, an empty list is returned.
        :rtype: List[CombatSwimmingTest]
        """
        return await self._get_subtype_tests_from_mil(
            CombatSwimmingTest, service_number, current_year
        )

    async def get_all_mfft_eval(
        self, session_id: int, current_year: bool = True
    ) -> list[MfftEvalTest]:
        """
        Fetches all MFFT (Modified Functional Fitness Test) evaluation tests associated with
        a given test session from the database. If `current_year` is True, only considers
        test sessions that fall within the running year.

        :param session_id: The unique identifier of the test session.
        :type session_id: int
        :param current_year: Flag indicating whether to include only test sessions from the
            current year. Defaults to True.
        :type current_year: bool, optional
        :return: A list of MfftEvalTest instances associated with the specified test session.
            Returns an empty list if no matching tests are found.
        :rtype: list[MfftEvalTest]
        """
        return await self._get_subtype_tests_from_session(MfftEvalTest, session_id, current_year)

    async def get_all_mfft_eval_from_mil(
        self, service_number: str, current_year: bool = True
    ) -> list[MfftEvalTest]:
        """
        Fetches all MFFT evaluation tests associated with a given service number. Depending on
        the `current_year` flag, it retrieves tests either from the current year or all available
        tests. The function interacts with the database asynchronously and ensures proper session
        management.

        :param service_number: The unique identifier of the service to fetch MFFT evaluation tests for.
        :param current_year: Boolean flag indicating whether to fetch tests for the current year only.
                             Defaults to True.
        :return: A list of `MfftEvalTest` objects associated with the given service number. Returns
                 an empty list if no tests are found or if an error occurs.
        """
        return await self._get_subtype_tests_from_mil(MfftEvalTest, service_number, current_year)

    async def get_upcoming_session_for_pti(self, serial_number_pti: str) -> Any | None:
        """
        Fetches the upcoming test sessions for a specific PTI (Process Test Identification) based
        on the provided serial number. It retrieves sessions from the database where the start
        datetime is equal to or after the current datetime. Results are filtered and sorted by
        the session start datetime in ascending order.

        :param serial_number_pti: The serial number corresponding to the PTI for which the
            upcoming test sessions are being queried.
        :type serial_number_pti: str
        :return: A list of test session objects that match the criteria or None if an error occurs.
        :rtype: Any | None
        :raises SQLAlchemyError: If there is an error while accessing the database.
        """
        try:
            async with self.SessionLocal() as session:
                current_datetime = datetime.now()
                query = (
                    select(TestSession)
                    .where(TestSession.serial_number_pti == serial_number_pti)
                    .where(TestSession.datetime_start >= current_datetime)
                    .order_by(TestSession.datetime_start)
                )
                result = await session.execute(query)
                return result.scalars().all()

        except SQLAlchemyError as e:
            self._logger.error(
                "Database error fetching upcoming session for PTI %s: %s",
                serial_number_pti,
                str(e),
            )
            return None
