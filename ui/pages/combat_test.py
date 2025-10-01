from shiny import ui, render, reactive
import pandas as pd
from sqlalchemy.sql.operators import truediv

from core.Gender import Gender
from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest, TestSession, CombatTestParatrooper
from logic.phef_calculator import PhefCalculator
from ui.services.db_service import DBService
from ..services.defense_external_service import DefenseExternalService
from ..user_store import UserStore


class CombatPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.external_services = DefenseExternalService()
        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None

    NO_SELECTION_MESSAGE = "No row selected"

    def get_ui(self):
        if UserStore.get_user():
            return ui.nav_panel(
                "Combat Tests",
                ui.h2("🧪 Combat Tests"),
                ui.layout_columns(
                    ui.div(
                        ui.card(
                            ui.card_header("Session"),
                            ui.input_select("combat_session_id", "Session", choices=[]),
                            full_screen=False,
                        ),
                        ui.card(

                            ui.input_text("combat_serialnr", "Serial Number"),
                            ui.input_action_button("combat_search", "search", width="150px"),
                            ui.output_text("combat_miltary", ),

                            ui.layout_columns(
                                ui.input_checkbox(
                                    "combat_obstacle",
                                    "Obstacle course",


                                ),

                                ui.div("Score :", ui.output_ui("combat_obstacle_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_checkbox(
                                    "combat_robe",
                                    "Robe Cours",

                                ),
                                ui.div("Score :", ui.output_ui("combat_robe_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_text(
                                    "combat_speedmars",
                                    "Speedmars time (mm:ss)",
                                    placeholder="e.g., 10:45 ",

                                ),
                                ui.div("Score :", ui.output_ui("combat_speedmars_score")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("combat_add_btn", "Add", disabled=self.selected_military is None,
                                                       width="150px"),
                                ui.input_action_button("combat_update_btn", "Update",
                                                       disabled=self.selected_military is None, width="150px"),
                                ui.input_action_button("combat_clear_btn", "Clear Form", width="150px"),
                                col_widths=(4,),
                            ),
                            ui.output_text("combat_status", ),
                            ui.br(),
                            #    ui.output_text("ph_status"),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Combat Tests"),
                        ui.output_data_frame("combat_grid"),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("combat_delete_btn", "Delete Selected"),
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
        combat_score_obstacle_val = reactive.Value(False)
        combat_score_robe_val = reactive.Value(False)
        combat_score_speedmars_val = reactive.Value("")

        # If you also want to prevent any code reacting to changes while locked:
        @reactive.Effect
        @reactive.event(input.ph_session_id)
        def _guard_session_change_when_locked():
            try:
                status.set(f"Session is set to {selected_session_id.get()}")
            except Exception:
                pass

        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")  # track current selection
        selected_combat_id = reactive.Value("")

        def _parse_time_to_seconds(val: str):
            txt = (val or "").strip()
            if not txt:
                return False, "Time value is required."
            try:
                if ":" in txt:
                    parts = txt.split(":")
                    if len(parts) != 2:
                        return False, "Time must be in mm:ss or seconds."
                    m = int(parts[0]);
                    s = int(parts[1])
                    total = m * 60 + s
                else:
                    total = int(float(txt))
                if total <= 0:
                    return False, "Time must be positive."
                return True, int(total)
            except Exception:
                return False, "Time must be numeric (mm:ss or seconds)."

        def _format_seconds(sec: float | int):
            m = sec // 60
            s = sec % 60
            return f"{int(m)}:{int(s):02d}"

        def _validate(data):
            if not (data["serialnr"] or "").strip():
                return False, "Serial number is required."
            # if not (data["session_id"] or "").strip():
            #    return False, "Session selection is required."


            ok_run, run = _parse_time_to_seconds(data["combat_speedmars"])
            if not ok_run:
                return False, f"combat_speedmars: {run}"

            return True, {
                #   "session_id_int": int(data["session_id"]),

                "combat_speedmars": run,
                "combat_obstacle": data["combat_obstacle"],
                "combat_robe": data["combat_robe"],
            }

        def _read_form():
            return {
                "serialnr": (input.combat_serialnr() or "").strip(),
                "session_id": (input.combat_session_id() or "").strip(),
                "combat_robe": input.combat_robe(),
                "combat_obstacle": input.combat_obstacle(),
                "combat_speedmars": (input.combat_speedmars() or "").strip(),
            }

        def _write_form(rec):
            session.send_input_message("ph_serialnr", {"value": rec.get("serialnr", "")})
            # session.send_input_message(
            #     "ph_session_id",
            #     {"value": "" if rec.get("session_id") is None else str(rec.get("session_id"))},
            # )
            cr_val = rec.get("combat_robe")
            co_val = rec.get("combat_obstacle")
            speedmars_val = rec.get("speedmars_s")
            session.send_input_message("combat_obstacle", {"value":  co_val })
            session.send_input_message("combat_robe", {"value": cr_val})
            session.send_input_message("combat_speedmars", {"value": "" if speedmars_val is None else _format_seconds(speedmars_val)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                #     "session_id": None,
                "combat_obstacle": False,
                "combat_robe": False,
                "combat_speedmars": None
            })

        # Populate sessions into the select input, preserving current selection when possible
        async def _refresh_session_choices():
            test_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.COMBAT)
            items = {  # key must be a string; label a human-readable string
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.ph_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("combat_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.combat_search, ignore_none=False)
        def combat_search():
            if input.combat_serialnr() is None or input.combat_serialnr() == "":
                ui.update_action_button("combat_add_btn", disabled=True)
                ui.update_action_button("combat_update_btn", disabled=True)
                return
            try:
                val = self.external_services.get_serviceman_by_serial(input.combat_serialnr() or "")
                self.selected_military = val
                # ui.update_text("ph_serialnr", value=val.service_number+val.first_name+" "+val.last_name)

                military.set(val.rank + " " + val.service_number + " " + val.first_name + " " + val.last_name)
                ui.update_action_button("combat_add_btn", disabled=False)
                ui.update_action_button("combat_update_btn", disabled=False)
            except Exception as e:
                ui.update_text("combat_serialnr", value="Not found")
                return

        @output
        @render.text
        def combat_status():
            return status.get()

        @output
        @render.text
        def combat_miltary():
            return military.get()


        @output
        @render.text
        def combat_speedmars_score():
            val = combat_score_speedmars_val.get()
            text = str(val)
            try:
                num = float(val)
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 10) else "green"
            return ui.span(text, style=f"color: {color};")

        @reactive.Effect
        @reactive.event(input.combat_speedmars)
        def combat_speedmars():
            # Update the 2400m score whenever the input changes
            raw = (input.combat_speedmars() or "").strip()
            ok, val = _parse_time_to_seconds(raw)
            if not ok:
                combat_score_speedmars_val.set("")
                return
            try:

                if val < 2400:
                    score = "Passes"
                else:
                    score = "Fails"

            except Exception:
                score = ""
            combat_score_speedmars_val.set(score)


        @reactive.calc
        async def sessions_combat__data():
            _ = self.refresh_tick.get()
            session_id = selected_session_id.get()
            if not session_id:
                return pd.DataFrame()
            try:
                combat_tests = await self.db.get_all_combat_test(int(session_id))
                # Create a list of dictionaries with values directly from the database objects
                data = []
                for r in combat_tests:
                    selected_military = self.external_services.get_serviceman_by_serial(r.serial_number)
                    if selected_military is None:
                        continue

                    total = r.rope_passed and r.obstacle_passed and r.running_time <= 7200

                    data.append({
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "speedmarsTime": _format_seconds(r.running_time),
                        "Speedmars Score": f"{r.running_time <= 7200}",
                        "ObstacleCourse": _is_passed(r.obstacle_passed),
                        "RobeCourse": _is_passed(r.rope_passed),

                        "Totale Score": f"{_is_passed(total)}",
                    })
                # Create DataFrame after collecting all data
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Error fetching PHEF data: {e}")
                return pd.DataFrame()

        def _is_passed(passed:bool)->str:
            if passed:
                return "Passed"
            else:
                return "Failed"

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
            score_cols = ["Running Score", "Sidebridge R Score", "Sidebridge L Score"]
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
        async def combat_grid():
            df = await sessions_combat__data()
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
            val = (input.combat_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.db.get_test_session_by_id(int(val))

        @reactive.Effect
        @reactive.event(input.combat_grid_selected_rows)
        async def _on_ph_row_selected():
            try:
                sel = input.combat_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row_idx = sel[0]
                df = await sessions_combat__data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return

                row = df.iloc[row_idx]
                selected_combat_id.set(row["ID"] or "")
                selected_session_id.set(input.combat_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = self.external_services.get_serviceman_by_serial(serial)
                oc = True if row.get("ObstacleCourse", None) == "Passed"  else False
                rc = True if row.get("RobeCourse") == "Passed" else False
                run_t = row.get("speedmarsTime", None)

                # Format to mm:ss where possible
                def fmt(x):
                    try:
                        return _format_seconds(int(x))
                    except Exception:
                        return ""

                ui.update_text("combat_serialnr", value=serial)
                ui.update_checkbox("combat_obstacle", value=oc)
                ui.update_checkbox("combat_robe", value=rc)
                ui.update_text("combat_speedmars", value=str(run_t))

                status.set(f"Selected Combat Test: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.combat_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            record = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],

                "combat_obstacle": res["combat_obstacle"],
                "combat_robe": res["combat_robe"],
                "combat_speedmars": res["combat_speedmars"],
            }
            cp = CombatTestParatrooper()
            cp.test_session_id = int(record["id"])
            cp.serial_number = record["serialnr"]
            cp.running_time = record["combat_speedmars"]
            cp.rope_passed = record["combat_robe"]
            cp.obstacle_passed = record["combat_obstacle"]

            added_combat = await self.db.add_fitness_test_to_TestSession(int(record["id"]), cp)
            if not added_combat:
                status.set(f"Failed to add Combat test for {cp.serial_number} in session {str(cp.test_session_id)}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])

            status.set(f"Added Combat test for {cp.serial_number} in session {str(cp.test_session_id)}.")
            _clear_form()

        # Helper to build a PhefTest from merged, validated input
        def _build_combat_from_form(payload: dict) -> CombatTestParatrooper:
            cp = CombatTestParatrooper()
            cp.id = selected_combat_id.get()
            cp.test_session_id = int(payload["session_id"])
            cp.serial_number = payload["serialnr"]
            cp.running_time = payload["combat_speedmars"]
            cp.obstacle_passed = payload["combat_obstacle"]
            cp.rope_passed = payload["combat_robe"]

            return cp

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
            combat:CombatTestParatrooper = _build_combat_from_form(payload)

            updated_combat:CombatTestParatrooper = await self.db.update_fitness_test(int(combat.id), combat)
            if not updated_combat:
                status.set(
                    f"Failed to update Combat test for {combat.serial_number} in session {str(combat.test_session_id)}."
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated Combat test for {combat.serial_number} in session {str(combat.test_session_id)}."
            )
            _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_delete_btn)
        async def _on_delete():
            sel = input.combat_grid_selected_rows()
            sel_session_id = input.combat_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            del_combat = await self.db.delete_fitness_test_from_test_session(int(sel_session_id),
                                                                           int(selected_combat_id.get()))
            if not del_combat:
                status.set(f"Failed to delete Combat test for record ID {sel[0]}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_combat__data()
                row_idx = sel[0]
                row = df.iloc[row_idx]
                status.set(f"Combat test for record ID {row['ID']} deleted successfully.")
            except Exception:
                status.set("Invalid selection.")

        @reactive.Effect
        @reactive.event(input.combat_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")


# Public API: keep same signatures
_page = CombatPage(DBService("ui/config/config.yml"))


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)