from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Optional

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.core.container import Container
from warriorfit.logic.Functional_calculator import FunctionalCalculator
from warriorfit.ui.controllers.functional_controller import FunctionalController
from warriorfit.ui.pages.base_test_page import BaseTestPage


@dataclass(frozen=True, slots=True)
class FunctionalFormData:
    serialnr: str
    session_id: str
    push_ups: int
    sit_ups: int
    pull_ups: int


class FunctionalPage(BaseTestPage):
    TAB_NAME: Final[str] = "Functional Tests"
    NO_SELECTION_MESSAGE: Final[str] = "No row selected"

    # Disable these inputs until serial is confirmed
    _DISABLE_IDS: Final[tuple[str, ...]] = (
        "functional_push_ups",
        "functional_push_ups_input",
        "functional_sit_ups",
        "functional_sit_ups_input",
        "functional_pull_ups",
        "functional_pull_ups_input",
    )

    @inject
    def __init__(
        self,
        controller: FunctionalController = Provide[Container.functional_controller],
    ) -> None:
        super().__init__()
        self.controller = controller

    def get_prefix(self) -> str:
        return "functional"

    def get_tab_name(self) -> str:
        return self.TAB_NAME

    def get_ui(self) -> NavPanel:
        return ui.nav_panel(
            self.TAB_NAME,
            # Register ONE JS handler (avoid repeated ui.insert_ui script injection smells)
            ui.tags.script(self.toggle_disabled_registered_func),
            ui.h2("🧪 Functional Tests"),
            ui.input_action_button(
                "functional_refresh_btn",
                "🔄 Refresh",
                class_="btn btn-secondary btn-sm my-2",
            ),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Session"),
                        ui.input_select("functional_session_id", "Session", choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.div(
                            ui.input_text(
                                "functional_serialnr",
                                "Serial Number",
                                placeholder="Service Number",
                            ),
                            ui.input_action_button(
                                "functional_serial_search_btn",
                                "🔍 Search own Unit",
                                class_="btn-info btn-sm",
                                style="margin-top: 5px;",
                            ),
                        ),
                        ui.input_action_button(
                            "functional_search",
                            "✅ Confirm Serial",
                            class_="btn btn-primary btn-sm",
                            width="200px",
                        ),
                        ui.output_text("functional_military"),
                        ui.layout_columns(
                            ui.input_numeric("functional_push_ups", "Push-ups", value=0, min=0),
                            ui.div("Score :", ui.output_ui("functional_push_ups_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_numeric("functional_sit_ups", "Sit-ups", value=0, min=0),
                            ui.div("Score :", ui.output_ui("functional_sit_ups_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_numeric("functional_pull_ups", "Pull-ups", value=0, min=0),
                            ui.div("Score :", ui.output_ui("functional_pull_ups_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.div("Result:", ui.output_ui("functional_total_score")),
                            col_widths=(12,),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "functional_add_btn",
                                "Add",
                                disabled=True,
                                width="150px",
                                class_="btn-primary w-100",
                            ),
                            ui.input_action_button(
                                "functional_update_btn",
                                "Update",
                                disabled=True,
                                width="150px",
                                class_="btn-warning w-100",
                            ),
                            ui.input_action_button(
                                "functional_clear_btn",
                                "Clear Form",
                                width="150px",
                                class_="btn-secondary w-100",
                            ),
                            ui.input_action_button(
                                "functional_delete_btn",
                                "Delete Selected",
                                class_="btn-danger w-100",
                            ),
                            col_widths=(4,),
                        ),
                        ui.output_text("functional_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header(
                        "Functional Tests: This list shows not only members of own Unit"
                    ),
                    ui.output_data_frame("functional_grid"),
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
        selected_functional_id = reactive.Value("")

        # Store *raw reps* for scoring (int values stored as strings in old code)
        push_val = reactive.Value("0")
        sit_val = reactive.Value("0")
        pull_val = reactive.Value("0")

        # ----------------------------
        # Helpers
        # ----------------------------

        async def _clear_form() -> None:
            await self._clear_form_hook(input, session)
            selected_functional_id.set("")

            push_val.set("0")
            sit_val.set("0")
            pull_val.set("0")

            await self.toggle_inputs(session, self._DISABLE_IDS, disabled=True)
            self.set_buttons(self.get_prefix(), can_add=False, can_update=False)

        def _read_form() -> FunctionalFormData:
            def _to_int(v: Any) -> int:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return 0

            return FunctionalFormData(
                serialnr=(input.functional_serialnr() or "").strip(),
                session_id=(input.functional_session_id() or "").strip(),
                push_ups=_to_int(input.functional_push_ups()),
                sit_ups=_to_int(input.functional_sit_ups()),
                pull_ups=_to_int(input.functional_pull_ups()),
            )

        async def _refresh_session_choices() -> None:
            await self.refresh_session_choices(input, self.controller)

        # ----------------------------
        # Outputs
        # ----------------------------
        @output
        @render.text
        def functional_status() -> str:
            return status.get()

        @output
        @render.text
        def functional_military() -> str:
            return military_text.get()

        def _score_span(value: object, *, pass_if_ge: float = 20.0) -> ui.Tag:
            text = "" if value is None else str(value)
            color = "inherit"
            try:
                num = float(value)  # type: ignore[arg-type]
                color = "green" if num >= pass_if_ge else "red"
            except (TypeError, ValueError):
                pass
            return ui.span(text, style=f"color: {color}; font-weight: 600;")

        def _calc_score_pushups(reps: int) -> Optional[int]:
            if self.selected_military is None:
                return None
            return int(
                FunctionalCalculator.get_score_pushup(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    reps,
                )
            )

        def _calc_score_situps(reps: int) -> Optional[int]:
            if self.selected_military is None:
                return None
            return int(
                FunctionalCalculator.get_score_situp(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    reps,
                )
            )

        def _calc_score_pullups(reps: int) -> Optional[int]:
            if self.selected_military is None:
                return None
            return int(
                FunctionalCalculator.get_score_pullup(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    reps,
                )
            )

        @output
        @render.ui
        def functional_push_ups_score() -> ui.Tag:
            try:
                reps = int(push_val.get() or 0)
            except Exception:
                reps = 0
            score = _calc_score_pushups(reps)
            return _score_span(score, pass_if_ge=20.0)

        @output
        @render.ui
        def functional_sit_ups_score() -> ui.Tag:
            try:
                reps = int(sit_val.get() or 0)
            except Exception:
                reps = 0
            score = _calc_score_situps(reps)
            return _score_span(score, pass_if_ge=20.0)

        @output
        @render.ui
        def functional_pull_ups_score() -> ui.Tag:
            try:
                reps = int(pull_val.get() or 0)
            except Exception:
                reps = 0
            score = _calc_score_pullups(reps)
            return _score_span(score, pass_if_ge=20.0)

        def _passes_total(push_reps: int, sit_reps: int, pull_reps: int) -> bool:
            if self.selected_military is None:
                return False
            try:
                p = _calc_score_pushups(push_reps) or 0
                s = _calc_score_situps(sit_reps) or 0
                pu = _calc_score_pullups(pull_reps) or 0
                return (p > 10) and (s > 10) and (pu > 10)
            except Exception:
                return False

        @output
        @render.ui
        def functional_total_score() -> ui.Tag:
            if self.selected_military is None:
                return ui.span("")
            try:
                passed = _passes_total(int(push_val.get()), int(sit_val.get()), int(pull_val.get()))
                return ui.span(
                    "PASSED" if passed else "FAILED",
                    style=(
                        "color: green; font-weight: 700;"
                        if passed
                        else "color: red; font-weight: 700;"
                    ),
                )
            except Exception:
                return ui.span("")

        # ----------------------------
        # Live rep tracking (kept simple)
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.functional_push_ups)
        def _on_push_change() -> None:
            try:
                push_val.set(str(int(input.functional_push_ups() or 0)))
            except Exception:
                push_val.set("0")

        @reactive.Effect
        @reactive.event(input.functional_sit_ups)
        def _on_sit_change() -> None:
            try:
                sit_val.set(str(int(input.functional_sit_ups() or 0)))
            except Exception:
                sit_val.set("0")

        @reactive.Effect
        @reactive.event(input.functional_pull_ups)
        def _on_pull_change() -> None:
            try:
                pull_val.set(str(int(input.functional_pull_ups() or 0)))
            except Exception:
                pull_val.set("0")

        # ----------------------------
        # Init & session selection
        # ----------------------------
        @reactive.Effect
        async def _init() -> None:
            _ = self.refresh_tick.get()
            await _refresh_session_choices()
            await _clear_form()
            status.set("Ready.")

        # Setup session management using base class
        self.setup_session_management(input, session, selected_session_id, status, self.controller)

        # ----------------------------
        # Search military / unlock inputs
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.functional_search, ignore_none=False)
        async def _on_search() -> None:
            if not self.require_session_selected(selected_session_id, status):
                return

            serial = (input.functional_serialnr() or "").strip()
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
                await self.toggle_inputs(session, self._DISABLE_IDS, disabled=True)
                self.set_buttons(self.get_prefix(), can_add=False, can_update=False)
                return

            military_text.set(f"{val.rank} {val.service_number} {val.first_name} {val.last_name}")
            status.set("Serial confirmed. Enter results.")
            await self.toggle_inputs(session, self._DISABLE_IDS, disabled=False)
            self.set_buttons(self.get_prefix(), can_add=True, can_update=True)

        # ----------------------------
        # Data grid
        # ----------------------------
        @reactive.calc
        async def sessions_functional_data() -> pd.DataFrame:
            _ = self.refresh_tick.get()
            sess_id = (selected_session_id.get() or "").strip()
            if not sess_id:
                return pd.DataFrame()
            try:
                return await self.controller.list_functional_tests_df(int(sess_id))
            except Exception:
                return pd.DataFrame()

        @output
        @render.data_frame
        async def functional_grid():
            df = await sessions_functional_data()

            # Early return for empty data
            if df.empty:
                return render.DataGrid(
                    df,
                    filters=False,
                    selection_mode="rows",
                    width="100%",
                )

            try:
                df = self.controller.decorate_grid(df)
                df = df.sort_values(by=["Serial"])
                df_view = df.drop(columns=["ID"], errors="ignore")
            except (KeyError, TypeError, ValueError, AttributeError):
                # Log the error for debugging (consider using proper logging)
                # For now, fall back to showing undecorated data
                df_view = df.drop(columns=["ID"], errors="ignore")

            return render.DataGrid(
                df_view,
                filters=False,
                selection_mode="rows",
                width="100%",
            )

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.functional_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.functional_grid_selected_rows()
            if not sel:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            df = await sessions_functional_data()
            if df is None or df.empty:
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(self.NO_SELECTION_MESSAGE)
                return

            row = df.iloc[row_idx]
            functional_id = str(row.get("ID", "") or "").strip()
            selected_functional_id.set(functional_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("functional_serialnr", value=serial)

            def _safe_int(v: Any) -> int:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return 0

            ui.update_numeric(
                "functional_push_ups",
                value=_safe_int(row.get("Push-ups", row.get("push_ups", 0))),
            )
            ui.update_numeric(
                "functional_sit_ups",
                value=_safe_int(row.get("Sit-ups", row.get("sit_ups", 0))),
            )
            ui.update_numeric(
                "functional_pull_ups",
                value=_safe_int(row.get("Pull-ups", row.get("pull_ups", 0))),
            )

            # Selection: allow Update, disable Add (avoids duplicate add)
            self.set_buttons(self.get_prefix(), can_add=False, can_update=True)

            try:
                self.selected_military = (
                    await self.controller.search_military(serial) if serial else None
                )
            except Exception:
                self.selected_military = None

            await self.toggle_inputs(
                session, self._DISABLE_IDS, disabled=(self.selected_military is None)
            )
            status.set(
                f"Selected Functional Test: {serial}" if serial else "Selected Functional Test."
            )

        # ----------------------------
        # CRUD
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.functional_add_btn)
        async def _on_add() -> None:
            if not self.require_session_selected(
                selected_session_id, status
            ) or not self.require_military_selected(status):
                return

            form = _read_form()
            ok, res = self.controller.validate_form(
                {
                    "serialnr": form.serialnr,
                    "session_id": form.session_id,
                    "push_ups": form.push_ups,
                    "sit_ups": form.sit_ups,
                    "pull_ups": form.pull_ups,
                }
            )
            if not ok:
                status.set(str(res))
                return

            record = {
                "id": form.session_id,
                "serialnr": form.serialnr,
                "push_ups": res["push_ups"],
                "sit_ups": res["sit_ups"],
                "pull_ups": res["pull_ups"],
            }

            added = await self.controller.add_functional(
                int(record["id"]),
                record,
                session=self.selected_session,
                military=self.selected_military,
            )
            if not added:
                status.set(
                    f"Failed to add Functional test for {record['serialnr']} in session {record['id']}."
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Added Functional test for {record['serialnr']} in session {record['id']}.")
            ui.notification_show(
                f"Functional test added for {record['serialnr']}.",
                type="message",
                duration=3,
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_update_btn)
        async def _on_update() -> None:
            if not self.require_session_selected(
                selected_session_id, status
            ) or not self.require_military_selected(status):
                return

            functional_id_raw = (selected_functional_id.get() or "").strip()
            if not functional_id_raw:
                status.set("Select a row to update.")
                return

            form = _read_form()
            ok, res = self.controller.validate_form(
                {
                    "serialnr": form.serialnr,
                    "session_id": form.session_id,
                    "push_ups": form.push_ups,
                    "sit_ups": form.sit_ups,
                    "pull_ups": form.pull_ups,
                }
            )
            if not ok:
                status.set(str(res))
                return

            payload = {
                "session_id": form.session_id,
                "serialnr": form.serialnr,
                "push_ups": res["push_ups"],
                "sit_ups": res["sit_ups"],
                "pull_ups": res["pull_ups"],
            }

            updated = await self.controller.update_functional(int(functional_id_raw), payload)
            if not updated:
                status.set(f"Failed to update Functional test for {payload['serialnr']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated Functional test for {payload['serialnr']}.")
            ui.notification_show(
                f"Functional test updated for {payload['serialnr']}.",
                type="message",
                duration=3,
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_delete_btn)
        async def _on_delete() -> None:
            sess_id_raw = (input.functional_session_id() or "").strip()
            functional_id_raw = (selected_functional_id.get() or "").strip()
            if not sess_id_raw or not functional_id_raw:
                status.set("Select a row to delete.")
                return

            ok = await self.controller.delete_functional(int(sess_id_raw), int(functional_id_raw))
            if not ok:
                status.set("Failed to delete selected Functional record.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set("Functional test deleted successfully.")
            ui.notification_show("Functional test deleted.", type="warning", duration=3)
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_refresh_btn)
        def _on_functional_refresh() -> None:
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.functional_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set("Form cleared.")

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.functional_serial_search_btn)
        async def _open_serial_search_modal() -> None:
            modal_content = ui.modal(
                ui.card(
                    ui.card_header("Select Serial Number"),
                    ui.output_data_frame("functional_serial_search_grid"),
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

        @render.data_frame
        async def functional_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="rows", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.functional_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.functional_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("functional_serialnr", value=str(row["service_number"]))
                    ui.modal_remove()

    async def _clear_form_hook(self, input: Any, session: Any) -> None:
        """Hook for page-specific form clearing logic."""
        session.send_input_message("functional_serialnr", {"value": ""})
        session.send_input_message("functional_push_ups", {"value": 0})
        session.send_input_message("functional_sit_ups", {"value": 0})
        session.send_input_message("functional_pull_ups", {"value": 0})
        self.selected_military = None


# Public API: keep same signatures
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = FunctionalPage()
    return _page


def get_ui() -> NavPanel:
    return _get_page().get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _get_page().server(input, output, session)
