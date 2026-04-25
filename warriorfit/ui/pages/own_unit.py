# Python
from __future__ import annotations

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.ui.controllers.own_unit_controller import OwnUnitController
from warriorfit.ui.pages.page import Page

_FAILED_STYLE = {"color": "orange", "font-weight": "bold"}


def _failed_styles(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    """Return DataGrid `styles` entries that color any cell containing
    'failed' (case-insensitive) in the given columns orange."""
    styles: list[dict] = []
    if df is None or df.empty:
        return styles
    for col in columns:
        if col not in df.columns:
            continue
        col_idx = df.columns.get_loc(col)
        failed_rows = [
            i for i, v in enumerate(df[col]) if "failed" in str(v).lower()
        ]
        if failed_rows:
            styles.append(
                {"rows": failed_rows, "cols": [col_idx], "style": _FAILED_STYLE}
            )
    return styles


class OwnUnitPage(Page):
    @inject
    def __init__(self, controller: OwnUnitController = Provide[Container.own_unit_controller]):
        super().__init__()
        self.controller = controller
        self._selected_serial = reactive.Value(None)
        self.report_path = reactive.Value(None)

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            "Status Unit",
            ui.card(
                ui.card_header(
                    f"Servicemen - {self.controller.unit_name} Status PHEF, COMBAT, SWIMMING"
                ),
                ui.input_action_button(
                    "refresh_servicemen",
                    "🔄 Refresh",
                    class_="btn btn-secondary btn-sm my-2",
                ),
                ui.output_data_frame("servicemen_grid"),
                ui.input_action_button("full_report_unit", "Pdf Satus Unit", width="150px"),
                ui.output_ui("download_btn_unit"),
                ui.br(),
                full_screen=True,
            ),
        )

    def server(self, input, output, session):
        self.refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, "Status Unit", self.refresh_tick)

        status_report_unit = reactive.Value("")

        @reactive.effect
        @reactive.event(input.full_report_unit)
        async def full_report_unit():
            self.report_path.set(None)
            status_report_unit.set("Generating report...")
            output_path = await self.controller._report_generator_pdf.generate_total_report_current_year_own_unit()
            if output_path:
                self.report_path.set(output_path)
                status_report_unit.set("Full report generated.")
                self.refresh_tick.set(self.refresh_tick.get() + 1)
                ui.notification_show("Report generated", type="message", duration=2)
            else:
                status_report_unit.set("Failed to generate report.")

        @output
        @render.ui
        def download_btn_unit():
            if self.report_path.get():
                ui.update_action_button("full_report_unit", disabled=True)
                return ui.download_button(
                    "download_generated_report_unit",
                    "Download PDF",
                    width="150px",
                    class_="btn-success",
                )
            return None

        @render.download(filename=lambda: f"Report_{self.controller.unit_name}.pdf")
        def download_generated_report_unit():
            path = self.report_path.get()
            ui.update_action_button("full_report_unit", disabled=False)
            self.report_path.set(None)

            if path:
                return path
            return None

        @output
        @render.data_frame
        async def servicemen_grid():
            df = await self.controller.fetch_servicemen_df()
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="rows",
                width="100%",
                styles=_failed_styles(
                    df,
                    ["Phef status", "Combat status", "Swim status", "March status"],
                ),
            )

        @reactive.Effect
        @reactive.event(input.refresh_servicemen)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.servicemen_grid_selected_rows)
        async def _on_row_selected():
            # Handles row selection; shows modal with serviceman tests
            try:
                sel = input.servicemen_grid_selected_rows()
                if not sel:
                    return
                row_idx = sel[0]
                df = await self.controller.fetch_servicemen_df()
                if row_idx < 0 or row_idx >= len(df):
                    return
                row = df.iloc[row_idx]
                serial = str(row.get("Service", "") or "").strip()
                if not serial:
                    return
                self._selected_serial.set(serial)  # type: ignore[arg-type]

                ui.modal_show(
                    ui.modal(
                        ui.h4(f"Executed Fitness Tests — {serial}"),
                        ui.output_data_frame("serviceman_tests_grid"),
                        easy_close=True,
                        footer=ui.input_action_button("close_serviceman_tests", "Close"),
                    )
                )
            except Exception:
                ui.notification_show("Error loading serviceman tests", type="error", duration=2)

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

                    return f"{txt}"

                df = df.copy()
                df["Status"] = df["Status"].apply(_fmt_status)

            return render.DataGrid(
                df,
                filters=False,
                selection_mode="none",
                width="100%",
                styles=_failed_styles(df, ["Status"]),
            )

        @reactive.Effect
        @reactive.event(input.close_serviceman_tests)
        def _close_modal():
            ui.modal_remove()


# Public API: keep same signatures
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = OwnUnitPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
