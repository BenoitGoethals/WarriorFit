from __future__ import annotations

import asyncio
from typing import Any

import pandas as pd

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    March,
    MfftEvalTest,
    PhefTest,
    ServiceMen,
)
from warriorfit.logic.mfft_eval_calculator import MfftEvalCalculator
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.data_collector import DataCollector
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.report_generator_pdf import ReportGeneratorPdf
from warriorfit.services.service_march import ServiceMarch
from warriorfit.services.service_test import ServiceTest
from warriorfit.utils.BenchmarkDecorator import benchmark


class OwnUnitController:
    """
    Controller for the 'Own Unit' page.
    - Fetch servicemen for the current unit
    - Build DataFrames for grids
    - Fetch tests for a selected serviceman
    """

    def __init__(
        self,
        mil_service: MilitaryService = None,
        data_collector: DataCollector = None,
        test_service: ServiceTest = None,
        march_service: ServiceMarch = None,
        config: ApplicationConfig = None,
        report_generator_pdf: ReportGeneratorPdf = None,
    ):
        _config = config if config is not None else ApplicationConfig()
        self._mil_service = mil_service if mil_service is not None else MilitaryService()
        self.unit_name: str = _config.own_unit
        self._data_collector = data_collector if data_collector is not None else DataCollector()
        self._service = test_service if test_service is not None else ServiceTest()
        self._service_mars = march_service if march_service is not None else ServiceMarch()
        self._report_generator_pdf = (
            report_generator_pdf if report_generator_pdf is not None else ReportGeneratorPdf()
        )

    @benchmark
    async def fetch_servicemen_df(self) -> pd.DataFrame:
        """
        Asynchronously fetches a DataFrame containing structured information about
        servicemen in a specified unit, including their statuses for various
        tests and attributes.
        """
        data = await self._mil_service.get_all_be_mil_from_unit(self.unit_name)
        service_men_list = data if isinstance(data, list) else ([data] if data is not None else [])

        if not service_men_list:
            return pd.DataFrame(
                columns=[
                    "Service",
                    "Rank",
                    "Last name",
                    "First name",
                    "Gender",
                    "Birthdate",
                    "Para",
                    "Ops Test",
                    "Cluster",
                    "Phef status",
                    "Combat status",
                    "Swim status",
                    "March status",
                    "MFFT status",
                ]
            )

        async def build_row(sm: ServiceMen) -> dict[str, Any]:
            # Run all status checks for this serviceman in parallel
            phef, combat, swim, march, mfft = await asyncio.gather(
                self._is_passed_phef(sm),
                self._is_passed_combat(sm),
                self._is_passed_swim(sm),
                self._is_passed_march(sm),
                self._is_passed_mfft(sm),
            )

            def format_status(val: bool | None) -> str:
                if val is True:
                    return "🟢 Passed"
                if val is False:
                    return "🔴 Failed"
                return "🔴 Not done"

            return {
                "Service": sm.service_number,
                "Rank": sm.rank_service_men.name if sm.rank else "Burger",
                "Last name": sm.last_name,
                "First name": sm.first_name,
                "Gender": getattr(sm.gender, "value", sm.gender) or "",
                "Birthdate": (sm.birthdate or ""),
                "Para": bool(sm.para),
                "Ops Test": bool(sm.ops_test),
                "Cluster": str(sm.cluster),
                "Phef status": format_status(phef),
                "Combat status": format_status(combat),
                "Swim status": format_status(swim),
                "March status": format_status(march),
                "MFFT status": format_status(mfft),
            }

        # Process all servicemen rows concurrently
        rows = await asyncio.gather(*(build_row(sm) for sm in service_men_list))
        return pd.DataFrame(rows)

    async def _is_passed_phef(self, service_men: ServiceMen) -> bool | None:
        """Determines if the service member has passed any PHEF test."""
        mils: list[PhefTest] = await self._service.get_all_phef_mil(service_men.service_number)
        if not mils:
            return None

        age = service_men.age_from_birthdate()
        gender = service_men.gender

        # Generator expression for lazy evaluation
        return any(
            PhefCalculator.calculate_phef_score(
                mil.running_time, mil.sideBridge_l, mil.sideBridge_r, age, gender
            )[4]
            for mil in mils
        )

    async def _is_passed_combat(self, service_men: ServiceMen) -> bool | None:
        """Determines whether the service member has passed combat tests."""
        mils: list[CombatTestParatrooper] = await self._service.get_all_combat_test_mil(
            service_men.service_number
        )
        if not mils:
            return None
        return any(x.running_time <= 7200 and x.rope_passed and x.obstacle_passed for x in mils)

    async def _is_passed_swim(self, service_men: ServiceMen) -> bool | None:
        """Determines whether a service member has passed the combat swimming test."""
        mils: list[CombatSwimmingTest] = await self._service.get_all_combat_test_swim(
            service_men.service_number
        )
        if not mils:
            return None
        return any(x.swim_paased for x in mils)

    async def _is_passed_march(self, sm: ServiceMen) -> bool | None:
        """Determines whether a given ServiceMen has passed at least one march."""
        mars: list[March] = await self._service_mars.get_march_from_service_men(sm.service_number)
        if not mars:
            return None
        return any(x.succeeded for x in mars)

    async def _is_passed_mfft(self, sm: ServiceMen) -> bool | None:
        """Tri-state MFFT verdict using strict semantics.

        ``None``  -> no MFFT test on record (renders as "Not done")
        ``False`` -> at least one MFFT test exists and **any** of them failed
                     (renders as "Failed")
        ``True``  -> at least one MFFT test exists and **all** of them passed
                     (renders as "Passed")
        """
        tests: list[MfftEvalTest] = await self._service.get_all_mfft_eval_mil(sm.service_number)
        if not tests:
            return None
        age = sm.age_from_birthdate()
        any_evaluated = False
        for test in tests:
            try:
                res = MfftEvalCalculator.evaluate(test, sm.cluster, age, sm.gender)
            except (AttributeError, TypeError, KeyError, ValueError):
                continue
            any_evaluated = True
            if not res.passed:
                return False
        return True if any_evaluated else None

    async def fetch_tests_for_serial_df(self, serial: str | None) -> pd.DataFrame:
        """Fetch test data for a given serial number and format it into a DataFrame."""
        tests_df = await DataCollector().collect_tests_for_serial(serial, current_year=True)  # type: ignore[arg-type]
        if tests_df is None or tests_df.empty:
            return pd.DataFrame(columns=["Test Type", "Session", "Status"])

        def _first_non_empty(*vals):
            for v in vals:
                if pd.notna(v) and str(v).strip() != "":
                    return v
            return ""

        out = pd.DataFrame(
            {
                "Test Type": tests_df.get("Type", pd.Series(dtype=str)).apply(_first_non_empty),
                "Session": tests_df.get("Date", pd.Series(dtype=str)).apply(_first_non_empty),
                "Status": tests_df.get("Result", pd.Series(dtype=str)).apply(_first_non_empty),
            }
        )
        return out[["Test Type", "Session", "Status"]].fillna("")
