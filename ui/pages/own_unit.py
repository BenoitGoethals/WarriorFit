# Python
from __future__ import annotations

from typing import Optional

import pandas as pd
from shiny import ui, render, reactive

from services.military_service import MilitaryService
from ui.controllers.own_unit_controller import OwnUnitController


class OwnUnitPage:
    def __init__(self, mil_service: Optional[MilitaryService] = None):
        self.controller = OwnUnitController(mil_service or MilitaryService())
        self.refresh_tick = reactive.Value(0)
        self._selected_serial = reactive.Value(None)

    def get_ui(self):
        return ui.nav_panel(
            "Status Unit",
            ui.card(
                ui.card_header(f"Servicemen - {self.controller.unit_name} Status PHEF, COMBAT, SWIMMING"),
                ui.input_action_button("refresh_servicemen", "Refresh"),
                ui.output_data_frame("servicemen_grid"),
                full_screen=True,
            ),
        )

    def server(self, input, output, session):
        @reactive.calc
        def _tick():
            input.refresh_servicemen()
            return self.refresh_tick.get()

        @output
        @render.data_frame
        async def servicemen_grid():
            _ = _tick()
            df = await self.controller.fetch_servicemen_df()
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

        @reactive.Effect
        @reactive.event(input.servicemen_grid_selected_rows)
        async def _on_row_selected():
            try:
                sel = input.servicemen_grid_selected_rows()
                if not sel:
                    return
                row_idx = sel[0]
                df = await self.controller.fetch_servicemen_df()
                if row_idx < 0 or row_idx >= len(df):
                    return
                row = df.iloc[row_idx]
                serial = str(row.get("Service #", "") or "").strip()
                if not serial:
                    return
                self._selected_serial.set(serial)

                ui.modal_show(
                    ui.modal(
                        ui.h4(f"Executed Fitness Tests — {serial}"),
                        ui.output_data_frame("serviceman_tests_grid"),
                        easy_close=True,
                        footer=ui.input_action_button("close_serviceman_tests", "Close"),
                    )
                )
            except Exception:
                pass

        @output
        @render.data_frame
        async def serviceman_tests_grid():
            serial = self._selected_serial.get()
            if not serial:
                return pd.DataFrame(columns=["Test Type", "Session", "Status"])
            df = await self.controller.fetch_tests_for_serial_df(serial)

            if not df.empty and "Status" in df.columns:
                def _fmt_status(s):
                    txt = str(s or "Unknown")
                    lo = txt.lower()
                    if lo.startswith("pass"):
                        return f"🟢 {txt}"
                    if lo.startswith("fail"):
                        return f"🔴 {txt}"
                    return f"🟡 {txt}"
                df = df.copy()
                df["Status"] = df["Status"].apply(_fmt_status)

            return render.DataGrid(
                df,
                filters=False,
                selection_mode="none",
                width="100%",
            )

        @reactive.Effect
        @reactive.event(input.close_serviceman_tests)
        def _close_modal():
            ui.modal_remove()


# Public API: keep same signatures
_page = OwnUnitPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)
