from typing import Any, Coroutine, List

from warriorfit.data.model.db_model import Reservation, Room
from warriorfit.services.reserve_fitness_room_service import ReserveFitnessRoomService


class ReserveFitnessRoomController:

    def __init__(self):
        self._service = ReserveFitnessRoomService()

    async def add_reservation(self, reservation) -> Reservation | None:
        return await self._service.add_reservation(reservation)

    async def rooms(self)->List[Room]:
        return await self._service.get_rooms()