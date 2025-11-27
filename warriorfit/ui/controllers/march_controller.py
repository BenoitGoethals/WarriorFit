import logging
from typing import Optional

from warriorfit.data.db.db_model import ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_march import ServiceMarch


class MarchController:

    def __init__(self,) -> None:
        self._service = ServiceMarch()
        self.be_mil_service = MilitaryService()
        self._logger = logging.getLogger(__name__)

    async def get_all_march(self):
        return await self._service.get_all_march()

    async def add_march(self, new_march):
        return await self._service.add_march(new_march)

    async def update_march(self, updated_march):
        return await self._service.update_march(updated_march)

    async def delete_march(self, current_id):
        return await self._service.delete_march(current_id)

    async def search_military(self, serial_nr: str) -> Optional[ServiceMen]:
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)
