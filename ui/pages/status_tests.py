from __future__ import annotations

from typing import Optional
from shiny import ui, render, reactive

from services.be_mil_service import BEMILService
from ui.controllers.status_tests_controller import StatusTestsController


class StatusTests:
    def __init__(self, mil_service: Optional[BEMILService] = None):
        self._controller:StatusTestsController = StatusTestsController(mil_service or BEMILService())
        self.refresh_tick = reactive.Value(0)
        self._selected_serial = reactive.Value(None)

    def get_ui(self):
        return ui.nav_panel(
            "PHEF Status",
            ui.card(
                ui.card_header(f"PHEF Status - {self._controller.unit_name}"),
                ui.input_action_button("refresh_own_unit_status_grid", "Refresh"),
                ui.output_data_frame("own_unit_status_grid"),
                full_screen=True,
            ),
        )

    def server(self, input, output, session):
        # @reactive.calc
        # def _tick():
        #     input.refresh_own_unit_status_grid()
        #     return self.refresh_tick.get()

        @output
        @render.data_frame
        async def own_unit_status_grid():
            #_ = _tick()
            df = await self._controller.get_data()
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="row",
                width="100%",
            )

        @reactive.Effect
        @reactive.event(input.refresh_servicemen)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        # @reactive.Effect
        # @reactive.event(input.servicemen_grid_selected_rows)
        # async def _on_row_selected():
        #     try:
        #         sel = input.own_unit_status_grid()
        #         if not sel:
        #             return
        #         row_idx = sel[0]
        #         df = await self.controller.get_data()
        #         if row_idx < 0 or row_idx >= len(df):
        #             return
        #         row = df.iloc[row_idx]
        #         serial = str(row.get("Service #", "") or "").strip()
        #         if not serial:
        #             return
        #         self._selected_serial.set(serial)
        #
        #         # ui.modal_show(
        #         #     ui.modal(
        #         #         ui.h4(f"Executed Fitness Tests — {serial}"),
        #         #         ui.output_data_frame("serviceman_tests_grid"),
        #         #         easy_close=True,
        #         #         footer=ui.input_action_button("close_serviceman_tests", "Close"),
        #         #     )
        #         #)
        #     except Exception:
        #         pass



        @reactive.Effect
        @reactive.event(input.close_serviceman_tests)
        def _close_modal():
            ui.modal_remove()

    # Public API: keep same signatures


_page = StatusTests()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)
