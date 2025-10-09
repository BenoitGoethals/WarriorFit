from shiny import reactive, ui
from shiny.express import render
import pandas as pd

from config.appliccation_config import ApplicationConfig
from logic.data_collector import DataCollector

from services.be_mil_service import BEMILService

class OwnUnitPage:
    def __init__(self, mil_service: BEMILService):
        self.unit_name = ApplicationConfig().own_unit
        self.refresh_tick = reactive.Value(0)
        self._mil_service = mil_service
        self._selected_serial = reactive.Value(None)

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
            # Ensure we always treat the result as a list
            data = await self._mil_service.get_all_be_mil_from_unit(self.unit_name)
            service_men_list = data if isinstance(data, list) else ([data] if data is not None else [])
            rows = [
                {
                    "Service #": sm.service_number,
                    "Rank": sm.rank,
                    "Last name": sm.last_name,
                    "First name": sm.first_name,
                    "Unit": (getattr(sm.unit, "name", sm.unit) or ""),
                    "Gender": getattr(sm.gender, "value", sm.gender) or "",
                    "Birthdate": (sm.birthdate or ""),
                    "Para": bool(sm.para),
                    "Ops Test": bool(sm.ops_test),
                }
                for sm in service_men_list
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

        # Build-and-show modal on demand (prevents UI blocking by persistent modal instances)
        @reactive.Effect
        @reactive.event(input.servicemen_grid_selected_rows)
        async def _on_row_selected():
            try:
                sel = input.servicemen_grid_selected_rows()
                if not sel:
                    return
                row_idx = sel[0]
                df = await _fetch_df()
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

        async def _fetch_tests_for_serial(serial: str) -> pd.DataFrame:
            try:
                # Fetch tests as a DataFrame using DataCollector (already returns a DataFrame)
                tests_df = await DataCollector().collect_tests_for_serial(serial)
            except Exception:
                tests_df = pd.DataFrame(
                    columns=["Date", "Type", "Details", "Scores", "Total", "Result", "Session ID", "Record ID"]
                )

            # Adapt DataCollector DataFrame to the 3-column grid expected by this page
            if tests_df is None or tests_df.empty:
                return pd.DataFrame(columns=["Test Type", "Session", "Status"])

            def _first_non_empty(*vals):
                for v in vals:
                    if pd.notna(v) and str(v).strip() != "":
                        return v
                return ""

            out = pd.DataFrame({
                "Test Type": tests_df.get("Type", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
                "Session": tests_df.get("Date", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
                "Status": tests_df.get("Result", pd.Series(dtype=str)).apply(lambda v: _first_non_empty(v)),
            })

            # Ensure correct column order and types
            out = out[["Test Type", "Session", "Status"]].fillna("")
            return out

        @output
        @render.data_frame
        async def serviceman_tests_grid():
            serial = self._selected_serial.get()
            if not serial:
                return pd.DataFrame(columns=["Test Type", "Session", "Status"])
            df = await _fetch_tests_for_serial(serial)

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
_page = OwnUnitPage(BEMILService())

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)