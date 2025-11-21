# Python
from __future__ import annotations

from typing import Optional

import pandas as pd
from shiny import ui, render, reactive


from ui.controllers.ind_test_show_controller import IndTestShowController


class IndTestShowPage:
    def __init__(self):

        self.controller = IndTestShowController()
        self.refresh_tick = reactive.Value(0)
        self.serial = reactive.Value("")
        self.mil_info = reactive.Value("No serviceman selected.")
        self.tests_df = reactive.Value(pd.DataFrame())

    def get_ui(self):
        return ui.nav_panel(
            "Individual",
            ui.h2("Individual Test History"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Lookup"),
                    ui.input_text("ind_serial", "Serial number"),
                    ui.input_action_button("ind_search", "Search", width="150px"),
                    ui.input_action_button("full_report_cy", "Full Report current Year", width="150px"),
                    ui.br(),
                    ui.output_text("ind_status"),
                    ui.hr(),
                    ui.h4("Serviceman"),
                    ui.output_text("ind_mil_info"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header("Test history"),
                    ui.output_data_frame("ind_grid"),
                    full_screen=False,
                ),
                col_widths=(3, 9),
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("Ready.")

        @reactive.effect
        @reactive.event(input.full_report_cy)
        def full_report_cy():


        @reactive.effect
        @reactive.event(input.ind_search, ignore_none=False)
        async def _on_search():
            s = (input.ind_serial() or "").strip()
            if not s:
                status.set("Enter a serial number.")
                self.mil_info.set("No serviceman selected.")
                self.tests_df.set(pd.DataFrame())
                return
            try:
                mil = await self.controller.find_military(s)
                if not mil:
                    raise ValueError("not found")
                self.serial.set(s)
                self.mil_info.set(f"{mil.rank} {mil.first_name} {mil.last_name} — {mil.service_number} — {mil.unit}")

                df = await self.controller.collect_tests_df(s)
                self.tests_df.set(df if isinstance(df, pd.DataFrame) else pd.DataFrame())
                status.set(f"Loaded {len(self.tests_df.get())} records." if not self.tests_df.get().empty else "No tests found.")
            except Exception as e:
                self.serial.set("")
                self.mil_info.set("Not found.")
                self.tests_df.set(pd.DataFrame())
                status.set(e)

        @output
        @render.text
        def ind_status():
            return status.get()

        @output
        @render.text
        def ind_mil_info():
            return self.mil_info.get()

        @output
        @render.data_frame
        def ind_grid():
            df = self.tests_df.get()
            if df is None or not isinstance(df, pd.DataFrame):
                df = pd.DataFrame()
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="none",
                width="100%",
                
            )

_page = IndTestShowPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)