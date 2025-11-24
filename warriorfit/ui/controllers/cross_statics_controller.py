import pandas as pd


from warriorfit.data.db.db_model import Runner, ServiceMen

from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_cross import ServiceCross
from warriorfit.utils.formaters import Formatter


class CrossStaticsController:
    def __init__(self, ) -> None:
        self._service = ServiceCross()
        self._mil_service = MilitaryService()
        self._stats = None

    async def load(self):
        self._stats = await self._service.get_cross_stats()

    async def get_average_time(self) -> float:
        return self._stats[0]

    async def get_gap_time(self):
        return self._stats[1]

    async def get_best_time(self):
        return self._stats[2]

    async def get_age_group(self):
        return self._stats[3]

    async def get_gender_time(self):
        return self._stats[4]

    async def best_10_all_df(self)->dict[int,pd.DataFrame]:
        data: dict[int, list[Runner]] = self._stats[5]
        data_panda_dict = {}
        for key, value in data.items():  # Added .items()
            data_p = []
            for runner in value:
                service_men: ServiceMen = await self._mil_service.get_servicemen_by_serial(runner.serial_number)
                data_p.append({
                    'serial_number': runner.serial_number,
                    'rank': service_men.rank,
                    'Name': service_men.first_name + ' ' + service_men.last_name,  # Added space
                    'running_time': Formatter.format_time(runner.running_time),
                    'distance': key,  # Added value for distance
                    'age': service_men.age_from_birthdate(),
                })
            data_panda = pd.DataFrame(
                data_p
            )
            data_panda_dict[key] = data_panda
        return data_panda_dict
