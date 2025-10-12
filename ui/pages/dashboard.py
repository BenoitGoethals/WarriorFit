from datetime import datetime

from shiny import ui, render, reactive
import pandas as pd

from services.be_mil_service import BEMILService
from services.db_service import DBService
from core.type_fitness_test import TypeFitnessTest
import plotly.express as px
import plotly.graph_objects as go

from ui.controllers.dashboard_controller import DashboardController


class DashboardPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = BEMILService()
        self.controller = DashboardController(self.db, self.be_mil_service)

    def get_ui(self):
        return ui.nav_panel(
            "Dashboard",
            ui.h2("📊 Dashboard " + str(datetime.now().year)),
            ui.br(),
            ui.layout_columns(
                ui.input_action_button("dashboard_refresh", "Refresh dashboard", class_="btn btn-outline-primary"),
            ),
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
            ui.layout_columns(
                ui.card(
                    ui.card_header("Test Type Distribution"),
                    ui.output_ui("test_distribution_chart"),
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

    def server(self, input, output, session):
        @reactive.Effect
        @reactive.event(input.dashboard_refresh)
        def _trigger_dashboard_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            ui.notification_show("Dashboard reloaded", type="message", duration=2)

        @output
        @render.ui
        async def phef_stats():
            _ = self.refresh_tick.get()
            try:
                stats = await self.controller.phef_stats()
                return self._ui_stats_card("Total Tests", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])
            except Exception as e:
                ui.notification_show(f"Error loading PHEF statistics: {str(e)}", type="error", duration=5)
                return self._ui_stats_card("Total Tests", 0, None, "", "")

        @output
        @render.ui
        async def combat_stats():
            _ = self.refresh_tick.get()
            stats = await self.controller.combat_stats()
            return self._ui_stats_card("Total Tests", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def functional_stats():
            _ = self.refresh_tick.get()
            stats = await self.controller.functional_stats()
            return self._ui_stats_card("Total Tests", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def swimming_stats():
            _ = self.refresh_tick.get()
            stats = await self.controller.swimming_stats()
            return self._ui_stats_card("Total Tests", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def test_distribution_chart():
            _ = self.refresh_tick.get()
            try:
                html = await self.controller.distribution_pie_html()
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.ui
        async def pass_fail_chart():
            _ = self.refresh_tick.get()
            try:
                html = await self.controller.pass_fail_bar_html()
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.data_frame
        async def recent_sessions_table():
            _ = self.refresh_tick.get()
            try:
                return await self.controller.recent_sessions_df()
            except Exception:
                return pd.DataFrame()

        @output
        @render.ui
        async def phef_score_histogram():
            _ = self.refresh_tick.get()
            try:
                html = await self.controller.phef_hist_html()
                if not html:
                    return ui.p("No PHEF data available", class_="text-muted")
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

        @output
        @render.ui
        async def performance_trend_chart():
            _ = self.refresh_tick.get()
            try:
                html = await self.controller.performance_trend_html()
                if not html:
                    return ui.p("No trend data available", class_="text-muted")
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")


# Public API
_page = DashboardPage(DBService())


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)