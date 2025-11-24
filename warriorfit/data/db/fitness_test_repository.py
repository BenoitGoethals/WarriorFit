import logging
from datetime import datetime
from typing import Optional, Any, List

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload, selectin_polymorphic

from warriorfit.core.role import Role
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.db.abc_repository import ABCRepository
from warriorfit.data.db.db_model import TestSession, FitnessTest, PhefTest, FunctionalTest, CombatTestParatrooper, \
    CombatSwimmingTest, User


class FitnessTestRepository(ABCRepository):
    def __init__(self):
        super().__init__()

        self.__logger = logging.getLogger(__name__)

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

    async def update_test_session(self, test_session: TestSession)->TestSession | None:
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

    async def get_all_test_sessions(self, this_year: bool = True) -> List[TestSession]:
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


    async def get_all_test_sessions_for_a_pti(self,serial_number_pti, this_year: bool = True) -> List[TestSession]:
        """
        Fetches all test sessions from the database for a particular PTI..

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = (select(TestSession)
                     .where(TestSession.serial_number_pti == serial_number_pti)
                     .where(TestSession.datetime_start.between(start, end))
                     .where(TestSession.datetime_start.between(start, end)))
        else:
            query = select(TestSession)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test(self, typetest: TypeFitnessTest, this_year: bool = True) -> List[
        TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = select(TestSession).where(TestSession.type_test == typetest).where(
                TestSession.datetime_start.between(start, end))
        else:
            query = select(TestSession).where(TestSession.type_test == typetest)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test_for_service_men(self, serial: str, typetest: TypeFitnessTest,
                                                                      this_year: bool = True) -> List[TestSession]:
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
            if this_year:
                end, start = await self.running_year()
                query = (
                    select(TestSession)
                    .join(TestSession.fitness_tests)
                    .where(TestSession.type_test == typetest)
                    .where(TestSession.datetime_start.between(start, end))
                    .where(FitnessTest.serial_number == serial)
                    .options(
                        selectinload(TestSession.fitness_tests).selectin_polymorphic([
                            PhefTest,
                            FunctionalTest,
                            CombatTestParatrooper,
                            CombatSwimmingTest
                        ])
                    )
                )
            else:
                query = (
                    select(TestSession)
                    .join(TestSession.fitness_tests)
                    .where(TestSession.type_test == typetest)
                    .where(FitnessTest.serial_number == serial)
                    .options(
                        selectinload(TestSession.fitness_tests).selectin_polymorphic([
                            PhefTest,
                            FunctionalTest,
                            CombatTestParatrooper,
                            CombatSwimmingTest
                        ])
                    )
                )

            results = await self.fetch_and_log(query, f"test sessions for service member {serial}")
            return results if results else []

        except SQLAlchemyError as e:
            self.__logger.error(f"Database error fetching test sessions for service member {serial}: {str(e)}")
            return []
        except Exception as e:
            self.__logger.error(f"Unexpected error fetching test sessions for service member {serial}: {str(e)}")
            return []

    async def get_all_test_sessions_type_fitnessTest_full(self, typetest: TypeFitnessTest, this_year: bool = True) -> \
    List[TestSession]:
        """
        Fetches all test sessions from the database.

        :return: A list of test session objects.
        :rtype: List[Any]
        """
        if this_year:
            end, start = await self.running_year()
            query = select(TestSession).where(TestSession.type_test == typetest).where(
                TestSession.datetime_start.between(start, end)).options(
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
        else:
            query = select(TestSession).where(TestSession.type_test == typetest).options(
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

    async def get_all_fitness_tests(self,current_year=True) -> list[FitnessTest]:
        """
        Fetches all fitness tests.

        :return: A list of FitnessTest objects (base or subtype instances).
        """

        if current_year:
            end, start = await self.running_year()
            query =select(FitnessTest).where(
                TestSession.datetime_start.between(start, end))
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
                query = select(FitnessTest).where(
                TestSession.datetime_start.between(start, end)).options(
                    selectin_polymorphic(FitnessTest,
                                         [PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest]),
                    selectinload(FitnessTest.test_sessions)
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

    async def get_all_fitness_tests_full_this_year(self) -> list[FitnessTest]:
        """
        Fetches all fitness tests with:
        - Polymorphic loading of concrete subtypes
        - Related TestSession objects

        :return: A list of FitnessTest objects with related data.
        """
        try:
            async with self.SessionLocal() as session:
                end, start = await self.running_year()
                query = select(FitnessTest).where(
                TestSession.datetime_start.between(start, end)).options(
                    selectin_polymorphic(FitnessTest,
                                         [PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest]),
                    selectinload(FitnessTest.test_sessions)
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

    async def get_all_phef(self, session_id: int,current_year=True) -> List[PhefTest]:
        """
        Fetch all PhefTest entities with their related TestSession objects.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = (
                            select(TestSession)
                            .where(TestSession.id == session_id).where(
                            TestSession.datetime_start.between(start, end))
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    else:
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

    async def get_all_combat_test(self, session_id: int,current_year=True) -> List[CombatTestParatrooper]:
        """
        Fetch all PhefTest entities with their related TestSession objects.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = (
                            select(TestSession)
                            .where(TestSession.id == session_id).where(
                            TestSession.datetime_start.between(start, end))
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    else:
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



    async def get_all_pti(self) -> list[User]:
        query = select(User).where(User.role == Role.PTI)
        results = await self.fetch_and_log(query, "users")
        return results if results else []

    async def get_all_test_sessions_type_fitness_test_from_a_test_session(self, type_test, session_id: int) -> list[
        FitnessTest]:
        query = select(TestSession).where(TestSession.type_test == type_test).where(TestSession.id == session_id)
        results = await self.fetch_and_log(query, "test sessions")
        return results if results else []

    async def get_all_functional_test(self, session_id,current_year=True) -> list[FunctionalTest]:
        """
              Fetch all PhefTest entities with their related TestSession objects.
              """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = (
                            select(TestSession)
                            .where(TestSession.id == session_id).where(
                                TestSession.datetime_start.between(start, end))
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    else:
                        query = (
                            select(TestSession)
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    result = await session.execute(query)
                    test_session = result.unique().scalar_one_or_none()

                    if test_session:
                        # Create a list of Functionals while the session is still active
                        func_test = [
                            test for test in test_session.fitness_tests
                            if isinstance(test, FunctionalTest)
                        ]
                        # Ensure all necessary data is loaded
                        for test in func_test:
                            await session.refresh(test)
                        return func_test
                    return []
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error fetching Functional tests: {str(e)}")
            return []

    async def get_all_combat_swimming_test(self, session_id,current_year=True) -> list[CombatSwimmingTest]:
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
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = (
                            select(TestSession)
                            .where(TestSession.id == session_id).where(
                                TestSession.datetime_start.between(start, end))
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    else:
                        query = (
                            select(TestSession)
                            .where(TestSession.id == session_id)
                            .options(selectinload(TestSession.fitness_tests))
                        )
                    result = await session.execute(query)
                    test_session = result.unique().scalar_one_or_none()

                    if test_session:
                        # Create a list of Functionals while the session is still active
                        func_test = [
                            test for test in test_session.fitness_tests
                            if isinstance(test, CombatSwimmingTest)
                        ]
                        # Ensure all necessary data is loaded
                        for test in func_test:
                            await session.refresh(test)
                        return func_test
                    return []
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error fetching Functional tests: {str(e)}")
            return []

    async def get_all_fitness_tests_from_military_units(self, unit: str) -> List[FitnessTest]:
        """
        Fetches all fitness tests associated with a specific military unit.

        This asynchronous method retrieves all the fitness tests that are linked
        to the military personnel belonging to the given unit. It achieves this
        by first fetching all military personnel in the specified unit and then
        filtering the fitness tests based on their association with the identified
        personnel. If no personnel or fitness tests are found, an empty list is
        returned.

        :param unit: The name or identifier of the military unit to query fitness
            tests for.
        :type unit: str
        :return: A list of fitness tests associated with the given unit, or an
            empty list if none are found.
        :rtype: List[FitnessTest]
        """
        try:
            mils = await self._be_mil_service.get_all_be_mil_from_unit(unit)
            fit_tests = await self.get_all_fitness_tests_full()
            if not (mils and fit_tests):
                return []
            return [test for test in fit_tests if test.serial_number in [m.service_number for m in mils]]
        except (SQLAlchemyError, Exception) as e:
            self.__logger.error(f"Error fetching fitness tests for unit {unit}: {str(e)}")
            return []

    async def get_all_fitness_tests_from_military_units_type_fitness_test(self, unit: str,
                                                                          fitness_type: TypeFitnessTest) -> List[
        FitnessTest | PhefTest | FunctionalTest | CombatTestParatrooper | CombatSwimmingTest]:
        """
        Fetches all fitness tests of a specific type for a given military unit.

        This method retrieves all test records of a specific fitness test type associated
        with the service numbers of personnel belonging to the specified military unit.
        It fetches the military personnel information and test sessions that correspond
        to the type of fitness test provided. If no relevant data is found, an empty
        list will be returned.

        :param unit: The identifier of the military unit.
        :type unit: str
        :param fitness_type: The specific type of fitness tests to retrieve.
        :type fitness_type: TypeFitnessTest
        :return: A list of fitness tests corresponding to the provided type and military unit.
        :rtype: List[FitnessTest | PhefTest | FunctionalTest | CombatTestParatrooper |
            CombatSwimmingTest]
        """
        try:
            mils = await self._be_mil_service.get_all_be_mil_from_unit(unit)
            sessions: List[TestSession] = await self.get_all_test_sessions_type_fitnessTest_full(fitness_type)
            if not (mils and sessions):
                return []

            service_numbers = {m.service_number for m in mils}
            return [
                ft
                for session in sessions
                for ft in session.fitness_tests
                if getattr(ft, "serial_number", None) in service_numbers
            ]
        except (SQLAlchemyError, Exception) as e:
            self.__logger.error(f"Error fetching fitness tests for unit {unit}: {str(e)}")
            return []

    async def get_all_phef_from_mil(self, serial, current_year) -> List[PhefTest]:
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
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = select(PhefTest).where(PhefTest.serial_number == serial).where(TestSession.datetime_start.between(start, end))
                    else :
                        query = (
                            select(PhefTest)
                            .where(PhefTest.serial_number == serial)
                        )
                    result = await session.execute(query)
                    phef_tests = result.scalars().all()
                    return list(phef_tests) if phef_tests else []
        except (SQLAlchemyError, Exception) as e:
            self.__logger.error(f"Error fetching PHEF tests for military unit {serial}: {str(e)}")
            return []

    async def get_all_combat_from_mil(self, service_number, current_year)-> List[CombatTestParatrooper]:
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
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = select(CombatTestParatrooper).where(PhefTest.serial_number == service_number).where(
                            TestSession.datetime_start.between(start, end))
                    else:
                        query = (
                            select(PhefTest)
                            .where(PhefTest.serial_number == service_number)
                        )
                    result = await session.execute(query)
                    phef_tests = result.scalars().all()
                    return list(phef_tests) if phef_tests else []
        except (SQLAlchemyError, Exception) as e:
            self.__logger.error(f"Error fetching PHEF tests for military unit {service_number}: {str(e)}")
            return []

    async def get_all_swim_from_mil(self, service_number, current_year)->List[CombatSwimmingTest]:
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
        try:
            async with self.SessionLocal() as session:
                async with session.begin():  # Add transaction context
                    if current_year:
                        end, start = await self.running_year()
                        query = select(CombatSwimmingTest).where(PhefTest.serial_number == service_number).where(
                            TestSession.datetime_start.between(start, end))
                    else:
                        query = (
                            select(PhefTest)
                            .where(PhefTest.serial_number == service_number)
                        )
                    result = await session.execute(query)
                    phef_tests = result.scalars().all()
                    return list(phef_tests) if phef_tests else []
        except (SQLAlchemyError, Exception) as e:
            self.__logger.error(f"Error fetching PHEF tests for military unit {service_number}: {str(e)}")
            return []

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
            self.__logger.error(f"Database error fetching upcoming session for PTI {serial_number_pti}: {str(e)}")
            return None

