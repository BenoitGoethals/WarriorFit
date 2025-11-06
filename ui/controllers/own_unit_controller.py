from __future__ import annotations

from typing import List, Dict, Any, Optional
import pandas as pd

from config.appliccation_config import ApplicationConfig

from data.db.db_model import PhefTest, CombatTestParatrooper, CombatSwimmingTest, ServiceMen
from logic.phef_calculator import PhefCalculator
from services.data_collector import DataCollector

from services.military_service import MilitaryService
from services.service_test import ServiceTest


class OwnUnitController:
    """
    Controller for the 'Own Unit' page.
    - Fetch servicemen for the current unit
    - Build DataFrames for grids
    - Fetch tests for a selected serviceman
    """

    def __init__(self, mil_service: Optional[MilitaryService] = None):
        self._mil_service = mil_service or MilitaryService()
        self.unit_name: str = ApplicationConfig().own_unit
        self._data_collector = DataCollector()
        self._service = ServiceTest()

    async def fetch_servicemen_df(self) -> pd.DataFrame:
        data = await self._mil_service.get_all_be_mil_from_unit(self.unit_name)
        service_men_list = data if isinstance(data, list) else ([data] if data is not None else [])
        rows: List[Dict[str, Any]] = [
            {
                "Service #": sm.service_number,
                "Rank": sm.rank,
                "Last name": sm.last_name,
                "First name": sm.first_name,
                "Unit": (getattr(sm.unit, "name", sm.unit) or ""),
                "Gender": getattr(sm.gender, "value", sm.gender) or "",
                "Birthdate": (sm.birthdate or ""),
                "Para": bool(sm.para),
                "Ops Test": bool(sm.ops_test),
                "Phef status": "🟢 Passed" if await self._is_passed_phef(sm) else "🔴 Failed",
                "Combat status": "🟢 Passed" if await self._is_passed_combat(sm) else "🔴 Failed",
                "Swim status": "🟢 Passed" if await self._is_passed_swim(sm) else "🔴 Failed"
            }
            for sm in service_men_list
        ]
        return pd.DataFrame(rows)


    async def _is_passed_phef(self, service_men:ServiceMen):
            mils: list[PhefTest] = await self._service.get_all_phef_mil(service_men.service_number)
            passed = any([(PhefCalculator.calculate_phef_score(mil.running_time, mil.sideBridge_l, mil.sideBridge_r,
                                                               service_men.age_from_birthdate(), service_men.gender)[4]) for mil in mils])
            return passed

    async def _is_passed_combat(self, service_men:ServiceMen):
            mils: list[CombatTestParatrooper] = await self._service.get_all_combat_test_mil(service_men.service_number)
            return len([x for x in mils if x.running_time <= 7200 and x.rope_passed and x.obstacle_passed]) > 0


    async def _is_passed_swim(self,service_men:ServiceMen):
        mils: list[CombatSwimmingTest] = await self._service.get_all_combat_test_swim(service_men.service_number)
        return len([x for x in mils if  x.swim_paased]) > 0



    async def fetch_tests_for_serial_df(self, serial: str|None) -> pd.DataFrame:
        try:
            tests_df = await DataCollector().collect_tests_for_serial(serial)
        except Exception:
            tests_df = pd.DataFrame(
                columns=["Date", "Type", "Details", "Scores", "Total", "Result", "Session ID", "Record ID"]
            )

        if tests_df is None or tests_df.empty:
            return pd.DataFrame(columns=["Test Type", "Session", "Status"])

        def _first_non_empty(*vals):
            for v in vals:
                if pd.notna(v) and str(v).strip() != "":
                    return v
            return ""

        out = pd.DataFrame({
            "Test Type": tests_df.get("Type", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
            "Session": tests_df.get("Date", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
            "Status": tests_df.get("Result", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
        })
        out = out[["Test Type", "Session", "Status"]].fillna("")
        return out