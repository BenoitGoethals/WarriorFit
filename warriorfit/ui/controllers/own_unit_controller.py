from __future__ import annotations

from typing import List, Dict, Any, Optional
import pandas as pd

from warriorfit.config.appliccation_config import ApplicationConfig

from warriorfit.data.model.db_model import PhefTest, CombatTestParatrooper, CombatSwimmingTest, ServiceMen, March
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.data_collector import DataCollector

from warriorfit.services.military_service import MilitaryService
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

    def __init__(self, mil_service: Optional[MilitaryService] = None):
        self._mil_service = mil_service or MilitaryService()
        self.unit_name: str = ApplicationConfig().own_unit
        self._data_collector = DataCollector()
        self._service = ServiceTest()
        self._service_mars = ServiceMarch()

    @benchmark
    async def fetch_servicemen_df(self) -> pd.DataFrame:
        """
        Asynchronously fetches a DataFrame containing structured information about
        servicemen in a specified unit, including their statuses for various
        tests and attributes.

        Summary:
        The method retrieves all servicemen data from a military service for a given
        unit. The data is processed into a tabular format, detailing relevant
        information such as rank, name, gender, birth date, and qualifications like
        para status, operational test results, and other skill statuses.

        The statuses for specific tasks such as PHEF, combat, swimming, and marching
        are determined asynchronously and are represented with visual indicators
        (e.g., a green or red circle for pass or fail respectively).

        :return: A pandas DataFrame containing detailed servicemen information
            structured with fields like Service Number, Rank, Name, Gender, Test
            Results, and other attributes.
        :rtype: pd.DataFrame
        """
        data = await self._mil_service.get_all_be_mil_from_unit(self.unit_name)
        service_men_list = data if isinstance(data, list) else ([data] if data is not None else [])
        rows: List[Dict[str, Any]] = [
            {
                "Service": sm.service_number,
                "Rank": sm.rank_service_men.name if sm.rank else "Burger",
                "Last name": sm.last_name,
                "First name": sm.first_name,
                #"Unit": (getattr(sm.unit, "name", sm.unit) or ""),
                "Gender": getattr(sm.gender, "value", sm.gender) or "",
                "Birthdate": (sm.birthdate or ""),
                "Para": bool(sm.para),
                "Ops Test": bool(sm.ops_test),
                "Phef status": "🟢 Passed" if await self._is_passed_phef(
                    sm) else "🔴 Failed" if await self._is_passed_phef(sm) is False else "🔴 Not done",
                "Combat status": "🟢 Passed" if await self._is_passed_combat(
                    sm) else "🔴 Failed" if await self._is_passed_combat(sm) is False else "🔴 Not done",
                "Swim status": "🟢 Passed" if await self._is_passed_swim(
                    sm) else "🔴 Failed" if await self._is_passed_swim(sm) is False else "🔴 Not done",
                "March status": "🟢 Passed" if await self._is_passed_march(
                    sm) else "🔴 Failed" if await self._is_passed_march(sm) is False else "🔴 Not done"
            }
            for sm in service_men_list
        ]
        return pd.DataFrame(rows)


    async def _is_passed_phef(self, service_men:ServiceMen):
        """
        Determines if the given service member has passed any PHEF (Physical Health Evaluation Form)
        test based on their records. This is achieved by evaluating all PHEF records for the service
        member using the `PhefCalculator`, and checking if at least one of them satisfies the passing
        criteria.

        :param service_men: The service member whose PHEF test results are being evaluated.
        :type service_men: ServiceMen

        :return: A boolean indicating whether the service member has passed any PHEF test.
                 Returns ``None`` if the service member has no PHEF records.
        :rtype: Optional[bool]
        """
        mils: list[PhefTest] = await self._service.get_all_phef_mil(service_men.service_number)
        if not mils or len(mils) == 0:
            return None
        passed = any([(PhefCalculator.calculate_phef_score(mil.running_time, mil.sideBridge_l, mil.sideBridge_r,
                                                           service_men.age_from_birthdate(), service_men.gender)[4]) for mil in mils])
        return passed

    async def _is_passed_combat(self, service_men:ServiceMen):
        """
        Determines whether the given service member has successfully passed combat tests.
        This is based on specific military test conditions such as running time, rope test,
        and obstacle course test performance.

        :param service_men: An instance of ServiceMen representing the service member
                            whose combat test results need to be checked.
        :type service_men: ServiceMen
        :returns: A boolean indicating whether the combat tests were successfully passed.
                  Returns None if no test records are found.
        :rtype: bool | None
        """
        mils: list[CombatTestParatrooper] = await self._service.get_all_combat_test_mil(service_men.service_number)
        if not mils or len(mils) == 0:
            return None
        return len([x for x in mils if x.running_time <= 7200 and x.rope_passed and x.obstacle_passed]) > 0


    async def _is_passed_swim(self,service_men:ServiceMen):
        """
        Determines whether a service member has passed the combat swimming test.

        :param service_men: The service member whose swimming test results are being checked.
        :type service_men: ServiceMen
        :return: True if the service member has passed the swimming test, False if not,
            or None if no swimming test records are found.
        :rtype: bool or None
        """
        mils: list[CombatSwimmingTest] = await self._service.get_all_combat_test_swim(service_men.service_number)
        if not mils or len(mils) == 0:
            return None
        return len([x for x in mils if  x.swim_paased]) > 0

    async def _is_passed_march(self, sm:ServiceMen):
        """
        Determines whether a given ServiceMen has successfully passed at least one march.

        This asynchronous method retrieves a list of marches associated with the
        provided ServiceMen entity by utilizing its service number. It then checks
        whether any of the retrieved marches are marked as succeeded.

        :param sm: The ServiceMen whose marches are being evaluated.
        :type sm: ServiceMen
        :return: True if at least one march associated with the ServiceMen was successful,
                 False otherwise, or None if no marches are available.
        :rtype: Optional[bool]
        """
        mars:List[March] = await self._service_mars.get_march_from_service_men(sm.service_number)
        if not mars or len(mars) == 0:
            return None
        return len([x for x in mars if x.succeeded]) > 0



    async def fetch_tests_for_serial_df(self, serial: str|None) -> pd.DataFrame:
        """
        Fetch test data for a given serial number and format it into a DataFrame.

        This function collects test data for the specified serial number asynchronously.
        The collected data is filtered for the current year and reformatted to include
        only the relevant columns: "Test Type", "Session", and "Status". Each column
        is processed to ensure that non-empty values are fetched. If no data is found,
        an empty DataFrame with the required structure is returned.

        :param serial: The serial number for which test data is to be fetched. Use None
                       if no serial number is specified.
        :type serial: str or None
        :return: A DataFrame containing the test data formatted into "Test Type",
                 "Session", and "Status" columns. If no data is found, returns an
                 empty DataFrame with the same column structure.
        :rtype: pd.DataFrame
        """
        tests_df = await DataCollector().collect_tests_for_serial(serial,current_year=True)
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
        return out[["Test Type", "Session", "Status"]].fillna("")


