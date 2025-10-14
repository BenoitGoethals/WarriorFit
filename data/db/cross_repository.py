import logging
from typing import List, Any
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import query

from data.db.abc_repository import ABCRepository
from data.db.db_model import Cross, Runner

class CrossRepository(ABCRepository):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

    async def get_cross(self, id: float) -> Cross | None:
        query = select(Cross).where(Cross.id == id)
        results = await self.fetch_and_log(query, "cross")
        return results[0] if results else None

    async def get_all_cross(self) -> List[Cross]:
        query = select(Cross)
        results = await self.fetch_and_log(query, "crosses")
        return results if results else []

    async def add_cross(self, cross) -> Cross | None:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(cross)
                await session.refresh(cross)
                return cross
        except IntegrityError as e:
            self._logger.error(f"Integrity error adding cross {cross.id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error adding cross {cross.id}: {str(e)}")
            return None

    async def remove_cross(self, id: float) -> bool:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    cross = await session.get(Cross, id)
                    if cross:
                        await session.delete(cross)
                        return True
                    else:
                        return False
        except IntegrityError as e:
            self._logger.error(e)
            return False
        except SQLAlchemyError as e:
            self._logger.error(f"Database error removing cross {id}: {str(e)}")
            return False

    async def add_runner(self, runner) -> Runner | None:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(runner)
                await session.refresh(runner)
                return runner
        except IntegrityError as e:
            self._logger.error(f"Integrity error adding runner {runner.id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error adding runner {runner.id}: {str(e)}")
            return None

    async def remove_runner(self, id) -> bool:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    runner = await session.get(Runner, id)
                    if runner:
                        await session.delete(runner)
                        return True
                    else:
                        return False
        except IntegrityError as e:
            self._logger.error(e)
            return False
        except SQLAlchemyError as e:
            self._logger.error(f"Database error removing runner {id}: {str(e)}")
            return False

    async def get_all_runners(self) -> List[Runner]:
        query = select(Runner)
        results = await self.fetch_and_log(query, "Runners")
        return results if results else []

    async def get_runner_by_serial(self, serial_number: str) -> Runner | None:
        query = select(Runner).where(Runner.serial_number == serial_number)
        results = await self.fetch_and_log(query, "Runners")
        return results[0] if results else None

    async def get_runners_from_a_cross(self,id:float) -> List[Runner]:
        query = select(Runner).where(Runner.cross_id == id)
        results = await self.fetch_and_log(query, "Runners")
        return results if results else []

    async def update_runner(self, id, r):
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_runner = await session.get(Runner, id)
                    if not existing_runner:
                        self._logger.error(f"Runner {id} not found for update")
                        return None
                    for key, value in r.__dict__.items():
                        if key != "_sa_instance_state" and value is not None:
                            setattr(existing_runner, key, value)
                await session.refresh(existing_runner)
                return existing_runner
        except IntegrityError as e:
            self._logger.error(f"Integrity error updating runner {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error updating runner {id}: {str(e)}")
            return None

    async def get_runner(self, runner_id):
        query = select(Runner).where(Runner.id == runner_id)
        results = await self.fetch_and_log(query, "Runners")
        return results[0] if results else None

