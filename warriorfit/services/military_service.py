from warriorfit.data.db.servicemen_repository import ServicemenRepository


class MilitaryService:
    def __init__(self):
        self._repo = ServicemenRepository()

    async def add_service_men(self, service_men):
        return await self._repo.create_serviceman(service_men)

    async def update_service_men(self, service_men):
        return await self._repo.update_serviceman(service_men=service_men)

    async def get_all_service_men(self):
        return await self._repo.list_all()

    async def get_servicemen_by_id(self, ind_id):
        return await self._repo.get_servicemen_by_id(ind_id)

    async def get_servicemen_by_serial(self, serial: str, lazy=True):
        return await self._repo.get_by_service_number(serial, lazy=lazy)

    async def get_all_units(self):
        return await self._repo.list_all_units()

    async def add_unit(self, unit):
        return await self._repo.add_unit(unit)

    def get_unit_by_id(self, ind_id):
        return self._repo.get_by_unit_id(ind_id)

    async def get_all_be_mil_from_unit(self, own_unit):
        return await self._repo.get_all_be_mil_from_unit(own_unit)
