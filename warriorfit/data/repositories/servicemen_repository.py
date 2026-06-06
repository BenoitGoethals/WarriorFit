from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from warriorfit.data.model.db_model import ServiceMen, Unit
from warriorfit.data.repositories.abc_repository import ABCRepository


class ServicemenRepository(ABCRepository):
    def __init__(self, config=None):
        super().__init__(config=config)

    async def create_serviceman(self, service_men: ServiceMen) -> ServiceMen | None:
        """
        Create a new serviceman.
        payload should contain fields compatible with ServiceMen model constructor.
        """
        session = None
        try:
            async with self.SessionLocal() as session, session.begin():
                service_men = await session.add(service_men)  # type: ignore[func-returns-value]
                await session.refresh(service_men)
                return service_men
        except SQLAlchemyError:
            self._logger.exception("Failed to create serviceman")
            if session is not None:
                await session.rollback()
            return None

    async def get_servicemen_by_id(self, serviceman_id: int) -> ServiceMen | None:
        """
        Get serviceman by primary key id.
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                res = await session.execute(
                    select(ServiceMen).where(ServiceMen.id == serviceman_id)
                )
                return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.exception(e)
            return None

    async def get_by_service_number(self, service_number: str, lazy=True) -> ServiceMen | None:
        """
        Get a single serviceman by unique service number.
        """
        if lazy:
            query = select(ServiceMen).where(ServiceMen.service_number == service_number)
        else:
            query = (
                select(ServiceMen)
                .where(ServiceMen.service_number == service_number)
                .options(selectinload(ServiceMen.unit))
            )
        results = await self.fetch_and_log(query, "ServiceMen")
        return results[0] if results else None

    async def list_all(self) -> list[ServiceMen]:
        query = select(ServiceMen)
        return await self.fetch_and_log(query, "ServiceMen")

    async def list_all_with_unit(self) -> list[ServiceMen]:
        query = select(ServiceMen).options(selectinload(ServiceMen.unit))
        return await self.fetch_and_log(query, "ServiceMen")

    async def list_by_unit_name(
        self, unit_name: str, limit: int = 100, offset: int = 0
    ) -> list[ServiceMen]:
        """
        List servicemen filtered by unit name.
        """

        query = (
            select(ServiceMen)
            .join(Unit, ServiceMen.unit_id == Unit.id)
            .where(Unit.name == unit_name)
            .limit(limit)
            .offset(offset)
        )

        return await self.fetch_and_log(query, "ServiceMen")

    async def update_serviceman(self, service_men: ServiceMen) -> ServiceMen | None:
        """
        Partially update fields of a serviceman and return the updated entity.
        """
        session = None
        try:
            async with self.SessionLocal() as session, session.begin():
                service_men_update = await session.execute(
                    select(ServiceMen).where(ServiceMen.id == service_men.id)
                )
                service_men_to_update = service_men_update.scalar_one_or_none()
                if service_men_to_update is None:
                    return None
                service_men_to_update.last_name = service_men.last_name
                service_men_to_update.first_name = service_men.first_name
                service_men_to_update.service_number = service_men.service_number
                service_men_to_update.rank = service_men.rank
                service_men_to_update.age = service_men.age  # type: ignore[misc]
                service_men_to_update.gender = service_men.gender
                service_men_to_update.unit_id = service_men.unit_id
                await session.commit()
                return service_men_to_update
        except SQLAlchemyError as e:
            self._logger.exception(e)
            if session is not None:
                await session.rollback()
            return None

    async def delete_serviceman(self, serviceman_id: int) -> bool:
        """
        Delete serviceman by id. Returns True if a row was deleted.
        """
        session = None
        try:
            async with self.SessionLocal() as session, session.begin():
                result = await session.execute(
                    sa_delete(ServiceMen).where(ServiceMen.id == serviceman_id)
                )
            return bool(getattr(result, "rowcount", 0))
        except SQLAlchemyError:
            self._logger.exception("Failed to delete serviceman id=%s", serviceman_id)
            if session is not None:
                await session.rollback()
            return False

    async def get_by_unit_id(self, id):
        """Retrieve a unit by its unique identifier.

        This asynchronous method fetches a `Unit` object from the database
        that matches the provided unique identifier. It attempts to perform
        the operation within an asynchronous session using SQLAlchemy. If
        the operation encounters an exception, it logs the exception and
        returns None.

        :param id: The unique identifier of the unit to be retrieved.
        :type id: int
        :return: A `Unit` object if found, otherwise None.
        :rtype: Optional[Unit]
        :raises SQLAlchemyError: If there is an error during the database operation.
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                res = await session.execute(select(Unit).where(Unit.id == id))
                return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.exception(e)
            return None

    async def add_unit(self, unit):
        """
        Adds a given unit to the database session and commits the transaction.

        This asynchronous method manages a database session to add a unit to the
        database. If the transaction is successful, it returns True. In case of an
        error during the transaction, it rolls back the changes, logs the exception,
        and returns False.

        :param unit: The unit object to be added to the database.
        :type unit: Any
        :return: True if the unit is successfully added and committed, otherwise False.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                session.add(unit)
                await session.commit()
                return True
        except SQLAlchemyError as e:
            session.rollback()  # type: ignore[unused-coroutine]
            self._logger.exception(e)
            return False

    async def list_all_units(self):
        """
        Asynchronously retrieves a list of all units from the database.

        This method establishes a new asynchronous database session, executes a query
        to select all entries from the Unit table, and fetches the results.

        :return: A list of Unit objects if the query succeeds, or None if an exception
            occurs.
        :rtype: list[Unit] | None
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                res = await session.execute(select(Unit))
                return res.scalars().all()
        except SQLAlchemyError as e:
            self._logger.exception(e)
            return None

    async def get_all_be_mil_from_unit(self, own_unit: str) -> list[ServiceMen]:
        """
        Asynchronously retrieves all `ServiceMen` entities associated with the specified
        unit name from the database. The method executes a database query to filter
        for servicemen whose unit matches the given `own_unit` name, using optimized
        loading strategies for improved performance.

        :param own_unit: The name of the unit to filter `ServiceMen` records.
        :type own_unit: str
        :return: A list of `ServiceMen` associated with the specified unit.
        :rtype: list[ServiceMen]
        """
        query = (
            select(ServiceMen)
            .join(Unit, ServiceMen.unit_id == Unit.id)
            .where(Unit.name == own_unit)
        )
        query = query.options(selectinload(ServiceMen.unit))
        return await self.fetch_and_log(query, "unit")
