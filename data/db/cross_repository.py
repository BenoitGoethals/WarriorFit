import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from data.db.abc_repository import ABCRepository
from data.db.db_model import Cross, Runner, CrossRunners  # ensure association table is imported

class CrossRepository(ABCRepository):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

    async def get_cross(self, id: int) -> Cross | None:
        query = select(Cross).where(Cross.id == id)
        results = await self.fetch_and_log(query, "cross")
        return results[0] if results else None

    async def get_all_cross(self) -> List[Cross]:
        query = select(Cross)
        results = await self.fetch_and_log(query, "crosses")
        return results if results else []

    async def add_cross(self, cross: Cross) -> Cross | None:
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

    async def add_runner(self, runner: Runner) -> Runner | None:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(runner)
                    await session.refresh(runner)
                    return runner
        except IntegrityError as e:
            self._logger.error(f"Integrity error adding runner {getattr(runner, 'id', 'unknown')}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error adding runner {getattr(runner, 'id', 'unknown')}: {str(e)}")
            return None

    async def remove_runner(self, id: int) -> bool:
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
        query = select(Runner)
        results = await self.fetch_and_log(query, "runners")
        return results if results else []

    async def get_runner_by_serial(self, serial_number: str) -> Runner | None:
        query = select(Runner).where(Runner.serial_number == serial_number)
        results = await self.fetch_and_log(query, "runners")
        return results[0] if results else None

    async def get_runners_from_a_cross(self, id: int) -> List[Runner]:
        # Many-to-many via association table; no Runner.cross_id column
        query = (
            select(Runner)
            .join(CrossRunners, Runner.id == CrossRunners.c.runner_id)
            .where(CrossRunners.c.cross_id == id)
        )
        results = await self.fetch_and_log(query, "runners")
        return results if results else []

    async def update_runner(self, id: int, r: Runner) -> Runner | None:
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
            async with self.SessionLocal() as session:
                await session.refresh(existing_runner)
            return existing_runner
        except IntegrityError as e:
            self._logger.error(f"Integrity error updating runner {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error updating runner {id}: {str(e)}")
            return None

    async def get_runner(self, runner_id: int) -> Runner | None:
        query = select(Runner).where(Runner.id == runner_id)
        results = await self.fetch_and_log(query, "runners")
        return results[0] if results else None

    async def update_cross(self, cross):
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


