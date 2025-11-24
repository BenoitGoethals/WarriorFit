# Python
from __future__ import annotations

import pandas as pd

from warriorfit.services.data_collector import DataCollector
from warriorfit.services.military_service import MilitaryService


class IndTestShowController:

    def __init__(self):
        self.be_mil = MilitaryService()

    async def find_military(self, serial: str):
        return await self.be_mil.get_servicemen_by_serial(serial,lazy=False)

    async def collect_tests_df(self, serial: str) -> pd.DataFrame:
        try:
            df = await DataCollector().collect_tests_for_serial(serial,current_year=False)


            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()