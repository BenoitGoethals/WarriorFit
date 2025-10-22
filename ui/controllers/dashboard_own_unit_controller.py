from __future__ import annotations
from typing import Optional, List, Dict, Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.appliccation_config import ApplicationConfig
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import TestSession, PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest
from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService

from services.service_test import ServiceTest


class DashboardOwnUnitController:
    """
    Dashboard controller focused on a single 'own unit'.
    Provides pre-aggregated stats, charts HTML, and tables for the page.
    """
    def __init__(self) -> None:
        self._service = ServiceTest()
        self.be_mil_service = BEMILService()
        self.unit_name=ApplicationConfig().own_unit

    # ---------- helpers ----------
    async def own_unit_serials(self) -> set[str]:
        try:
            people = await self.be_mil_service.get_all_be_mil_from_unit(self.unit_name)
            return {p.service_number for p in (people or [])}
        except Exception as e:
            return set()

    async def phef_total_score(self, test: PhefTest) -> float:
        val = await self.be_mil_service.get_be_mil_by_id(test.serial_number or "")
        age = val.age_from_birthdate()
        gender = val.gender
        score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, age, gender)
        score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, age, gender)
        score_run = PhefCalculator.running_result(test.running_time, age, gender)
        return (score_run * (50 / 20)) + ((score_r + score_l) * (25 / 20))

    # ---------- fetch all tests by type but filtered to own unit ----------
    async def _tests_for_unit(self, t: TypeFitnessTest) -> List[Any]:
        sessions = await self._service.get_all_test_sessions()
        sessions.sort(
            key=lambda x: x.datetime_start,
            reverse=True,
        )
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
            results.extend([t for t in tests if getattr(t, "serial_number", None) in serials])
        return results

    # ---------- top-cards ----------
    async def personnel_stats(self) -> Dict[str, Any]:
        serials = await self.own_unit_serials()
        phef_tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        passed = failed = 0
        for t in phef_tests:
            try:
                total = await self.phef_total_score(t)
            except Exception:
                total = 0
            if total >= 50:
                passed += 1
            else:
                failed += 1
        subtitle = f"✅ {passed} | ❌ {failed}"
        return {"total": len(serials), "sub_value": subtitle, "sub_label": "PHEF Passed | Failed", "sub_class": "text-secondary"}

    async def phef_stats(self) -> Dict[str, Any]:
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        total_tests = len(tests)
        passed = 0
        for t in tests:
            if await self.phef_total_score(t) >= 50:
                passed += 1
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        return {"total": total_tests, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-success"}

    async def combat_stats(self) -> Dict[str, Any]:
        tests: List[CombatTestParatrooper] = await self._tests_for_unit(TypeFitnessTest.COMBAT)
        total = len(tests)
        passed = sum(1 for t in tests if t.rope_passed and t.obstacle_passed and t.running_time <= 7200)
        pass_rate = (passed / total * 100) if total > 0 else 0
        return {"total": total, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-success"}

    async def functional_stats(self) -> Dict[str, Any]:
        tests: List[FunctionalTest] = await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL)
        total = len(tests)
        agg = sum(int(t.push_ups or 0) + int(t.sit_ups or 0) + int(t.pull_ups or 0) for t in tests)
        avg = (agg / total) if total > 0 else 0
        return {"total": total, "sub_value": f"{avg:.1f}", "sub_label": "Avg Total Score", "sub_class": "text-warning"}

    async def swimming_stats(self) -> Dict[str, Any]:
        tests: List[CombatSwimmingTest] = await self._tests_for_unit(TypeFitnessTest.SWIMMING)
        total = len(tests)
        passed = sum(1 for t in tests if t.swim_paased)
        pass_rate = (passed / total * 100) if total > 0 else 0
        return {"total": total, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-info"}

    # ---------- charts ----------
    async def distribution_pie_html(self) -> str:
        counts = {
            "PHEF": len(await self._tests_for_unit(TypeFitnessTest.PHEF)),
            "Combat": len(await self._tests_for_unit(TypeFitnessTest.COMBAT)),
            "Functional": len(await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL)),
            "Swimming": len(await self._tests_for_unit(TypeFitnessTest.SWIMMING)),
        }
        data = pd.DataFrame({"Test Type": list(counts.keys()), "Count": list(counts.values())})
        fig = px.pie(data, values="Count", names="Test Type",
                     color_discrete_sequence=["#0d6efd", "#198754", "#ffc107", "#0dcaf0"])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return fig.to_html(include_plotlyjs="cdn", div_id="own_unit_distribution")

    async def pass_fail_bar_html(self) -> str:
        phef_tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        phef_pass = len([t for t in phef_tests if await self.phef_total_score(t) >= 50])
        phef_fail = len(phef_tests) - phef_pass

        combat_tests: List[CombatTestParatrooper] = await self._tests_for_unit(TypeFitnessTest.COMBAT)
        combat_pass = sum(1 for t in combat_tests if t.rope_passed and t.obstacle_passed and t.running_time <= 7200)
        combat_fail = len(combat_tests) - combat_pass

        functional_tests: List[FunctionalTest] = await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL)
        func_pass = sum(1 for t in functional_tests if (int(t.push_ups or 0) + int(t.sit_ups or 0) + int(t.pull_ups or 0)) >= 50)
        func_fail = len(functional_tests) - func_pass

        swim_tests: List[CombatSwimmingTest] = await self._tests_for_unit(TypeFitnessTest.SWIMMING)
        swim_pass = sum(1 for t in swim_tests if t.swim_paased)
        swim_fail = len(swim_tests) - swim_pass

        fig = go.Figure(data=[
            go.Bar(name="Passed", x=["PHEF", "Combat", "Functional", "Swimming"],
                   y=[phef_pass, combat_pass, func_pass, swim_pass], marker_color="#198754"),
            go.Bar(name="Failed", x=["PHEF", "Combat", "Functional", "Swimming"],
                   y=[phef_fail, combat_fail, func_fail, swim_fail], marker_color="#dc3545"),
        ])
        fig.update_layout(barmode="group", margin=dict(t=20, b=40, l=40, r=20),
                          xaxis_title="Test Type", yaxis_title="Count")
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
                rows.append({
                    "Date": sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                    "Type": sess.type_test.name,
                    "PTI": sess.serial_number_pti or "N/A",
                    "Status": "✅ Executed" if sess.executed else "⏳ Pending",
                    "Description": sess.description or "",
                })
            if len(rows) >= 10:
                break
        return pd.DataFrame(rows)

    async def phef_hist_html(self) -> str | None:
        serials = await self.own_unit_serials()
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        scores = []
        for t in tests:
            if t.serial_number in serials:
                scores.append(await self.phef_total_score(t))
        if not scores:
            return None
        fig = px.histogram(scores, nbins=20,
                           labels={"value": "Score", "count": "Frequency"},
                           color_discrete_sequence=["#0d6efd"])
        fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                          xaxis_title="PHEF Score", yaxis_title="Number of Tests",
                          showlegend=False)
        fig.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Pass Threshold")
        return fig.to_html(include_plotlyjs="cdn", div_id="own_unit_phef_hist")

    async def failed_phef_df(self) -> pd.DataFrame:
        tests: List[PhefTest] = await self._tests_for_unit(TypeFitnessTest.PHEF)
        rows = []
        for t in tests:
            total = 0
            try:
                total = await self.phef_total_score(t)
            except Exception:
                pass
            if total < 50:
                rows.append({"Type": "PHEF", "Serial": t.serial_number, "Reason": f"Total {total:.1f} < 50"})
        return pd.DataFrame(rows)

    async def failed_all_df(self) -> pd.DataFrame:
        rows = []

        for t in await self._tests_for_unit(TypeFitnessTest.PHEF):
            try:
                total = await self.phef_total_score(t)
            except Exception:
                total = 0
            if total < 50:
                rows.append({"Type": "PHEF", "Serial": t.serial_number, "Reason": f"Total {total:.1f} < 50"})

        for t in await self._tests_for_unit(TypeFitnessTest.COMBAT):
            rope = bool(getattr(t, "rope_passed", False))
            obst = bool(getattr(t, "obstacle_passed", False))
            run_s = int(getattr(t, "running_time", 0) or 0)
            passed = rope and obst and run_s <= 7200
            if not passed:
                reason_parts = []
                if not rope: reason_parts.append("Rope")
                if not obst: reason_parts.append("Obstacle")
                if run_s > 7200: reason_parts.append(f"Run {run_s}s > 7200s")
                rows.append({"Type": "Combat", "Serial": t.serial_number, "Reason": ", ".join(reason_parts) or "Failed"})

        for t in await self._tests_for_unit(TypeFitnessTest.FUNCTIONAL):
            total = int(getattr(t, "push_ups", 0) or 0) + int(getattr(t, "sit_ups", 0) or 0) + int(getattr(t, "pull_ups", 0) or 0)
            if total < 50:
                rows.append({"Type": "Functional", "Serial": t.serial_number, "Reason": f"Total {total} < 50"})

        for t in await self._tests_for_unit(TypeFitnessTest.SWIMMING):
            if not bool(getattr(t, "swim_paased", False)):
                rows.append({"Type": "Swimming", "Serial": t.serial_number, "Reason": "Not passed"})

        return pd.DataFrame(rows)