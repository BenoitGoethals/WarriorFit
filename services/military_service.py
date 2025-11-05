from data.db.servicemen_repository import ServicemenRepository
from services.service import Service


class MilitaryService(Service):
    def __init__(self):
        super().__init__()
        self._repo=ServicemenRepository()

    async def add_service_men(self, service_men):
        return await self._repo.create_serviceman(service_men)

    async def update_service_men(self, service_men):
        return await self._repo.update_serviceman(service_men=service_men)

    async def get_all_service_men(self):
        return await self._repo.list_all()

    async def get_servicemen_by_id(self, id):
        return await self._repo.get_servicemen_by_id(id)


    async def get_all_units(self):
        return await self._repo.list_all_units()

    async def add_unit(self, unit):
        return  await self._repo.add_unit(unit)

    def get_unit_by_id(self, id):
        return self._repo.get_by_unit_id(id)

