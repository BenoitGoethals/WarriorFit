import logging

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from warriorfit.data.db.abc_repository import ABCRepository
from warriorfit.data.db.db_model import March


class MarchRepository(ABCRepository):
    """
    MarchRepository provides operations for managing and querying March records.

    This class is responsible for implementing CRUD operations and various query functions
    to retrieve and manage `March` entities in the database. It uses SQLAlchemy for database
    communication and asynchronous operations.

    :ivar SessionLocal: The database session factory used to manage database sessions.
    :type SessionLocal: Callable[[], AsyncSession]
    """
    def __init__(self):
        super().__init__()


    async def get_march_by_id(self, id_march: int) -> March | None:
        """
        Retrieve a `March` instance by its ID.

        This function performs an asynchronous database operation to fetch a
        `March` record that matches the given ID. If no record is found, it
        returns `None`.

        :param id_march: The ID of the `March` record to retrieve.
        :type id_march: int
        :return: The `March` instance matching the ID, or `None` if no match
                 is found.
        :rtype: March | None
        """
        query = select(March).where(March.id == id_march)
        results = await self.fetch_and_log(query, "March")
        return results

    async def get_all_march(self) -> list[March]:
        """
        Asynchronously retrieves all `March` objects from the database.

        This method performs a database query to fetch all instances of the
        `March` model. If no results are found, an empty list is returned.

        :raises sqlalchemy.exc.SQLAlchemyError: If the database operation fails.

        :return: A list containing all `March` objects retrieved from the
            database or an empty list if no objects are found.
        :rtype: list[March]
        """
        query = select(March)
        results = await self.fetch_and_log(query, "March")
        return results if results else []

    async def get_all_march_by_unit_name(self, unit_name: str) -> list[March]:
        """
        Retrieve all March objects associated with a specific unit name.

        This method performs an asynchronous query to fetch all March records
        that are associated with the service men belonging to the specified
        unit name. The results are returned as a list of March objects.

        :param unit_name: The name of the unit to search for related March records.
        :type unit_name: str
        :return: A list of March objects associated with the service men of the given unit name.
                 If no records are found, an empty list is returned.
        :rtype: list[March]
        """
        query = (
            select(March)
            .join(March.service_men)
            .where(March.service_men.has(unit_name=unit_name))
        )
        results = await self.fetch_and_log(query, "March")
        return results if results else []

    async def get_all_march_form_service_men(self, service_men: str,this_year=True) -> list[March]:
        """
        Fetches all marches associated with a given service member, optionally filtering
        for the current year.

        :param service_men: The service number of the service member for which to
            retrieve marches.
        :param this_year: A boolean indicating whether to filter marches for the
            current year. Defaults to True.
        :return: A list of March objects associated with the service member. If no
            records are found, an empty list is returned.
        """
        if this_year:
            end, start = await self.running_year()
            query = select(March).where(March.service_number == service_men).where(March.datetime_executed.between(start, end))
        else:
            query = select(March).where(March.service_number == service_men)
        results = await self.fetch_and_log(query, "March")
        return results if results else []

    async def add_march(self, mars: March):
        """
        Adds a new `March` object to the database asynchronously. This method handles
        the creation of a database session, adding the provided `March` instance,
        flushing and refreshing it to ensure the instance is updated with data generated
        by the database. If an error occurs during the process, it attempts to roll
        back the transaction to maintain database consistency.

        :param mars: The `March` object to be added to the database.
        :type mars: March
        :return: The added `March` object if the operation succeeds, or `None` if an
            error occurs.
        :rtype: Optional[March]
        """
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(mars)
                    await session.flush()
                    await session.refresh(mars)
                    return mars
        except SQLAlchemyError as e:
            self._logger.exception(e)
            if session is not None:
                try:
                    await session.rollback()
                    return None
                except Exception as e:
                    self._logger.exception(e)
                    return None

    async def delete_march(self, ind_march):
        """
        Deletes a March record from the database based on the provided ID.

        The method attempts to delete a March entry by executing a SQL `DELETE`
        query. If the specified `March.id` is not found, the method logs an
        error message and returns `False`. In case of any database-related
        error during the process, the session is rolled back (if possible),
        and the method logs the exception.

        :param ind_march: An integer that represents the ID of the March record
            to be deleted.
        :return: A boolean indicating whether the deletion was successful.
            Returns `True` if the deletion was successful, or `False` if no
            record was deleted, or if an error occurred during the process.
        """
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(March).where(March.id == ind_march)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self._logger.error(f"No March found with ID {ind_march}.")
                        return False
                    return True
        except SQLAlchemyError as e:
            self._logger.exception("Failed to delete March")
            if session is not None:
                try:
                    await session.rollback()
                    return False
                except Exception as e:
                    self._logger.exception(e)
                    return False

    async def update_march(self, march: March) -> March | None:
        """
        Asynchronously updates an existing March record in the database with new values.

        This method searches for a March record by the provided ID. If the record exists,
        the values of `service_number`, `distance`, `succeeded`, and `datetime_executed`
        are updated. If the record does not exist, an appropriate log message is generated,
        and the method returns None. In case of any database-related errors, it attempts
        to roll back the transaction and logs the exception.

        :param march: The March instance containing the updated values.
        :type march: March
        :return: The updated March instance if the update is successful,
                 or None if the record does not exist or an error occurs.
        :rtype: March | None
        :raises SQLAlchemyError: If a database-related error occurs.
        """
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_mars = await session.get(March, march.id)
                    if not existing_mars:
                        self._logger.error(f"No march found with ID {march.id}")
                        return None
                    existing_mars.service_number = march.service_number
                    existing_mars.distance = march.distance
                    existing_mars.succeeded = march.succeeded
                    existing_mars.datetime_executed = march.datetime_executed
                    await session.flush()
                    await session.refresh(existing_mars)
                    return existing_mars
        except SQLAlchemyError as e:
            self._logger.exception(f"Failed to update March with ID {march.id}: {str(e)}")
            if session is not None:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    self._logger.exception(f"Rollback failed: {str(rollback_error)}")
            return None
