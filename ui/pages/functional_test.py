from shiny import ui, render, reactive
import pandas as pd

from core.Gender import Gender
from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import FunctionalTest, TestSession
from logic.Functional_calculator import FunctionalCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService


class FunctionalPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = BEMILService()
        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None

    NO_SELECTION_MESSAGE = "No row selected"

    def get_ui(self):

            return ui.nav_panel(
                "Functional Tests",
                ui.h2("🧪 Functional Tests"),
                ui.layout_columns(
                    ui.div(
                        ui.card(
                            ui.card_header("Session"),
                            ui.input_select("functional_session_id", "Session", choices=[]),
                            full_screen=False,
                        ),
                        ui.card(
                            ui.input_text("functional_serialnr", "Serial Number"),
                            ui.input_action_button("functional_search", "search", width="150px"),
                            ui.output_text("functional_miltary", ),

                            ui.layout_columns(
                                ui.input_numeric(
                                    "functional_push_ups",
                                    "Push-ups",
                                    value=0,
                                    min=0,
                                ),
                                ui.div("Score :", ui.output_ui("functional_push_ups_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_numeric(
                                    "functional_sit_ups",
                                    "Sit-ups",
                                    value=0,
                                    min=0,
                                ),
                                ui.div("Score :", ui.output_ui("functional_sit_ups_score")),
                                col_widths=(8, 4),
                            ),

                            ui.layout_columns(
                                ui.input_numeric(
                                    "functional_pull_ups",
                                    "Pull-ups",
                                    value=0,
                                    min=0,
                                ),
                                ui.div("Score :", ui.output_ui("functional_pull_ups_score")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("functional_add_btn", "Add",
                                                       disabled=self.selected_military is None,
                                                       width="150px"),
                                ui.input_action_button("functional_update_btn", "Update",
                                                       disabled=self.selected_military is None,
                                                       width="150px"),
                                ui.input_action_button("functional_clear_btn", "Clear Form",
                                                       width="150px"),
                                col_widths=(4,),
                            ),
                            ui.output_text("functional_status", ),
                            ui.br(),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Functional Tests"),
                        ui.output_data_frame("functional_grid"),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("functional_delete_btn", "Delete Selected"),
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
        functional_score_push_ups_val = reactive.Value("")
        functional_score_sit_ups_val = reactive.Value("")
        functional_score_pull_ups_val = reactive.Value("")

        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        selected_functional_id = reactive.Value("")

        def _validate(data):
            if not (data["serialnr"] or "").strip():
                return False, "Serial number is required."

            try:
                push_ups = int(data["push_ups"])
                sit_ups = int(data["sit_ups"])
                pull_ups = int(data["pull_ups"])

                if push_ups < 0 or sit_ups < 0 or pull_ups < 0:
                    return False, "All exercise counts must be non-negative."

                return True, {
                    "push_ups": push_ups,
                    "sit_ups": sit_ups,
                    "pull_ups": pull_ups,
                }
            except ValueError:
                return False, "All exercise counts must be valid numbers."

        def _read_form():
            return {
                "serialnr": (input.functional_serialnr() or "").strip(),
                "session_id": (input.functional_session_id() or "").strip(),
                "push_ups": input.functional_push_ups(),
                "sit_ups": input.functional_sit_ups(),
                "pull_ups": input.functional_pull_ups(),
            }

        def _write_form(rec):
            session.send_input_message("functional_serialnr", {"value": rec.get("serialnr", "")})
            session.send_input_message("functional_push_ups", {"value": rec.get("push_ups", 0)})
            session.send_input_message("functional_sit_ups", {"value": rec.get("sit_ups", 0)})
            session.send_input_message("functional_pull_ups", {"value": rec.get("pull_ups", 0)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "push_ups": 0,
                "sit_ups": 0,
                "pull_ups": 0
            })

        async def _refresh_session_choices():
            test_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.FUNCTIONAL)
            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.functional_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("functional_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.functional_search, ignore_none=False)
        async def functional_search():
            if input.functional_serialnr() is None or input.functional_serialnr() == "":
                ui.update_action_button("functional_add_btn", disabled=True)
                ui.update_action_button("functional_update_btn", disabled=True)
                return
            try:
                val = await self.be_mil_service.get_be_mil_by_id(input.functional_serialnr() or "")
                self.selected_military = val
                military.set(val.rank + " " + val.service_number + " " + val.first_name + " " + val.last_name)
                ui.update_action_button("functional_add_btn", disabled=False)
                ui.update_action_button("functional_update_btn", disabled=False)
            except Exception as e:
                ui.update_text("functional_serialnr", value="Not found")
                return

        @output
        @render.text
        def functional_status():
            return status.get()

        @output
        @render.text
        def functional_miltary():
            return military.get()

        @output
        @render.text
        def functional_push_ups_score():
            val = functional_score_push_ups_val.get()
            try:
                if self.selected_military:
                    num = FunctionalCalculator.get_score_pushup(self.selected_military.gender, self.selected_military.age_from_birthdate(), int(val))
                else:
                    num = 0
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 20) else "green"
            return ui.span(str(num), style=f"color: {color};")

        @output
        @render.text
        def functional_sit_ups_score():
            val = functional_score_sit_ups_val.get()
            try:
                if self.selected_military:
                    num = FunctionalCalculator.get_score_situp(self.selected_military.gender,
                                                            self.selected_military.age_from_birthdate(), int(val))
                else:
                    num = 0
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 20) else "green"
            return ui.span(str(num), style=f"color: {color};")

        @output
        @render.text
        def functional_pull_ups_score():
            val = functional_score_pull_ups_val.get()
            try:
                if self.selected_military:
                    num = FunctionalCalculator.get_score_pullup(self.selected_military.gender, self.selected_military.age_from_birthdate(), int(val))
                else:
                    num = 0
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 20) else "green"
            return ui.span(str(num), style=f"color: {color};")

        @reactive.Effect
        @reactive.event(input.functional_push_ups)
        def on_push_ups_change():
            try:
                val = int(input.functional_push_ups() or 0)
                functional_score_push_ups_val.set(str(val))
            except Exception:
                functional_score_push_ups_val.set("")

        @reactive.Effect
        @reactive.event(input.functional_sit_ups)
        def on_sit_ups_change():
            try:
                val = int(input.functional_sit_ups() or 0)
                functional_score_sit_ups_val.set(str(val))
            except Exception:
                functional_score_sit_ups_val.set("")

        @reactive.Effect
        @reactive.event(input.functional_pull_ups)
        def on_pull_ups_change():
            try:
                val = int(input.functional_pull_ups() or 0)
                functional_score_pull_ups_val.set(str(val))
            except Exception:
                functional_score_pull_ups_val.set("")

        @reactive.calc
        async def sessions_functional_data():
            _ = self.refresh_tick.get()
            session_id = selected_session_id.get()
            if not session_id:
                return pd.DataFrame()
            try:
                functional_tests = await self.db.get_all_functional_test(int(session_id))
                data = []
                for r in functional_tests:
                    selected_military = await self.be_mil_service.get_be_mil_by_id(r.serial_number)
                    if selected_military is None:
                        continue
                    if isinstance(selected_military.gender,str):
                        if selected_military.gender.lower() == "m":
                            gender = Gender.MALE
                        else:
                            gender = Gender.FEMALE
                    else:
                        gender = selected_military.gender

                    pull = FunctionalCalculator.get_score_pullup(gender, selected_military.age_from_birthdate(), int(r.pull_ups))
                    situp = FunctionalCalculator.get_score_situp(gender, selected_military.age_from_birthdate(), int(r.sit_ups))
                    push =  FunctionalCalculator.get_score_pushup(gender, selected_military.age_from_birthdate(), int(r.push_ups))
                    total_score = ((pull + situp + push)/60)*100
                    data.append({
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "Push-ups": r.push_ups,
                        "Push-ups-score": push,
                        "Sit-ups": r.sit_ups,
                        "Sit-ups-score": situp,
                        "Pull-ups": r.pull_ups,
                        "Pull-ups-score": pull,
                        "Total Score": total_score,
                    })
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Error fetching Functional test data: {e}")
                return pd.DataFrame()

        def _decorate_scores_for_grid(df):
            if df.empty:
                return df

            df2 = df.copy()

            # Color code based on thresholds
            if "Total Score" in df2.columns:
                def _fmt_total(s):
                    try:
                        n = int(s)
                        return f"🟥 {s}" if n < 50 else f"🟩 {s}"
                    except Exception:
                        return s

                df2["Total Score"] = df2["Total Score"].apply(_fmt_total)

            return df2

        @output
        @render.data_frame
        async def functional_grid():
            df = await sessions_functional_data()
            df = _decorate_scores_for_grid(df)
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="rows",
            )

        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            val = (input.functional_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.db.get_test_session_by_id(int(val))
                status.set(f"Session is set to {val}")

        @reactive.Effect
        @reactive.event(input.functional_grid_selected_rows)
        async def _on_functional_row_selected():
            try:
                sel = input.functional_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row_idx = sel[0]
                df = await sessions_functional_data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return

                row = df.iloc[row_idx]
                selected_functional_id.set(row["ID"] or "")
                selected_session_id.set(input.functional_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.be_mil_service.get_be_mil_by_id(serial)

                push_ups = row.get("Push-ups", 0)
                sit_ups = row.get("Sit-ups", 0)
                pull_ups = row.get("Pull-ups", 0)

                ui.update_text("functional_serialnr", value=serial)
                ui.update_numeric("functional_push_ups", value=int(push_ups))
                ui.update_numeric("functional_sit_ups", value=int(sit_ups))
                ui.update_numeric("functional_pull_ups", value=int(pull_ups))

                status.set(f"Selected Functional Test: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.functional_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            record = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],
                "push_ups": res["push_ups"],
                "sit_ups": res["sit_ups"],
                "pull_ups": res["pull_ups"],
            }

            ft = FunctionalTest()
            ft.serial_number = record["serialnr"]
            ft.push_ups = record["push_ups"]
            ft.sit_ups = record["sit_ups"]
            ft.pull_ups = record["pull_ups"]

            added_functional = await self.db.add_fitness_test_to_TestSession(int(record["id"]), ft)
            if not added_functional:
                status.set(f"Failed to add Functional test for {ft.serial_number} in session {record['id']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])

            status.set(f"Added Functional test for {ft.serial_number} in session {record['id']}.")
            _clear_form()

        def _build_functional_from_form(payload: dict) -> FunctionalTest:
            ft = FunctionalTest()
            ft.id = int(selected_functional_id.get())
            ft.serial_number = payload["serialnr"]
            ft.push_ups = payload["push_ups"]
            ft.sit_ups = payload["sit_ups"]
            ft.pull_ups = payload["pull_ups"]
            return ft

        @reactive.Effect
        @reactive.event(input.functional_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            payload = {**data, **res}
            functional: FunctionalTest = _build_functional_from_form(payload)

            updated_functional: FunctionalTest = await self.db.update_fitness_test(int(functional.id), functional)
            if not updated_functional:
                status.set(
                    f"Failed to update Functional test for {functional.serial_number}."
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated Functional test for {functional.serial_number}."
            )
            _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_delete_btn)
        async def _on_delete():
            sel = input.functional_grid_selected_rows()
            sel_session_id = input.functional_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            del_functional = await self.db.delete_fitness_test_from_test_session(
                int(sel_session_id),
                int(selected_functional_id.get())
            )
            if not del_functional:
                status.set(f"Failed to delete Functional test for record ID {sel[0]}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_functional_data()
                row_idx = sel[0]
                row = df.iloc[row_idx] if row_idx < len(df) else None
                if row is not None:
                    status.set(f"Functional test for record ID {row['ID']} deleted successfully.")
                else:
                    status.set("Functional test deleted successfully.")
            except Exception:
                status.set("Functional test deleted successfully.")

        @reactive.Effect
        @reactive.event(input.functional_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")


# Public API: keep same signatures
_page = FunctionalPage(DBService("ui/config/config.yml"))


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)