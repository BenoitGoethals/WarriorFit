from shiny import ui, render, reactive
import pandas as pd

from core.service_men import ServiceMen
from data.db.db_model import TestSession
from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService
from ui.controllers.phef_controller import PhefController
from ui.pages.notify_mail import NotifyMail


class PhefPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = BEMILService()
        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None
        self.controller = PhefController(self.db, self.be_mil_service)

    NO_SELECTION_MESSAGE = "No row selected"

    def get_ui(self):
        return ui.nav_panel(
            "PHEF Tests",
            ui.h2("🧪 PHEF Tests "),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.card_header("Session"),
                        ui.input_select("ph_session_id", "Session", choices=[]),
                        full_screen=False,
                    ),
                    ui.card(
                        ui.input_text("ph_serialnr", "Serial Number"),
                        ui.input_action_button("ph_search", "search", width="150px"),
                        ui.output_text("ph_miltary"),
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
                                "Side-bridge time Left (mm:ss)",
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
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("ph_add_btn", "Add",
                                                   disabled=self.selected_military is None, width="150px"),
                            ui.input_action_button("ph_update_btn", "Update",
                                                   disabled=self.selected_military is None, width="150px"),
                            ui.input_action_button("ph_clear_btn", "Clear Form", width="150px"),
                            col_widths=(4,),
                        ),
                        ui.output_text("ph_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("PHEF Tests (You must pass running and side-bridge tests to have a pass on the PHEF test)"),
                    ui.output_data_frame("ph_grid"),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button("ph_delete_btn", "Delete Selected"),
                        col_widths=(6, 3, 3),
                    ),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        # Reactive state
        ph_side_bridge_r_score_val = reactive.Value("")
        ph_side_bridge_l_score_val = reactive.Value("")
        ph_run_2400_score_val = reactive.Value("")
        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        selected_phef_id = reactive.Value("")

        # Form helpers
        def _read_form():
            return {
                "serialnr": (input.ph_serialnr() or "").strip(),
                "session_id": (input.ph_session_id() or "").strip(),
                "side_bridge_r": (input.ph_side_bridge_r() or "").strip(),
                "side_bridge_l": (input.ph_side_bridge_l() or "").strip(),
                "run_2400": (input.ph_run_2400() or "").strip(),
            }

        def _write_form(rec):
            session.send_input_message("ph_serialnr", {"value": rec.get("serialnr", "")})
            session.send_input_message("ph_side_bridge_r", {"value": rec.get("side_bridge_r", "")})
            session.send_input_message("ph_side_bridge_l", {"value": rec.get("side_bridge_l", "")})
            session.send_input_message("ph_run_2400", {"value": rec.get("run_2400", "")})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "side_bridge_r": "",
                "side_bridge_l": "",
                "run_2400": "",
            })

        async def _refresh_session_choices():
            test_sessions = await self.controller.load_sessions()
            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.ph_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("ph_session_id", choices=items, selected=selected)

        # Search military
        @reactive.effect
        @reactive.event(input.ph_search, ignore_none=False)
        async def ph_search():
            if not (input.ph_serialnr() or "").strip():
                ui.update_action_button("ph_add_btn", disabled=True)
                ui.update_action_button("ph_update_btn", disabled=True)
                return
            val = await self.controller.search_military(input.ph_serialnr() or "")
            self.selected_military = val
            if val is None:
                ui.update_text("ph_serialnr", value="Not found")
                return
            military.set(f"{val.rank} {val.service_number} {val.first_name} {val.last_name}")
            ui.update_action_button("ph_add_btn", disabled=False)
            ui.update_action_button("ph_update_btn", disabled=False)

        # Status outputs
        @output
        @render.text
        def ph_status():
            return status.get()

        @output
        @render.text
        def ph_miltary():
            return military.get()

        # Score outputs
        @output
        @render.ui
        def ph_side_bridge_r_score():
            text = str(ph_side_bridge_r_score_val.get())
            try:
                num = float(ph_side_bridge_r_score_val.get())
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")

        @output
        @render.ui
        def ph_side_bridge_l_score():
            text = str(ph_side_bridge_l_score_val.get())
            try:
                num = float(ph_side_bridge_l_score_val.get())
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")

        @output
        @render.text
        def ph_run_2400_score():
            text = str(ph_run_2400_score_val.get())
            try:
                num = float(ph_run_2400_score_val.get())
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")

        # Live score calculations
        @reactive.Effect
        @reactive.event(input.ph_side_bridge_r)
        def _on_side_bridge_r_change():
            raw = (input.ph_side_bridge_r() or "").strip()
            ok, val = self.controller.parse_time_to_seconds(raw)
            if not ok or not self.selected_military:
                ph_side_bridge_r_score_val.set("")
                return
            try:
                score = PhefCalculator.side_bridge_result(
                    val,
                    self.selected_military.age_from_birthdate(),
                    self.selected_military.gender,
                )
            except Exception:
                score = ""
            ph_side_bridge_r_score_val.set(score)

        @reactive.Effect
        @reactive.event(input.ph_side_bridge_l)
        def _on_side_bridge_l_change():
            raw = (input.ph_side_bridge_l() or "").strip()
            ok, val = self.controller.parse_time_to_seconds(raw)
            if not ok or not self.selected_military:
                ph_side_bridge_l_score_val.set("")
                return
            try:
                score = PhefCalculator.side_bridge_result(
                    val,
                    self.selected_military.age_from_birthdate(),
                    self.selected_military.gender,
                )
            except Exception:
                score = ""
            ph_side_bridge_l_score_val.set(score)

        @reactive.Effect
        @reactive.event(input.ph_run_2400)
        def _on_run_change():
            raw = (input.ph_run_2400() or "").strip()
            ok, val = self.controller.parse_time_to_seconds(raw)
            if not ok or not self.selected_military:
                ph_run_2400_score_val.set("")
                return
            try:
                score = PhefCalculator.running_result(
                    val,
                    self.selected_military.age_from_birthdate(),
                    self.selected_military.gender,
                )
            except Exception:
                score = ""
            ph_run_2400_score_val.set(score)

        # Data
        @reactive.calc
        async def sessions_phef__data():
            _ = self.refresh_tick.get()
            session_id = selected_session_id.get()
            if not session_id:
                return pd.DataFrame()
            sess_date = self.selected_session.datetime_start if self.selected_session else None
            return await self.controller.list_phef_df(int(session_id), session_date=sess_date)

        @output
        @render.data_frame
        async def ph_grid():
            df = await sessions_phef__data()
            df = self.controller.decorate_grid(df)
            return render.DataGrid(df, filters=False, selection_mode="rows")

        # Init and session selection
        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            val = (input.ph_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.controller.get_session_by_id(int(val))

        # Row selection
        @reactive.Effect
        @reactive.event(input.ph_grid_selected_rows)
        async def _on_ph_row_selected():
            try:
                sel = input.ph_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row_idx = sel[0]
                df = await sessions_phef__data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row = df.iloc[row_idx]
                selected_phef_id.set(row["ID"] or "")
                selected_session_id.set(input.ph_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.controller.search_military(serial)
                ui.update_text("ph_serialnr", value=serial)
                ui.update_text("ph_side_bridge_l", value=row.get("Sidebridge L", ""))
                ui.update_text("ph_side_bridge_r", value=row.get("Sidebridge R", row.get("Sidebridge R ", "")))
                ui.update_text("ph_run_2400", value=row.get("runningTime", ""))
                status.set(f"Selected PHEF: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        # CRUD
        def _validate(data):
            return self.controller.validate_form(data)

        @reactive.Effect
        @reactive.event(input.ph_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return
            payload = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],
                "side_bridge_r_s": res["side_bridge_r_s"],
                "side_bridge_l_s": res["side_bridge_l_s"],
                "run2400_s": res["run2400_s"],
            }
            added = await self.controller.add_phef(int(payload["id"]), payload)
            if not added:
                status.set(f"Failed to add PHEF test for {payload['serialnr']} in session {str(payload['id'])}.")
                return
            if self.selected_military and getattr(self.selected_military, "mail", None) and self.selected_session:
                body = self.controller.build_email_body(self.selected_military, self.selected_session, payload)
                await NotifyMail().send_mail(body=body, subject="Result Test", to=self.selected_military.mail)
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Added PHEF test for {payload['serialnr']} in session {str(payload['id'])}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            updated = await self.controller.update_phef(int(selected_phef_id.get()), payload)
            if not updated:
                status.set(
                    f"Failed to update PHEF test for {payload['serialnr']} in session {str(payload['session_id'])}."
                )
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated PHEF test for {payload['serialnr']} in session {str(payload['session_id'])}."
            )
            _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_delete_btn)
        async def _on_delete():
            sel = input.ph_grid_selected_rows()
            sel_session_id = input.ph_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            ok = await self.controller.delete_phef(int(sel_session_id), int(selected_phef_id.get()))
            if not ok:
                status.set(f"Failed to delete PHEF test for record ID {sel[0]}.")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_phef__data()
                row_idx = sel[0]
                row = df.iloc[row_idx]
                status.set(f"PHEF test for record ID {row['ID']} deleted successfully.")
            except Exception:
                status.set("Invalid selection.")


# Public API
_page = PhefPage(DBService())


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)