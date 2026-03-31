# Python
from __future__ import annotations

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.ui.controllers.ind_test_show_controller import IndTestShowController
from warriorfit.ui.pages.page import Page


class IndTestShowPage(Page):
    @inject
    def __init__(
        self,
        controller: IndTestShowController = Provide[Container.ind_test_show_controller],
    ):
        super().__init__()
        self.controller = controller
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
                    ui.div(
                        ui.input_text("ind_serial", "Serial number"),
                        class_="wf-serial-input",
                    ),
                    ui.input_action_button(
                        "ind_search_serial_search_btn",
                        "🔍 Search own Unit",
                        class_="btn btn-info btn-sm w-100 mt-1",
                    ),
                    ui.input_action_button(
                        "ind_search",
                        "✅ Confirm Serviceman",
                        class_="btn btn-primary btn-sm w-100 mt-2",
                    ),
                    ui.hr(),
                    ui.input_action_button(
                        "full_report_cy",
                        "📄 Generate Full Report",
                        class_="btn btn-secondary btn-sm w-100",
                    ),
                    ui.output_ui("download_btn_ui"),
                    ui.input_action_button(
                        "ind_refresh_btn",
                        "🔄 Refresh",
                        class_="btn btn-secondary btn-sm w-100 mt-1",
                    ),
                    ui.hr(),
                    ui.output_text("ind_status"),
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
        @reactive.event(input.ind_refresh_btn)
        async def _on_ind_refresh():
            s = self.serial.get()
            if s:
                try:
                    df = await self.controller.collect_tests_df(s)
                    self.tests_df.set(df if isinstance(df, pd.DataFrame) else pd.DataFrame())
                    status.set(f"Refreshed {len(self.tests_df.get())} records.")
                except Exception:
                    pass

        @reactive.effect
        @reactive.event(input.full_report_cy)
        async def full_report_cy():
            s = (input.ind_serial() or "").strip()
            self.report_path.set(None)
            if s:
                status.set("Generating report...")
                output_path = await self.controller._report_generator_pdf.generate_ind_report(
                    serial_number=s
                )
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
                return ui.download_button(
                    "download_generated_report",
                    "Download PDF",
                    width="150px",
                    class_="btn-success",
                )
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
                self.mil_info.set(
                    f"{mil.rank} {mil.first_name} {mil.last_name} — {mil.service_number} — {mil.unit}"
                )
                df = await self.controller.collect_tests_df(s)
                self.tests_df.set(df if isinstance(df, pd.DataFrame) else pd.DataFrame())
                status.set(
                    f"Loaded {len(self.tests_df.get())} records."
                    if not self.tests_df.get().empty
                    else "No tests found."
                )
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                self.serial.set("")
                self.mil_info.set("Not found.")
                self.tests_df.set(pd.DataFrame())
                status.set(e)  # type: ignore[arg-type]

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

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.ind_search_serial_search_btn)
        async def _open_ind_search_serial_search_btn_modal() -> None:
            modal_content = ui.modal(
                ui.card(
                    ui.card_header("Select Serial Number"),
                    ui.output_data_frame("ind_serial_search_grid"),
                    full_screen=False,
                ),
                size="l",
                easy_close=True,
            )
            ui.modal_show(modal_content)

        @render.data_frame
        async def ind_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="rows", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.ind_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.ind_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("ind_serial", value=str(row["service_number"]))
                    ui.modal_remove()

        @reactive.calc
        async def get_all_servicemen_df() -> pd.DataFrame:
            servicemen = await self.controller.be_mil.get_all_service_men()
            if not servicemen:
                return pd.DataFrame(columns=["service_number", "first_name", "last_name", "gender"])

            df = pd.DataFrame(
                [
                    {
                        "service_number": s.service_number,
                        "first_name": s.first_name,
                        "last_name": s.last_name,
                        "gender": s.gender,
                    }
                    for s in servicemen
                ]
            )
            return df.sort_values(by=["service_number"])


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = IndTestShowPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
