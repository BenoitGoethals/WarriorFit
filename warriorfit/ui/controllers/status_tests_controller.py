from __future__ import annotations

from typing import Optional
import pandas as pd

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.services.data_collector import DataCollector
from warriorfit.services.military_service import MilitaryService


class StatusTestsController:
    def __init__(self, mil_service: Optional[MilitaryService] = None):
        self._mil_service = mil_service or MilitaryService()
        self.data_collector = DataCollector()
        self.unit_name: str = ApplicationConfig().own_unit

    async def get_data(self) -> pd.DataFrame:
       data = await DataCollector().collect_all_mil_from_own_unit_not_executed_phefs()
       return data

