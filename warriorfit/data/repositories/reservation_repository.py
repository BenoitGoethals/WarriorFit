from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError
from warriorfit.data.model.db_model import Reservation, Room
from warriorfit.data.repositories.abc_repository import ABCRepository


class ReservationRepository(ABCRepository):

    async def add_reservation(self, reservation: Reservation) -> Reservation:
        async with self.SessionLocal() as session:
            async with session.begin():
                try:
                    session.add(reservation)
                    await session.commit()
                    await session.refresh(reservation)
                    return reservation
                except IntegrityError as e:
                    await session.rollback()
                    self._logger.error(f"Integrity error while creating reservation: {str(e)}")
                    raise
                except SQLAlchemyError as e:
                    await session.rollback()
                    self._logger.error(f"Database error while creating reservation: {str(e)}")
                    raise

    async def get_reservation(self, id_r: int) -> Reservation | None:
        try:
            async with self.SessionLocal() as session:
                reservation = await session.get(Reservation, id_r)
                return reservation
        except SQLAlchemyError as e:
            self._logger.error(f"Database error while fetching reservation: {str(e)}")
            return None

    async def get_all_reservation(self):
        try:
            async with self.SessionLocal() as session:
                reservations = await session.query(Reservation).all()
                return reservations
        except SQLAlchemyError as e:
            self._logger.error(f"Database error while fetching all reservations: {str(e)}")
            return None

    async def delete_reservation(self, id_r: int):
        async with self.SessionLocal() as session:
            async with session.begin():
                try:
                    reservation = await session.get(Reservation, id_r)
                    if reservation:
                        session.delete(reservation)
                        await session.commit()
                        return True
                    return False
                except SQLAlchemyError as e:
                    await session.rollback()
                    self._logger.error(f"Database error while deleting reservation: {str(e)}")
                    return False

    async def update_reservation(self, reservation):
        async with self.SessionLocal() as session:
            async with session.begin():
                try:
                    session.add(reservation)
                    await session.commit()
                    return True
                except IntegrityError as e:
                    await session.rollback()
                    self._logger.error(f"Integrity error while updating reservation: {str(e)}")
                    return False
                except SQLAlchemyError as e:
                    await session.rollback()
                    self._logger.error(f"Database error while updating reservation: {str(e)}")
                    return False

    async def delete_all_reservation(self):
        async with self.SessionLocal() as session:
            async with session.begin():
                try:
                    await session.query(Reservation).delete()
                    await session.commit()
                    return True
                except SQLAlchemyError as e:
                    await session.rollback()
                    self._logger.error(f"Database error while deleting all reservations: {str(e)}")
                    return False


    async def get_rooms(self)->list[Room]:
        query = select(Room)
        results = await self.fetch_and_log(query, "March")
        return results if results else []

