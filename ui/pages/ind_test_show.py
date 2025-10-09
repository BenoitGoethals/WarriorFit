from shiny import ui, render, reactive
import pandas as pd

from logic.data_collector import DataCollector
from services.db_service import DBService
from services.be_mil_service import BEMILService


class IndTestShowPage:
    def __init__(self, db: DBService):
        self.db = db
        self.be_mil = BEMILService()
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
                    full_screen=True,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("Ready.")

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
                mil = await self.be_mil.get_be_mil_by_id(s)
                self.serial.set(s)
                self.mil_info.set(f"{mil.rank} {mil.first_name} {mil.last_name} — {mil.service_number} — {mil.unit}")

                df = await DataCollector().collect_tests_for_serial(s)
                self.tests_df.set(df)
                status.set(f"Loaded {len(df)} records." if not df.empty else "No tests found.")
            except Exception:
                self.serial.set("")
                self.mil_info.set("Not found.")
                self.tests_df.set(pd.DataFrame())
                status.set("Serviceman not found.")

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
            return render.DataGrid(
                self.tests_df.get(),
                filters=False,
                selection_mode="none",
            )


_page = IndTestShowPage(DBService())

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)