from __future__ import annotations

import datetime
from shiny import ui, render, reactive

from warriorfit.ui.controllers.status_tests_controller import StatusTestsController
from warriorfit.ui.pages.page import Page
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container


class StatusTests(Page):
    @inject
    def __init__(self, controller: StatusTestsController = Provide[Container.status_tests_controller]):
        super().__init__()
        self._controller = controller
        self.refresh_tick = reactive.Value(0)
        self._selected_serial = reactive.Value(None)

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "PHEF Not done",
            ui.card(
                ui.card_header(
                    f"List of Military who did NOT executed PHEF test from current year {datetime.datetime.now().year} - {self._controller.unit_name}"
                ),
                ui.input_action_button("refresh_own_unit_status_grid", "Refresh"),
                ui.output_data_frame("own_unit_status_grid"),
                full_screen=False,
            ),
        )

    def server(self, input, output, session):
        @reactive.calc
        def _tick():
            input.refresh_own_unit_status_grid()
            return self.refresh_tick.get()

        @output
        @render.data_frame
        async def own_unit_status_grid():
            try:
                df = await self._controller.get_data()
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                import pandas as pd

                df = pd.DataFrame(columns=["Message"])
                df.loc[len(df)] = [f"Error loading data: {e}"]
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="rows",
                width="100%",
            )

        @reactive.Effect
        @reactive.event(input.refresh_own_unit_status_grid)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = StatusTests()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
