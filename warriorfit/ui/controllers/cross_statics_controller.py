import logging
import pandas as pd


from warriorfit.data.model.db_model import Runner, ServiceMen

from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_cross import ServiceCross
from warriorfit.utils.formaters import Formatter

logger = logging.getLogger(__name__)


class CrossStaticsController:
    def __init__(
        self,
    ) -> None:
        self._service = ServiceCross()
        self._mil_service = MilitaryService()
        self._stats = None

    async def load(self):
        self._stats = await self._service.get_cross_stats()

    async def get_average_time(self) -> float:
        if self._stats is None:
            await self.load()
        return self._stats[0]

    async def get_gap_time(self):
        if self._stats is None:
            await self.load()
        return self._stats[1]

    async def get_best_time(self):
        if self._stats is None:
            await self.load()
        return self._stats[2]

    async def get_age_group(self):
        if self._stats is None:
            await self.load()
        return self._stats[3]

    async def get_gender_time(self):
        if self._stats is None:
            await self.load()
        return self._stats[4]

    async def best_10_all_df(self) -> dict[int, pd.DataFrame]:
        """
        Generates a dictionary of pandas DataFrames representing the best 10 runners
        for each distance. Each DataFrame contains detailed information about the
        runners and their performance.

        The method collects data from the runner statistics and enriches it with
        information fetched asynchronously about the servicemen associated with each
        runner. The resulting structured data is then converted to pandas DataFrames.

        :param self: Instance of the class containing this method.
        :return: A dictionary where the keys are distance values and each value is a
            pandas DataFrame that includes the columns `serial_number`, `rank`,
            `Name`, `running_time`, `distance`, `age`.
        :rtype: dict[int, pd.DataFrame]
        """
        # Ensure stats are loaded before accessing them
        if self._stats is None:
            await self.load()

        data: dict[int, list[Runner]] = self._stats[5]
        data_panda_dict = {}
        for key, value in data.items():  # Added .items()
            if not value:  # Skip keys with no data
                continue
            data_p = []
            for runner in value:
                if runner.serial_number is None:
                    continue
                service_men: ServiceMen = (
                    await self._mil_service.get_servicemen_by_serial(
                        runner.serial_number
                    )
                )
                if service_men:
                    data_p.append(
                        {
                            "serial_number": runner.serial_number,
                            "rank": service_men.rank,
                            "Name": service_men.first_name
                            + " "
                            + service_men.last_name,  # Added space
                            "running_time": Formatter.format_time(runner.running_time),
                            "distance": key,  # Added value for distance
                            "age": service_men.age_from_birthdate(),
                        }
                    )
                else:
                    logger.warning(
                        f"ServiceMen not found for serial_number: {runner.serial_number} (distance: {key})"
                    )
                    data_p.append(
                        {
                            "serial_number": runner.serial_number,
                            "rank": "N/A",
                            "Name": "Unknown",
                            "running_time": Formatter.format_time(runner.running_time),
                            "distance": key,
                            "age": None,
                        }
                    )
            data_panda = pd.DataFrame(data_p)
            data_panda_dict[int(key)] = data_panda
        return data_panda_dict
