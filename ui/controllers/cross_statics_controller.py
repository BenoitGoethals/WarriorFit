from numpy.ma.extras import average

from services.service_cross import ServiceCross


class CrossStaticsController:
    def __init__(self,) -> None:
        self._service = ServiceCross()

    async def get_average_time(self)-> float:
        return await self._service.get_average()

    async def get_gap_time(self):
        return await self._service.get_gap_time()


    async def get_best_time(self):
        return await self._service.get_best_time()


    async def get_age_group(self):
        return await self._service.get_age_group()

    async def get_gender_time(self):
        return await self._service.get_gender_time()
