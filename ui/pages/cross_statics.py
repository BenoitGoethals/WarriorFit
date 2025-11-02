from shiny import ui, render, reactive

from services.service_cross import ServiceCross
from ui.controllers.cross_statics_controller import CrossStaticsController


class CrossStaticsPage:
    def __init__(self):
        self._controller = CrossStaticsController()

    def get_ui(self):
        return ui.nav_panel(
            "Cross Statics",
            ui.h2("Cross Statics"),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("1. Basic Performance Metrics", class_="bg-success text-white"),
                    # Replaced table with simple labels as requested
                    ui.div(
                        ui.strong("Average time: "),
                        ui.output_ui("cross_average_time"),
                    ),
                    ui.div(
                        ui.strong("Best Time: "),
                        ui.output_ui("cross_best_time"),
                    ),
                    ui.div(
                        ui.strong("Gap between best and worst: "),
                        ui.output_ui("cross_gap"),
                    ),


                ),
                ui.card(
                    ui.card_header("2. Breakdowns based on demographics", class_="bg-success text-white"),
                    ui.div(
                        ui.strong("Age groups : "),
                        ui.output_ui("cross_age_group"),
                    ),
                    ui.div(
                        ui.strong("Gender M / F averages: "),
                        ui.output_ui("cross_gender"),
                    ),
                ),
                col_widths=[3, 3,],
            ),



        )

    def server(self, input, output, session):
        @reactive.Effect
        async def _init():
            await self._controller.load()

        @output
        @render.ui
        async def cross_average_time():
            average = await self._controller.get_average_time()
            return ui.p(f"{format_time(average)}")



        @output
        @render.ui
        async def cross_best_time():
            average = await self._controller.get_best_time()
            return ui.p(f"{format_time(average)}")

        @output
        @render.ui
        async def cross_gap():
            average = await self._controller.get_gap_time()
            return ui.p(f"{format_time(average)}")

        @output
        @render.ui
        async def cross_age_group():
            ages = await self._controller.get_age_group()
            return ui.p(f"{ages}")

        @output
        @render.ui
        async def cross_gender():
            average_f,average_m = await self._controller.get_gender_time()
            return ui.p(F" F {format_time(average_f)} / M {format_time(average_m)}")

        def format_time(seconds):
            if seconds is None:
                return "-"
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

_page = CrossStaticsPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)