import logging
from typing import Optional

from data.db.db_model import ServiceMen
from services.military_service import MilitaryService
from services.service_mars import ServiceMars


class MarsController:

    def __init__(self,) -> None:
        self._service = ServiceMars()
        self.be_mil_service = MilitaryService()
        self._logger = logging.getLogger(__name__)

    async def get_all_mars(self):
        return await self._service.get_all_mars()

    async def add_mars(self, new_mars):
        return await self._service.add_mars(new_mars)

    async def update_mars(self, updated_mars):
        return await self._service.update_mars(updated_mars)

    async def delete_mars(self, current_id):
        return await self._service.delete_mars(current_id)

    async def search_military(self, serial_nr: str) -> Optional[ServiceMen]:
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)
