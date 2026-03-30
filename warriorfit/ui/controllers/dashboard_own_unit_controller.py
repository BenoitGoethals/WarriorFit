from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from warriorfit.config.appliccation_config import ApplicationConfig

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import (
    PhefTest,
    FunctionalTest,
    CombatTestParatrooper,
    CombatSwimmingTest,
    ServiceMen,
    March,
)
from warriorfit.logic.phef_calculator import PhefCalculator

from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_march import ServiceMarch
from warriorfit.services.service_test import ServiceTest


class DashboardOwnUnitController:
    """
    Handles operations and statistics related to a military unit's fitness tests and personnel
    performance evaluation.

    This class is designed to provide tools for fetching data related to a military unit’s
    personnel, their fitness tests, and overall evaluation metrics. It includes methods to
    gather and calculate statistics for various fitness test types, manage cached test and
    personnel data, and retrieve results as needed.

    :ivar be_mil_service: Service used for fetching personnel data specific to a unit.
    :type be_mil_service: MilitaryService
    :ivar unit_name: Name of the owning unit.
    :type unit_name: str
    """

    def __init__(
        self,
        test_service: ServiceTest = None,
        mil_service: MilitaryService = None,
        march_service: ServiceMarch = None,
        config: ApplicationConfig = None,
    ) -> None:
        _config = config if config is not None else ApplicationConfig()
        self._service = test_service if test_service is not None else ServiceTest()
        self.be_mil_service = (
            mil_service if mil_service is not None else MilitaryService()
        )
        self.unit_name = _config.own_unit
        self._mils = None
        self._all_military_own_unit = None
        self._results_tests_for_unit: dict[str, list[Any]] = {}
        self._march_service = (
            march_service if march_service is not None else ServiceMarch()
        )

    # ---------- helpers ----------
    async def own_unit_serials(self) -> set[str]:
        """
        Asynchronously fetches and returns a set of unique serial numbers associated
        with the owning unit. If the serial numbers are already cached, it retrieves
        them from the stored data; otherwise, it queries the external service to update
        the cache.

        :raises Exception: If an error occurs during the external service call.

        :return: A set of unique serial numbers associated with the owning unit.
        :rtype: set[str]
        """
        try:
            if self._mils is None:
                people = await self.be_mil_service.get_all_be_mil_from_unit(
                    self.unit_name
                )
                self._mils = {p.service_number for p in (people or [])}
            return self._mils
        except (AttributeError, TypeError) as e:
            return set()

    async def _get_all_military_own_unit(self) -> dict[str, ServiceMen]:
        """
        Fetches all servicemen belonging to the current unit asynchronously.

        This method fetches the details of all servicemen from a specific unit using
        an external service. It caches the result after the first fetch and returns
        the cached data on subsequent calls.

        :raises Exception: If an error occurs during the fetching of servicemen.

        :return: A dictionary where keys are the service numbers (str) of servicemen
            and values are `ServiceMen` objects representing detailed servicemen
            information.
        :rtype: dict[str, ServiceMen]
        """
        try:
            if self._all_military_own_unit is None:
                data = await self.be_mil_service.get_all_be_mil_from_unit(
                    self.unit_name
                )
                self._all_military_own_unit = {s.service_number: s for s in data}
            return self._all_military_own_unit
        except (AttributeError, TypeError) as e:
            return {}

    async def phef_total_score(self, test: PhefTest) -> tuple[float, bool]:
        """
        Calculate the total PHEF (Physical Fitness Evaluation Framework) score for a given test.

        The method computes a military personnel’s PHEF total score using results for running time
        and side bridge exercises (left and right). Scores are adjusted based on the individual's
        age and gender. The final score is derived using weighted calculations for running and
        side bridge results.

        :param test: Test data containing the side bridge, running time, and serial number details.
        :type test: PhefTest
        :return: The total calculated PHEF score as a float.
        :rtype: float
        """
        mils: dict[str, ServiceMen] = await self._get_all_military_own_unit()
        val: ServiceMen = mils.get(test.serial_number)
        age = val.age_from_birthdate()
        gender = val.gender
        score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, age, gender)
        score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, age, gender)
        score_run = PhefCalculator.running_result(test.running_time, age, gender)
        passed = score_run >= 10 and score_r + score_l >= 20
        return (score_run * (50 / 20)) + ((score_r + score_l) * (25 / 20)), passed

    def reset_cache(self):
        self._mils = None
        self._results_tests_for_unit = {}

    async def _tests_for_unit(self, t: TypeFitnessTest) -> List[Any]:
        """
        Fetches all test results for a specific unit fitness test type asynchronously.

        This method retrieves all test sessions, sorts them by their start date
        in descending order, and fetches test results of the specified type for
        the sessions. It filters the results to include only those associated
        with the serial numbers relevant to the unit. If the test results for
        the specified type are already cached, they are returned directly.

        :param t: The type of fitness test for which results are to be retrieved.
        :type t: TypeFitnessTest
        :return: A list of filtered test results associated with the specified fitness test type.
        :rtype: List[Any]
        """
        key = t.name
        if key not in self._results_tests_for_unit:
            sessions = await self._service.get_all_test_sessions()
            sessions.sort(key=lambda x: x.datetime_start, reverse=True)
            serials = await self.own_unit_serials()
            results: List[Any] = []
            for sess in sessions:
                if t == TypeFitnessTest.PHEF:
                    tests = await self._service.get_all_phef(sess.id)
                elif t == TypeFitnessTest.COMBAT:
                    tests = await self._service.get_all_combat_test(sess.id)
                elif t == TypeFitnessTest.FUNCTIONAL:
                    tests = await self._service.get_all_functional_test(sess.id)
                elif t == TypeFitnessTest.SWIMMING:
                    tests = await self._service.get_all_combat_swimming_test(sess.id)
                else:
                    tests = []
                results.extend(
                    [
                        test
                        for test in tests
                        if getattr(test, "serial_number", None) in serials
                    ]
                )
            self._results_tests_for_unit[key] = results
        return self._results_tests_for_unit.get(key, [])

    # ---------- top-cards ----------
    async def personnel_stats(self) -> Dict[str, Any]:
        """
        Gathers and returns statistical information about personnel based on their unit's PHEF
        (Physical Health Evaluation and Fitness) test results. The statistics include the total
        number of personnel, the count of individuals who passed or failed the tests, and a
        formatted subtitle providing a quick summary.

        :return: A dictionary containing personnel statistics and related details.
        :rtype: Dict[str, Any]
        """
        serials = await self.own_unit_serials()
        phef_tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        passed = failed = 0
        passed_test = False
        for t in phef_tests:
            try:
                _, passed_test = await self.phef_total_score(t)
            except (AttributeError, TypeError, KeyError):
                passed_test = False
            if passed_test:
                passed += 1
            else:
                failed += 1
        subtitle = f"✅ {passed} | ❌ {failed}"
        return {
            "total": len(serials),
            "sub_value": subtitle,
            "sub_label": "PHEF Passed | Failed",
            "sub_class": "text-secondary",
        }

    async def phef_stats(self) -> Dict[str, Any]:
        """
        Calculate and return PHEF test statistics.
        This method retrieves all PHEF tests for a given unit, calculates the total
        number of tests and determines how many of those tests have a passing score.
        The pass rate is evaluated and returned along with the total counts in a
        formatted dictionary.

        :return: A dictionary containing the total number of tests, pass rate (as a
            percentage), a label for the pass rate, and a CSS class indicating success
            for UI purposes.
        :rtype: Dict[str, Any]
        """
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        total_tests = len(tests)
        passed_tot = 0
        for t in tests:
            _, passed = await self.phef_total_score(t)
            if passed:
                passed_tot += 1
        pass_rate = (passed_tot / total_tests * 100) if total_tests > 0 else 0
        return {
            "total": total_tests,
            "sub_value": f"{pass_rate:.1f}%",
            "sub_label": "Pass Rate",
            "sub_class": "text-success",
        }

    async def combat_stats(self) -> Dict[str, Any]:
        tests: List[CombatTestParatrooper] = await self._tests_for_unit(
            TypeFitnessTest.COMBAT
        )
        total = len(tests)
        passed = sum(
            1
            for t in tests
            if t.rope_passed and t.obstacle_passed and t.running_time <= 7200
        )
        pass_rate = (passed / total * 100) if total > 0 else 0
        return {
            "total": total,
            "sub_value": f"{pass_rate:.1f}%",
            "sub_label": "Pass Rate",
            "sub_class": "text-success",
        }

    async def functional_stats(self) -> Dict[str, Any]:
        tests: List[FunctionalTest] = await self._tests_for_unit(
            TypeFitnessTest.FUNCTIONAL
        )
        total = len(tests)
        agg = sum(
            int(t.push_ups or 0) + int(t.sit_ups or 0) + int(t.pull_ups or 0)
            for t in tests
        )
        avg = (agg / total) if total > 0 else 0
        return {
            "total": total,
            "sub_value": f"{avg:.1f}",
            "sub_label": "Avg Total Score",
            "sub_class": "text-warning",
        }

    async def swimming_stats(self) -> Dict[str, Any]:
        tests: List[CombatSwimmingTest] = await self._tests_for_unit(
            TypeFitnessTest.SWIMMING
        )
        total = len(tests)
        passed = sum(1 for t in tests if t.swim_paased)
        pass_rate = (passed / total * 100) if total > 0 else 0
        return {
            "total": total,
            "sub_value": f"{pass_rate:.1f}%",
            "sub_label": "Pass Rate",
            "sub_class": "text-info",
        }

    async def march_stats(self):
        tests_march: List[March] = await self._march_service.get_all_march_from_unit()
        total_march = len(tests_march)
        passed = sum(1 for t in tests_march if t.succeeded)
        pass_rate = (passed / total_march * 100) if total_march > 0 else 0
        return {
            "total": total_march,
            "sub_value": f"{pass_rate:.1f}%",
            "sub_label": "Pass Rate",
            "sub_class": "text-info",
        }

    # ---------- charts ----------
    async def distribution_pie_html(self) -> str:
        counts = {
            "PHEF": len(await self._tests_for_unit(TypeFitnessTest.PHEF)),
            "Combat": len(await self._tests_for_unit(TypeFitnessTest.COMBAT)),
            "Functional": len(await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL)),
            "Swimming": len(await self._tests_for_unit(TypeFitnessTest.SWIMMING)),
        }
        data = pd.DataFrame(
            {"Test Type": list(counts.keys()), "Count": list(counts.values())}
        )
        fig = px.pie(
            data,
            values="Count",
            names="Test Type",
            color_discrete_sequence=["#0d6efd", "#198754", "#ffc107", "#0dcaf0"],
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return fig.to_html(include_plotlyjs="cdn", div_id="own_unit_distribution")

    async def pass_fail_bar_html(self) -> str:
        phef_tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        phef_pass = 0
        for t in phef_tests:
            _, passed = await self.phef_total_score(t)
            if passed:
                phef_pass += 1
        phef_fail = len(phef_tests) - phef_pass

        combat_tests: List[CombatTestParatrooper] = await self._tests_for_unit(
            TypeFitnessTest.COMBAT
        )
        combat_pass = sum(
            1
            for t in combat_tests
            if t.rope_passed and t.obstacle_passed and t.running_time <= 7200
        )
        combat_fail = len(combat_tests) - combat_pass

        functional_tests: List[FunctionalTest] = await self._tests_for_unit(
            TypeFitnessTest.FUNCTIONAL
        )
        func_pass = sum(
            1
            for t in functional_tests
            if (int(t.push_ups or 0) + int(t.sit_ups or 0) + int(t.pull_ups or 0)) >= 50
        )
        func_fail = len(functional_tests) - func_pass

        swim_tests: List[CombatSwimmingTest] = await self._tests_for_unit(
            TypeFitnessTest.SWIMMING
        )
        swim_pass = sum(1 for t in swim_tests if t.swim_paased)
        swim_fail = len(swim_tests) - swim_pass

        march_tests: List[March] = await self._march_service.get_all_march_from_unit()
        passed_march: int = len([m for m in march_tests if m.succeeded])
        failed_march: int = len([m for m in march_tests if not m.succeeded])

        fig = go.Figure(
            data=[
                go.Bar(
                    name="Passed",
                    x=["PHEF", "Combat", "Functional", "Swimming", "March"],
                    y=[phef_pass, combat_pass, func_pass, swim_pass, passed_march],
                    marker_color="#198754",
                ),
                go.Bar(
                    name="Failed",
                    x=["PHEF", "Combat", "Functional", "Swimming", "March"],
                    y=[phef_fail, combat_fail, func_fail, swim_fail, failed_march],
                    marker_color="#dc3545",
                ),
            ]
        )
        fig.update_layout(
            barmode="group",
            margin=dict(t=20, b=40, l=40, r=20),
            xaxis_title="Test Type",
            yaxis_title="Count",
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="own_unit_pass_fail")

    # ---------- tables ----------
    async def recent_sessions_df(self) -> pd.DataFrame:
        serials = await self.own_unit_serials()
        all_sessions = await self._service.get_all_test_sessions()
        all_sessions.sort(key=lambda x: x.datetime_start, reverse=True)

        rows = []
        for sess in all_sessions:
            tests = []
            if sess.type_test == TypeFitnessTest.PHEF:
                tests = await self._service.get_all_phef(sess.id)
            elif sess.type_test == TypeFitnessTest.COMBAT:
                tests = await self._service.get_all_combat_test(sess.id)
            elif sess.type_test == TypeFitnessTest.FUNCTIONAL:
                tests = await self._service.get_all_functional_test(sess.id)
            elif sess.type_test == TypeFitnessTest.SWIMMING:
                tests = await self._service.get_all_combat_swimming_test(sess.id)
            if any(getattr(t, "serial_number", None) in serials for t in tests):
                rows.append(
                    {
                        "Date": sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                        "Type": sess.type_test.name,
                        "PTI": sess.serial_number_pti or "N/A",
                        "Status": "❌ Canceled" if sess.canceled else "⏳ Planned",
                        "Description": sess.description or "",
                    }
                )
            if len(rows) >= 10:
                break
        return pd.DataFrame(rows)

    async def phef_hist_html(self) -> str | None:
        serials = await self.own_unit_serials()
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        scores = []
        for t in tests:
            if t.serial_number in serials:
                score, _ = await self.phef_total_score(t)
                scores.append(score)
        if not scores:
            return None
        fig = px.histogram(
            scores,
            nbins=20,
            labels={"value": "Score", "count": "Frequency"},
            color_discrete_sequence=["#0d6efd"],
        )
        fig.update_layout(
            margin=dict(t=20, b=40, l=40, r=20),
            xaxis_title="PHEF Score",
            yaxis_title="Number of Tests",
            showlegend=False,
        )
        fig.add_vline(
            x=50, line_dash="dash", line_color="red", annotation_text="Pass Threshold"
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="own_unit_phef_hist")

    async def failed_phef_df(self) -> pd.DataFrame:
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        rows = []
        for t in tests:
            total = 0
            passed = False
            try:
                total, passed = await self.phef_total_score(t)
            except (AttributeError, TypeError, KeyError):
                pass
            if passed:
                rows.append(
                    {
                        "Type": "PHEF",
                        "Serial": t.serial_number,
                        "Reason": f"Total {total:.1f} < 50",
                    }
                )
        return pd.DataFrame(rows)

    async def failed_all_df(self) -> pd.DataFrame:
        rows = []

        for t in await self._tests_for_unit(TypeFitnessTest.PHEF):
            try:
                score, passed = await self.phef_total_score(t)
            except (AttributeError, TypeError, KeyError):
                passed = False
            if passed:
                rows.append(
                    {
                        "Type": "PHEF",
                        "Serial": t.serial_number,
                        "Reason": f"Passed {passed:.1f}",
                    }
                )

        for t in await self._tests_for_unit(TypeFitnessTest.COMBAT):
            rope = bool(getattr(t, "rope_passed", False))
            obst = bool(getattr(t, "obstacle_passed", False))
            run_s = int(getattr(t, "running_time", 0) or 0)
            passed = rope and obst and run_s <= 7200
            if not passed:
                reason_parts = []
                if not rope:
                    reason_parts.append("Rope")
                if not obst:
                    reason_parts.append("Obstacle")
                if run_s > 7200:
                    reason_parts.append(f"Run {run_s}s > 7200s")
                rows.append(
                    {
                        "Type": "Combat",
                        "Serial": t.serial_number,
                        "Reason": ", ".join(reason_parts) or "Failed",
                    }
                )

        for t in await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL):
            total = (
                int(getattr(t, "push_ups", 0) or 0)
                + int(getattr(t, "sit_ups", 0) or 0)
                + int(getattr(t, "pull_ups", 0) or 0)
            )
            if total < 50:
                rows.append(
                    {
                        "Type": "Functional",
                        "Serial": t.serial_number,
                        "Reason": f"Total {total} < 50",
                    }
                )

        for t in await self._tests_for_unit(TypeFitnessTest.SWIMMING):
            if not bool(getattr(t, "swim_paased", False)):
                rows.append(
                    {
                        "Type": "Swimming",
                        "Serial": t.serial_number,
                        "Reason": "Not passed",
                    }
                )

        return pd.DataFrame(rows)
