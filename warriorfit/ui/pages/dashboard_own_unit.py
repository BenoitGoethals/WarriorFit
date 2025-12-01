from datetime import datetime

from shiny import ui, render, reactive
import pandas as pd

from warriorfit.ui.controllers.dashboard_own_unit_controller import DashboardOwnUnitController
from warriorfit.ui.pages.page import Page


class DashboardOwnUnitPage(Page):
    def __init__(self):
        self.controller = DashboardOwnUnitController()

    def get_ui(self):
        return ui.nav_panel(
            "Dashboard",
            ui.h2(f"📊 {self.controller.unit_name} Dashboard " + str(datetime.now().year)),
            ui.br(),
            # ui.layout_columns(
            #     ui.input_action_button("own_unit_refresh", "Refresh", class_="btn btn-outline-primary"),
            # ),
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
                    ui.card_header("🏊 Swimming Tests", class_="bg-info text-white"),
                    ui.output_ui("own_unit_swimming_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🏊 March Tests", class_="bg-info text-white"),
                    ui.output_ui("own_unit_march_stats"),
                    class_="text-center",
                ),

            ),
            ui.br(),
            ui.layout_columns(

                ui.card(
                    ui.card_header("Pass/Fail Rates by Test Type (Own Unit)"),
                    ui.output_ui("own_unit_pass_fail_chart"),
                    full_screen=True,
                ),
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("PHEF Score Distribution (Own Unit)"),
                    ui.output_ui("own_unit_phef_score_histogram"),
                    full_screen=True,
                ),
            ),
            ui.br(),

        )


    def _ui_stats_card(self, total_text: str, total_value: int | float, sub_value: str | None, sub_label: str, sub_class: str):
        return ui.div(
            ui.h1(str(total_value), class_="display-4 fw-bold"),
            ui.p(total_text),
            ui.hr(),
            (ui.h4(sub_value, class_=sub_class) if sub_value is not None else ui.div()),
            (ui.p(sub_label) if sub_value is not None else ui.div()),
        )

    def refresh(self):
        self.controller.reset_cache()

    def server(self, input, output, session):
        # Create a session-specific reactive value
        refresh_tick = reactive.Value(0)
        

        self.refresh_on_nav(input, "Dashboard", refresh_tick)

        # @reactive.Effect
        # @reactive.event(input.own_unit_refresh)
        # def _trigger_refresh():
        #     self.controller.reset_cache()
        #     refresh_tick.set(refresh_tick.get() + 1)
        #     ui.notification_show("Own unit dashboard reloaded", type="message", duration=2)


        @output
        @render.ui
        async def own_unit_personnel_stats():
            _ = refresh_tick.get()
            stats = await self.controller.personnel_stats()
            return self._ui_stats_card("Service members in unit", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def own_unit_phef_stats():
            _ = refresh_tick.get()
            stats = await self.controller.phef_stats()
            return self._ui_stats_card("Total Tests (Own Unit)", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def own_unit_combat_stats():
            _ = refresh_tick.get()
            stats = await self.controller.combat_stats()
            return self._ui_stats_card("Total Tests (Own Unit)", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])


        @output
        @render.ui
        async def own_unit_swimming_stats():
            _ = refresh_tick.get()
            stats = await self.controller.swimming_stats()
            return self._ui_stats_card("Total Tests (Own Unit)", stats["total"], stats["sub_value"], stats["sub_label"], stats["sub_class"])

        @output
        @render.ui
        async def own_unit_march_stats():
            _ = refresh_tick.get()
            stats = await self.controller.march_stats()
            return self._ui_stats_card("Total Tests (Own Unit)", stats["total"], stats["sub_value"], stats["sub_label"],
                                       stats["sub_class"])

        @output
        @render.ui
        async def own_unit_pass_fail_chart():
            _ = refresh_tick.get()
            try:
                html = await self.controller.pass_fail_bar_html()
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")



        @output
        @render.ui
        async def own_unit_phef_score_histogram():
            _ = refresh_tick.get()
            try:
                html = await self.controller.phef_hist_html()
                if not html:
                    return ui.p("No PHEF data available for your unit", class_="text-muted")
                return ui.HTML(html)
            except Exception as e:
                return ui.p(f"No data available: {str(e)}", class_="text-muted")

# Public API
_page = DashboardOwnUnitPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)