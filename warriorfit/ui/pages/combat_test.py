from shiny import ui, render, reactive
import pandas as pd


from warriorfit.data.db.db_model import TestSession, ServiceMen

from warriorfit.ui.controllers.combat_controller import CombatController
from warriorfit.ui.pages.page import Page


class CombatPage(Page):
    def __init__(self):

        self.refresh_tick = reactive.Value(0)

        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None
        self.controller = CombatController()  # <-- controller instance

    NO_SELECTION_MESSAGE = "No row selected"

    def refresh(self):
        pass

    def get_ui(self):
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
                            ui.input_action_button("combat_search", "Conform Serial", width="150px"),
                            ui.output_text("combat_military", ),

                            ui.layout_columns(
                                ui.input_checkbox(
                                    "combat_obstacle",
                                    "Obstacle course",
                                ),                               
                            ),

                            ui.layout_columns(
                                ui.input_checkbox(
                                    "combat_robe",
                                    "Robe Cours",
                                ),
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
                            ui.layout_columns(
                                ui.div("Score :", ui.output_ui("combat_total_score")),
                                col_widths=(8, 4),
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("combat_add_btn", "Add", disabled=self.selected_military is None,
                                                       width="150px", class_="btn-primary w-100"),
                                ui.input_action_button("combat_update_btn", "Update",
                                                       disabled=self.selected_military is None, width="150px", class_="btn-warning w-100"),
                                ui.input_action_button("combat_clear_btn", "Clear Form", width="150px", class_="btn-secondary w-100"),
                                ui.input_action_button("combat_delete_btn", "Delete Selected",
                                                       class_="btn-danger w-100"),
                                col_widths=(4,),
                            ),
                            ui.output_text("combat_status", ),
                            ui.br(),
                            #    ui.output_text("ph_status"),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Combat Tests  (To pass the combat test, you must pass all test)"),
                        ui.output_data_frame("combat_grid"),

                        full_screen=False,
                    ),
                    col_widths=(4, 8),  # Records occupies ~2/3 width
                ),
            )


    def server(self, input, output, session):
        # Reactive state
        records = reactive.Value([])        
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
        selected_session_id = reactive.Value("")
        selected_combat_id = reactive.Value("")

        def _parse_time_to_seconds(val: str):
            return self.controller.parse_time_to_seconds(val)

        def _format_seconds(sec: float | int):
            return self.controller.format_seconds(sec)

        def _validate(data):
            return self.controller.validate_form(data)

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
            cr_val = rec.get("combat_robe")
            co_val = rec.get("combat_obstacle")
            speedmars_val = rec.get("speedmars_s")
            session.send_input_message("combat_obstacle", {"value":  co_val })
            session.send_input_message("combat_robe", {"value": cr_val})
            session.send_input_message("combat_speedmars", {"value": "" if speedmars_val is None else _format_seconds(speedmars_val)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "combat_obstacle": False,
                "combat_robe": False,
                "combat_speedmars": None
            })

        async def _refresh_session_choices():
            test_sessions = await self.controller.load_sessions()
            items = {
                str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
                for s in (test_sessions or [])
            }
            current = (input.ph_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("combat_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.combat_search, ignore_none=False)
        async def combat_search():
            if input.combat_serialnr() is None or input.combat_serialnr() == "":
                ui.update_action_button("combat_add_btn", disabled=True)
                ui.update_action_button("combat_update_btn", disabled=True)
                return
            val = await self.controller.search_military(input.combat_serialnr() or "")
            self.selected_military = val
            if val is None:
                ui.update_text("combat_serialnr", value="Not found")
                return
            military.set(
                f"{val.rank} {val.service_number} {val.first_name} {val.last_name} {val.gender} {val.age_from_birthdate()} years old")
            ui.update_action_button("combat_add_btn", disabled=False)
            ui.update_action_button("combat_update_btn", disabled=False)


        @output
        @render.text
        def combat_status():
            return status.get()

        @output
        @render.text
        def combat_military():
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

        @output
        @render.text
        def combat_total_score():
            try:
                speedmars = combat_score_speedmars_val.get()
                if speedmars == "Passes" and input.combat_robe() and input.combat_obstacle():
                    return ui.span("Passed", style="color: green; font-weight: bold;")
                return ui.span("Failed", style="color: red; font-weight: bold;")
            except (TypeError, ValueError):
                return ui.span("")

        @reactive.Effect
        @reactive.event(input.combat_speedmars)
        def combat_speedmars():
            raw = (input.combat_speedmars() or "").strip()
            ok, val = _parse_time_to_seconds(raw)
            if not ok:
                combat_score_speedmars_val.set("")
                return
            try:
                score = "Passes" if val < 2400 else "Fails"
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
                return await self.controller.list_combat_tests_df(int(session_id))
            except Exception:
                return pd.DataFrame()

        @output
        @render.data_frame
        async def combat_grid():
            df = await sessions_combat__data()
            df = self.controller.decorate_grid(df)
            return render.DataGrid(
                df,
                filters=False,
                selection_mode="rows",
                width="100%",
            )

        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            val = (input.combat_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.controller.get_test_session_by_id(int(val))

        @reactive.Effect
        @reactive.event(input.combat_grid_selected_rows)
        async def _on_ph_row_selected():
            try:
                sel = input.combat_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                ui.update_action_button("combat_add_btn", disabled=True)
                ui.update_action_button("combat_update_btn", disabled=True)
                row_idx = sel[0]
                df = await sessions_combat__data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                row = df.iloc[row_idx]
                selected_combat_id.set(row["ID"] or "")
                selected_session_id.set(input.combat_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.controller.search_military(serial)
                oc = True if row.get("ObstacleCourse", None) == "Passed"  else False
                rc = True if row.get("RobeCourse") == "Passed" else False
                run_t = row.get("speedmarsTime", None)
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
            added = await self.controller.add_combat(int(record["id"]), record, session=self.selected_session,military=self.selected_military)
            if not added:
                status.set(f"Failed to add Combat test for {record['serialnr']} in session {str(record['id'])}.")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [record])
            status.set(f"Added Combat test for {record['serialnr']} in session {str(record['id'])}.")
            _clear_form()



        @reactive.Effect
        @reactive.event(input.combat_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            updated = await self.controller.update_combat(int(selected_combat_id.get()), payload)
            if not updated:
                status.set(
                    f"Failed to update Combat test for {payload['serialnr']} in session {str(payload['session_id'])}."
                )
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(
                f"Updated Combat test for {payload['serialnr']} in session {str(payload['session_id'])}."
            )
            _clear_form()

        @reactive.Effect
        @reactive.event(input.combat_delete_btn)
        async def _on_delete():
            sel = input.combat_grid_selected_rows()
            sel_session_id = input.combat_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            ok = await self.controller.delete_combat(int(sel_session_id), int(selected_combat_id.get()))
            if not ok:
                status.set(f"Failed to delete Combat test for record ID {sel[0]}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            try:
                df = await sessions_combat__data()
                row_idx = sel[0]
                row = df.iloc[row_idx]
                status.set(f"Combat test for record ID {row['ID']} deleted successfully.")
            except Exception:
                status.set("Invalid selection.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.combat_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")

_page = CombatPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)