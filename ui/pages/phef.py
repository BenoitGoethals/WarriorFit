from shiny import ui, render, reactive
import pandas as pd

from core.Gender import Gender
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest
from logic.phef_calculator import PhefCalculator
from ui.services.db_service import DBService
from ..services.defense_external_service import DefenseExternalService
from ..user_store import UserStore

class PhefPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.external_services=DefenseExternalService()


    NO_SELECTION_MESSAGE = "No row selected"
    def get_ui(self):
        if UserStore.get_user():
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

                            ui.layout_columns(
                            ui.input_text(
                                "ph_side_bridge_r",
                                "Side-bridge Right time (mm:ss)",
                                placeholder="e.g., 2:30",
                            ),

                                ui.div("Score :", ui.output_text("ph_side_bridge_r_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_text(
                                    "ph_side_bridge_l",
                                    "Side-bridge time Left (mm:ss)",
                                    placeholder="e.g., 2:30",
                                ),
                                ui.div("Score :", ui.output_text("ph_side_bridge_l_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_text(
                                    "ph_run_2400",
                                    "2400m run time (mm:ss)",
                                    placeholder="e.g., 10:45 ",
                                ),
                                ui.div("Score :", ui.output_text("ph_run_2400_score")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("ph_add_btn", "Add"),
                                ui.input_action_button("ph_update_btn", "Update"),
                                ui.input_action_button("ph_clear_btn", "Clear Form"),
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
        return None

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

                # Re-apply the current value (optional safeguard)

                try:
                    status.set(f"Session is set to {selected_session_id.get()}" )
                except Exception:
                    pass


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
            session.send_input_message(
                "ph_session_id",
                {"value": "" if rec.get("session_id") is None else str(rec.get("session_id"))},
            )
            sbr_val = rec.get("side_bridge_r_s")
            sbl_val = rec.get("side_bridge_l_s")
            run_val = rec.get("run2400_s")
            session.send_input_message("ph_side_bridge_r", {"value": "" if sbr_val is None else _format_seconds(sbr_val)})
            session.send_input_message("ph_side_bridge_l", {"value": "" if sbl_val is None else _format_seconds(sbl_val)})
            session.send_input_message("ph_run_2400", {"value": "" if run_val is None else _format_seconds(run_val)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "session_id": None,
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
        def ph_search():
            status.set(f"Bad : {input.ph_serialnr()}")
            ui.update_text("ph_serialnr", value="")


        @output
        @render.text
        def ph_status():
            return status.get()

        @output
        @render.text
        def ph_side_bridge_r_score():
            return str(ph_side_bridge_r_score_val.get() or "")

        @output
        @render.text
        def ph_side_bridge_l_score():
            return str(ph_side_bridge_l_score_val.get() or "")

        @output
        @render.text
        def ph_run_2400_score():
            # Render the latest calculated score (empty when no/invalid input)
            return str(ph_run_2400_score_val.get() or "")

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
                score = PhefCalculator.running_result(val, 20, Gender.MALE)
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
                score = PhefCalculator.side_bridge_result(val, 20, Gender.MALE)
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
                score = PhefCalculator.side_bridge_result(val, 20, Gender.MALE)
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
                    run = PhefCalculator.running_result(r.running_time,20,Gender.MALE)
                    run_score_real=(run * (50 / 20))
                    side_r = PhefCalculator.side_bridge_result(r.sideBridge_r,20,Gender.MALE)
                    side_r_score_real=(side_r * (25 / 20))
                    side_l = PhefCalculator.side_bridge_result(r.sideBridge_l,20,Gender.MALE)
                    side_l_score_real=(side_l * (25 / 20))
                    total =run_score_real+(side_r_score_real+side_l_score_real)

                    data.append({
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "runningTime": _format_seconds(r.running_time),
                        "Running score": f"{run}/20",
                        "Sidebridge R ": _format_seconds(r.sideBridge_r),
                        "Sidebridge R score": f"{side_r}/20",
                        "Sidebridge L": _format_seconds(r.sideBridge_l),
                        "Sidebridge L score":f"{side_l}/20",
                        "Totale Score": f"{total}/100",
                    })
                # Create DataFrame after collecting all data
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Error fetching PHEF data: {e}")
                return pd.DataFrame()

        @output
        @render.data_frame
        async def ph_grid():
            df = await sessions_phef__data()
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
        def _on_session_change():
            # Track selection changes
            val = (input.ph_session_id() or "").strip()
            selected_session_id.set(val)

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

            # Placeholder: local-only add (no DB persistence implemented here)
            new_id = max([r["id"] for r in records.get()] + [0]) + 1
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
            df = await sessions_phef__data()
            del_phef = await self.db.delete_fitness_test_from_test_session(int(sel_session_id),int(selected_session_id.get()))
            if not del_phef:
                status.set(f"Failed to delete PHEF test for record ID {sel[0]}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
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
_page = PhefPage(DBService("ui/config/config.yml"))

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)