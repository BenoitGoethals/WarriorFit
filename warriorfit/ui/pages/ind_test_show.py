# Python
from __future__ import annotations

import pandas as pd
from shiny import ui, render, reactive

from warriorfit.services.report_generator_pdf import ReportGeneratorPdf
from warriorfit.ui.controllers.ind_test_show_controller import IndTestShowController
from warriorfit.ui.pages.page import Page


class IndTestShowPage(Page):
    def __init__(self):
        super().__init__()
        self.controller = IndTestShowController()
        self.serial = reactive.Value("")
        self.mil_info = reactive.Value("No serviceman selected.")
        self.tests_df = reactive.Value(pd.DataFrame())
        self.report_path = reactive.Value(None)

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Individual",
            ui.h2("Individual Test History"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Lookup"),
                    ui.input_text("ind_serial", "Serial number"),
                    ui.input_action_button("ind_search", "Search", width="150px"),
                    ui.input_action_button("full_report_cy", "Generate Full Report", width="150px"),
                    ui.output_ui("download_btn_ui"),
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
        async def full_report_cy():
            s = (input.ind_serial() or "").strip()
            self.report_path.set(None)
            if s:
                status.set("Generating report...")
                report_generator = ReportGeneratorPdf()
                output_path = await report_generator.generate_ind_report_current_year(serial_number=s)
                if output_path:
                    self.report_path.set(output_path)
                    status.set(f"Full report for {s} generated.")
                    self.refresh_tick.set(self.refresh_tick.get() + 1)
                    ui.notification_show("Report generated", type="message", duration=2)
                else:
                    status.set("Failed to generate report.")
            else:
                status.set("No serviceman selected.")

        @output
        @render.ui
        def download_btn_ui():
            if self.report_path.get():
                return ui.download_button("download_generated_report", "Download PDF", width="150px", class_="btn-success")
            return None

        @render.download(filename=lambda: f"Report_{input.ind_serial()}.pdf")
        def download_generated_report():
            path = self.report_path.get()
            if path:
                return path
            return None

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