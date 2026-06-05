from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.ui.controllers.phef_controller import PhefController
from warriorfit.ui.pages.base_test_page import BaseTestPage


@dataclass(frozen=True, slots=True)
class PhefFormData:
    serialnr: str
    session_id: str
    side_bridge_r: str
    side_bridge_l: str
    run_2400: str


class PhefPage(BaseTestPage):
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

    @inject
    def __init__(
        self, controller: PhefController = Provide[Container.phef_controller]
    ) -> None:
        super().__init__()
        self.controller = controller

    def get_prefix(self) -> str:
        return "ph"

    def get_tab_name(self) -> str:
        return self.TAB_NAME

    def get_ui(self) -> NavPanel:  # type: ignore[override]
        return ui.nav_panel(
            t("nav.phef_tests"),
            # Register ONE custom-message handler to toggle disabling inputs.
            ui.tags.script(self.toggle_disabled_registered_func),
            ui.h2(t("phef.title")),
            ui.input_action_button(
                "ph_refresh_btn", t("common.refresh"), class_="btn btn-secondary btn-sm my-2"
            ),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header(t("common.session")),
                        ui.input_select("ph_session_id", t("common.session"), choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.div(
                            ui.input_text(
                                "ph_serialnr",
                                t("common.serial_number"),
                                placeholder=t("common.service_number"),
                            ),
                            ui.input_action_button(
                                "ph_serial_search_btn",
                                t("common.search_own_unit"),
                                class_="btn-info btn-sm",
                                style="margin-top: 5px;",
                            ),
                        ),
                        ui.input_action_button(
                            "ph_search",
                            t("common.confirm_serial"),
                            class_="btn btn-primary btn-sm",
                            width="200px",
                        ),
                        ui.output_text("ph_military"),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_side_bridge_r",
                                t("phef.side_bridge_r"),
                                placeholder="e.g., 2:30",
                            ),
                            ui.div(t("phef.score"), ui.output_ui("ph_side_bridge_r_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_side_bridge_l",
                                t("phef.side_bridge_l"),
                                placeholder="e.g., 2:30",
                            ),
                            ui.div(t("phef.score"), ui.output_ui("ph_side_bridge_l_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.input_text(
                                "ph_run_2400",
                                t("phef.run_2400"),
                                placeholder="e.g., 10:45",
                            ),
                            ui.div(t("phef.score"), ui.output_ui("ph_run_2400_score")),
                            col_widths=(8, 4),
                        ),
                        ui.layout_columns(
                            ui.div(t("phef.total"), ui.output_ui("ph_total_score")),
                            col_widths=(12,),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "ph_add_btn",
                                t("common.add"),
                                disabled=True,
                                width="150px",
                                class_="btn-primary w-100",
                            ),
                            ui.input_action_button(
                                "ph_update_btn",
                                t("common.update"),
                                disabled=True,
                                width="150px",
                                class_="btn-warning w-100",
                            ),
                            ui.input_action_button(
                                "ph_clear_btn",
                                t("common.clear_form"),
                                width="150px",
                                class_="btn-secondary w-100",
                            ),
                            ui.input_action_button(
                                "ph_delete_btn",
                                t("common.delete_selected"),
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
                    ui.card_header(t("phef.table_header")),
                    ui.output_data_frame("ph_grid"),
                    ui.br(),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
            value=self.TAB_NAME,
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        self.refresh_on_nav(input, self.TAB_NAME)

        status = reactive.Value(t("common.ready"))
        military_text = reactive.Value(t("common.no_selection"))
        selected_session_id = reactive.Value("")
        selected_phef_id = reactive.Value("")

        side_r_score = reactive.Value("")  # expected numeric-as-string from calculator
        side_l_score = reactive.Value("")
        run_score = reactive.Value("")

        # ----------------------------
        # UI state helpers
        # ----------------------------

        async def _clear_form() -> None:
            await self._clear_form_hook(input, session)
            selected_phef_id.set("")

            side_r_score.set("")
            side_l_score.set("")
            run_score.set("")

            await self.toggle_inputs(session, self._DISABLE_IDS, disabled=True)
            self.set_buttons(self.get_prefix(), can_add=False, can_update=False)

        def _read_form() -> PhefFormData:
            return PhefFormData(
                serialnr=(input.ph_serialnr() or "").strip(),
                session_id=(input.ph_session_id() or "").strip(),
                side_bridge_r=(input.ph_side_bridge_r() or "").strip(),
                side_bridge_l=(input.ph_side_bridge_l() or "").strip(),
                run_2400=(input.ph_run_2400() or "").strip(),
            )

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
                    style=(
                        "color: green; font-weight: 700;"
                        if passed
                        else "color: red; font-weight: 700;"
                    ),
                )
            except (TypeError, ValueError):
                return ui.span("")

        # ----------------------------
        # Session choices + selection
        # ----------------------------
        async def _refresh_session_choices() -> None:
            await self.refresh_session_choices(input, self.controller)

        @reactive.Effect
        async def _init() -> None:
            _ = self.refresh_tick.get()
            await _refresh_session_choices()
            await _clear_form()
            status.set(t("common.ready"))

        # Setup session management using base class
        self.setup_session_management(
            input, session, selected_session_id, status, self.controller
        )

        # ----------------------------
        # Search military / unlock form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.ph_search, ignore_none=False)
        async def _on_search() -> None:
            if not self.require_session_selected(selected_session_id, status):
                return

            serial = (input.ph_serialnr() or "").strip()
            if not serial:
                status.set(t("common.enter_serial"))
                await _clear_form()
                return

            try:
                val = await self.controller.search_military(serial)
            except Exception:
                val = None

            self.selected_military = val
            if val is None:
                military_text.set(t("common.not_found"))
                status.set(t("common.serial_not_found"))
                await self.toggle_inputs(session, self._DISABLE_IDS, disabled=True)
                self.set_buttons(self.get_prefix(), can_add=False, can_update=False)
                return

            military_text.set(
                f"{val.rank} {val.service_number} {val.first_name} {val.last_name} "
                f"{val.gender} {val.age_from_birthdate()} years old"
            )
            status.set(t("common.serial_confirmed"))
            await self.toggle_inputs(session, self._DISABLE_IDS, disabled=False)
            self.set_buttons(self.get_prefix(), can_add=True, can_update=True)

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

            sess_date = (
                self.selected_session.datetime_start if self.selected_session else None
            )
            try:
                df = await self.controller.list_phef_df(
                    int(sess_id), session_date=sess_date
                )
            except Exception:
                return pd.DataFrame()

            try:
                df = self.controller.decorate_grid(df)
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
            return render.DataGrid(
                df_view, filters=False, selection_mode="rows", width="100%"
            )

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.ph_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.ph_grid_selected_rows()
            if not sel:
                status.set(t("common.no_row_selected"))
                return

            df = await sessions_phef__data()
            if df is None or df.empty:
                status.set(t("common.no_row_selected"))
                return

            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(t("common.no_row_selected"))
                return

            row = df.iloc[row_idx]
            phef_id = str(row.get("ID", "") or "").strip()
            selected_phef_id.set(phef_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("ph_serialnr", value=serial)
            ui.update_text(
                "ph_side_bridge_l", value=str(row.get("Sidebridge L", "") or "")
            )
            ui.update_text(
                "ph_side_bridge_r",
                value=str(row.get("Sidebridge R", row.get("Sidebridge R ", "")) or ""),
            )
            ui.update_text("ph_run_2400", value=str(row.get("runningTime", "") or ""))

            # Selecting an existing record means we should allow Update, but not Add.
            self.set_buttons(self.get_prefix(), can_add=False, can_update=True)

            # Try to resolve military (so scores can compute as user edits)
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
                f"Selected PHEF record for: {serial}"
                if serial
                else "Selected PHEF record."
            )

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
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                return False, f"Validation failed: {e}"

        @reactive.Effect
        @reactive.event(input.ph_add_btn)
        async def _on_add() -> None:
            if not self.require_session_selected(
                selected_session_id, status
            ) or not self.require_military_selected(status):
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
                status.set(
                    t("phef.failed_add").format(serial=form.serialnr, session=form.session_id)
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                t("phef.added_status").format(serial=form.serialnr, session=form.session_id)
            )
            ui.notification_show(
                t("phef.added").format(serial=form.serialnr), type="message", duration=3
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_update_btn)
        async def _on_update() -> None:
            if not self.require_session_selected(
                selected_session_id, status
            ) or not self.require_military_selected(status):
                return

            phef_id_raw = (selected_phef_id.get() or "").strip()
            if not phef_id_raw:
                status.set(t("common.select_row_to_update"))
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
                status.set(
                    t("phef.failed_update").format(serial=form.serialnr, session=form.session_id)
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                t("phef.updated_status").format(serial=form.serialnr, session=form.session_id)
            )
            ui.notification_show(
                t("phef.updated").format(serial=form.serialnr), type="message", duration=3
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_delete_btn)
        async def _on_delete() -> None:
            sess_id_raw = (input.ph_session_id() or "").strip()
            phef_id_raw = (selected_phef_id.get() or "").strip()

            if not sess_id_raw or not phef_id_raw:
                status.set(t("common.select_row_to_delete"))
                return

            ok = await self.controller.delete_phef(int(sess_id_raw), int(phef_id_raw))
            if not ok:
                status.set(t("phef.failed_delete"))
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("phef.deleted_success"))
            ui.notification_show(t("phef.deleted"), type="warning", duration=3)
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_refresh_btn)
        def _on_ph_refresh() -> None:
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.ph_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set(t("common.form_cleared"))

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.ph_serial_search_btn)
        async def _open_serial_search_modal() -> None:
            modal_content = ui.modal(
                ui.card(
                    ui.card_header(t("common.select_serial_number")),
                    ui.output_data_frame("ph_serial_search_grid"),
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
                return pd.DataFrame(
                    columns=["service_number", "first_name", "last_name", "gender"]
                )

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
        async def ph_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(
                df, selection_mode="rows", filters=True, width="100%"
            )

        @reactive.Effect
        @reactive.event(input.ph_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.ph_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("ph_serialnr", value=str(row["service_number"]))
                    ui.modal_remove()

    async def _clear_form_hook(self, input: Any, session: Any) -> None:
        """Hook for page-specific form clearing logic."""
        session.send_input_message("ph_serialnr", {"value": ""})
        session.send_input_message("ph_side_bridge_r", {"value": ""})
        session.send_input_message("ph_side_bridge_l", {"value": ""})
        session.send_input_message("ph_run_2400", {"value": ""})
        self.selected_military = None


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = PhefPage()
    return _page


def get_ui() -> NavPanel:
    return _get_page().get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _get_page().server(input, output, session)
