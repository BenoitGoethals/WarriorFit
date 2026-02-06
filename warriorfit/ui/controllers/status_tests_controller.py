from __future__ import annotations

from typing import Optional
import pandas as pd

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.services.data_collector import DataCollector
from warriorfit.services.military_service import MilitaryService


class StatusTestsController:
    """
    Manages status tests operations and data collection from a specified military unit.

    This class is responsible for interacting with the military service and data
    collection systems. It is used to fetch and manage status test-related data
    originating from the unit defined by the application configuration.

    :ivar data_collector: Instance of DataCollector responsible for collecting data.
    :type data_collector: DataCollector
    :ivar unit_name: Name of the unit as defined in the application configuration.
    :type unit_name: str
    """

    def __init__(self, mil_service: Optional[MilitaryService] = None):
        self._mil_service = mil_service or MilitaryService()
        self.data_collector = DataCollector()
        self.unit_name: str = ApplicationConfig().own_unit

    async def get_data(self) -> pd.DataFrame:
        data = await DataCollector().collect_all_mil_from_own_unit_not_executed_phefs()
        return data
