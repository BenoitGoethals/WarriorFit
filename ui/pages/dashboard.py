from datetime import datetime

from shiny import ui, render, reactive
import pandas as pd

from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService
from core.type_fitness_test import TypeFitnessTest
import plotly.express as px
import plotly.graph_objects as go


class DashboardPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = BEMILService()

    def get_ui(self):
        return ui.nav_panel(
            "Dashboard",
            ui.h2("📊 Dashboard " + str(datetime.now().year)),
            ui.br(),
            ui.layout_columns(
            ui.input_action_button("dashboard_refresh", "Refresh dashboard", class_="btn btn-outline-primary"),
            ),
            # Top row: Status cards
            ui.layout_columns(
                ui.card(
                    ui.card_header("🏃 PHEF Tests", class_="bg-primary text-white"),
                    ui.output_ui("phef_stats"),
                    full_screen=False,
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🪖 Combat Tests", class_="bg-success text-white"),
                    ui.output_ui("combat_stats"),
                    full_screen=False,
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("💪 Functional Tests", class_="bg-warning text-white"),
                    ui.output_ui("functional_stats"),
                    full_screen=False,
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🏊 Swimming Tests", class_="bg-info text-white"),
                    ui.output_ui("swimming_stats"),
                    full_screen=False,
                    class_="text-center",
                ),
                col_widths=[3, 3, 3, 3],
            ),
            
            ui.br(),
            
            # Second row: Charts
            ui.layout_columns(
                ui.card(
                    ui.card_header("Test Type Distribution"),
                    ui.output_ui("test_phef__distribution_chart"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Pass/Fail Rates by Test Type"),
                    ui.output_ui("pass_fail_chart"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            
            ui.br(),
            
            # Third row: Recent sessions and trends
            ui.layout_columns(
                ui.card(
                    ui.card_header("Recent Test Sessions"),
                    ui.output_data_frame("recent_sessions_table"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("PHEF Score Distribution"),
                    ui.output_ui("phef_score_histogram"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            
            ui.br(),
            
            # Fourth row: Performance trends
            ui.layout_columns(
                ui.card(
                    ui.card_header("Performance Trends Over Time"),
                    ui.output_ui("performance_trend_chart"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
        )


    def _ui_stats_card(self, total_text: str, total_value: int | float, sub_value: str | None, sub_label: str, sub_class: str):
        return ui.div(
            ui.h1(str(total_value), class_="display-4 fw-bold"),
            ui.p(total_text),
            ui.hr(),
            (ui.h4(sub_value, class_=sub_class) if sub_value is not None else ui.div()),
            (ui.p(sub_label) if sub_value is not None else ui.div()),
        )

    async def _safe_sessions_by_type(self, test_type: TypeFitnessTest):
        try:
            return await self.db.get_all_test_sessions_type_fitnessTest(test_type)
        except Exception:
            return []

    async def _phef_total_score(self, test) -> float:
        val = await self.be_mil_service.get_be_mil_by_id(test.serial_number or "")
        age = val.age_from_birthdate()
        gender = val.gender
        score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, age, gender)
        score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, age, gender)
        score_run = PhefCalculator.running_result(test.running_time, age, gender)
        return (score_run * (50 / 20)) + ((score_r + score_l) * (25 / 20))

    async def _count_tests(self, sessions, fetch_tests_coro):
        total = 0
        for sess in sessions:
            tests = await fetch_tests_coro(sess.id)
            total += len(tests)
        return total

    async def _collect_tests(self, sessions, fetch_tests_coro):
        results = []
        for sess in sessions:
            results.extend(await fetch_tests_coro(sess.id))
        return results

    def server(self, input, output, session):
        
        # Refresh trigger
        @reactive.Effect
        @reactive.event(input.dashboard_refresh)
        def _trigger_dashboard_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            ui.notification_show("Dashboard reloaded", type="message", duration=2)
        
        # PHEF Statistics
        @output
        @render.ui
        async def phef_stats():
            _ = self.refresh_tick.get()
            try:
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                total_tests = 0
                passed_tests = 0
                for sess in sessions:
                    tests = await self.db.get_all_phef(sess.id)
                    for test in tests:
                        total_tests += 1
                        if await self._phef_total_score(test) >= 50:
                            passed_tests += 1
                pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests", total_tests, f"{pass_rate:.1f}%", "Pass Rate", "text-success")
            except Exception as e:
                ui.notification_show(f"Error loading PHEF statistics: {str(e)}", type="error", duration=5)
                return self._ui_stats_card("Total Tests", 0, None, "", "")


        # Combat Statistics
        @output
        @render.ui
        async def combat_stats():
            _ = self.refresh_tick.get()
            try:
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                total_tests = 0
                passed_tests = 0
                for sess in sessions:
                    tests = await self.db.get_all_combat_test(sess.id)
                    for test in tests:
                        total_tests += 1
                        if test.rope_passed and test.obstacle_passed and test.running_time <= 7200:
                            passed_tests += 1
                pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests", total_tests, f"{pass_rate:.1f}%", "Pass Rate", "text-success")
            except Exception:
                return self._ui_stats_card("Total Tests", 0, None, "", "")

        # Functional Statistics
        @output
        @render.ui
        async def functional_stats():
            _ = self.refresh_tick.get()
            try:
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                total_tests = 0
                total_score = 0
                for sess in sessions:
                    tests = await self.db.get_all_functional_test(sess.id)
                    for test in tests:
                        total_tests += 1
                        total_score += test.push_ups + test.sit_ups + test.pull_ups
                avg_score = (total_score / total_tests) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests", total_tests, f"{avg_score:.1f}", "Avg Total Score", "text-warning")
            except Exception:
                return self._ui_stats_card("Total Tests", 0, None, "", "")

        # Swimming Statistics
        @output
        @render.ui
        async def swimming_stats():
            _ = self.refresh_tick.get()
            try:
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.SWIMMING)
                total_tests = 0
                passed_tests = 0
                for sess in sessions:
                    tests = await self.db.get_all_combat_swimming_test(sess.id)
                    for test in tests:
                        total_tests += 1
                        if test.swim_paased:
                            passed_tests += 1
                pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests", total_tests, f"{pass_rate:.1f}%", "Pass Rate", "text-info")
            except Exception:
                return self._ui_stats_card("Total Tests", 0, None, "", "")

        # Test Distribution Chart
        @output
        @render.ui
        async def test_phef__distribution_chart():
            _ = self.refresh_tick.get()
            try:
                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                combat_sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                functional_sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                swimming_sessions = await self._safe_sessions_by_type(TypeFitnessTest.SWIMMING)
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
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="test_phef__distribution_chart"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        # Pass/Fail Chart
        @output
        @render.ui
        async def pass_fail_chart():
            _ = self.refresh_tick.get()
            try:
                # PHEF pass/fail
                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                phef_pass = phef_fail = 0
                for sess in phef_sessions:
                    for test in await self.db.get_all_phef(sess.id):
                        phef_pass += 1 if await self._phef_total_score(test) >= 50 else 0
                        phef_fail += 0 if await self._phef_total_score(test) >= 50 else 1

                # Combat pass/fail
                combat_sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                combat_pass = combat_fail = 0
                for sess in combat_sessions:
                    for test in await self.db.get_all_combat_test(sess.id):
                        passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                        if passed:
                            combat_pass += 1
                        else:
                            combat_fail += 1

                # Functional pass/fail (threshold 50)
                functional_sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                func_pass = func_fail = 0
                for sess in functional_sessions:
                    for test in await self.db.get_all_functional_test(sess.id):
                        total = test.push_ups + test.sit_ups + test.pull_ups
                        if total >= 50:
                            func_pass += 1
                        else:
                            func_fail += 1

                # Swimming pass/fail
                swim_sessions = await self._safe_sessions_by_type(TypeFitnessTest.SWIMMING)
                swim_pass = swim_fail = 0
                for sess in swim_sessions:
                    for test in await self.db.get_all_combat_swimming_test(sess.id):
                        if test.swim_paased:
                            swim_pass += 1
                        else:
                            swim_fail += 1

                fig = go.Figure(data=[
                    go.Bar(name='Passed', x=['PHEF', 'Combat', 'Functional', 'Swimming'],
                           y=[phef_pass, combat_pass, func_pass, swim_pass],
                           marker_color='#198754'),
                    go.Bar(name='Failed', x=['PHEF', 'Combat', 'Functional', 'Swimming'],
                           y=[phef_fail, combat_fail, func_fail, swim_fail],
                           marker_color='#dc3545')
                ])
                fig.update_layout(barmode='group', margin=dict(t=20, b=40, l=40, r=20),
                                  xaxis_title="Test Type", yaxis_title="Count")
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="pass_fail"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        # Recent Sessions Table
        @output
        @render.data_frame
        async def recent_sessions_table():
            _ = self.refresh_tick.get()
            try:
                all_sessions = await self.db.get_all_test_sessions()
                all_sessions.sort(key=lambda x: x.datetime_start, reverse=True)
                recent = all_sessions[:10]
                data = [{
                    'Date': sess.datetime_start.strftime('%Y-%m-%d %H:%M'),
                    'Type': sess.type_test.name,
                    'PTI': sess.serial_number_pti or 'N/A',
                    'Status': '✅ Executed' if sess.executed else '⏳ Pending',
                    'Description': sess.description or ''
                } for sess in recent]
                return pd.DataFrame(data)
            except Exception:
                return pd.DataFrame()

        # PHEF Score Histogram
        @output
        @render.ui
        async def phef_score_histogram():
            _ = self.refresh_tick.get()
            try:
                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                scores = []
                for sess in phef_sessions:
                    for test in await self.db.get_all_phef(sess.id):
                        scores.append(await self._phef_total_score(test))
                if not scores:
                    return ui.p("No PHEF data available", class_="text-muted")
                fig = px.histogram(scores, nbins=20,
                                   labels={'value': 'Score', 'count': 'Frequency'},
                                   color_discrete_sequence=['#0d6efd'])
                fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                                  xaxis_title="PHEF Score", yaxis_title="Number of Tests",
                                  showlegend=False)
                fig.add_vline(x=50, line_dash="dash", line_color="red",
                              annotation_text="Pass Threshold")
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="phef_hist"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        # Performance Trends Over Time
        @output
        @render.ui
        async def performance_trend_chart():
            _ = self.refresh_tick.get()
            try:
                all_sessions = await self.db.get_all_test_sessions()
                all_sessions.sort(key=lambda x: x.datetime_start)
                trend_data = []
                for sess in all_sessions:
                    date = sess.datetime_start.strftime('%Y-%m-%d')
                    if sess.type_test == TypeFitnessTest.PHEF:
                        for test in await self.db.get_all_phef(sess.id):
                            trend_data.append({'Date': date, 'Type': 'PHEF', 'Score': await self._phef_total_score(test)})
                    elif sess.type_test == TypeFitnessTest.COMBAT:
                        for test in await self.db.get_all_combat_test(sess.id):
                            passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                            trend_data.append({'Date': date, 'Type': 'Combat', 'Score': 100 if passed else 0})
                    elif sess.type_test == TypeFitnessTest.FUNCTIONAL:
                        for test in await self.db.get_all_functional_test(sess.id):
                            total = test.push_ups + test.sit_ups + test.pull_ups
                            trend_data.append({'Date': date, 'Type': 'Functional', 'Score': total})
                if not trend_data:
                    return ui.p("No trend data available", class_="text-muted")
                df = pd.DataFrame(trend_data)
                df_avg = df.groupby(['Date', 'Type'])['Score'].mean().reset_index()
                fig = px.line(df_avg, x='Date', y='Score', color='Type',
                              color_discrete_map={'PHEF': '#0d6efd', 'Combat': '#198754',
                                                  'Functional': '#ffc107'})
                fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                                  xaxis_title="Date", yaxis_title="Average Score")
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="trends"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")


# Public API
_page = DashboardPage(DBService())


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)