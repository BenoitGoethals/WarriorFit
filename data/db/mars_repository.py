import logging
from typing import Any, Coroutine

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from data.db.abc_repository import ABCRepository
from data.db.db_model import Mars


class MarsRepository(ABCRepository):
    def __init__(self):
        super().__init__()

        self.__logger = logging.getLogger(__name__)

    async def get_mars_by_id(self, id_mars: int) -> Mars | None:
        query = select(Mars).where(Mars.id == id_mars)
        results = await self.fetch_and_log(query, "mars_by_id")
        return results

    async def get_all_mars(self) -> list[Mars]:
        query = select(Mars)
        results = await self.fetch_and_log(query, "marses")
        return results if results else []

    async def get_all_mars_by_unit_name(self, unit_name: str) -> list[Mars]:
        query = (
            select(Mars)
            .join(Mars.service_men)
            .where(Mars.service_men.has(unit_name=unit_name))
        )
        results = await self.fetch_and_log(query, "marses_from_unit")
        return results if results else []

    async def get_all_mars_form_service_men(self, service_men: str) -> list[Mars]:
        query = select(Mars).where(Mars.service_number == service_men)
        results = await self.fetch_and_log(query, "marses_service_men")
        return results if results else []

    async def add_mars(self, mars: Mars):
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(mars)
                    await session.flush()
                    await session.refresh(mars)
                    return mars
        except SQLAlchemyError as e:
            self.__logger.exception(e)
            if session is not None:
                try:
                    await session.rollback()
                    return None
                except Exception as e:
                    self.__logger.exception(e)
                    return None

    async def delete_mars(self, ind_mars):
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(Mars).where(Mars.id == ind_mars)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self.__logger.error(f"No mars found with ID {ind_mars}.")
                        return False
                    return True
        except SQLAlchemyError as e:
            self.__logger.exception("Failed to delete mars")
            if session is not None:
                try:
                    await session.rollback()
                    return False
                except Exception as e:
                    self.__logger.exception(e)
                    return False

    async def update_mars(self, mars: Mars) -> Mars | None:
        session = None
        try:
            async with self.SessionLocal() as session:
                async with session.begin():                  
                    existing_mars = await session.get(Mars, mars.id)
                    if not existing_mars:
                        self.__logger.error(f"No mars found with ID {mars.id}")
                        return None

                    # Update the existing record
                    existing_mars.service_number = mars.service_number
                    existing_mars.distance = mars.distance
                    existing_mars.succeeded = mars.succeeded
                    existing_mars.datetime_executed = mars.datetime_executed
                    await session.flush()
                    await session.refresh(existing_mars)
                    return existing_mars

        except SQLAlchemyError as e:
            self.__logger.exception(f"Failed to update mars with ID {mars.id}: {str(e)}")
            if session is not None:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    self.__logger.exception(f"Rollback failed: {str(rollback_error)}")
            return None
