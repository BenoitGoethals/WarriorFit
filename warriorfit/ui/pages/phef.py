from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Optional

import pandas as pd
from shiny import ui, render, reactive
from shiny.ui._navs import NavPanel

from warriorfit.data.model.db_model import ServiceMen, TestSession
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.ui.controllers.phef_controller import PhefController
from warriorfit.ui.pages.page import Page


@dataclass(frozen=True, slots=True)
class PhefFormData:
    serialnr: str
    session_id: str
    side_bridge_r: str
    side_bridge_l: str
    run_2400: str


class PhefPage(Page):
    TAB_NAME: Final[str] = "PHEF Tests"
    NO_SELECTION_MESSAGE: Final[str] = "No row selected"

    # These IDs are disabled until the user confirms a valid serial.
    _DISABLE_IDS: Final[tuple[str, ...]] = (
        "ph_run_2400",
        "ph_run_2400_input",
        "ph_side_bridge_r",
        "ph_side_bridge_r_input",
        "ph_side_bridge_l",
        "ph_side_bridge_l_input",
    )

    def __init__(self) -> None:
        super().__init__()
        self.be_mil_service = MilitaryService()  # kept for compatibility/side-effects if used elsewhere
        self.selected_military: Optional[ServiceMen] = None
        self.selected_session: Optional[TestSession] = None
        self.controller = PhefController()

    def refresh(self) -> None:
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self) -> NavPanel:
        return ui.nav_panel(
            self.TAB_NAME,
            # Register ONE custom-message handler to toggle disabling inputs.
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
            ui.h2("🧪 PHEF Tests"),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Session"),
                        ui.input_select("ph_session_id", "Session", choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.input_text("ph_serialnr", "Serial Number"),
                        ui.input_action_button("ph_search", "Confirm Serial", width="150px"),
                        ui.output_text("ph_military"),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_side_bridge_r",
                                "Side-bridge Right time (mm:ss)",
                                placeholder="e.g., 2:30",
                            ),
                            ui.div("Score :", ui.output_ui("ph_side_bridge_r_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_side_bridge_l",
                                "Side-bridge Left time (mm:ss)",
                                placeholder="e.g., 2:30",
                            ),
                            ui.div("Score :", ui.output_ui("ph_side_bridge_l_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_run_2400",
                                "2400m run time (mm:ss)",
                                placeholder="e.g., 10:45",
                            ),
                            ui.div("Score :", ui.output_ui("ph_run_2400_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.div("Total:", ui.output_ui("ph_total_score")),
                            col_widths=(12,),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "ph_add_btn",
                                "Add",
                                disabled=True,
                                width="150px",
                                class_="btn-primary w-100",
                            ),
                            ui.input_action_button(
                                "ph_update_btn",
                                "Update",
                                disabled=True,
                                width="150px",
                                class_="btn-warning w-100",
                            ),
                            ui.input_action_button(
                                "ph_clear_btn",
                                "Clear Form",
                                width="150px",
                                class_="btn-secondary w-100",
                            ),
                            ui.input_action_button(
                                "ph_delete_btn",
                                "Delete Selected",
                                class_="btn-danger w-100",
                            ),
                            col_widths=(4,),
                        ),
                        ui.output_text("ph_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header(
                        "PHEF Tests (Pass requires running and both side-bridge tests). "
                        "List includes members outside own unit."
                    ),
                    ui.output_data_frame("ph_grid"),
                    ui.br(),
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
        selected_phef_id = reactive.Value("")

        side_r_score = reactive.Value("")  # expected numeric-as-string from calculator
        side_l_score = reactive.Value("")
        run_score = reactive.Value("")

        # ----------------------------
        # UI state helpers
        # ----------------------------
        async def _toggle_inputs(disabled: bool) -> None:
            # One custom message instead of inserting script repeatedly.
            try:
                await session.send_custom_message(
                    "wf_toggle_disabled",
                    {"ids": list(self._DISABLE_IDS), "disabled": bool(disabled)},
                )
            except Exception:
                # Fail open; app stays usable even if custom message fails.
                pass

        def _set_buttons(*, can_add: bool, can_update: bool) -> None:
            ui.update_action_button("ph_add_btn", disabled=not can_add)
            ui.update_action_button("ph_update_btn", disabled=not can_update)

        async def _clear_form() -> None:
            session.send_input_message("ph_serialnr", {"value": ""})
            session.send_input_message("ph_side_bridge_r", {"value": ""})
            session.send_input_message("ph_side_bridge_l", {"value": ""})
            session.send_input_message("ph_run_2400", {"value": ""})

            self.selected_military = None
            selected_phef_id.set("")

            side_r_score.set("")
            side_l_score.set("")
            run_score.set("")

            await _toggle_inputs(disabled=True)
            _set_buttons(can_add=False, can_update=False)

        def _read_form() -> PhefFormData:
            return PhefFormData(
                serialnr=(input.ph_serialnr() or "").strip(),
                session_id=(input.ph_session_id() or "").strip(),
                side_bridge_r=(input.ph_side_bridge_r() or "").strip(),
                side_bridge_l=(input.ph_side_bridge_l() or "").strip(),
                run_2400=(input.ph_run_2400() or "").strip(),
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
        def ph_status() -> str:
            return status.get()

        @output
        @render.text
        def ph_military() -> str:
            return military_text.get()

        def _score_span(value: object, *, pass_if_ge: float = 10.0) -> ui.Tag:
            text = "" if value is None else str(value)
            color = "inherit"
            try:
                num = float(value)  # type: ignore[arg-type]
                color = "green" if num >= pass_if_ge else "red"
            except (TypeError, ValueError):
                pass
            return ui.span(text, style=f"color: {color}; font-weight: 600;")

        @output
        @render.ui
        def ph_side_bridge_r_score() -> ui.Tag:
            return _score_span(side_r_score.get(), pass_if_ge=10.0)

        @output
        @render.ui
        def ph_side_bridge_l_score() -> ui.Tag:
            return _score_span(side_l_score.get(), pass_if_ge=10.0)

        @output
        @render.ui
        def ph_run_2400_score() -> ui.Tag:
            return _score_span(run_score.get(), pass_if_ge=10.0)

        @output
        @render.ui
        def ph_total_score() -> ui.Tag:
            try:
                side_total = float(side_r_score.get()) + float(side_l_score.get())
                run_val = float(run_score.get())
                passed = not (side_total < 20 or run_val < 10)
                label = f"{side_total:.0f} " + ("PASSED" if passed else "FAILED")
                return ui.span(
                    label,
                    style=("color: green; font-weight: 700;" if passed else "color: red; font-weight: 700;"),
                )
            except (TypeError, ValueError):
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
            current = (input.ph_session_id() or "").strip()
            ui.update_select("ph_session_id", choices=items, selected=(current if current in items else None))

        @reactive.Effect
        async def _init() -> None:
            # Triggered on init and whenever refresh_tick changes
            self.refresh_tick.get()
            await _refresh_session_choices()
            await _clear_form()
            status.set("Ready.")

        @reactive.Effect
        async def _on_session_change() -> None:
            val = (input.ph_session_id() or "").strip()
            selected_session_id.set(val)

            # Changing sessions should reset form state (avoid mixing records/scores).
            await _clear_form()

            if not val:
                self.selected_session = None
                status.set("Select a session.")
                return

            status.set("Session selected. Confirm a serial to enter results.")

        @reactive.Effect
        @reactive.event(input.ph_session_id)
        async def _load_session_object() -> None:
            val = (input.ph_session_id() or "").strip()
            if not val:
                self.selected_session = None
                return
            try:
                self.selected_session = await self.controller.get_session_by_id(int(val))
            except Exception:
                self.selected_session = None

        # ----------------------------
        # Search military / unlock form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.ph_search, ignore_none=False)
        async def _on_search() -> None:
            if not _require_session_selected():
                return

            serial = (input.ph_serialnr() or "").strip()
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
        # Live scoring (only if military selected)
        # ----------------------------
        def _compute_side_bridge_score(raw: str) -> str:
            if self.selected_military is None:
                return ""
            ok, seconds = self.controller.parse_time_to_seconds(raw)
            if not ok:
                return ""
            try:
                return str(
                    PhefCalculator.side_bridge_result(
                        seconds,
                        self.selected_military.age_from_birthdate(),
                        self.selected_military.gender,
                    )
                )
            except Exception:
                return ""

        def _compute_run_score(raw: str) -> str:
            if self.selected_military is None:
                return ""
            ok, seconds = self.controller.parse_time_to_seconds(raw)
            if not ok:
                return ""
            try:
                return str(
                    PhefCalculator.running_result(
                        seconds,
                        self.selected_military.age_from_birthdate(),
                        self.selected_military.gender,
                    )
                )
            except Exception:
                return ""

        @reactive.Effect
        @reactive.event(input.ph_side_bridge_r)
        def _on_side_bridge_r_change() -> None:
            raw = (input.ph_side_bridge_r() or "").strip()
            side_r_score.set(_compute_side_bridge_score(raw) if raw else "")

        @reactive.Effect
        @reactive.event(input.ph_side_bridge_l)
        def _on_side_bridge_l_change() -> None:
            raw = (input.ph_side_bridge_l() or "").strip()
            side_l_score.set(_compute_side_bridge_score(raw) if raw else "")

        @reactive.Effect
        @reactive.event(input.ph_run_2400)
        def _on_run_change() -> None:
            raw = (input.ph_run_2400() or "").strip()
            run_score.set(_compute_run_score(raw) if raw else "")

        # ----------------------------
        # Grid data
        # ----------------------------
        @reactive.calc
        async def sessions_phef__data() -> pd.DataFrame:
            _ = self.refresh_tick.get()
            sess_id = (selected_session_id.get() or "").strip()
            if not sess_id:
                return pd.DataFrame()

            sess_date = self.selected_session.datetime_start if self.selected_session else None
            try:
                df = await self.controller.list_phef_df(int(sess_id), session_date=sess_date)
            except Exception:
                return pd.DataFrame()

            try:
                df= self.controller.decorate_grid(df)
                return df.sort_values(by=["Serial"])
            except Exception:
                return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        @reactive.calc
        async def sessions_phef__data_view() -> pd.DataFrame:
            df = await sessions_phef__data()

            # Hide ID in the grid, but keep it in sessions_phef__data() for selection/update/delete logic
            return df.drop(columns=["ID"], errors="ignore")

        @output
        @render.data_frame
        async def ph_grid():
            df_view = await sessions_phef__data_view()
            return render.DataGrid(df_view, filters=False, selection_mode="rows", width="100%")

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.ph_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.ph_grid_selected_rows()
            if not sel:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            df = await sessions_phef__data()
            if df is None or df.empty:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row = df.iloc[row_idx]
            phef_id = str(row.get("ID", "") or "").strip()
            selected_phef_id.set(phef_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("ph_serialnr", value=serial)
            ui.update_text("ph_side_bridge_l", value=str(row.get("Sidebridge L", "") or ""))
            ui.update_text("ph_side_bridge_r", value=str(row.get("Sidebridge R", row.get("Sidebridge R ", "")) or ""))
            ui.update_text("ph_run_2400", value=str(row.get("runningTime", "") or ""))

            # Selecting an existing record means we should allow Update, but not Add.
            _set_buttons(can_add=False, can_update=True)

            # Try to resolve military (so scores can compute as user edits)
            try:
                self.selected_military = await self.controller.search_military(serial) if serial else None
            except Exception:
                self.selected_military = None

            await _toggle_inputs(disabled=(self.selected_military is None))
            status.set(f"Selected PHEF record for: {serial}" if serial else "Selected PHEF record.")

        # ----------------------------
        # CRUD
        # ----------------------------
        def _validate(form: PhefFormData) -> tuple[bool, Any]:
            # controller expects a dict
            try:
                return self.controller.validate_form(
                    {
                        "serialnr": form.serialnr,
                        "session_id": form.session_id,
                        "side_bridge_r": form.side_bridge_r,
                        "side_bridge_l": form.side_bridge_l,
                        "run_2400": form.run_2400,
                    }
                )
            except Exception as e:
                return False, f"Validation failed: {e}"

        @reactive.Effect
        @reactive.event(input.ph_add_btn)
        async def _on_add() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            form = _read_form()
            ok, res = _validate(form)
            if not ok:
                status.set(str(res))
                return

            payload = {
                "id": form.session_id,
                "serialnr": form.serialnr,
                "side_bridge_r_s": res["side_bridge_r_s"],
                "side_bridge_l_s": res["side_bridge_l_s"],
                "run2400_s": res["run2400_s"],
            }

            added = await self.controller.add_phef(
                int(form.session_id),
                payload,
                self.selected_military,
                self.selected_session,
            )
            if not added:
                status.set(f"Failed to add PHEF test for {form.serialnr} in session {form.session_id}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Added PHEF test for {form.serialnr} in session {form.session_id}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_update_btn)
        async def _on_update() -> None:
            if not _require_session_selected() or not _require_military_selected():
                return

            phef_id_raw = (selected_phef_id.get() or "").strip()
            if not phef_id_raw:
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
                "side_bridge_r_s": res["side_bridge_r_s"],
                "side_bridge_l_s": res["side_bridge_l_s"],
                "run2400_s": res["run2400_s"],
            }

            updated = await self.controller.update_phef(int(phef_id_raw), payload)
            if not updated:
                status.set(f"Failed to update PHEF test for {form.serialnr} in session {form.session_id}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated PHEF test for {form.serialnr} in session {form.session_id}.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_delete_btn)
        async def _on_delete() -> None:
            sess_id_raw = (input.ph_session_id() or "").strip()
            phef_id_raw = (selected_phef_id.get() or "").strip()

            if not sess_id_raw or not phef_id_raw:
                status.set("Select a row to delete.")
                return

            ok = await self.controller.delete_phef(int(sess_id_raw), int(phef_id_raw))
            if not ok:
                status.set("Failed to delete selected PHEF record.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set("PHEF record deleted successfully.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set("Form cleared.")


_page = PhefPage()


def get_ui() -> NavPanel:
    return _page.get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _page.server(input, output, session)