import pandas as pd
from shiny import ui, render, reactive

from warriorfit.ui.controllers.cross_statics_controller import CrossStaticsController
from warriorfit.ui.pages.page import Page
from warriorfit.utils.formaters import Formatter


class CrossStaticsPage(Page):
    def __init__(self):
        self._controller = CrossStaticsController()
        self.refresh_tick = reactive.Value(0)

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

                col_widths=[3, 3,4]),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("3. Best 10 all 5M", class_="bg-success text-white"),
                        ui.div(
                            ui.output_data_frame("best_10_all_grid")
                        ),
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("3. Best 10 all 10 km", class_="bg-success text-white"),
                            ui.div(
                                ui.output_data_frame("best_10_all_grid_10")
                            ),
                        ),
                ),
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
            return ui.p(f"{Formatter.format_time(average)}")

        @output
        @render.data_frame
        async def best_10_all_grid():
            df = None
           # _ = self.refresh_tick.get()
            try:
                dfc = await self._controller.best_10_all_df()
                df = dfc[5]
            except Exception:
                print("Error fetching data")
               # df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            if df is None:
                df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            return render.DataGrid(
                df, # if isinstance(df, pd.DataFrame) else pd.DataFrame(columns=["Type", "Serial", "Reason"]),
                filters=False,
                selection_mode="none",
                width="100%",
            )

        @output
        @render.data_frame
        async def best_10_all_grid_10():
            df = None
            # _ = self.refresh_tick.get()
            try:
                dfc = await self._controller.best_10_all_df()
                df = dfc[10]
            except Exception:
                print("Error fetching data")
            # df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            if df is None:
                df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            return render.DataGrid(
                df,  # if isinstance(df, pd.DataFrame) else pd.DataFrame(columns=["Type", "Serial", "Reason"]),
                filters=False,
                selection_mode="none",
                width="100%",
            )



        @output
        @render.ui
        async def cross_best_time():
            average = await self._controller.get_best_time()
            return ui.p(f"{Formatter.format_time(average)}")

        @output
        @render.ui
        async def cross_gap():
            average = await self._controller.get_gap_time()
            return ui.p(f"{Formatter.format_time(average)}")

        @output
        @render.ui
        async def cross_age_group():
            ages:dict[int,int] = await self._controller.get_age_group()
            uv_p=ui.p(f"Age Group")
            for key,value in ages.items():
               uv_p.append(ui.p(f"Age {key} - Count {value}"))
            return uv_p

        @output
        @render.ui
        async def cross_gender():
            average_f,average_m = await self._controller.get_gender_time()
            return ui.p(F" F {Formatter.format_time(average_f)}  /  M {Formatter.format_time(average_m)}")



_page = CrossStaticsPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)