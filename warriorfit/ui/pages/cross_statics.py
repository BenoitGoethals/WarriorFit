import pandas as pd
from shiny import ui, render, reactive

from warriorfit.ui.controllers.cross_statics_controller import CrossStaticsController
from warriorfit.ui.pages.page import Page
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container
from warriorfit.utils.formaters import Formatter


class CrossStaticsPage(Page):
    @inject
    def __init__(self, controller: CrossStaticsController = Provide[Container.cross_statics_controller]):
        super().__init__()
        self._controller = controller

    async def refresh(self):
        await self._controller.load()

    def get_ui(self):
        return ui.nav_panel(
            "Cross Statics",
            ui.h2("Cross Statistics"),
            ui.input_action_button("cs_refresh_btn", "🔄 Refresh", class_="btn btn-secondary btn-sm my-2"),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "1. Breakdowns based on demographics",
                        class_="bg-success text-white",
                    ),
                    ui.div(
                        ui.strong("Age groups : "),
                        ui.output_ui("cross_age_group"),
                    ),
                ),
                col_widths=[3, 3],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("2. Best 10 all 5M", class_="bg-success text-white"),
                    ui.div(ui.output_data_frame("best_10_all_grid_5")),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header(
                            "3. Best 10 all 10 km", class_="bg-success text-white"
                        ),
                        ui.div(ui.output_data_frame("best_10_all_grid_10")),
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

        @reactive.Effect
        @reactive.event(input.cs_refresh_btn)
        async def _on_cs_refresh():
            await self.refresh()
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @output
        @render.data_frame
        async def best_10_all_grid_5():
            _ = self.refresh_tick.get()
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
            _ = self.refresh_tick.get()
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
            ages: dict[int, int] = await self._controller.get_age_group()
            uv_p = ui.p(f"Age Group")
            for key, value in ages.items():
                uv_p.append(ui.p(f"Age {key} - Count {value}"))
            return uv_p


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = CrossStaticsPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)
