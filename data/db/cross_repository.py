import logging
from typing import List
from sqlalchemy import select, insert, exists, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import aliased, selectinload

from data.db.abc_repository import ABCRepository
from data.db.db_model import Cross, Runner, CrossRunners  # ensure association table is imported

class CrossRepository(ABCRepository):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

    async def get_cross(self, id: int) -> Cross | None:
        """
        Fetches a Cross object from the database by its unique identifier.

        This asynchronous method executes a query to retrieve a Cross record
        from the database that matches the given identifier. If a matching record
        is found, the first result is returned, otherwise it returns None.

        :param id: The unique identifier of the Cross object to retrieve.
        :type id: int
        :return: A Cross object if found, otherwise None.
        :rtype: Cross | None
        """
        query = select(Cross).where(Cross.id == id)
        results = await self.fetch_and_log(query, "cross")
        return results[0] if results else None

    async def get_cross_full(self, id: int) -> Cross | None:
        """
        Asynchronously retrieves a Cross instance by its ID, including its related runners.

        This method performs a database query to fetch the specified Cross instance along with
        its associated runners (eagerly loaded).

        :param id: The unique identifier of the Cross instance to retrieve.
        :type id: int
        :return: The Cross instance with the specified ID and its related runners if found, or
            None if no matching instance is found.
        :rtype: Cross | None
        """
        query = (
            select(Cross)
            .options(selectinload(Cross.runners))  # Eager load runners
            .where(Cross.id == id)
        )
        results = await self.fetch_and_log(query, "cross")
        return results[0] if results else None

    async def get_all_cross(self,lazy=True) -> List[Cross]:
        """
        Asynchronously retrieves all `Cross` objects from the database.

        This method performs a database query to fetch all instances of the `Cross`
        model. If no results are found, an empty list will be returned. The method
        also logs the execution of the query with the specified log type.

        :raises DatabaseError: If there is an issue with the database connection or
            execution of the query.
        :raises OperationalError: If there are errors during query execution that are
            related to operational issues.
        :param self: The instance of the class this method is bound to.
        :return: A list of `Cross` objects or an empty list if no data is found.
        :rtype: List[Cross]
        """
        # if lazy is False, eagerly load all runners for all crosses
        if not lazy:
            query = select(Cross).options(selectinload(Cross.runners))
        else:
            query = select(Cross)
        results = await self.fetch_and_log(query, "crosses")
        return results if results else []

    async def add_cross(self, cross: Cross) -> Cross | None:
        """
        Adds a new cross record into the database asynchronously.

        This method attempts to add the given `cross` to the database within a
        transaction. If the transaction completes successfully, it refreshes
        the state of the `cross` instance to ensure it reflects the committed
        state of the database. In case of any exceptions, such as an
        `IntegrityError` or another `SQLAlchemyError`, the error is logged
        and the method returns `None`.

        :param cross: The Cross instance to be added to the database.
        :type cross: Cross
        :return: The added Cross instance if successful, otherwise `None`.
        :rtype: Cross | None
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(cross)  # sync; do not await
                await session.refresh(cross)  # refresh after commit, same session
            return cross
        except IntegrityError as e:
            self._logger.error(f"Integrity error adding cross {getattr(cross, 'id', 'unknown')}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error adding cross {getattr(cross, 'id', 'unknown')}: {str(e)}")
            return None

    async def remove_cross(self, id: int) -> bool:
        """
        Removes a `Cross` record from the database by its ID. This method accesses the database
        asynchronously, beginning a session and fetching the record with the provided ID. If the
        record is found, it is removed from the database. If the record does not exist, or if an
        error occurs during the process, appropriate values or actions are taken.

        :param id: The ID of the `Cross` record to remove.
        :return: A boolean indicating whether the operation was successful. Returns `True`
            if the record is found and removed successfully. Returns `False` if the record
            does not exist or if an error occurs during the operation.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    cross = await session.get(Cross, id)
                    if not cross:
                        return False
                    await session.delete(cross)  # delete supports await with AsyncSession in SA 2.x
                    return True
        except IntegrityError as e:
            self._logger.error(f"Integrity error removing cross {id}: {str(e)}")
            return False
        except SQLAlchemyError as e:
            self._logger.error(f"Database error removing cross {id}: {str(e)}")
            return False

    async def add_runner_to_cross(self, cross_id: int, runner: Runner) -> Runner | None:
        """
        Adds a runner to a specified cross, ensuring the runner is not already linked to the cross
        and persisting the runner to the database if it doesn't exist. Handles cases where the runner is
        either new or detached. Avoids lazy loading of `cross.runners` to optimize performance.

        :param cross_id: The unique identifier of the cross to which the runner will be added.
        :type cross_id: int

        :param runner: The Runner object that will be associated with the specified cross.
        :type runner: Runner

        :return: The Runner object after being linked to the cross or refreshed in the database.
                 If the cross does not exist or the runner is already linked, returns None.
        :rtype: Runner | None
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    cross = await session.get(Cross, cross_id)
                    if not cross:
                        self._logger.error(f"Cross {cross_id} not found")
                        return None

                    already_encoded =await session.execute(
                    select(1).where(
                        CrossRunners.cross_id == cross_id,
                        CrossRunners.runner_id == runner.id,
                    ))
                    if already_encoded.scalar() is not None:
                        return None


                    # Persist runner (new or detached)
                    if runner.id is None:
                        session.add(runner)
                        await session.flush()  # ensure runner.id
                    else:
                        # ensure runner is attached to this session
                        runner = await session.merge(runner)
                        await session.flush()

                    # Avoid touching cross.runners (prevents lazy-load)
                    exists = await session.execute(
                        select(1).select_from(CrossRunners).where(
                            CrossRunners.cross_id == cross_id,
                            CrossRunners.runner_id == runner.id,
                        )
                    )
                    if exists.scalar() is None:
                        await session.execute(
                            insert(CrossRunners).values(cross_id=cross_id, runner_id=runner.id)
                        )

                    # If you need current state, refresh here while session is active
                    await session.refresh(runner)

            return runner
        except Exception as e:
            self._logger.error(f"Linking runner to cross failed: {e}")
            return None

    async def remove_runner(self, id: int) -> bool:
        """
        Removes a runner from the database using the provided runner ID. The removal is
        performed within an asynchronous SQLAlchemy session, ensuring that the session
        is properly managed and any database modifications are committed. If any
        database errors occur, they are logged appropriately, and the method will
        return a failure response.

        :param id: The ID of the runner to be removed.
        :type id: int
        :return: Returns True if the runner was successfully removed, False otherwise.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    runner = await session.get(Runner, id)
                    if not runner:
                        return False
                    await session.delete(runner)
                    return True
        except IntegrityError as e:
            self._logger.error(f"Integrity error removing runner {id}: {str(e)}")
            return False
        except SQLAlchemyError as e:
            self._logger.error(f"Database error removing runner {id}: {str(e)}")
            return False

    async def get_all_runners(self) -> List[Runner]:
        """
        Retrieves all runners from the database.

        :return: List of Runner objects
        """
        query = select(Runner)
        results = await self.fetch_and_log(query, "runners")
        return results if results else []

    async def get_runner_by_serial(self, serial_number: str) -> Runner | None:
        """
        Retrieves a runner from the database by its serial number.

        :param serial_number: The serial number of the runner
        :type serial_number: str
        :return: Runner object or None if not found
        """
        query = select(Runner).where(Runner.serial_number == serial_number)
        results = await self.fetch_and_log(query, "runners")
        return results[0] if results else None

    async def get_runners_from_a_cross(self, id: int) -> List[Runner]:
        """
        Retrieves all runners associated with a specific cross.

        :param id: The ID of the cross
        :type id: int
        :return: List of Runner objects
        """
        query = (
            select(Runner)
            .join(CrossRunners, Runner.id == CrossRunners.runner_id)
            .where(CrossRunners.cross_id == id)
        )
        results = await self.fetch_and_log(query, "runners")
        return results if results else []

    async def update_runner(self, id: int, r: Runner) -> Runner | None:
        """
        Updates a runner's information in the database.

        :param id: The ID of the runner to be updated
        :type id: int
        :param r: The updated Runner object
        :type r: Runner
        :return: The updated Runner object or None if not found
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_runner = await session.get(Runner, id)
                    if not existing_runner:
                        self._logger.error(f"Runner {id} not found for update")
                        return None
                    # whitelist updatable attributes
                    fields = ("serial_number", "running_time")
                    for key in fields:
                        val = getattr(r, key, None)
                        if val is not None:
                            setattr(existing_runner, key, val)
                    # refresh within the same session where the object is persistent
                    await session.flush()
                    await session.refresh(existing_runner)
            return existing_runner
        except IntegrityError as e:
            self._logger.error(f"Integrity error updating runner {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error updating runner {id}: {str(e)}")
            return None

    async def get_runner(self, runner_id: int) -> Runner | None:
        """
        Retrieves a runner from the database by its ID.

        :param runner_id: The ID of the runner
        :type runner_id: int
        :return: Runner object or None if not found
        """
        query = select(Runner).where(Runner.id == runner_id)
        results = await self.fetch_and_log(query, "runners")
        return results[0] if results else None

    async def update_cross(self, cross):
        """
        Updates a cross's information in the database.

        :param cross: The updated Cross object
        :type cross: Cross
        :return: The updated Cross object or None if not found
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_cross = await session.get(Cross, cross.id)  # use class, not instance
                    if not existing_cross:
                        self._logger.error(f"Cross with ID {cross.id} not found.")
                        return None

                    # Update fields (whitelist as needed)
                    existing_cross.datetime_start = cross.datetime_start
                    existing_cross.description = cross.description
                    existing_cross.distance = cross.distance
                    existing_cross.executed = cross.executed

                # after commit
                await session.refresh(existing_cross)
                return existing_cross

        except IntegrityError as e:
            self._logger.error(f"Integrity error updating cross {getattr(cross, 'id', 'unknown')}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error updating cross {getattr(cross, 'id', 'unknown')}: {str(e)}")
            return None

    async def exist_in_cross(self, serial: str, cross_id: int) -> bool:
        """
        Check if a runner with given serial number exists in a specific cross.
        """
        if not serial:
            return False
        serial = serial.strip()

        try:
            cross_id_int = int(cross_id)
        except (TypeError, ValueError):
            self._logger.warning(f"exist_in_cross called with non-integer cross_id={cross_id!r}")
            return False

        stmt = select(
            exists().where(
                and_(
                    CrossRunners.cross_id == cross_id_int,
                    Runner.id == CrossRunners.runner_id,
                    Runner.serial_number == serial,
                )
            )
        )

        try:
            async with self.SessionLocal() as session:
                result = await session.execute(stmt)
                return bool(result.scalar())
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error checking runner existence in cross: %s", e, exc_info=True
            )
            return False