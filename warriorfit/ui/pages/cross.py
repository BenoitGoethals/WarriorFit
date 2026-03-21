from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from shiny import ui, render, reactive

from warriorfit.ui.pages.page import Page

# UI:
ui.output_ui("runner_card")

from warriorfit.ui.controllers.cross_controller import CrossController
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container


class CrossPage(Page):
    @inject
    def __init__(self, controller: CrossController = Provide[Container.cross_controller]):
        super().__init__()
        self.controller = controller
        self.refresh_tick = reactive.Value(0)
        self.selected_cross_id = reactive.Value("")
        self.selected_runner_id = reactive.Value("")
        self.selected_military = reactive.Value(None)
        self._logger = logging.getLogger(__name__)
        self._last_paths = None

    NO_SELECTION_MESSAGE = "No row selected"

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Cross",
            ui.h2("🏃 Cross Runners"),
            ui.input_action_button("cross_refresh_btn", "🔄 Refresh", class_="btn btn-secondary btn-sm my-2"),
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

                    ui.output_ui("upload_btn_ui"),
                    ui.output_ui("download_generated_report_btn_ui"),


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
        async def upload_btn_ui():
            df = await runners_df()
            if not df.empty:
                return ui.div()  # hidden: no cross selected or no runners registered
            return ui.input_file("file", "Upload Chronos Data", accept=".xml")

        @output
        @render.ui
        async def download_generated_report_btn_ui():
            df = await runners_df()
            if not cross_selected_id.get() or df.empty:
                return ui.div()
            return ui.div(
                ui.input_action_button("report_lst_run", "Generate Report", class_="btn-secondary"),
                ui.download_button("download_report_cross_run", "Download", class_="btn-primary"),
            )

        @output
        @render.ui
        def runner_card():
            if not cross_selected_id.get():
                return ui.div()  # hidden
            return ui.card(
                ui.card_header("Runner"),
                ui.input_text("runner_serialnr", "Serial Number"),
                ui.input_action_button(
                    "runner_search", "✅ Confirm Serial",
                    class_="btn btn-primary btn-sm", width="200px",
                ),
                ui.output_text("runner_military"),
                ui.input_text(
                    "runner_time",
                    "Running time (hh::mm:ss)",
                    placeholder="e.g., 01:10:45",
                ),
                ui.layout_columns(
                    ui.input_action_button(
                        "runner_add_btn",
                        "Add",
                        width="120px",
                        class_="btn-primary w-100",
                    ),
                    ui.input_action_button(
                        "runner_update_btn",
                        "Update",
                        width="120px",
                        class_="btn-warning w-100",
                    ),
                    ui.input_action_button(
                        "runner_clear_btn",
                        "Clear Form",
                        width="120px",
                        class_="btn-secondary w-100",
                    ),
                    ui.input_action_button(
                        "runner_delete_btn",
                        "Delete Selected",
                        width="240px",
                        class_="btn-danger w-100",
                    ),
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

        @reactive.effect
        async def _handle_file_upload():
            f = input.file()
            if not f:
                return
            passed = await self.controller.parse_chronos_data(f)
            if passed is not None:
                ui.notification_show("File uploaded successfully.", type="message", duration=3)
            else:
                ui.notification_show("Failed to upload file.", type="error", duration=3)



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
            # status.set("Form cleared.")

        async def _refresh_cross_choices():
            crosses = await self.controller.load_crosses()
            items = {
                str(c.id): getattr(
                    c, "name", f"Cross  {c.datetime_start.strftime('%d-%m-%y %H:%M')}"
                )
                for c in (crosses or [])
            }
            cur = (input.cross_id() or "").strip()
            selected = cur if cur in items else None
            ui.update_select("cross_id", choices=items, selected=selected)

        @reactive.calc
        async def runners_df():
            cid = self.selected_cross_id.get()
            _ = self.refresh_tick.get()
            if not cid:
                return pd.DataFrame()
            df = await self.controller.list_runners_df(int(cid))
            return df

        @output
        @render.data_frame
        async def runners_grid():
            df = await runners_df()
            return render.DataGrid(
                df.drop(columns=["ID"], errors="ignore"),
                filters=False,
                selection_mode="rows",
                width="100%",
            )

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
                return ""  # f"{sm.rank} {sm.service_number} {sm.first_name} {sm.last_name}"
            except Exception:
                return "Selected"

        @reactive.calc
        async def cross_df():
            _ = self.refresh_tick.get()  # dependency for re-render

        @reactive.Effect
        async def _init():
            await _refresh_cross_choices()

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
                status.set(
                    f"Service {sm.rank} {sm.last_name} {sm.service_number} member found."
                )

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
                self.selected_military.set(
                    await self.controller.search_military(row["Serial"])
                )
                serial = str(row.get("Serial", "") or "")
                run_t = str(row.get("Running Time", "") or "")
                ui.update_text("runner_serialnr", value=serial)
                ui.update_text("runner_time", value=run_t)
                status.set(f"Selected Runner: {serial}")
            except (KeyError, TypeError, ValueError, AttributeError) as e:
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
            ui.notification_show(f"Runner {payload['serialnr']} added.", type="message", duration=3)

        @reactive.Effect
        @reactive.event(input.runner_update_btn)
        async def _on_update():
            rid = self.selected_runner_id.get()
            if not rid:
                status.set("Select a row first.")
                return
            data = _read_form()
            data["old_serialnr"] = getattr(
                self.selected_military.get(), "service_number", None
            )
            ok, res = await self.controller.validate_form(data, True)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            updated = await self.controller.update_runner(int(rid), payload)
            if not updated:
                status.set(f"Failed to update runner {payload['serialnr']}.")
                return
            self.selected_runner_id.set("")
            self.refresh_tick.set(self.refresh_tick.get() + 1)  # triggers runners_df
            status.set(f"Updated runner {payload['serialnr']}.")
            ui.notification_show(f"Runner {payload['serialnr']} updated.", type="message", duration=3)

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
            ok = await self.controller.delete_runner(int(rid))
            if not ok:
                status.set("Failed to delete runner.")
                return
            status.set("Runner deleted successfully.")
            ui.notification_show("Runner deleted.", type="warning", duration=3)
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            _clear_form()

        @reactive.Effect
        @reactive.event(input.cross_refresh_btn)
        def _on_cross_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.effect
        @reactive.event(input.report_lst_run)
        async def _on_generate():
            self._last_paths = await self.controller.generate_report_cross(
                cross_selected_id.get()
            )
            if not self._last_paths:
                status.set("No report generated.")
                return

        @render.download(filename=lambda: "reports_run.zip")
        def download_report_cross_run():
            import io
            import zipfile

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:

                try:
                    path_obj = Path(self._last_paths)
                    if path_obj.is_file():
                        zf.write(path_obj, arcname=path_obj.name)
                except Exception:
                    logging.exception("Failed to add file to zip")
            buf.seek(0)
            data = buf.read()

            # Return an iterator yielding bytes (not text, not int)
            def _iter():
                yield data

            return _iter()


# Expose singleton-style API compatible with app.py import pattern
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = CrossPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)
