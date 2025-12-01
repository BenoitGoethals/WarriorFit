from shiny import ui, render, reactive
import pandas as pd

from warriorfit.data.db.db_model import TestSession, ServiceMen
from warriorfit.logic.Functional_calculator import FunctionalCalculator

from warriorfit.services.military_service import MilitaryService

from warriorfit.ui.controllers.functional_controller import FunctionalController
from warriorfit.ui.pages.page import Page


class FunctionalPage(Page):
    def __init__(self,):

        self.refresh_tick = reactive.Value(0)
        self.be_mil_service = MilitaryService()
        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None
        self.controller = FunctionalController()

    NO_SELECTION_MESSAGE = "No row selected"

    def refresh(self):
        pass

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
                        ui.input_action_button("functional_search", "Conform Serial", width="150px"),
                        ui.output_text("functional_miltary"),
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
                            ui.div("Score :", ui.output_ui("functional_total_score")),
                            col_widths=(8, 4),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("functional_add_btn", "Add",
                                                   disabled=self.selected_military is None, width="150px", class_="btn-primary w-100"),
                            ui.input_action_button("functional_update_btn", "Update",
                                                   disabled=self.selected_military is None, width="150px", class_="btn-warning w-100"),
                            ui.input_action_button("functional_clear_btn", "Clear Form", width="150px", class_="btn-secondary w-100"),
                            ui.input_action_button("functional_delete_btn", "Delete Selected",
                                                   class_="btn-danger w-100"),
                            col_widths=(4,),
                        ),
                        ui.output_text("functional_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("Functional Tests : This list shows not only members of own Unit"),
                    ui.output_data_frame("functional_grid"),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        records = reactive.Value([])
        functional_score_push_ups_val = reactive.Value("")
        functional_score_sit_ups_val = reactive.Value("")
        functional_score_pull_ups_val = reactive.Value("")
        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        selected_functional_id = reactive.Value("")

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
            _write_form({"serialnr": "", "push_ups": 0, "sit_ups": 0, "pull_ups": 0})

        async def _refresh_session_choices():
            test_sessions = await self.controller.load_sessions()
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
            if not (input.functional_serialnr() or "").strip():
                ui.update_action_button("functional_add_btn", disabled=True)
                ui.update_action_button("functional_update_btn", disabled=True)
                return
            try:
                val = await self.controller.search_military(input.functional_serialnr() or "")
                self.selected_military = val
                if val is None:
                    ui.update_text("functional_serialnr", value="Not found")
                    return
                military.set(f"{val.rank} {val.service_number} {val.first_name} {val.last_name}")
                ui.update_action_button("functional_add_btn", disabled=False)
                ui.update_action_button("functional_update_btn", disabled=False)
            except Exception:
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
                    num = FunctionalCalculator.get_score_pushup(
                        self.selected_military.gender,
                        self.selected_military.age_from_birthdate(),
                        int(val),
                    )
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
                    num = FunctionalCalculator.get_score_situp(
                        self.selected_military.gender,
                        self.selected_military.age_from_birthdate(),
                        int(val),
                    )
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
                    num = FunctionalCalculator.get_score_pullup(
                        self.selected_military.gender,
                        self.selected_military.age_from_birthdate(),
                        int(val),
                    )
                else:
                    num = 0
            except (TypeError, ValueError):
                num = None
            color = "red" if (num is not None and num < 20) else "green"
            return ui.span(str(num), style=f"color: {color};")

        def _calculate_total_score(push_ups, sit_ups, pull_ups)->bool:
            try:
                push_ups_score = FunctionalCalculator.get_score_pushup(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    int(push_ups),
                )
                sit_ups_score = FunctionalCalculator.get_score_situp(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    int(sit_ups),
                )
                pull_ups_score = FunctionalCalculator.get_score_pullup(
                    self.selected_military.gender,
                    self.selected_military.age_from_birthdate(),
                    int(pull_ups),
                )
                return push_ups_score>10 or sit_ups_score>10 + pull_ups_score>10
            except (TypeError, ValueError):
                return False


        @output
        @render.text
        def functional_total_score():
            if self.selected_military:
                try:
                    if _calculate_total_score(functional_score_push_ups_val.get(), functional_score_sit_ups_val.get(), functional_score_pull_ups_val.get()):
                        return ui.span("PASSED", style="color: green; font-weight: bold;")
                    return ui.span( " FAILED", style="color: red; font-weight: bold;")
                except (TypeError, ValueError):
                    return ui.span("")
            return ui.span("")

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
                return await self.controller.list_functional_tests_df(int(session_id))
            except Exception as e:
                print(f"Error fetching Functional test data: {e}")
                return pd.DataFrame()

        @output
        @render.data_frame
        async def functional_grid():
            df = await sessions_functional_data()
            df = self.controller.decorate_grid(df)
            return render.DataGrid(df, filters=False, selection_mode="rows", width="100%",)

        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            val = (input.functional_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.controller.get_session_by_id(int(val))
                status.set(f"Session is set to {val}")

        @reactive.Effect
        @reactive.event(input.functional_grid_selected_rows)
        async def _on_functional_row_selected():
            try:
                sel = input.functional_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                ui.update_action_button("functional_add_btn", disabled=True)
                ui.update_action_button("functional_update_btn", disabled=True)
                row_idx = sel[0]
                df = await sessions_functional_data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return

                row = df.iloc[row_idx]
                selected_functional_id.set(row["ID"] or "")
                selected_session_id.set(input.functional_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.controller.search_military(serial)

                ui.update_text("functional_serialnr", value=serial)
                ui.update_numeric("functional_push_ups", value=int(row.get("Push-ups", 0)))
                ui.update_numeric("functional_sit_ups", value=int(row.get("Sit-ups", 0)))
                ui.update_numeric("functional_pull_ups", value=int(row.get("Pull-ups", 0)))

                status.set(f"Selected Functional Test: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        @reactive.Effect
        @reactive.event(input.functional_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = self.controller.validate_form(data)
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

            added_functional = await self.controller.add_functional(int(record["id"]), record,session=self.selected_session,military=self.selected_military)
            if not added_functional:
                status.set(f"Failed to add Functional test for {record['serialnr']} in session {record['id']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])
            status.set(f"Added Functional test for {record['serialnr']} in session {record['id']}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = self.controller.validate_form(data)
            if not ok:
                status.set(res)
                return

            payload = {**data, **res}
            updated_functional = await self.controller.update_functional(int(selected_functional_id.get()), payload)
            if not updated_functional:
                status.set(f"Failed to update Functional test for {payload['serialnr']}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated Functional test for {payload['serialnr']}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.functional_delete_btn)
        async def _on_delete():
            sel = input.functional_grid_selected_rows()
            sel_session_id = input.functional_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            ok = await self.controller.delete_functional(int(sel_session_id), int(selected_functional_id.get()))
            if not ok:
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
_page = FunctionalPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)