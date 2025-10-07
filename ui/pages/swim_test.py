from shiny import ui, render, reactive
import pandas as pd

from core.Gender import Gender
from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import CombatSwimmingTest, TestSession
from ui.services.db_service import DBService
from ..services.be_mil_service import BEMILService
from ..services.defense_external_service import DefenseExternalService
from ..user_store import UserStore


class SwimTestPage:
    def __init__(self, db: DBService):
        self.db = db
        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = BEMILService()
        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None

    NO_SELECTION_MESSAGE = "No row selected"

    def get_ui(self):

            return ui.nav_panel(
                "Swimming Tests",
                ui.h2("🏊 Swimming Tests"),
                ui.layout_columns(
                    ui.div(
                        ui.card(
                            ui.card_header("Session"),
                            ui.input_select("swim_session_id", "Session", choices=[]),
                            full_screen=False,
                        ),
                        ui.card(
                            ui.input_text("swim_serialnr", "Serial Number"),
                            ui.input_action_button("swim_search", "search", width="150px"),
                            ui.output_text("swim_miltary", ),

                            ui.layout_columns(
                                ui.input_checkbox(
                                    "swim_passed",
                                    "Swimming Test Passed",
                                ),
                                ui.div("Status :", ui.output_ui("swim_status_display")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("swim_add_btn", "Add",
                                                       disabled=self.selected_military is None,
                                                       width="150px"),
                                ui.input_action_button("swim_update_btn", "Update",
                                                       disabled=self.selected_military is None,
                                                       width="150px"),
                                ui.input_action_button("swim_clear_btn", "Clear Form",
                                                       width="150px"),
                                col_widths=(4,),
                            ),
                            ui.output_text("swim_status", ),
                            ui.br(),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Swimming Tests"),
                        ui.output_data_frame("swim_grid"),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("swim_delete_btn", "Delete Selected"),
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
        swim_passed_val = reactive.Value(False)

        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        selected_swim_id = reactive.Value("")

        def _validate(data):
            if not (data["serialnr"] or "").strip():
                return False, "Serial number is required."

            return True, {
                "swim_passed": data["swim_passed"],
            }

        def _read_form():
            return {
                "serialnr": (input.swim_serialnr() or "").strip(),
                "session_id": (input.swim_session_id() or "").strip(),
                "swim_passed": input.swim_passed(),
            }

        def _write_form(rec):
            session.send_input_message("swim_serialnr", {"value": rec.get("serialnr", "")})
            session.send_input_message("swim_passed", {"value": rec.get("swim_passed", False)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "swim_passed": False
            })

        async def _refresh_session_choices():
            test_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.SWIMMING)
            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.swim_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("swim_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.swim_search, ignore_none=False)
        async def swim_search():
            if input.swim_serialnr() is None or input.swim_serialnr() == "":
                ui.update_action_button("swim_add_btn", disabled=True)
                ui.update_action_button("swim_update_btn", disabled=True)
                return
            try:
                val = await self.be_mil_service.get_be_mil_by_id(input.swim_serialnr() or "")
                self.selected_military = val
                military.set(val.rank + " " + val.service_number + " " + val.first_name + " " + val.last_name)
                ui.update_action_button("swim_add_btn", disabled=False)
                ui.update_action_button("swim_update_btn", disabled=False)
            except Exception as e:
                ui.update_text("swim_serialnr", value="Not found")
                return

        @output
        @render.text
        def swim_status():
            return status.get()

        @output
        @render.text
        def swim_miltary():
            return military.get()

        @output
        @render.text
        def swim_status_display():
            val = swim_passed_val.get()
            text = "PASSED" if val else "FAILED"
            color = "green" if val else "red"
            return ui.span(text, style=f"color: {color}; font-weight: bold;")

        @reactive.Effect
        @reactive.event(input.swim_passed)
        def on_swim_passed_change():
            swim_passed_val.set(input.swim_passed())

        @reactive.calc
        async def sessions_swim_data():
            _ = self.refresh_tick.get()
            session_id = selected_session_id.get()
            if not session_id:
                return pd.DataFrame()
            try:
                swim_tests = await self.db.get_all_combat_swimming_test(int(session_id))
                data = []
                for r in swim_tests:
                    selected_military = await self.be_mil_service.get_be_mil_by_id(r.serial_number)
                    if selected_military is None:
                        continue

                    data.append({
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "Name": f"{selected_military.first_name} {selected_military.last_name}",
                        "Result": "PASSED" if r.swim_paased else "FAILED",
                    })
                return pd.DataFrame(data)
            except Exception as e:
                print(f"Error fetching Swimming test data: {e}")
                return pd.DataFrame()

        def _decorate_scores_for_grid(df):
            if df.empty:
                return df

            df2 = df.copy()

            # Color code results
            if "Result" in df2.columns:
                def _fmt_result(s):
                    if s == "PASSED":
                        return f"🟩 {s}"
                    else:
                        return f"🟥 {s}"

                df2["Result"] = df2["Result"].apply(_fmt_result)

            return df2

        @output
        @render.data_frame
        async def swim_grid():
            df = await sessions_swim_data()
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
            val = (input.swim_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.db.get_test_session_by_id(int(val))
                status.set(f"Session is set to {val}")

        @reactive.Effect
        @reactive.event(input.swim_grid_selected_rows)
        async def _on_swim_row_selected():
            try:
                sel = input.swim_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row_idx = sel[0]
                df = await sessions_swim_data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return

                row = df.iloc[row_idx]
                selected_swim_id.set(row["ID"] or "")
                selected_session_id.set(input.swim_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.be_mil_service.get_be_mil_by_id(serial)

                swim_passed = row.get("Result", "FAILED") == "PASSED"

                ui.update_text("swim_serialnr", value=serial)
                ui.update_checkbox("swim_passed", value=swim_passed)

                status.set(f"Selected Swimming Test: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.swim_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            record = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],
                "swim_passed": res["swim_passed"],
            }

            st = CombatSwimmingTest()
            st.serial_number = record["serialnr"]
            st.swim_paased = record["swim_passed"]

            added_swim = await self.db.add_fitness_test_to_TestSession(int(record["id"]), st)
            if not added_swim:
                status.set(f"Failed to add Swimming test for {st.serial_number} in session {record['id']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])

            status.set(f"Added Swimming test for {st.serial_number} in session {record['id']}.")
            _clear_form()

        def _build_swim_from_form(payload: dict) -> CombatSwimmingTest:
            st = CombatSwimmingTest()
            st.id = int(selected_swim_id.get())
            st.serial_number = payload["serialnr"]
            st.swim_paased = payload["swim_passed"]
            return st

        @reactive.Effect
        @reactive.event(input.swim_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            payload = {**data, **res}
            swim_test: CombatSwimmingTest = _build_swim_from_form(payload)

            updated_swim: CombatSwimmingTest = await self.db.update_fitness_test(int(swim_test.id), swim_test)
            if not updated_swim:
                status.set(
                    f"Failed to update Swimming test for {swim_test.serial_number}."
                )
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated Swimming test for {swim_test.serial_number}."
            )
            _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_delete_btn)
        async def _on_delete():
            sel = input.swim_grid_selected_rows()
            sel_session_id = input.swim_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            del_swim = await self.db.delete_fitness_test_from_test_session(
                int(sel_session_id),
                int(selected_swim_id.get())
            )
            if not del_swim:
                status.set(f"Failed to delete Swimming test for record ID {sel[0]}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_swim_data()
                row_idx = sel[0]
                row = df.iloc[row_idx] if row_idx < len(df) else None
                if row is not None:
                    status.set(f"Swimming test for record ID {row['ID']} deleted successfully.")
                else:
                    status.set("Swimming test deleted successfully.")
            except Exception:
                status.set("Swimming test deleted successfully.")

        @reactive.Effect
        @reactive.event(input.swim_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")


# Public API: keep same signatures
_page = SwimTestPage(DBService("ui/config/config.yml"))


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)