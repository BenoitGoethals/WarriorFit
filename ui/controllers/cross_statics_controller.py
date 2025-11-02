from numpy.ma.extras import average
from shiny import reactive

from services.service_cross import ServiceCross


class CrossStaticsController:
    def __init__(self,) -> None:
        self._service = ServiceCross()
        self._stats=None


    async def load(self):
        self._stats= await self._service.get_cross_stats()

    async def get_average_time(self)-> float:
        return self._stats[0]
    async def get_gap_time(self):
        return self._stats[1]


    async def get_best_time(self):
        return self._stats[2]


    async def get_age_group(self):
        return self._stats[3]

    async def get_gender_time(self):
        return self._stats[4]
