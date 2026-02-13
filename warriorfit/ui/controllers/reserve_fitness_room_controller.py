from typing import Any, Coroutine, List

from warriorfit.data.model.db_model import Reservation, Room
from warriorfit.services.reserve_fitness_room_service import ReserveFitnessRoomService


class ReserveFitnessRoomController:

    def __init__(
        self,
        service: ReserveFitnessRoomService = None,
    ):
        self._service = service if service is not None else ReserveFitnessRoomService()

    async def add_reservation(self, reservation) -> Reservation | None:
        return await self._service.add_reservation(reservation)

    async def rooms(self) -> List[Room]:
        return await self._service.get_rooms()

    async def reservations(self):
        return await self._service.get_all_reservations()

    async def delete_reservation(self, id_r) -> bool:
        return await self._service.delete_reservation(id_r)

    async def update_reservation(self, reservation) -> Reservation | None:
        return await self._service.update_reservation(reservation)

    async def get_reservation_by_id(self, id_r) -> Reservation | None:
        return await self._service.get_reservation_by_id(id_r)

    async def get_all_pti(self):
        return await self._service.get_all_pti()
