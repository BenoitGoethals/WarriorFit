from __future__ import annotations
from typing import Optional, List, Dict, Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import TestSession, PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest
from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService


class DashboardController:
    """
    Encapsulates all Dashboard data retrieval and computations.
    The UI layer should only call these methods and render their results.
    """
    def __init__(self, db: DBService, be_mil_service: Optional[BEMILService] = None) -> None:
        self.db = db
        self.be_mil_service = be_mil_service or BEMILService()

    # ---------- Sessions ----------
    async def sessions_by_type(self, test_type: TypeFitnessTest) -> List[TestSession]:
        try:
            return await self.db.get_all_test_sessions_type_fitnessTest(test_type)
        except Exception:
            return []

    async def all_sessions(self) -> List[TestSession]:
        try:
            return await self.db.get_all_test_sessions()
        except Exception:
            return []

    # ---------- PHEF helpers ----------
    async def phef_total_score(self, test: PhefTest) -> float:
        val = await self.be_mil_service.get_be_mil_by_id(test.serial_number or "")
        age = val.age_from_birthdate()
        gender = val.gender
        score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, age, gender)
        score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, age, gender)
        score_run = PhefCalculator.running_result(test.running_time, age, gender)
        return (score_run * (50 / 20)) + ((score_r + score_l) * (25 / 20))

    # ---------- Top cards ----------
    async def phef_stats(self) -> Dict[str, Any]:
        sessions = await self.sessions_by_type(TypeFitnessTest.PHEF)
        total_tests = 0
        passed_tests = 0
        for sess in sessions:
            tests = await self.db.get_all_phef(sess.id)
            for test in tests:
                total_tests += 1
                if await self.phef_total_score(test) >= 50:
                    passed_tests += 1
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        return {"total": total_tests, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-success"}

    async def combat_stats(self) -> Dict[str, Any]:
        sessions = await self.sessions_by_type(TypeFitnessTest.COMBAT)
        total_tests = 0
        passed_tests = 0
        for sess in sessions:
            tests = await self.db.get_all_combat_test(sess.id)
            for test in tests:
                total_tests += 1
                if test.rope_passed and test.obstacle_passed and test.running_time <= 7200:
                    passed_tests += 1
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        return {"total": total_tests, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-success"}

    async def functional_stats(self) -> Dict[str, Any]:
        sessions = await self.sessions_by_type(TypeFitnessTest.FUNCTIONAL)
        total_tests = 0
        total_score = 0
        for sess in sessions:
            tests = await self.db.get_all_functional_test(sess.id)
            for test in tests:
                total_tests += 1
                total_score += test.push_ups + test.sit_ups + test.pull_ups
        avg_score = (total_score / total_tests) if total_tests > 0 else 0
        return {"total": total_tests, "sub_value": f"{avg_score:.1f}", "sub_label": "Avg Total Score", "sub_class": "text-warning"}

    async def swimming_stats(self) -> Dict[str, Any]:
        sessions = await self.sessions_by_type(TypeFitnessTest.SWIMMING)
        total_tests = 0
        passed_tests = 0
        for sess in sessions:
            tests = await self.db.get_all_combat_swimming_test(sess.id)
            for test in tests:
                total_tests += 1
                if test.swim_paased:
                    passed_tests += 1
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        return {"total": total_tests, "sub_value": f"{pass_rate:.1f}%", "sub_label": "Pass Rate", "sub_class": "text-info"}

    # ---------- Charts ----------
    async def distribution_pie_html(self) -> str:
        phef_sessions = await self.sessions_by_type(TypeFitnessTest.PHEF)
        combat_sessions = await self.sessions_by_type(TypeFitnessTest.COMBAT)
        functional_sessions = await self.sessions_by_type(TypeFitnessTest.FUNCTIONAL)
        swimming_sessions = await self.sessions_by_type(TypeFitnessTest.SWIMMING)

        phef_count = await self._count_tests(phef_sessions, self.db.get_all_phef)
        combat_count = await self._count_tests(combat_sessions, self.db.get_all_combat_test)
        functional_count = await self._count_tests(functional_sessions, self.db.get_all_functional_test)
        swimming_count = await self._count_tests(swimming_sessions, self.db.get_all_combat_swimming_test)

        data = pd.DataFrame({
            'Test Type': ['PHEF', 'Combat', 'Functional', 'Swimming'],
            'Count': [phef_count, combat_count, functional_count, swimming_count]
        })
        fig = px.pie(data, values='Count', names='Test Type',
                     color_discrete_sequence=['#0d6efd', '#198754', '#ffc107', '#0dcaf0'])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return fig.to_html(include_plotlyjs='cdn', div_id="test_distribution")

    async def pass_fail_bar_html(self) -> str:
        phef_sessions = await self.sessions_by_type(TypeFitnessTest.PHEF)
        phef_pass = phef_fail = 0
        for sess in phef_sessions:
            for test in await self.db.get_all_phef(sess.id):
                if await self.phef_total_score(test) >= 50:
                    phef_pass += 1
                else:
                    phef_fail += 1

        combat_sessions = await self.sessions_by_type(TypeFitnessTest.COMBAT)
        combat_pass = combat_fail = 0
        for sess in combat_sessions:
            for test in await self.db.get_all_combat_test(sess.id):
                passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                combat_pass += 1 if passed else 0
                combat_fail += 0 if passed else 1

        functional_sessions = await self.sessions_by_type(TypeFitnessTest.FUNCTIONAL)
        func_pass = func_fail = 0
        for sess in functional_sessions:
            for test in await self.db.get_all_functional_test(sess.id):
                total = test.push_ups + test.sit_ups + test.pull_ups
                func_pass += 1 if total >= 50 else 0
                func_fail += 0 if total >= 50 else 1

        swim_sessions = await self.sessions_by_type(TypeFitnessTest.SWIMMING)
        swim_pass = swim_fail = 0
        for sess in swim_sessions:
            for test in await self.db.get_all_combat_swimming_test(sess.id):
                swim_pass += 1 if test.swim_paased else 0
                swim_fail += 0 if test.swim_paased else 1

        fig = go.Figure(data=[
            go.Bar(name='Passed', x=['PHEF', 'Combat', 'Functional', 'Swimming'],
                   y=[phef_pass, combat_pass, func_pass, swim_pass], marker_color='#198754'),
            go.Bar(name='Failed', x=['PHEF', 'Combat', 'Functional', 'Swimming'],
                   y=[phef_fail, combat_fail, func_fail, swim_fail], marker_color='#dc3545')
        ])
        fig.update_layout(barmode='group', margin=dict(t=20, b=40, l=40, r=20),
                          xaxis_title="Test Type", yaxis_title="Count")
        return fig.to_html(include_plotlyjs='cdn', div_id="pass_fail")

    async def recent_sessions_df(self) -> pd.DataFrame:
        all_sessions = await self.all_sessions()
        all_sessions.sort(key=lambda x: x.datetime_start, reverse=True)
        recent = all_sessions[:10]
        return pd.DataFrame([{
            'Date': sess.datetime_start.strftime('%Y-%m-%d %H:%M'),
            'Type': sess.type_test.name,
            'PTI': sess.serial_number_pti or 'N/A',
            'Status': '✅ Executed' if sess.executed else '⏳ Pending',
            'Description': sess.description or ''
        } for sess in recent])

    async def phef_hist_html(self) -> str | None:
        phef_sessions = await self.sessions_by_type(TypeFitnessTest.PHEF)
        scores = []
        for sess in phef_sessions:
            for test in await self.db.get_all_phef(sess.id):
                scores.append(await self.phef_total_score(test))
        if not scores:
            return None
        fig = px.histogram(scores, nbins=20,
                           labels={'value': 'Score', 'count': 'Frequency'},
                           color_discrete_sequence=['#0d6efd'])
        fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                          xaxis_title="PHEF Score", yaxis_title="Number of Tests",
                          showlegend=False)
        fig.add_vline(x=50, line_dash="dash", line_color="red",
                      annotation_text="Pass Threshold")
        return fig.to_html(include_plotlyjs='cdn', div_id="phef_hist")

    async def performance_trend_html(self) -> str | None:
        all_sessions = await self.all_sessions()
        all_sessions.sort(key=lambda x: x.datetime_start)
        trend_data = []
        for sess in all_sessions:
            date = sess.datetime_start.strftime('%Y-%m-%d')
            if sess.type_test == TypeFitnessTest.PHEF:
                for test in await self.db.get_all_phef(sess.id):
                    trend_data.append({'Date': date, 'Type': 'PHEF', 'Score': await self.phef_total_score(test)})
            elif sess.type_test == TypeFitnessTest.COMBAT:
                for test in await self.db.get_all_combat_test(sess.id):
                    passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                    trend_data.append({'Date': date, 'Type': 'Combat', 'Score': 100 if passed else 0})
            elif sess.type_test == TypeFitnessTest.FUNCTIONAL:
                for test in await self.db.get_all_functional_test(sess.id):
                    total = test.push_ups + test.sit_ups + test.pull_ups
                    trend_data.append({'Date': date, 'Type': 'Functional', 'Score': total})
        if not trend_data:
            return None
        df = pd.DataFrame(trend_data)
        df_avg = df.groupby(['Date', 'Type'])['Score'].mean().reset_index()
        fig = px.line(df_avg, x='Date', y='Score', color='Type',
                      color_discrete_map={'PHEF': '#0d6efd', 'Combat': '#198754', 'Functional': '#ffc107'})
        fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                          xaxis_title="Date", yaxis_title="Average Score")
        return fig.to_html(include_plotlyjs='cdn', div_id="trends")

    # ---------- Internals ----------
    @staticmethod
    async def _count_tests(sessions: List[TestSession], fetch_tests_coro) -> int:
        total = 0
        for sess in sessions:
            tests = await fetch_tests_coro(sess.id)
            total += len(tests)
        return total