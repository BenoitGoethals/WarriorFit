from datetime import datetime
from shiny import ui, render, reactive
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.config.appliccation_config import ApplicationConfig
from ui.services.be_mil_service import BEMILService
from ui.services.db_service import DBService
from core.type_fitness_test import TypeFitnessTest
from logic.phef_calculator import PhefCalculator
from ui.services.defense_external_service import DefenseExternalService


class DashboardOwnUnitPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.external_services = DefenseExternalService()
        self._own_unit = ApplicationConfig().own_unit
        self._be_mil_service = BEMILService()

    def get_ui(self):
        return ui.nav_panel(
            "Own Dashboard",
            ui.h2(f"📊 {self._own_unit} Dashboard " + str(datetime.now().year)),
            ui.br(),
            ui.layout_columns(
                ui.input_action_button("own_unit_refresh", "Refresh", class_="btn btn-outline-primary"),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("👥 Unit Personnel", class_="bg-secondary text-white"),
                    ui.output_ui("own_unit_personnel_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🏃 PHEF Tests", class_="bg-primary text-white"),
                    ui.output_ui("own_unit_phef_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🪖 Combat Tests", class_="bg-success text-white"),
                    ui.output_ui("own_unit_combat_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("💪 Functional Tests", class_="bg-warning text-white"),
                    ui.output_ui("own_unit_functional_stats"),
                    class_="text-center",
                ),
                col_widths=[3, 3, 3, 3],
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Test Type Distribution (Own Unit)"),
                    ui.output_ui("own_unit_test_distribution_chart"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Pass/Fail Rates by Test Type (Own Unit)"),
                    ui.output_ui("own_unit_pass_fail_chart"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Recent Test Sessions (Own Unit)"),
                    ui.output_data_frame("own_unit_recent_sessions_table"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("PHEF Score Distribution (Own Unit)"),
                    ui.output_ui("own_unit_phef_score_histogram"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Performance Trends Over Time (Own Unit)"),
                    ui.output_ui("own_unit_performance_trend_chart"),
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

    def _phef_total_score(self, test) -> float:
        val = self.external_services.get_serviceman_by_serial(test.serial_number or "")
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

    async def _own_unit_serials(self) -> set[str]:
        try:
            people = await self._be_mil_service.get_all_be_mil_from_unit(self._own_unit)
            return {p.serial_number for p in people}
        except Exception:
            return set()

    def server(self, input, output, session):

        @reactive.Effect
        @reactive.event(input.own_unit_refresh)
        def _trigger_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            ui.notification_show("Own unit dashboard reloaded", type="message", duration=2)

        @output
        @render.ui
        async def own_unit_personnel_stats():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                return self._ui_stats_card("Total Personnel", len(serials), None, "", "")
            except Exception:
                return self._ui_stats_card("Total Personnel", 0, None, "", "")

        @output
        @render.ui
        async def own_unit_phef_stats():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                total_tests = passed_tests = 0
                for sess in sessions:
                    for test in await self.db.get_all_phef(sess.id):
                        if test.serial_number in serials:
                            total_tests += 1
                            if self._phef_total_score(test) >= 50:
                                passed_tests += 1
                pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests (Own Unit)", total_tests, f"{pass_rate:.1f}%", "Pass Rate", "text-success")
            except Exception:
                return self._ui_stats_card("Total Tests (Own Unit)", 0, None, "", "")

        @output
        @render.ui
        async def own_unit_combat_stats():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                total_tests = passed_tests = 0
                for sess in sessions:
                    for test in await self.db.get_all_combat_test(sess.id):
                        if test.serial_number in serials:
                            total_tests += 1
                            passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                            if passed:
                                passed_tests += 1
                pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests (Own Unit)", total_tests, f"{pass_rate:.1f}%", "Pass Rate", "text-success")
            except Exception:
                return self._ui_stats_card("Total Tests (Own Unit)", 0, None, "", "")

        @output
        @render.ui
        async def own_unit_functional_stats():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                total_tests = 0
                total_score = 0
                for sess in sessions:
                    for test in await self.db.get_all_functional_test(sess.id):
                        if test.serial_number in serials:
                            total_tests += 1
                            total_score += test.push_ups + test.sit_ups + test.pull_ups
                avg_score = (total_score / total_tests) if total_tests > 0 else 0
                return self._ui_stats_card("Total Tests (Own Unit)", total_tests, f"{avg_score:.1f}", "Avg Total Score", "text-warning")
            except Exception:
                return self._ui_stats_card("Total Tests (Own Unit)", 0, None, "", "")

        @output
        @render.ui
        async def own_unit_test_distribution_chart():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                combat_sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                functional_sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                swimming_sessions = await self._safe_sessions_by_type(TypeFitnessTest.SWIMMING)

                async def _count_for_serials(sessions, fetch):
                    cnt = 0
                    for sess in sessions:
                        for t in await fetch(sess.id):
                            if t.serial_number in serials:
                                cnt += 1
                    return cnt

                phef_count = await _count_for_serials(phef_sessions, self.db.get_all_phef)
                combat_count = await _count_for_serials(combat_sessions, self.db.get_all_combat_test)
                functional_count = await _count_for_serials(functional_sessions, self.db.get_all_functional_test)
                swimming_count = await _count_for_serials(swimming_sessions, self.db.get_all_combat_swimming_test)

                data = pd.DataFrame({
                    'Test Type': ['PHEF', 'Combat', 'Functional', 'Swimming'],
                    'Count': [phef_count, combat_count, functional_count, swimming_count]
                })
                fig = px.pie(data, values='Count', names='Test Type',
                             color_discrete_sequence=['#0d6efd', '#198754', '#ffc107', '#0dcaf0'])
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="own_unit_test_dist"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.ui
        async def own_unit_pass_fail_chart():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()

                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                phef_pass = phef_fail = 0
                for sess in phef_sessions:
                    for test in await self.db.get_all_phef(sess.id):
                        if test.serial_number in serials:
                            if self._phef_total_score(test) >= 50:
                                phef_pass += 1
                            else:
                                phef_fail += 1

                combat_sessions = await self._safe_sessions_by_type(TypeFitnessTest.COMBAT)
                combat_pass = combat_fail = 0
                for sess in combat_sessions:
                    for test in await self.db.get_all_combat_test(sess.id):
                        if test.serial_number in serials:
                            passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                            if passed:
                                combat_pass += 1
                            else:
                                combat_fail += 1

                functional_sessions = await self._safe_sessions_by_type(TypeFitnessTest.FUNCTIONAL)
                func_pass = func_fail = 0
                for sess in functional_sessions:
                    for test in await self.db.get_all_functional_test(sess.id):
                        if test.serial_number in serials:
                            total = test.push_ups + test.sit_ups + test.pull_ups
                            if total >= 50:
                                func_pass += 1
                            else:
                                func_fail += 1

                swim_sessions = await self._safe_sessions_by_type(TypeFitnessTest.SWIMMING)
                swim_pass = swim_fail = 0
                for sess in swim_sessions:
                    for test in await self.db.get_all_combat_swimming_test(sess.id):
                        if test.serial_number in serials:
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
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="own_unit_pass_fail"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.data_frame
        async def own_unit_recent_sessions_table():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                all_sessions = await self.db.get_all_test_sessions()
                all_sessions.sort(key=lambda x: x.datetime_start, reverse=True)

                def _sess_has_unit_member(sess) -> bool:
                    try:
                        fetch_map = {
                            TypeFitnessTest.PHEF: self.db.get_all_phef,
                            TypeFitnessTest.COMBAT: self.db.get_all_combat_test,
                            TypeFitnessTest.FUNCTIONAL: self.db.get_all_functional_test,
                            TypeFitnessTest.SWIMMING: self.db.get_all_combat_swimming_test,
                        }
                        fetch = fetch_map.get(sess.type_test)
                        return fetch is not None
                    except Exception:
                        return False

                recent_rows = []
                for sess in all_sessions:
                    if not _sess_has_unit_member(sess):
                        continue
                    tests = []
                    if sess.type_test == TypeFitnessTest.PHEF:
                        tests = await self.db.get_all_phef(sess.id)
                    elif sess.type_test == TypeFitnessTest.COMBAT:
                        tests = await self.db.get_all_combat_test(sess.id)
                    elif sess.type_test == TypeFitnessTest.FUNCTIONAL:
                        tests = await self.db.get_all_functional_test(sess.id)
                    elif sess.type_test == TypeFitnessTest.SWIMMING:
                        tests = await self.db.get_all_combat_swimming_test(sess.id)

                    if any(t.serial_number in serials for t in tests):
                        recent_rows.append({
                            'Date': sess.datetime_start.strftime('%Y-%m-%d %H:%M'),
                            'Type': sess.type_test.name,
                            'PTI': sess.serial_number_pti or 'N/A',
                            'Status': '✅ Executed' if sess.executed else '⏳ Pending',
                            'Description': sess.description or ''
                        })
                    if len(recent_rows) >= 10:
                        break

                return pd.DataFrame(recent_rows)
            except Exception:
                return pd.DataFrame()

        @output
        @render.ui
        async def own_unit_phef_score_histogram():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                phef_sessions = await self._safe_sessions_by_type(TypeFitnessTest.PHEF)
                scores = []
                for sess in phef_sessions:
                    for test in await self.db.get_all_phef(sess.id):
                        if test.serial_number in serials:
                            scores.append(self._phef_total_score(test))
                if not scores:
                    return ui.p("No PHEF data available for your unit", class_="text-muted")
                fig = px.histogram(scores, nbins=20,
                                   labels={'value': 'Score', 'count': 'Frequency'},
                                   color_discrete_sequence=['#0d6efd'])
                fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                                  xaxis_title="PHEF Score", yaxis_title="Number of Tests",
                                  showlegend=False)
                fig.add_vline(x=50, line_dash="dash", line_color="red",
                              annotation_text="Pass Threshold")
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="own_unit_phef_hist"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.ui
        async def own_unit_performance_trend_chart():
            _ = self.refresh_tick.get()
            try:
                serials = await self._own_unit_serials()
                all_sessions = await self.db.get_all_test_sessions()
                all_sessions.sort(key=lambda x: x.datetime_start)
                trend_data = []
                for sess in all_sessions:
                    date = sess.datetime_start.strftime('%Y-%m-%d')
                    if sess.type_test == TypeFitnessTest.PHEF:
                        for test in await self.db.get_all_phef(sess.id):
                            if test.serial_number in serials:
                                trend_data.append({'Date': date, 'Type': 'PHEF', 'Score': self._phef_total_score(test)})
                    elif sess.type_test == TypeFitnessTest.COMBAT:
                        for test in await self.db.get_all_combat_test(sess.id):
                            if test.serial_number in serials:
                                passed = test.rope_passed and test.obstacle_passed and test.running_time <= 7200
                                trend_data.append({'Date': date, 'Type': 'Combat', 'Score': 100 if passed else 0})
                    elif sess.type_test == TypeFitnessTest.FUNCTIONAL:
                        for test in await self.db.get_all_functional_test(sess.id):
                            if test.serial_number in serials:
                                total = test.push_ups + test.sit_ups + test.pull_ups
                                trend_data.append({'Date': date, 'Type': 'Functional', 'Score': total})
                if not trend_data:
                    return ui.p("No trend data available for your unit", class_="text-muted")
                df = pd.DataFrame(trend_data)
                df_avg = df.groupby(['Date', 'Type'])['Score'].mean().reset_index()
                fig = px.line(df_avg, x='Date', y='Score', color='Type',
                              color_discrete_map={'PHEF': '#0d6efd', 'Combat': '#198754',
                                                  'Functional': '#ffc107'})
                fig.update_layout(margin=dict(t=20, b=40, l=40, r=20),
                                  xaxis_title="Date", yaxis_title="Average Score")
                return ui.HTML(fig.to_html(include_plotlyjs='cdn', div_id="own_unit_trends"))
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")


# Simple module-level helpers to align with existing app wiring
_page_instance: DashboardOwnUnitPage | None = None

def get_ui():
    global _page_instance
    if _page_instance is None:
        _page_instance = DashboardOwnUnitPage(DBService("ui/config/config.yml"))
    return _page_instance.get_ui()

def server(input, output, session):
    global _page_instance
    if _page_instance is None:
        _page_instance = DashboardOwnUnitPage(DBService("ui/config/config.yml"))
    _page_instance.server(input, output, session)