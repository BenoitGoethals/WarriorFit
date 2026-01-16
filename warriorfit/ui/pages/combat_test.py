from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Optional

import pandas as pd
from pandas import DataFrame
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.data.model.db_model import ServiceMen, TestSession
from warriorfit.services.military_service import MilitaryService
from warriorfit.ui.controllers.combat_controller import CombatController
from warriorfit.ui.pages.page import Page


@dataclass(frozen=True, slots=True)
class CombatFormData:
    serialnr: str
    session_id: str
    combat_robe: bool
    combat_obstacle: bool
    combat_speedmars: str


class CombatPage(Page):
    TAB_NAME: Final[str] = "Combat Tests"
    NO_SELECTION_MESSAGE: Final[str] = "No row selected"

    # Disable these inputs until serial is confirmed
    _DISABLE_IDS: Final[tuple[str, ...]] = (
        "combat_speedmars",
        "combat_speedmars_input",
        "combat_obstacle",
        "combat_obstacle_input",
        "combat_robe",
        "combat_robe_input",
    )

    def __init__(self) -> None:
        super().__init__()
        self.be_mil_service = MilitaryService()  # kept for compatibility
        self.selected_military: Optional[ServiceMen] = None
        self.selected_session: Optional[TestSession] = None
        self.controller = CombatController()

    def refresh(self) -> None:
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self) -> NavPanel:
        return ui.nav_panel(
            self.TAB_NAME,
            # Register ONE JS custom message handler (same pattern as PHEF)
            ui.tags.script(
                """
                (function () {
                  if (window.__wf_toggle_disabled_registered) return;
                  window.__wf_toggle_disabled_registered = true;

                  Shiny.addCustomMessageHandler("wf_toggle_disabled", function (payload) {
                    try {
                      const ids = (payload && payload.ids) ? payload.ids : [];
                      const disabled = !!(payload && payload.disabled);
                      ids.forEach((id) => {
                        const el = document.getElementById(id);
                        if (el) el.disabled = disabled;
                      });
                    } catch (e) {
                      // no-op
                    }
                  });
                })();
                """
            ),
            ui.h2("🧪 Combat Tests"),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Session"),
                        ui.input_select("combat_session_id", "Session", choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.div(
                            ui.input_text("combat_serialnr", "Serial Number"),
                            ui.input_action_button("combat_serial_search_btn", "🔍 Search", class_="btn-info btn-sm",
                                                  style="margin-top: 5px;"),
                        ),
                        ui.input_action_button("combat_search", "Confirm Serial", width="150px"),
                        ui.output_text("combat_military"),
                        ui.layout_columns(
                            ui.input_checkbox("combat_obstacle", "Obstacle course", value=False),
                        ),
                        ui.layout_columns(
                            ui.input_checkbox("combat_robe", "Robe Course", value=False),
                        ),
                        ui.layout_columns(
                            ui.input_text(
                                "combat_speedmars",
                                "Speedmars time (mm:ss)",
                                placeholder="e.g., 10:45",
                            ),
                            ui.div("Score:", ui.output_ui("combat_speedmars_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.div("Total:", ui.output_ui("combat_total_score")),
                            col_widths=(12,),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "combat_add_btn",
                                "Add",
                                disabled=True,
                                width="150px",
                                class_="btn-primary w-100",
                            ),
                            ui.input_action_button(
                                "combat_update_btn",
                                "Update",
                                disabled=True,
                                width="150px",
                                class_="btn-warning w-100",
                            ),
                            ui.input_action_button(
                                "combat_clear_btn",
                                "Clear Form",
                                width="150px",
                                class_="btn-secondary w-100",
                            ),
                            ui.input_action_button(
                                "combat_delete_btn",
                                "Delete Selected",
                                class_="btn-danger w-100",
                            ),
                            col_widths=(4,),
                        ),
                        ui.output_text("combat_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("Combat Tests (Pass requires all tests)"),
                    ui.output_data_frame("combat_grid"),
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
        selected_combat_id = reactive.Value("")

        speedmars_pass_fail = reactive.Value("")  # "Passes" / "Fails" / ""

        @reactive.Effect
        async def _init() -> None:
            # Triggered on init and whenever refresh_tick changes
            self.refresh_tick.get()
            await _refresh_session_choices()
            await _clear_form()
            status.set("Ready.")

        # ----------------------------
        # UI state helpers
        # ----------------------------
        async def _toggle_inputs(disabled: bool) -> None:
            try:
                await session.send_custom_message(
                    "wf_toggle_disabled",
                    {"ids": list(self._DISABLE_IDS), "disabled": bool(disabled)},
                )
            except Exception:
                # Fail open; app stays usable even if custom message fails.
                pass

        def _set_buttons(*, can_add: bool, can_update: bool) -> None:
            ui.update_action_button("combat_add_btn", disabled=not can_add)
            ui.update_action_button("combat_update_btn", disabled=not can_update)

        async def _clear_form() -> None:
            session.send_input_message("combat_serialnr", {"value": ""})
            session.send_input_message("combat_obstacle", {"value": False})
            session.send_input_message("combat_robe", {"value": False})
            session.send_input_message("combat_speedmars", {"value": ""})

            self.selected_military = None
            selected_combat_id.set("")
            speedmars_pass_fail.set("")

            await _toggle_inputs(disabled=True)
            _set_buttons(can_add=False, can_update=False)

        def _read_form() -> CombatFormData:
            return CombatFormData(
                serialnr=(input.combat_serialnr() or "").strip(),
                session_id=(input.combat_session_id() or "").strip(),
                combat_robe=bool(input.combat_robe()),
                combat_obstacle=bool(input.combat_obstacle()),
                combat_speedmars=(input.combat_speedmars() or "").strip(),
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

        # ----------------------------
        # Outputs
        # ----------------------------
        @output
        @render.text
        def combat_status() -> str:
            return status.get()

        @output
        @render.text
        def combat_military() -> str:
            return military_text.get()

        @output
        @render.ui
        def combat_speedmars_score() -> ui.Tag:
            val = speedmars_pass_fail.get()
            if not val:
                return ui.span("")
            color = "green" if val == "Passes" else "red"
            return ui.span(val, style=f"color: {color}; font-weight: 600;")

        @output
        @render.ui
        def combat_total_score() -> ui.Tag:
            try:
                passed = (
                    speedmars_pass_fail.get() == "Passes"
                    and bool(input.combat_robe())
                    and bool(input.combat_obstacle())
                )
                return ui.span(
                    "Passed" if passed else "Failed",
                    style=("color: green; font-weight: 700;" if passed else "color: red; font-weight: 700;"),
                )
            except Exception:
                return ui.span("")

        # ----------------------------
        # Session choices + selection
        # ----------------------------
        async def _refresh_session_choices() -> None:
            try:
                test_sessions = await self.controller.load_sessions()
            except Exception:
                test_sessions = []

            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.combat_session_id() or "").strip()
            ui.update_select("combat_session_id", choices=items, selected=(current if current in items else None))

        @reactive.Effect
        async def _init() -> None:
            await _refresh_session_choices()
            await _clear_form()
            status.set("Ready.")

        @reactive.Effect
        async def _on_session_change() -> None:
            val = (input.combat_session_id() or "").strip()
            selected_session_id.set(val)

            # Prevent mixing records between sessions
            await _clear_form()
            self.selected_session = None

            if not val:
                status.set("Select a session.")
                return
            status.set("Session selected. Confirm a serial to enter results.")

        @reactive.Effect
        @reactive.event(input.combat_session_id)
        async def _load_session_object() -> None:
            val = (input.combat_session_id() or "").strip()
            if not val:
                self.selected_session = None
                return
            try:
                self.selected_session = await self.controller.get_test_session_by_id(int(val))
            except Exception:
                self.selected_session = None

        # ----------------------------
        # Search military / unlock form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.combat_search, ignore_none=False)
        async def _on_search() -> None:
            if not _require_session_selected():
                return

            serial = (input.combat_serialnr() or "").strip()
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

            military_text.set(
                f"{val.rank} {val.service_number} {val.first_name} {val.last_name} "
                f"{val.gender} {val.age_from_birthdate()} years old"
            )
            status.set("Serial confirmed. Enter results.")
            await _toggle_inputs(disabled=False)
            _set_buttons(can_add=True, can_update=True)

        # ----------------------------
        # Live scoring
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.combat_speedmars)
        def _on_speedmars_change() -> None:
            raw = (input.combat_speedmars() or "").strip()
            if not raw:
                speedmars_pass_fail.set("")
                return

            ok, seconds = self.controller.parse_time_to_seconds(raw)
            if not ok:
                speedmars_pass_fail.set("")
                return


            try:
                speedmars_pass_fail.set("Passes" if float(seconds) < 120 * 60 else "Fails")
            except Exception:
                speedmars_pass_fail.set("")

        # ----------------------------
        # Grid data
        # ----------------------------
        @reactive.calc
        async def combat_df() -> DataFrame | None:
            _ = self.refresh_tick.get()
            sess_id = (selected_session_id.get() or "").strip()
            if not sess_id:
                return pd.DataFrame()
            try:
                df = await self.controller.list_combat_tests_df(int(sess_id))
            except Exception:
                return pd.DataFrame()
            try:
                df = self.controller.decorate_grid(df)
                df = df.drop(columns=["id"], errors="ignore")  # hide ID in UI only
                return df.sort_values(by=["Serial"])
            except Exception:
                return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        @output
        @render.data_frame
        async def combat_grid():
            df = await combat_df()
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="row",
                width="100%",
            )

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.combat_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.combat_grid_selected_rows()
            if not sel:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            df = await combat_df()
            if df is None or df.empty:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row = df.iloc[row_idx]
            combat_id = str(row.get("ID", "") or "").strip()
            selected_combat_id.set(combat_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("combat_serialnr", value=serial)

            obstacle_passed = str(row.get("ObstacleCourse", "") or "").strip().lower() == "passed"
            robe_passed = str(row.get("RobeCourse", "") or "").strip().lower() == "passed"

            ui.update_checkbox("combat_obstacle", value=obstacle_passed)
            ui.update_checkbox("combat_robe", value=robe_passed)

            speedmars_val = row.get("speedmarsTime", "")
            ui.update_text("combat_speedmars", value=str(speedmars_val or ""))

            # Selecting an existing record: Update/Delete, but not Add
            _set_buttons(can_add=False, can_update=True)

            # Resolve military so live scoring/validation behaves
            try:
                self.selected_military = await self.controller.search_military(serial) if serial else None
            except Exception:
                self.selected_military = None

            await _toggle_inputs(disabled=(self.selected_military is None))
            status.set(f"Selected Combat record for: {serial}" if serial else "Selected Combat record.")

        # ----------------------------
        # CRUD
        # ----------------------------
        def _validate(form: CombatFormData) -> tuple[bool, Any]:
            try:
                return self.controller.validate_form(
                    {
                        "serialnr": form.serialnr,
                        "session_id": form.session_id,
                        "combat_robe": form.combat_robe,
                        "combat_obstacle": form.combat_obstacle,
                        "combat_speedmars": form.combat_speedmars,
                    }
                )
            except Exception as e:
                return False, f"Validation failed: {e}"

        @reactive.Effect
        @reactive.event(input.combat_add_btn)
        async def _on_add() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            form = _read_form()
            ok, res = _validate(form)
            if not ok:
                status.set(str(res))
                return

            # The controller seems to return normalized values in `res` (per old code style)
            payload = {
                "id": form.session_id,
                "serialnr": form.serialnr,
                "combat_obstacle": res.get("combat_obstacle", form.combat_obstacle),
                "combat_robe": res.get("combat_robe", form.combat_robe),
                "combat_speedmars": res.get("combat_speedmars", form.combat_speedmars),
            }

            added = await self.controller.add_combat(
                int(form.session_id),
                payload,
                session=self.selected_session,
                military=self.selected_military,
            )
            if not added:
                status.set(f"Failed to add Combat test for {form.serialnr} in session {form.session_id}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Added Combat test for {form.serialnr} in session {form.session_id}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.combat_update_btn)
        async def _on_update() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            combat_id_raw = (selected_combat_id.get() or "").strip()
            if not combat_id_raw:
                status.set("Select a row to update.")
                return

            form = _read_form()
            ok, res = _validate(form)
            if not ok:
                status.set(str(res))
                return

            payload = {
                "session_id": form.session_id,
                "serialnr": form.serialnr,
                **(res if isinstance(res, dict) else {}),
            }

            updated = await self.controller.update_combat(int(combat_id_raw), payload)
            if not updated:
                status.set(f"Failed to update Combat test for {form.serialnr} in session {form.session_id}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated Combat test for {form.serialnr} in session {form.session_id}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.combat_delete_btn)
        async def _on_delete() -> None:
            sess_id_raw = (input.combat_session_id() or "").strip()
            combat_id_raw = (selected_combat_id.get() or "").strip()
            if not sess_id_raw or not combat_id_raw:
                status.set("Select a row to delete.")
                return

            ok = await self.controller.delete_combat(int(sess_id_raw), int(combat_id_raw))
            if not ok:
                status.set("Failed to delete selected Combat record.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set("Combat record deleted successfully.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.combat_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set("Form cleared.")

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.combat_serial_search_btn)
        async def _open_serial_search_modal() -> None:
            modal_content = ui.modal(
                ui.card(
                    ui.card_header("Select Serial Number"),
                    ui.output_data_frame("combat_serial_search_grid"),
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
        async def combat_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="row", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.combat_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.combat_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("combat_serialnr", value=str(row["service_number"]))
                    ui.modal_remove()


_page = CombatPage()


def get_ui() -> NavPanel:
    return _page.get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _page.server(input, output, session)