# Python
from __future__ import annotations

import pandas as pd

from services.data_collector import DataCollector
from services.be_mil_service import BEMILService


class IndTestShowController:

    def __init__(self):
        self.be_mil = BEMILService()

    async def find_military(self, serial: str):
        return await self.be_mil.get_be_mil_by_id(serial)

    async def collect_tests_df(self, serial: str) -> pd.DataFrame:
        try:
            df = await DataCollector().collect_tests_for_serial(serial)
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()