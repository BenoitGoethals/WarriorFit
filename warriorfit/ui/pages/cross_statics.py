import pandas as pd
from shiny import ui, render, reactive

from warriorfit.ui.controllers.cross_statics_controller import CrossStaticsController
from warriorfit.ui.pages.page import Page
from warriorfit.utils.formaters import Formatter


class CrossStaticsPage(Page):
    def __init__(self):
        super().__init__()
        self._controller = CrossStaticsController()


    async def refresh(self):
        await self._controller.load()

    def get_ui(self):
        return ui.nav_panel(
            "Cross Statics",
            ui.h2("Cross Statistics"),
            ui.br(),
            ui.layout_columns(

                ui.card(
                    ui.card_header("1. Breakdowns based on demographics", class_="bg-success text-white"),
                    ui.div(
                        ui.strong("Age groups : "),
                        ui.output_ui("cross_age_group"),
                    ),

                ),

                col_widths=[3, 3]),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("2. Best 10 all 5M", class_="bg-success text-white"),
                        ui.div(
                            ui.output_data_frame("best_10_all_grid_5")
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
        self.refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, "Cross Statistics", self.refresh_tick)
        @reactive.Effect
        async def _init():
            await self._controller.load()


        @output
        @render.data_frame
        async def best_10_all_grid_5():
            """
            Renders the best 10 all-grid data as a DataGrid component.

            This method fetches data asynchronously from the controller and constructs
            a DataGrid view for the top ten entries. If no data is available, it creates
            an empty DataFrame with default columns "Type", "Serial", and "Reason".

            :return: A DataGrid representation of the best 10 all-grid data.
            :rtype: render.DataGrid
            """
            dfc = await self._controller.best_10_all_df()
            if dfc.get(5) is None:
                df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            else:
                df = dfc[5]
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="none",
                width="100%",
            )

        @output
        @render.data_frame
        async def best_10_all_grid_10():
            """
            Render a DataGrid showcasing the top 10 items across all grids. If no data is
            available for the specific index, returns an empty DataFrame with predefined
            columns: "Type", "Serial", and "Reason".

            This asynchronous function interacts with a controller to retrieve the relevant
            data and ensures that a fallback mechanism is in place when no result is
            retrieved for the specified index.

            :return: A DataGrid rendered with the specified content and settings.
            :rtype: DataGrid
            """
            dfc = await self._controller.best_10_all_df()
            if dfc.get(10) is None:
                df = pd.DataFrame(columns=["Type", "Serial", "Reason"])
            else:
                df = dfc[10]
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="none",
                width="100%",
            )




        @output
        @render.ui
        async def cross_age_group():
            ages:dict[int,int] = await self._controller.get_age_group()
            uv_p=ui.p(f"Age Group")
            for key,value in ages.items():
               uv_p.append(ui.p(f"Age {key} - Count {value}"))
            return uv_p




_page = CrossStaticsPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)