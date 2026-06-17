from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import pandas as pd
from dependency_injector.wiring import Provide, inject
from pandas import DataFrame
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.mfft_eval_controller import MfftEvalController
from warriorfit.ui.pages.base_test_page import BaseTestPage


@dataclass(frozen=True, slots=True)
class MfftFormData:
    serialnr: str
    session_id: str
    pull_ups: str
    burpees: str
    farmer_m: str
    push_ups: str
    drag_m: str
    sandbag_m: str
    combat_run: str
    combat_swim: str


class MfftEvalPage(BaseTestPage):
    TAB_NAME: Final[str] = "MFFT Eval"
    NO_SELECTION_MESSAGE: Final[str] = "common.no_row_selected"

    _DISABLE_IDS: Final[tuple[str, ...]] = (
        "mfft_pull_ups",
        "mfft_burpees",
        "mfft_farmer_m",
        "mfft_push_ups",
        "mfft_drag_m",
        "mfft_sandbag_m",
        "mfft_combat_run",
        "mfft_combat_swim",
    )

    @inject
    def __init__(
        self,
        controller: MfftEvalController = Provide[Container.mfft_eval_controller],
    ) -> None:
        super().__init__()
        self.controller = controller

    def get_prefix(self) -> str:
        return "mfft"

    def get_tab_name(self) -> str:
        return self.TAB_NAME

    @staticmethod
    def _event_row(
        left: tuple[str, str, str],
        right: tuple[str, str, str],
    ) -> Any:
        """Two events on one row, each with the status badge **next to** the input.

        Each event renders as a flexbox: label sits above the input (Shiny
        default), and the status badge is positioned to the right of the
        input, vertically aligned with the input's bottom edge. The two
        events share the row 6 / 6.

        ``left`` and ``right`` are ``(input_id, label, kind)`` where ``kind``
        is ``"n"`` for numeric or ``"t"`` for text (mm:ss).
        """

        def cell(input_id: str, label: str, kind: str) -> ui.Tag:
            field = (
                ui.input_numeric(input_id, label, value=1, min=1)
                if kind == "n"
                else ui.input_text(input_id, label, placeholder="mm:ss")
            )
            return ui.div(
                ui.div(field, class_="event-field"),
                ui.div(
                    ui.output_ui(f"{input_id}_status"),
                    class_="event-status",
                ),
                class_="event-row",
            )

        return ui.layout_columns(
            cell(*left),
            cell(*right),
            col_widths=(6, 6),
            class_="g-2 mb-1",
        )

    def get_ui(self) -> NavPanel:  # type: ignore[override]
        return ui.nav_panel(
            t("nav.mfft_eval_tests"),
            ui.tags.script(self.toggle_disabled_registered_func),
            ui.h2(t("mfft_eval.title")),
            ui.input_action_button(
                "mfft_refresh_btn",
                t("common.refresh"),
                class_="btn btn-secondary btn-sm my-2",
            ),
            ui.tags.style(
                """
                .mfft-form .card-body { padding: .6rem !important; }
                .mfft-form .form-label {
                    font-size: .72rem;
                    margin-bottom: 1px;
                    line-height: 1.1;
                    font-weight: 600;
                    color: #333;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .mfft-form .form-control {
                    padding: .2rem .4rem;
                    height: 32px;
                    line-height: 1.4;
                    font-size: .82rem;
                }
                .mfft-form .form-select {
                    padding: .3rem 1.75rem .3rem .5rem;
                    height: 36px;
                    line-height: 1.5;
                    font-size: .85rem;
                }
                .mfft-form .btn { padding: .2rem .4rem; font-size: .75rem; }
                .mfft-form h6 {
                    font-size: .78rem;
                    margin: .5rem 0 .2rem;
                    color: #555;
                    font-weight: 700;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 2px;
                }
                .mfft-form .event-row {
                    display: flex;
                    align-items: flex-end;
                    gap: .3rem;
                }
                .mfft-form .event-field { flex: 1; min-width: 0; }
                .mfft-form .event-field .shiny-input-container { width: 100%; margin-bottom: 0; }
                .mfft-form .event-status {
                    font-size: .7rem;
                    line-height: 1.15;
                    padding-bottom: 6px;
                    min-width: 60px;
                    text-align: right;
                    white-space: nowrap;
                }
                .mfft-form .mfft-result {
                    font-size: .85rem;
                    border-top: 1px solid #ddd;
                    padding-top: .5rem;
                    margin-top: .5rem;
                }
                .mfft-form .form-group { margin-bottom: 0; }
                """
            ),
            ui.layout_columns(
                ui.card(
                    ui.input_select(
                        "mfft_session_id",
                        t("common.session"),
                        choices=[],
                    ),
                    ui.input_text(
                        "mfft_serialnr",
                        t("common.serial_number"),
                        placeholder=t("common.service_number"),
                    ),
                    ui.layout_columns(
                        ui.input_action_button(
                            "mfft_serial_search_btn",
                            "🔍",
                            class_="btn-info w-100",
                        ),
                        ui.input_action_button(
                            "mfft_search",
                            "✓",
                            class_="btn-primary w-100",
                        ),
                        col_widths=(6, 6),
                        class_="g-1 mt-1",
                    ),
                    ui.output_text("mfft_military"),
                    ui.tags.h6(t("mfft_eval.block1")),
                    self._event_row(
                        ("mfft_pull_ups", t("mfft_eval.event.pull_up"), "n"),
                        ("mfft_burpees", t("mfft_eval.event.burpees"), "n"),
                    ),
                    self._event_row(
                        ("mfft_farmer_m", t("mfft_eval.event.farmer_walk"), "n"),
                        ("mfft_push_ups", t("mfft_eval.event.push_up"), "n"),
                    ),
                    self._event_row(
                        ("mfft_drag_m", t("mfft_eval.event.casualty_drag"), "n"),
                        ("mfft_sandbag_m", t("mfft_eval.event.sandbag_carry"), "n"),
                    ),
                    ui.tags.h6(f"{t('mfft_eval.block2')} · {t('mfft_eval.block3')}"),
                    self._event_row(
                        ("mfft_combat_run", "Run (mm:ss)", "t"),
                        ("mfft_combat_swim", "Swim (mm:ss)", "t"),
                    ),
                    ui.div(
                        ui.output_ui("mfft_tier_info", inline=True),
                        " · ",
                        ui.output_ui("mfft_overall", inline=True),
                        class_="mfft-result",
                    ),
                    ui.layout_columns(
                        ui.input_action_button(
                            "mfft_add_btn",
                            t("common.add"),
                            disabled=True,
                            class_="btn-primary w-100",
                        ),
                        ui.input_action_button(
                            "mfft_update_btn",
                            t("common.update"),
                            disabled=True,
                            class_="btn-warning w-100",
                        ),
                        ui.input_action_button(
                            "mfft_clear_btn",
                            "↺",
                            class_="btn-secondary w-100",
                        ),
                        ui.input_action_button(
                            "mfft_delete_btn",
                            "🗑",
                            class_="btn-danger w-100",
                        ),
                        col_widths=(3, 3, 3, 3),
                        class_="g-1 mt-2",
                    ),
                    ui.output_text("mfft_status"),
                    class_="mfft-form",
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header(t("mfft_eval.table_header")),
                    ui.output_data_frame("mfft_grid"),
                    full_screen=True,
                ),
                col_widths=(3, 9),
            ),
            value=self.TAB_NAME,
        )

    def server(self, input: Any, output: Any, session: Any) -> None:  # noqa: C901
        self.refresh_on_nav(input, self.TAB_NAME)

        status = reactive.Value(t("common.ready"))
        military_text = reactive.Value(t("common.no_selection"))
        selected_session_id = reactive.Value("")
        selected_mfft_id = reactive.Value("")

        tier_info_text = reactive.Value("")
        overall_text = reactive.Value("")

        # Per-event status. Each value is one of:
        #   ""               -> not evaluated yet (empty or invalid input)
        #   "INVALID:<msg>"  -> input failed validation (0, non-numeric, bad time)
        #   "<MfftLevel>"    -> COMBAT-equivalent tier (GOLD/SILVER/BRONZE/FIT/UNFIT)
        event_status: list[reactive.Value[str]] = [reactive.Value("") for _ in range(8)]

        def _render_event_badge(val: str) -> ui.Tag:
            if not val:
                return ui.span("—", style="color: #bbb;")
            if val.startswith("INVALID:"):
                msg = val.split(":", 1)[1]
                return ui.span(
                    f"⚠ {msg}",
                    style="color: #b00; font-weight: 600;",
                    title=msg,
                )
            if val == "VALID":
                return ui.span(
                    "✓",
                    style="color: #198754; font-weight: 700;",
                    title="Value valid — select a serial to evaluate tier",
                )
            colors = {
                "GOLD": "#d4af37",
                "SILVER": "#8a8a8a",
                "BRONZE": "#cd7f32",
                "FIT": "green",
                "UNFIT": "red",
            }
            mark = "✗" if val == "UNFIT" else "✓"
            color = colors.get(val, "black")
            return ui.span(
                f"{mark} {val}",
                style=f"color: {color}; font-weight: 700;",
            )

        @reactive.Effect
        async def _init() -> None:
            self.refresh_tick.get()
            await _refresh_session_choices()
            await _clear_form()
            status.set(t("common.ready"))

        async def _toggle_inputs(disabled: bool) -> None:
            await self.toggle_inputs(session, self._DISABLE_IDS, disabled)

        def _set_buttons(*, can_add: bool, can_update: bool) -> None:
            self.set_buttons("mfft", can_add, can_update)

        async def _clear_form() -> None:
            session.send_input_message("mfft_serialnr", {"value": ""})
            for input_id in (
                "mfft_pull_ups",
                "mfft_burpees",
                "mfft_farmer_m",
                "mfft_push_ups",
                "mfft_drag_m",
                "mfft_sandbag_m",
            ):
                session.send_input_message(input_id, {"value": 1})
            session.send_input_message("mfft_combat_run", {"value": ""})
            session.send_input_message("mfft_combat_swim", {"value": ""})
            self.selected_military = None
            selected_mfft_id.set("")
            tier_info_text.set("")
            overall_text.set("")
            for s in event_status:
                s.set("")
            await _toggle_inputs(disabled=True)
            _set_buttons(can_add=False, can_update=False)

        def _read_form() -> MfftFormData:
            return MfftFormData(
                serialnr=(input.mfft_serialnr() or "").strip(),
                session_id=(input.mfft_session_id() or "").strip(),
                pull_ups=str(input.mfft_pull_ups() or ""),
                burpees=str(input.mfft_burpees() or ""),
                farmer_m=str(input.mfft_farmer_m() or ""),
                push_ups=str(input.mfft_push_ups() or ""),
                drag_m=str(input.mfft_drag_m() or ""),
                sandbag_m=str(input.mfft_sandbag_m() or ""),
                combat_run=(input.mfft_combat_run() or "").strip(),
                combat_swim=(input.mfft_combat_swim() or "").strip(),
            )

        def _require_session_selected() -> bool:
            return self.require_session_selected(selected_session_id, status)

        def _require_military_selected() -> bool:
            return self.require_military_selected(status)

        # ----------------------------
        # Outputs
        # ----------------------------
        @output
        @render.text
        def mfft_status() -> str:
            return status.get()

        @output
        @render.text
        def mfft_military() -> str:
            return military_text.get()

        @output
        @render.ui
        def mfft_tier_info() -> ui.Tag:
            val = tier_info_text.get()
            return ui.span(val or "", style="font-weight: 600;")

        @output
        @render.ui
        def mfft_overall() -> ui.Tag:
            val = overall_text.get()
            if not val:
                return ui.span("")
            color = "green" if val.lower().startswith("pass") else "red"
            return ui.span(val, style=f"color: {color}; font-weight: 700;")

        @output
        @render.ui
        def mfft_pull_ups_status() -> ui.Tag:
            return _render_event_badge(event_status[0].get())

        @output
        @render.ui
        def mfft_burpees_status() -> ui.Tag:
            return _render_event_badge(event_status[1].get())

        @output
        @render.ui
        def mfft_farmer_m_status() -> ui.Tag:
            return _render_event_badge(event_status[2].get())

        @output
        @render.ui
        def mfft_push_ups_status() -> ui.Tag:
            return _render_event_badge(event_status[3].get())

        @output
        @render.ui
        def mfft_drag_m_status() -> ui.Tag:
            return _render_event_badge(event_status[4].get())

        @output
        @render.ui
        def mfft_sandbag_m_status() -> ui.Tag:
            return _render_event_badge(event_status[5].get())

        @output
        @render.ui
        def mfft_combat_run_status() -> ui.Tag:
            return _render_event_badge(event_status[6].get())

        @output
        @render.ui
        def mfft_combat_swim_status() -> ui.Tag:
            return _render_event_badge(event_status[7].get())

        # ----------------------------
        # Session management
        # ----------------------------
        async def _refresh_session_choices() -> None:
            await self.refresh_session_choices(input, self.controller)

        self.setup_session_management(input, session, selected_session_id, status, self.controller)

        # ----------------------------
        # Search military
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.mfft_search, ignore_none=False)
        async def _on_search() -> None:
            if not _require_session_selected():
                return
            serial = (input.mfft_serialnr() or "").strip()
            if not serial:
                status.set(t("common.enter_serial"))
                await _clear_form()
                return

            val = await self.search_set_military(self.controller, serial, military_text, status)
            if val is None:
                await _toggle_inputs(disabled=True)
                _set_buttons(can_add=False, can_update=False)
                return

            military_text.set(
                f"{val.rank} {val.service_number} {val.first_name} {val.last_name} "
                f"{val.gender} {val.age_from_birthdate()} years old "
                f"[{val.cluster}]"
            )
            status.set(t("common.serial_confirmed"))
            await _toggle_inputs(disabled=False)
            _set_buttons(can_add=True, can_update=True)

        # ----------------------------
        # Live scoring + per-event validation
        # ----------------------------
        @reactive.Effect
        async def _on_form_change() -> None:
            form = _read_form()

            int_inputs = (
                ("Pull-ups", form.pull_ups),
                ("Burpees", form.burpees),
                ("Farmer walk", form.farmer_m),
                ("Push-ups", form.push_ups),
                ("Casualty drag", form.drag_m),
                ("Sandbag carry", form.sandbag_m),
            )
            time_inputs = (
                ("Combat run", form.combat_run),
                ("Combat swim", form.combat_swim),
            )

            parsed_values: list[int | None] = []
            any_invalid = False

            for idx, (label, raw) in enumerate(int_inputs):
                ok, val = self.controller._parse_int(raw, field=label)
                if not ok:
                    event_status[idx].set(f"INVALID:{val}")
                    parsed_values.append(None)
                    any_invalid = True
                else:
                    parsed_values.append(int(val))  # type: ignore[arg-type]

            for offset, (_label, raw) in enumerate(time_inputs):
                idx = 6 + offset
                if not raw:
                    event_status[idx].set("INVALID:Required (mm:ss)")
                    parsed_values.append(None)
                    any_invalid = True
                    continue
                ok, val = self.controller.parse_time_to_seconds(raw)
                if not ok:
                    event_status[idx].set(f"INVALID:{val}")
                    parsed_values.append(None)
                    any_invalid = True
                else:
                    parsed_values.append(int(val))  # type: ignore[arg-type]

            mil = self.selected_military
            if mil is None:
                # Valid inputs without a selected serial -> show a green ✓
                # so the PTI still sees per-event live validation feedback.
                for idx in range(8):
                    if parsed_values[idx] is not None:
                        event_status[idx].set("VALID")
                tier_info_text.set("")
                overall_text.set("")
                return

            if any_invalid:
                tier_info_text.set("")
                overall_text.set("")
                return

            payload = {
                "pull_ups": parsed_values[0],
                "burpees": parsed_values[1],
                "farmer_m": parsed_values[2],
                "push_ups": parsed_values[3],
                "drag_m": parsed_values[4],
                "sandbag_m": parsed_values[5],
                "run_seconds": parsed_values[6],
                "swim_seconds": parsed_values[7],
            }
            try:
                age = mil.age_from_birthdate()
                outcome = self.controller.evaluate_payload(payload, mil.cluster, age, mil.gender)
                for i, tier in enumerate(outcome.per_event):
                    event_status[i].set(str(tier))
                tier_info_text.set(str(outcome.tier_info))
                overall_text.set(
                    f"PASSED ({outcome.overall})"
                    if outcome.passed
                    else f"FAILED ({outcome.overall})"
                )
            except Exception:
                tier_info_text.set("")
                overall_text.set("")

        # ----------------------------
        # Grid
        # ----------------------------
        @reactive.calc
        async def mfft_df() -> DataFrame | None:
            _ = self.refresh_tick.get()
            sess_id = (selected_session_id.get() or "").strip()
            if not sess_id:
                return pd.DataFrame()
            try:
                df = await self.controller.list_mfft_tests_df(int(sess_id))
            except Exception:
                return pd.DataFrame()
            try:
                df = self.controller.decorate_grid(df)
                df = df.drop(columns=["ID"], errors="ignore")
                return df.sort_values(by=["Serial"])
            except Exception:
                return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        @output
        @render.data_frame
        async def mfft_grid():
            df = await mfft_df()
            return render.DataGrid(df, filters=False, selection_mode="rows", width="100%")

        # ----------------------------
        # Row selection -> populate form
        # ----------------------------
        @reactive.Effect
        @reactive.event(input.mfft_grid_selected_rows)
        async def _on_row_selected() -> None:
            sel = input.mfft_grid_selected_rows()
            if not sel:
                status.set(t(self.NO_SELECTION_MESSAGE))
                return
            df = await mfft_df()
            if df is None or df.empty:
                status.set(t(self.NO_SELECTION_MESSAGE))
                return
            row_idx = sel[0]
            if row_idx < 0 or row_idx >= len(df):
                status.set(t(self.NO_SELECTION_MESSAGE))
                return
            row = df.iloc[row_idx]
            mfft_id = str(row.get("ID", "") or "").strip()
            selected_mfft_id.set(mfft_id)

            serial = str(row.get("Serial", "") or "").strip()
            ui.update_text("mfft_serialnr", value=serial)
            ui.update_numeric("mfft_pull_ups", value=int(row.get("PullUps", 0) or 0))
            ui.update_numeric("mfft_burpees", value=int(row.get("Burpees", 0) or 0))
            ui.update_numeric("mfft_farmer_m", value=int(row.get("FarmerM", 0) or 0))
            ui.update_numeric("mfft_push_ups", value=int(row.get("PushUps", 0) or 0))
            ui.update_numeric("mfft_drag_m", value=int(row.get("DragM", 0) or 0))
            ui.update_numeric("mfft_sandbag_m", value=int(row.get("SandbagM", 0) or 0))
            ui.update_text("mfft_combat_run", value=str(row.get("Run", "") or ""))
            ui.update_text("mfft_combat_swim", value=str(row.get("Swim", "") or ""))

            _set_buttons(can_add=False, can_update=True)

            try:
                self.selected_military = (
                    await self.controller.search_military(serial) if serial else None
                )
            except Exception:
                self.selected_military = None

            await _toggle_inputs(disabled=(self.selected_military is None))
            status.set(
                f"Selected MFFT record for: {serial}" if serial else "Selected MFFT record."
            )

        # ----------------------------
        # CRUD
        # ----------------------------
        def _validate(form: MfftFormData) -> tuple[bool, Any]:
            """
            Validates the given form using a controller method that checks the values of specific
            fields within the supplied `MfftFormData`. If validation fails, an appropriate error
            message will be returned.

            :param form: An instance of `MfftFormData` containing the attributes required
                for processing. Each attribute corresponds to an exercise or measure
                in the form.
            :type form: MfftFormData

            :return: A tuple where the first element is a boolean indicating whether the
                validation was successful, and the second element is either a result
                object from the controller or an error message on failure.
            :rtype: tuple[bool, Any]
            """
            try:
                return self.controller.validate_form(
                    {
                        "serialnr": form.serialnr,
                        "pull_ups": form.pull_ups,
                        "burpees": form.burpees,
                        "farmer_m": form.farmer_m,
                        "push_ups": form.push_ups,
                        "drag_m": form.drag_m,
                        "sandbag_m": form.sandbag_m,
                        "combat_run": form.combat_run,
                        "combat_swim": form.combat_swim,
                    }
                )
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                return False, f"Validation failed: {e}"

        @reactive.Effect
        @reactive.event(input.mfft_add_btn)
        async def _on_add() -> None:
            """
            Handles the addition of an MFFT evaluation process upon activation of the input button.

            This function is reactive and listens for the click event of a designated button. It performs
            input validation, processes the form data, interacts with a controller to execute the addition
            operation, and provides feedback to the user via notifications. If the action is successful,
            it triggers a refresh of the current session's data.

            :param input.mfft_add_btn: The button event that triggers the function.
            :return: None
            """
            if not _require_session_selected() or not _require_military_selected():
                return
            form = _read_form()
            ok, res = _validate(form)
            if not ok or not isinstance(res, dict):
                status.set(str(res))
                ui.notification_show(
                    f"Invalid input: {res}", type="error", duration=5
                )
                return
            added = await self.controller.add_mfft(
                int(form.session_id),
                res,
                session=self.selected_session,  # type: ignore[arg-type]
                military=self.selected_military,  # type: ignore[arg-type]
            )
            if not added:
                status.set(t("mfft_eval.failed_add").format(serial=form.serialnr))
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("mfft_eval.added_status").format(serial=form.serialnr))
            ui.notification_show(
                t("mfft_eval.added").format(serial=form.serialnr), type="message", duration=3
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.mfft_update_btn)
        async def _on_update() -> None:
            """
            Triggered by the "update" button event, this function handles the update operation
            for a selected MFFT entry. It carries out a sequence of operations, including
            validations, payload preparation, interaction with the controller to perform the update,
            and refreshes the UI upon success.

            :raises KeyError: If entries expected in the form dictionary are not found during
                payload preparation.
            :raises TypeError: If the result of validation is not of the expected type.
            :raises ValueError: If the raw MFFT ID cannot be cast to an integer.
            """
            if not _require_session_selected() or not _require_military_selected():
                return
            mfft_id_raw = (selected_mfft_id.get() or "").strip()
            if not mfft_id_raw:
                status.set(t("common.select_row_to_update"))
                return
            form = _read_form()
            ok, res = _validate(form)
            if not ok or not isinstance(res, dict):
                status.set(str(res))
                ui.notification_show(
                    f"Invalid input: {res}", type="error", duration=5
                )
                return
            payload = {"session_id": form.session_id, **res}
            updated = await self.controller.update_mfft(int(mfft_id_raw), payload)
            if not updated:
                status.set(t("mfft_eval.failed_update").format(serial=form.serialnr))
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("mfft_eval.updated_status").format(serial=form.serialnr))
            ui.notification_show(
                t("mfft_eval.updated").format(serial=form.serialnr),
                type="message",
                duration=3,
            )
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.mfft_delete_btn)
        async def _on_delete() -> None:
            """
            The `_on_delete` function handles the deletion of a selected MFFT session and record,
            triggered by the delete button event. It validates the input session ID and MFFT record
            ID, then performs the deletion through the controller. Depending on the result of the
            deletion attempt, it updates the status message for the user and optionally refreshes
            the UI. Notifications are displayed to inform the user of successful or unsuccessful
            deletion. If successful, the form is cleared after the operation.

            :param None: The function does not accept any parameters directly, but relies on attached
                         reactive inputs.
            :return: None
            """
            sess_id_raw = (input.mfft_session_id() or "").strip()
            mfft_id_raw = (selected_mfft_id.get() or "").strip()
            if not sess_id_raw or not mfft_id_raw:
                status.set(t("common.select_row_to_delete"))
                return
            ok = await self.controller.delete_mfft(int(sess_id_raw), int(mfft_id_raw))
            if not ok:
                status.set(t("mfft_eval.failed_delete"))
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("mfft_eval.deleted_success"))
            ui.notification_show(t("mfft_eval.deleted"), type="warning", duration=3)
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.mfft_refresh_btn)
        def _on_refresh() -> None:
            """
            This function is a reactive effect triggered by the `input.mfft_refresh_btn` event.
            Upon activation, it increments the value of the `refresh_tick` property by 1.
            This is used to notify any reactive expressions or computations dependent on
            `refresh_tick` of a state change, ensuring proper updates.

            :return: None
            """
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.mfft_clear_btn)
        async def _on_clear() -> None:
            await _clear_form()
            status.set(t("common.form_cleared"))

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.mfft_serial_search_btn)
        async def _open_serial_search_modal() -> None:
            """
            Represents a reactive effect that listens to the event triggered by the
            `mfft_serial_search_btn` input. When invoked, it displays a modal dialog
            allowing selection of a serial number from a displayed data frame.

            This function is expected to handle the event asynchronously, establishing
            the modal content and invoking its display. The modal is built with a card
            containing a header and a data frame output. The modal supports easy close
            functionality and is not displayed in full-screen mode.

            :return: None
            """
            modal_content = ui.modal(
                ui.card(
                    ui.card_header(t("common.select_serial_number")),
                    ui.output_data_frame("mfft_serial_search_grid"),
                    full_screen=False,
                ),
                size="l",
                easy_close=True,
            )
            ui.modal_show(modal_content)

        @reactive.calc
        async def get_all_servicemen_df() -> pd.DataFrame:
            return await self.fetch_all_servicemen_df(self.controller)

        @render.data_frame
        async def mfft_serial_search_grid():
            """
            Initiates the rendering of a serial search grid for servicemen data in the form of a data grid.
            The data grid allows row selection, filtering, and adjusts its width to 100%.

            :raises Exception: If the operation to fetch the servicemen DataFrame fails.

            :return: A rendered data grid populated with servicemen data, allowing rows to be
                selected and filtered.
            :rtype: render.DataGrid
            """
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="rows", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.mfft_serial_search_grid_selected_rows)
        async def _on_serial_selected() -> None:
            indices = input.mfft_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("mfft_serialnr", value=str(row["service_number"]))
                    ui.modal_remove()

    async def _clear_form_hook(self, input: Any, session: Any) -> None:
        session.send_input_message("mfft_serialnr", {"value": ""})
        for input_id in (
            "mfft_pull_ups",
            "mfft_burpees",
            "mfft_farmer_m",
            "mfft_push_ups",
            "mfft_drag_m",
            "mfft_sandbag_m",
        ):
            session.send_input_message(input_id, {"value": 1})
        session.send_input_message("mfft_combat_run", {"value": ""})
        session.send_input_message("mfft_combat_swim", {"value": ""})
        self.selected_military = None


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = MfftEvalPage()
    return _page


def get_ui() -> NavPanel:
    return _get_page().get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _get_page().server(input, output, session)
