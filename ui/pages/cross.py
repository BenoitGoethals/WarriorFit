from __future__ import annotations

from typing import Dict, Any, Optional

import pandas as pd
from shiny import ui, render, reactive

# UI:
ui.output_ui("runner_card")

from ui.controllers.cross_controller import CrossController


class CrossPage:
    def __init__(self):
        self.controller = CrossController()
        self.refresh_tick = reactive.Value(0)
        self.selected_cross_id = reactive.Value("")
        self.selected_runner_id = reactive.Value("")
        self.selected_military = reactive.Value(None)

    NO_SELECTION_MESSAGE = "No row selected"

    def get_ui(self):
        return ui.nav_panel(
            "Cross",
            ui.h2("🏃 Cross Runners"),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Cross"),
                        ui.input_select("cross_id", "Cross", choices=[]),
                        ui.input_action_button("cross_locker", "Select", width="150px"),

                        full_screen=False,
                    ),
                    ui.output_ui("runner_card"),
                ),
                ui.card(
                    ui.card_header("Runners"),
                    ui.output_data_frame("runners_grid"),
                    ui.br(),
                    ui.input_action_button("report_lst", "Generate Report"),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("Ready.")

        cross_selected_id = reactive.Value("")  # or None

        @output
        @render.ui
        def runner_card():
            if not cross_selected_id.get():
                return ui.div()  # hidden
            return ui.card(
                ui.card_header("Runner"),
                ui.input_text("runner_serialnr", "Serial Number"),
                ui.input_action_button("runner_search", "Confirm Serial", width="150px"),
                ui.output_text("runner_military"),
                ui.input_text("runner_time", "Running time (hh::mm:ss)", placeholder="e.g., 01:10:45"),
                ui.layout_columns(
                    ui.input_action_button("runner_add_btn", "Add", width="120px"),
                    ui.input_action_button("runner_update_btn", "Update", width="120px"),
                    ui.input_action_button("runner_clear_btn", "Clear Form", width="120px"),
                    ui.input_action_button("runner_delete_btn", "Delete Selected", width="240px"),
                    col_widths=(4, 4, 4),
                ),
                ui.output_text("runner_status"),
                full_screen=False,
            )

        # Example: when a cross is chosen from a select
        @reactive.Effect
        @reactive.event(input.cross_select)
        def on_cross_select():
            val = (input.cross_select() or "").strip()
            self.selected_cross_id.set(val)



        @reactive.Effect
        @reactive.event(input.cross_locker)
        def on_cross_locker():
            val = (input.cross_id() or "").strip()
            cross_selected_id.set(val)
            self.selected_cross_id.set(val)
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        def _read_form() -> Dict[str, Any]:
            return {
                "serialnr": (input.runner_serialnr() or "").strip(),
                "running_time": (input.runner_time() or "").strip(),
                "cross_id": (input.cross_id() or "").strip(),
            }

        def _clear_form():
            session.send_input_message("runner_serialnr", {"value": ""})
            session.send_input_message("runner_time", {"value": ""})
            self.selected_runner_id.set("")
            #status.set("Form cleared.")

        async def _refresh_cross_choices():
            crosses = await self.controller.load_crosses()
            items = {str(c.id): getattr(c, "name", f"Cross {c.id}") for c in (crosses or [])}
            cur = (input.cross_id() or "").strip()
            selected = cur if cur in items else None
            ui.update_select("cross_id", choices=items, selected=selected)

        @reactive.calc
        async def runners_df():

            cid = self.selected_cross_id.get()
            _ = self.refresh_tick.get()  # depend on refresh to re-query

            if not cid:
                return pd.DataFrame()
            return await self.controller.list_runners_df(int(cid))


        @output
        @render.data_frame
        async def runners_grid():
            df = await runners_df()
            return render.DataGrid(df, filters=False, selection_mode="rows")

        @output
        @render.text
        def runner_status():
            return status.get()

        @output
        @render.text
        def runner_military():
            sm = self.selected_military.get()
            if not sm:
                return "No selection"
            try:
                return "" #f"{sm.rank} {sm.service_number} {sm.first_name} {sm.last_name}"
            except Exception:
                return "Selected"

        @reactive.calc
        async def cross_df():
            _ = self.refresh_tick.get()  # dependency for re-render
            # ... load and return DataFrame ...

        @reactive.Effect
        async def _init():
            await _refresh_cross_choices()

      #  @reactive.Effect
        async def _on_cross_change():
            val = (input.cross_id() or "").strip()
            self.selected_cross_id.set(val)
            if val:
                _ = await self.controller.get_cross_by_id(int(val))
                self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.runner_search)
        async def _on_search_serial():
            serial = (input.runner_serialnr() or "").strip()
            if not serial:
                self.selected_military.set(None)
                status.set("Enter a serial number.")
                return
            sm = await self.controller.search_military(serial)
            self.selected_military.set(sm)
            if sm is None:
                status.set("Not found.")
            else:
                status.set(f"Service {sm.rank} {sm.last_name} {sm.service_number} member found.")

        @reactive.Effect
        @reactive.event(input.runners_grid_selected_rows)
        async def _on_row_selected():
            try:
                sel = input.runners_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row_idx = sel[0]
                df = await runners_df()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row = df.iloc[row_idx]
                self.selected_runner_id.set(str(row["ID"]))
                serial = str(row.get("Serial", "") or "")
                run_t = str(row.get("Running Time", "") or "")
                ui.update_text("runner_serialnr", value=serial)
                ui.update_text("runner_time", value=run_t)
                status.set(f"Selected Runner: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.runner_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = await self.controller.validate_form(data)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            # ensure cross id is set
            if not payload.get("cross_id"):
                status.set("Select a Cross first.")
                return
            added = await self.controller.add_runner(int(payload["cross_id"]), payload)
            if not added:
                status.set(f"Failed to add runner {payload['serialnr']}.")
                return
            self.selected_runner_id.set("")
            self.refresh_tick.set(self.refresh_tick.get() + 1)  # triggers runners_df
            status.set(f"Added runner {payload['serialnr']}.")

        @reactive.Effect
        @reactive.event(input.runner_update_btn)
        async def _on_update():
            rid = self.selected_runner_id.get()
            if not rid:
                status.set("Select a row first.")
                return
            data = _read_form()
            ok, res = self.controller.validate_form(data)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            updated = await self.controller.update_runner(int(rid), payload)
            if not updated:
                status.set(f"Failed to update runner {payload['serialnr']}.")
                return
            status.set(f"Updated runner {payload['serialnr']}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            _clear_form()

        @reactive.Effect
        @reactive.event(input.runner_delete_btn)
        async def _on_delete():
            sel = input.runners_grid_selected_rows()
            cid = (input.cross_id() or "").strip()
            rid = self.selected_runner_id.get()
            if not sel or not cid or not rid:
                status.set("Select a row to delete.")
                return
            ok = await self.controller.delete_runner(int(cid), int(rid))
            if not ok:
                status.set("Failed to delete runner.")
                return
            status.set("Runner deleted successfully.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            _clear_form()


# Expose singleton-style API compatible with app.py import pattern
_page = CrossPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)