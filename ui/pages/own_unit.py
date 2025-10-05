from shiny import reactive, ui
from shiny.express import render
import pandas as pd

from ui.config.appliccation_config import ApplicationConfig
from ui.services.be_mil_service import BEMILService

class OwnUnitPage:
    def __init__(self, mil_service: BEMILService):
        self.unit_name = ApplicationConfig().own_unit
        self.refresh_tick = reactive.Value(0)
        self._mil_service = mil_service

    def get_ui(self):
        return ui.nav_panel(
            "Own Unit",
            ui.card(
                ui.card_header(f"Servicemen - {self.unit_name}"),
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

        async def _fetch_df() -> pd.DataFrame:
            # Always create a fresh awaitable; do not reuse an already awaited coroutine
            data = await self._mil_service.get_all_be_mil_from_unit(self.unit_name)
            rows = [
                {
                    "Service #": sm.service_number,
                    "Rank": sm.rank,
                    "Last name": sm.last_name,
                    "First name": sm.first_name,
                    "Unit": (sm.unit or ""),
                    "Gender": (sm.gender or ""),
                    "Birthdate": (sm.birthdate or ""),
                    "Para": bool(sm.para),
                    "Ops Test": bool(sm.ops_test),
                }
                for sm in (data or [])
            ]
            return pd.DataFrame(rows)

        @output
        @render.data_frame
        async def servicemen_grid():
            _ = _tick()
            df = await _fetch_df()
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

# Public API: keep same signatures
_page = OwnUnitPage(BEMILService())

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)