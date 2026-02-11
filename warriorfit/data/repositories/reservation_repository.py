from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError
from sqlalchemy.orm import selectinload

from warriorfit.data.model.db_model import Reservation, Room
from warriorfit.data.repositories.abc_repository import ABCRepository


class ReservationRepository(ABCRepository):

    def __init__(self):
        super().__init__()

    async def add_reservation(self, reservation: Reservation) -> Any | None:
        async with self.SessionLocal() as session:
            try:
                session.add(reservation)
                await session.commit()
                await session.refresh(reservation)

                # Re-fetch the reservation with the room relationship loaded
                # This ensures the room data is available when the object is detached
                stmt = (
                    select(Reservation)
                    .options(selectinload(Reservation.room))
                    .where(Reservation.id == reservation.id)
                )
                result = await session.execute(stmt)
                reservation = result.scalar_one()

                return reservation
            except IntegrityError as e:
                await session.rollback()
                self._logger.error(
                    "Integrity error while creating reservation: %s", str(e)
                )

    async def get_reservation(self, id_r: int) -> Reservation | None:
        try:
            async with self.SessionLocal() as session:
                reservation = await session.get(
                    Reservation, id_r, options=[selectinload(Reservation.room)]
                )
                return reservation
        except SQLAlchemyError as e:
            self._logger.error("Database error while fetching reservation: %s", str(e))
            return None

    async def get_all_reservation(self):
        try:
            async with self.SessionLocal() as session:
                # Fix: Await the scalars() coroutine first, then call .all() on the result
                result = await session.scalars(
                    select(Reservation).options(selectinload(Reservation.room))
                )
                reservations = result.all()
                return reservations
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error while fetching all reservations: %s", str(e)
            )
            return None

    async def delete_reservation(self, id_r: int):
        async with self.SessionLocal() as session:
            try:
                reservation = await session.get(Reservation, id_r)
                if reservation:
                    await session.delete(reservation)
                    await session.commit()
                    return True
                return False
            except SQLAlchemyError as e:
                await session.rollback()
                self._logger.error(
                    "Database error while deleting reservation: %s", str(e)
                )
                return False

    async def update_reservation(self, reservation):
        async with self.SessionLocal() as session:
            try:
                session.add(reservation)
                await session.commit()
                return True
            except IntegrityError as e:
                await session.rollback()
                self._logger.error(
                    "Integrity error while updating reservation: %s", str(e)
                )
                return False
            except SQLAlchemyError as e:
                await session.rollback()
                self._logger.error(
                    "Database error while updating reservation: %s", str(e)
                )
                return False

    async def delete_all_reservation(self):
        async with self.SessionLocal() as session:
            try:
                await session.query(Reservation).delete()
                await session.commit()
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                self._logger.error(
                    "Database error while deleting all reservations: %s", str(e)
                )
                return False

    async def get_rooms(self) -> list[Room]:
        query = select(Room)
        results = await self.fetch_and_log(query, "March")
        return results if results else []
