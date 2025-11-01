from __future__ import annotations

from typing import Optional
import pandas as pd

from config.appliccation_config import ApplicationConfig
from services.data_collector import DataCollector
from services.be_mil_service import BEMILService


class StatusTestsController:
    def __init__(self, mil_service: Optional[BEMILService] = None):
        self._mil_service = mil_service or BEMILService()
        self.data_collector = DataCollector()
        self.unit_name: str = ApplicationConfig().own_unit

    async def get_data(self) -> pd.DataFrame:
       data = await DataCollector().collect_all_mil_from_own_unit_not_executed_phefs()
       return data

