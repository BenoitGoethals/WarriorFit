from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Optional

import pandas as pd
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.data.model.db_model import ServiceMen, TestSession
from warriorfit.ui.controllers.swimming_controller import SwimmingController
from warriorfit.ui.pages.page import Page


@dataclass(frozen=True, slots=True)
class SwimFormData:
    serialnr: str
    session_id: str
    swim_passed: bool


class SwimTestPage(Page):
    TAB_NAME: Final[str] = "Swimming Tests"
    NO_SELECTION_MESSAGE: Final[str] = "No row selected"

    # Disable these inputs until serial is confirmed
    _DISABLE_IDS: Final[tuple[str, ...]] = (
        "swim_passed",
        "swim_passed_input",
    )

    def __init__(self) -> None:
        super().__init__()
        self.selected_military: Optional[ServiceMen] = None
        self.selected_session: Optional[TestSession] = None
        self.controller = SwimmingController()

    def refresh(self) -> None:
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self) -> NavPanel:
        return ui.nav_panel(
            self.TAB_NAME,
            # One JS custom message handler to toggle input disabling (no repeated script injection).
            ui.tags.script(
                self.toggle_disabled_registered_func
            ),
            ui.h2("🏊 Swimming Tests"),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Session"),
                        ui.input_select("swim_session_id", "Session", choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.div(
                            ui.input_text("swim_serialnr", "Serial Number", placeholder="Service Number"),
                            ui.input_action_button("swim_serial_search_btn", "🔍 Search own Unit", class_="btn-info btn-sm",
                                                  style="margin-top: 5px;"),
                        ),
                        ui.input_action_button("swim_search", "Confirm Serial", width="200px"),
                        ui.output_text("swim_military"),
                        ui.layout_columns(
                            ui.input_checkbox("swim_passed", "Swimming Test Passed", value=False),
                            ui.div("Status:", ui.output_ui("swim_status_display")),
                            col_widths=(8, 4),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "swim_add_btn",
                                "Add",
                                disabled=True,
                                width="150px",
                                class_="btn-primary w-100",
                            ),
                            ui.input_action_button(
                                "swim_update_btn",
                                "Update",
                                disabled=True,
                                width="150px",
                                class_="btn-warning w-100",
                            ),
                            ui.input_action_button(
                                "swim_clear_btn",
                                "Clear Form",
                                width="150px",
                                class_="btn-secondary w-100",
                            ),
                            ui.input_action_button(
                                "swim_delete_btn",
                                "Delete Selected",
                                class_="btn-danger w-100",
                            ),
                            col_widths=(4,),
                        ),
                        ui.output_text("swim_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("Swimming Tests (includes members outside own unit)"),
                    ui.output_data_frame("swim_grid"),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        self.refresh_on_nav(input, self.TAB_NAME)

        status = reactive.Value("Ready.")
        military_text = reactive.Value("No selection")

        selected_session_id = reactive.Value("")
        selected_swim_id = reactive.Value("")

        swim_passed_val = reactive.Value(False)

        # ----------------------------
        # UI state helpers
        # ----------------------------
        async def _toggle_inputs(disabled: bool) -> None:
            # NOTE: send_custom_message is async; must be awaited (otherwise RuntimeWarning).
            try:
                await session.send_custom_message(
                    "wf_toggle_disabled",
                    {"ids": list(self._DISABLE_IDS), "disabled": bool(disabled)},
                )
            except Exception:
                # Fail open; app stays usable even if custom message fails.
                pass

        def _set_buttons(*, can_add: bool, can_update: bool) -> None:
            ui.update_action_button("swim_add_btn", disabled=not can_add)
            ui.update_action_button("swim_update_btn", disabled=not can_update)

        async def _clear_form() -> None:
            session.send_input_message("swim_serialnr", {"value": ""})
            session.send_input_message("swim_passed", {"value": False})

            self.selected_military = None
            selected_swim_id.set("")
            swim_passed_val.set(False)

            await _toggle_inputs(disabled=True)
            _set_buttons(can_add=False, can_update=False)

        def _read_form() -> SwimFormData:
            return SwimFormData(
                serialnr=(input.swim_serialnr() or "").strip(),
                session_id=(input.swim_session_id() or "").strip(),
                swim_passed=bool(input.swim_passed()),
            )

        def _require_session_selected() -> bool:
            if not (selected_session_id.get() or "").strip():
                status.set("Select a session first.")
                return False
            return True

        def _require_military_selected() -> bool:
            if self.selected_military is None:
                status.set("Confirm a valid serial first.")
                return False
            return True

        async def _refresh_session_choices() -> None:
            try:
                sessions = await self.controller.load_sessions()
            except Exception:
                sessions = []

            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (sessions or [])
            }
            current = (input.swim_session_id() or "").strip()
            ui.update_select("swim_session_id", choices=items, selected=(current if current in items else None))

        # ----------------------------
        # Outputs
        # ----------------------------
        @output
        @render.text
        def swim_status() -> str:
            return status.get()

        @output
        @render.text
        def swim_military() -> str:
            return military_text.get()

        @output
        @render.ui
        def swim_status_display() -> ui.Tag:
            passed = bool(swim_passed_val.get())
            text = "PASSED" if passed else "FAILED"
            color = "green" if passed else "red"
            return ui.span(text, style=f"color: {color}; font-weight: 700;")

        # Keep the reactive value in sync with the checkbox
        @reactive.Effect
        @reactive.event(input.swim_passed)
        def _on_swim_passed_change() -> None:
            swim_passed_val.set(bool(input.swim_passed()))

        # ----------------------------
        # Init / session selection
        # ----------------------------
        @reactive.Effect
        async def _init() -> None:
            await _refresh_session_choices()
            await _clear_form()
            status.set("Ready.")

        @reactive.Effect
        async def _on_session_change() -> None:
            val = (input.swim_session_id() or "").strip()
            selected_session_id.set(val)

            # Switching sessions should reset form state.
            await _clear_form()
            self.selected_session = None

            if not val:
                status.set("Select a session.")
                return
            status.set("Session selected. Confirm a serial to enter results.")

        @reactive.Effect
        @reactive.event(input.swim_session_id)
        async def _load_session_object() -> None:
            val = (input.swim_session_id() or "").strip()
            if not val:
                self.selected_session = None
                return
            try:
                self.selected_session = await self.controller.get_session_by_id(int(val))
            except Exception:
                self.selected_session = None

        # ----------------------------
        # Search military / unlock inputs
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.swim_search, ignore_none=False)
        async def _on_search() -> None:
            if not _require_session_selected():
                return

            serial = (input.swim_serialnr() or "").strip()
            if not serial:
                status.set("Enter a serial number.")
                await _clear_form()
                return

            try:
                val = await self.controller.search_military(serial)
            except Exception:
                val = None

            self.selected_military = val
            if val is None:
                military_text.set("Not found")
                status.set("Serial not found.")
                await _toggle_inputs(disabled=True)
                _set_buttons(can_add=False, can_update=False)
                return

            military_text.set(f"{val.rank} {val.service_number} {val.first_name} {val.last_name}")
            status.set("Serial confirmed. Set result and save.")
            await _toggle_inputs(disabled=False)
            _set_buttons(can_add=True, can_update=True)

        # ----------------------------
        # Grid data
        # ----------------------------
        @reactive.calc
        async def sessions_swim_data() -> pd.DataFrame:
            _ = self.refresh_tick.get()
            sess_id = (selected_session_id.get() or "").strip()
            if not sess_id:
                return pd.DataFrame()
            try:
                return await self.controller.list_swim_df(int(sess_id))
            except Exception:
                return pd.DataFrame()

        @output
        @render.data_frame
        async def swim_grid():
            df = await sessions_swim_data()
            df_view = pd.DataFrame()

            try:
                df = self.controller.decorate_grid(df)
                df.sort_values(by=["Serial"], inplace=True)
                df_view = df.drop(columns=["ID"], errors="ignore")
            except Exception:
                df_view = df if not df.empty else pd.DataFrame()

            return render.DataGrid(
                df_view,
                filters=False,
                selection_mode="row",
                width="100%",
            )

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.swim_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.swim_grid_selected_rows()
            if not sel:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            df = await sessions_swim_data()
            if df is None or df.empty:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row = df.iloc[row_idx]
            swim_id = str(row.get("ID", "") or "").strip()
            selected_swim_id.set(swim_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("swim_serialnr", value=serial)

            result_txt = str(row.get("Result", "") or "").strip().upper()
            passed = result_txt == "PASSED"
            ui.update_checkbox("swim_passed", value=passed)

            # Selecting an existing record: allow Update, disable Add.
            _set_buttons(can_add=False, can_update=True)

            try:
                self.selected_military = await self.controller.search_military(serial) if serial else None
            except Exception:
                self.selected_military = None

            await _toggle_inputs(disabled=(self.selected_military is None))
            status.set(f"Selected Swimming Test: {serial}" if serial else "Selected Swimming Test.")

        # ----------------------------
        # CRUD
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.swim_add_btn)
        async def _on_add() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            form = _read_form()
            ok, res = self.controller.validate_form(
                {
                    "serialnr": form.serialnr,
                    "session_id": form.session_id,
                    "swim_passed": form.swim_passed,
                }
            )
            if not ok:
                status.set(str(res))
                return

            payload = {
                "id": form.session_id,
                "serialnr": form.serialnr,
                "swim_passed": res["swim_passed"],
            }

            added = await self.controller.add_swim(
                int(payload["id"]),
                payload,
                session=self.selected_session,
                military=self.selected_military,
            )
            if not added:
                status.set(f"Failed to add Swimming test for {payload['serialnr']} in session {payload['id']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Added Swimming test for {payload['serialnr']} in session {payload['id']}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_update_btn)
        async def _on_update() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            swim_id_raw = (selected_swim_id.get() or "").strip()
            if not swim_id_raw:
                status.set("Select a row to update.")
                return

            form = _read_form()
            ok, res = self.controller.validate_form(
                {
                    "serialnr": form.serialnr,
                    "session_id": form.session_id,
                    "swim_passed": form.swim_passed,
                }
            )
            if not ok:
                status.set(str(res))
                return

            payload = {
                "session_id": form.session_id,
                "serialnr": form.serialnr,
                "swim_passed": res["swim_passed"],
            }

            updated = await self.controller.update_swim(int(swim_id_raw), payload)
            if not updated:
                status.set(f"Failed to update Swimming test for {payload['serialnr']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated Swimming test for {payload['serialnr']}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_delete_btn)
        async def _on_delete() -> None:
            sess_id_raw = (input.swim_session_id() or "").strip()
            swim_id_raw = (selected_swim_id.get() or "").strip()
            if not sess_id_raw or not swim_id_raw:
                status.set("Select a row to delete.")
                return

            ok = await self.controller.delete_swim(int(sess_id_raw), int(swim_id_raw))
            if not ok:
                status.set("Failed to delete selected Swimming record.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set("Swimming test deleted successfully.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set("Form cleared.")

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.swim_serial_search_btn)
        async def _open_serial_search_modal() -> None:
            modal_content = ui.modal(
                ui.card(
                    ui.card_header("Select Serial Number"),
                    ui.output_data_frame("swim_serial_search_grid"),
                    full_screen=False,
                ),
                size="l",
                easy_close=True,
            )
            ui.modal_show(modal_content)

        @reactive.calc
        async def get_all_servicemen_df() -> pd.DataFrame:
            servicemen = await self.controller.be_mil_service.get_all_service_men()
            if not servicemen:
                return pd.DataFrame(columns=["service_number",  "first_name", "last_name", "gender"])

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

        @render.data_frame
        async def swim_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="row", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.swim_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.swim_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("swim_serialnr", value=str(row["service_number"]))
                    ui.modal_remove()


# Public API
_page = SwimTestPage()


def get_ui() -> ui.Tag:
    return _page.get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _page.server(input, output, session)