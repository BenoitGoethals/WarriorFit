import datetime
from typing import Any

from pandas import Series
from shiny import ui, render, reactive
import pandas as pd

from config.appliccation_config import ApplicationConfig
from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest, TestSession
from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService
from services.mail_service import MailService
from ui.pages.notify_mail import NotifyMail


class PhefPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service=BEMILService()
        self.selected_military:ServiceMen=None
        self.selected_session:TestSession=None



    NO_SELECTION_MESSAGE = "No row selected"
    def get_ui(self):

            return ui.nav_panel(
                "PHEF Tests",
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
                                ui.input_action_button("ph_search", "search", width="150px"),
                            ui.output_text("ph_miltary", ),

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
                                    placeholder="e.g., 10:45 ",

                                ),
                                ui.div("Score :", ui.output_ui("ph_run_2400_score")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("ph_add_btn", "Add",disabled=self.selected_military is None, width="150px"),
                                ui.input_action_button("ph_update_btn", "Update",disabled=self.selected_military is None, width="150px"),
                                ui.input_action_button("ph_clear_btn", "Clear Form", width="150px"),
                                col_widths=(4,),
                            ),
                            ui.output_text("ph_status", ),
                            ui.br(),
                        #    ui.output_text("ph_status"),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Phef Tests"),
                        ui.output_data_frame("ph_grid"),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("ph_delete_btn", "Delete Selected"),
                            col_widths=(6, 3, 3),
                        ),
                        full_screen=False,
                    ),
                    col_widths=(4, 8),  # Records occupies ~2/3 width
                ),
            )


    def server(self, input, output, session):
        # Reactive state
        records = reactive.Value([])
        ph_side_bridge_r_score_val = reactive.Value("")
        ph_side_bridge_l_score_val = reactive.Value("")
        ph_run_2400_score_val = reactive.Value("")
        # If you also want to prevent any code reacting to changes while locked:
        @reactive.Effect
        @reactive.event(input.ph_session_id)
        def _guard_session_change_when_locked():
                try:
                    status.set(f"Session is set to {selected_session_id.get()}" )
                except Exception:
                    pass


        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")  # track current selection
        selected_phef_id= reactive.Value("")
        def _parse_time_to_seconds(val: str):
            txt = (val or "").strip()
            if not txt:
                return False, "Time value is required."
            try:
                if ":" in txt:
                    parts = txt.split(":")
                    if len(parts) != 2:
                        return False, "Time must be in mm:ss or seconds."
                    m = int(parts[0]); s = int(parts[1])
                    total = m * 60 + s
                else:
                    total = int(float(txt))
                if total <= 0:
                    return False, "Time must be positive."
                return True, int(total)
            except Exception:
                return False, "Time must be numeric (mm:ss or seconds)."

        def _format_seconds(sec: float|int):
            m = sec // 60
            s = sec % 60
            return f"{int(m)}:{int(s):02d}"



        def _validate(data):
            if not (data["serialnr"] or "").strip():
                return False, "Serial number is required."
            #if not (data["session_id"] or "").strip():
            #    return False, "Session selection is required."

            ok_sbr, sbr = _parse_time_to_seconds(data["side_bridge_r"])
            if not ok_sbr:
                return False, f"Side-bridge Right: {sbr}"
            ok_sbl, sbl = _parse_time_to_seconds(data["side_bridge_l"])
            if not ok_sbl:
                return False, f"Side-bridge Left: {sbl}"
            ok_run, run = _parse_time_to_seconds(data["run_2400"])
            if not ok_run:
                return False, f"2400m run: {run}"

            
            return True, {
             #   "session_id_int": int(data["session_id"]),
                "side_bridge_r_s": sbr,
                "side_bridge_l_s": sbl,
                "run2400_s": run,
            }

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
           # session.send_input_message(
           #     "ph_session_id",
           #     {"value": "" if rec.get("session_id") is None else str(rec.get("session_id"))},
           # )
            sbr_val = rec.get("side_bridge_r_s")
            sbl_val = rec.get("side_bridge_l_s")
            run_val = rec.get("run2400_s")
            session.send_input_message("ph_side_bridge_r", {"value": "" if sbr_val is None else _format_seconds(sbr_val)})
            session.send_input_message("ph_side_bridge_l", {"value": "" if sbl_val is None else _format_seconds(sbl_val)})
            session.send_input_message("ph_run_2400", {"value": "" if run_val is None else _format_seconds(run_val)})

        def _clear_form():
            _write_form({
                "serialnr": "",
           #     "session_id": None,
                "side_bridge_r_s": None,
                "side_bridge_l_s": None,
                "run2400_s": None
            })

        # Populate sessions into the select input, preserving current selection when possible
        async def _refresh_session_choices():
            test_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.PHEF)
            items = {  # key must be a string; label a human-readable string
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.ph_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("ph_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.ph_search, ignore_none=False)
        async def ph_search():
            if input.ph_serialnr() is None or input.ph_serialnr() == "":
                ui.update_action_button("ph_add_btn", disabled=True)
                ui.update_action_button("ph_update_btn", disabled=True)
                return
            try:

                val=await self.be_mil_service.get_be_mil_by_id(input.ph_serialnr() or "")
                self.selected_military=val
               # ui.update_text("ph_serialnr", value=val.service_number+val.first_name+" "+val.last_name)

                military.set(val.rank+" "+val.service_number+" "+val.first_name+" "+val.last_name)
                ui.update_action_button("ph_add_btn",disabled=False)
                ui.update_action_button("ph_update_btn",  disabled=False)
            except Exception as e:
                ui.update_text("ph_serialnr", value="Not found")
                return


        @output
        @render.text
        def ph_status():
            return status.get()

        @output
        @render.text
        def ph_miltary():
            return military.get()


        @output
        @render.ui
        def ph_side_bridge_r_score():
            val = ph_side_bridge_r_score_val.get()
            text = str(val)
            try:
                num = float(val)
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")

        @output
        @render.ui
        def ph_side_bridge_l_score():
            val = ph_side_bridge_l_score_val.get()
            text = str(val)
            try:
                num = float(val)
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")



        @output
        @render.text
        def ph_run_2400_score():
            val = ph_run_2400_score_val.get()
            text = str(val)
            try:
                num = float(val)
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")


        @reactive.Effect
        @reactive.event(input.ph_run_2400)
        def ph_run_2400():
            # Update the 2400m score whenever the input changes
            raw = (input.ph_run_2400() or "").strip()
            ok, val = _parse_time_to_seconds(raw)
            if not ok:
                ph_run_2400_score_val.set("")
                return
            try:

                score = PhefCalculator.running_result(val, self.selected_military.age_from_birthdate(), self.selected_military.gender)
            except Exception:
                score = ""
            ph_run_2400_score_val.set(score)

        @reactive.Effect
        @reactive.event(input.ph_side_bridge_r)
        def ph_side_bridge_r():
            # Update the Side-bridge Right score whenever the input changes
            raw = (input.ph_side_bridge_r() or "").strip()
            ok, val = _parse_time_to_seconds(raw)
            if not ok:
                ph_side_bridge_r_score_val.set("")
                return
            try:
                score = PhefCalculator.side_bridge_result(val, self.selected_military.age_from_birthdate(), self.selected_military.gender)
            except Exception:
                score = ""
            ph_side_bridge_r_score_val.set(score)

        @reactive.Effect
        @reactive.event(input.ph_side_bridge_l)
        def ph_side_bridge_l():
            # Update the Side-bridge Left score whenever the input changes
            raw = (input.ph_side_bridge_l() or "").strip()
            ok, val = _parse_time_to_seconds(raw)
            if not ok:
                ph_side_bridge_l_score_val.set("")
                return
            try:
                score = PhefCalculator.side_bridge_result(val, self.selected_military.age_from_birthdate(),self.selected_military.gender)
            except Exception:
                score = ""
            ph_side_bridge_l_score_val.set(score)

        @reactive.calc
        async def sessions_phef__data():
            _ = self.refresh_tick.get()
            session_id = selected_session_id.get()
            if not session_id:
                return pd.DataFrame()
            try:
                phef_tests = await self.db.get_all_phef(int(session_id))
                # Create a list of dictionaries with values directly from the database objects
                data = []
                for r in phef_tests:
                    selected_military:ServiceMen=await self.be_mil_service.get_be_mil_by_id(r.serial_number)
                    if selected_military is None:
                        continue
                    run, side_l, side_r, total = await _calculate_phef_results(r, selected_military)

                    data.append({
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "runningTime": _format_seconds(r.running_time),
                        "Running Score": f"{run}/20",
                        "Sidebridge R ": _format_seconds(r.sideBridge_r),
                        "Sidebridge R Score": f"{side_r}/20",
                        "Sidebridge L": _format_seconds(r.sideBridge_l),
                        "Sidebridge L Score":f"{side_l}/20",
                        "Totale Score": f"{total}/100",
                    })
                # Create DataFrame after collecting all data
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Error fetching PHEF data: {e}")
                return pd.DataFrame()

        async def _calculate_phef_results(r: PhefTest, selected_military: ServiceMen) -> tuple:
            age = selected_military.age_from_birthdate_and_session_date(self.selected_session.datetime_start)
            run = PhefCalculator.running_result(r.running_time, age, selected_military.gender)
            run_score_real = (run * (50 / 20))
            side_r = PhefCalculator.side_bridge_result(r.sideBridge_r, age, selected_military.gender)
            side_r_score_real = (side_r * (25 / 20))
            side_l = PhefCalculator.side_bridge_result(r.sideBridge_l, age, selected_military.gender)
            side_l_score_real = (side_l * (25 / 20))
            total = run_score_real + (side_r_score_real + side_l_score_real)
            return run, side_l, side_r, total

        def _decorate_scores_for_grid(df):
            def _total_num(s):
                try:
                    # Expecting format like "NN/100"
                    return float(str(s).split("/")[0])
                except Exception:
                    return None

            df2 = df.copy()

            # Totale Score: prefix with red/green indicator
            if "Totale Score" in df2.columns:
                def _fmt_total(s):
                    n = _total_num(s)
                    if n is None:
                        return s
                    return f"🟥 {s}" if n < 50 else f"🟩 {s}"
                df2["Totale Score"] = df2["Totale Score"].apply(_fmt_total)

            # Per-exercise scores (<10 red else green)
            score_cols = ["Running Score",  "Sidebridge R Score", "Sidebridge L Score"]
            for col in score_cols:
                if col in df2.columns:
                    def _fmt_score(v):
                        n = _total_num(v)
                        if n is None:
                            return v
                        return f"🟥 {v}" if n < 10 else f"🟩 {v}"
                    df2[col] = df2[col].apply(_fmt_score)

            return df2

        @output
        @render.data_frame
        async def ph_grid():
            df = await sessions_phef__data()
            df = _decorate_scores_for_grid(df)
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="rows",
            )
        # Single async initializer to avoid resetting choices
        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            # Track selection changes
            val = (input.ph_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.db.get_test_session_by_id(int(val))


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
                selected_session_id.set(input.ph_session_id()  or "")
                # Extract fields safely (note: "Sidebridge R " has a trailing space in the DataFrame)
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.be_mil_service.get_be_mil_by_id(serial)
                side_l = row.get("Sidebridge L", None)
                side_r = row.get("Sidebridge R ", row.get("Sidebridge R", None))
                run_t = row.get("runningTime", None)

                # Format to mm:ss where possible
                def fmt(x):
                    try:
                        return _format_seconds(int(x))
                    except Exception:
                        return ""

                ui.update_text("ph_serialnr", value=serial)
                ui.update_text("ph_side_bridge_l", value=(side_l))
                ui.update_text("ph_side_bridge_r", value=(side_r))
                ui.update_text("ph_run_2400", value=(run_t))

                status.set(f"Selected PHEF: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.ph_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            record = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],

                "side_bridge_r_s": res["side_bridge_r_s"],
                "side_bridge_l_s": res["side_bridge_l_s"],
                "run2400_s": res["run2400_s"],
            }
            phef= PhefTest()
            phef.test_session_id=int(record["id"])
            phef.serial_number=record["serialnr"]
            phef.running_time=record["run2400_s"]
            phef.sideBridge_r=record["side_bridge_r_s"]
            phef.sideBridge_l=record["side_bridge_l_s"]
            phef.pointBridge_r=0
            phef.pointBridge_l=0
            phef.pointsRunning=0
            added_phef= await self.db.add_fitness_test_to_TestSession(int(record["id"]), phef)

            if not added_phef:
                status.set(f"Failed to add PHEF test for {phef.serial_number} in session {str(phef.test_session_id)}.")
                return
            run, side_l, side_r, total = await _calculate_phef_results(phef, self.selected_military)
            body = f"""
                <h2>PHEF Test Results</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Service Member Information</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Service Member:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{self.selected_military.rank} {self.selected_military.service_number}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Name:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{self.selected_military.first_name} {self.selected_military.last_name}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Test Session ID:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{str(phef.test_session_id)}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Serial Number:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{phef.serial_number}</td>
                    </tr>
                    
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Test Results</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Running (2400m)</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            Time: {_format_seconds(phef.running_time)}<br>
                            Score: {run}/20
                        </td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Right</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            Time: {_format_seconds(phef.sideBridge_r)}<br>
                            Score: {side_r}/20
                        </td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Left</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            Time: {_format_seconds(phef.sideBridge_l)}<br>
                            Score: {side_l}/20
                        </td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">Total Score</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">{total}/100</th>
                    </tr>
                </table>
            """
            await NotifyMail().send_mail(body=body,subject="Result Test",to=self.selected_military.mail)
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])

            status.set(f"Added PHEF test for {phef.serial_number} in session {str(phef.test_session_id)}.")
            _clear_form()

        # Helper to build a PhefTest from merged, validated input
        def _build_phef_from_form(payload: dict) -> PhefTest:
            phef = PhefTest()
            phef.id = selected_phef_id.get()
            phef.test_session_id = int(payload["session_id"])
            phef.serial_number = payload["serialnr"]
            phef.running_time = payload["run2400_s"]
            phef.sideBridge_r = payload["side_bridge_r_s"]
            phef.sideBridge_l = payload["side_bridge_l_s"]
            phef.pointBridge_r = 0
            phef.pointBridge_l = 0
            phef.pointsRunning = 0
            return phef

        @reactive.Effect
        @reactive.event(input.ph_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            # Merge raw data (for ids/text) with validated/normalized values
            payload = {**data, **res}
            phef = _build_phef_from_form(payload)

            updated_phef = await self.db.update_fitness_test(int(phef.id), phef)
            if not updated_phef:
                status.set(
                    f"Failed to update PHEF test for {phef.serial_number} in session {str(phef.test_session_id)}."
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated PHEF test for {phef.serial_number} in session {str(phef.test_session_id)}."
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
            del_phef = await self.db.delete_fitness_test_from_test_session(int(sel_session_id),int(selected_phef_id.get()))
            if not del_phef:
                status.set(f"Failed to delete PHEF test for record ID {sel[0]}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_phef__data()
                row_idx = sel[0]
                row = df.iloc[row_idx]
                status.set(f"PHEF test for record ID {row['ID']} deleted successfully.")
            except Exception:
                status.set("Invalid selection.")

        @reactive.Effect
        @reactive.event(input.ph_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")



# Public API: keep same signatures
_page = PhefPage(DBService())

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)