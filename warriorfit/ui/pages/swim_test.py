from shiny import ui, render, reactive
import pandas as pd


from warriorfit.data.model.db_model import TestSession, ServiceMen

from warriorfit.ui.controllers.swimming_controller import SwimmingController
from warriorfit.ui.pages.page import Page


class SwimTestPage(Page):
    def __init__(self,):

        self.refresh_tick = reactive.Value(0)

        self.selected_military: ServiceMen = None
        self.selected_session: TestSession = None
        self.controller = SwimmingController()

    NO_SELECTION_MESSAGE = "No row selected"

    def refresh(self):
        pass

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
                        ui.input_action_button("swim_search", "Conform Serial", width="150px"),
                        ui.output_text("swim_miltary"),
                        ui.layout_columns(
                            ui.input_checkbox("swim_passed", "Swimming Test Passed"),
                            ui.div("Status :", ui.output_ui("swim_status_display")),
                            col_widths=(8, 4),
                        ),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button(
                                "swim_add_btn", "Add", disabled=self.selected_military is None, width="150px", class_="btn-primary w-100"
                            ),
                            ui.input_action_button(
                                "swim_update_btn", "Update", disabled=self.selected_military is None, width="150px", class_="btn-warning w-100"
                            ),
                            ui.input_action_button("swim_clear_btn", "Clear Form", width="150px", class_="btn-secondary w-100"),
                            ui.input_action_button("swim_delete_btn", "Delete Selected", class_="btn-danger w-100"),
                            col_widths=(4,),
                        ),
                        ui.output_text("swim_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("Swimming Tests, This list shows not only members of own unit"),
                    ui.output_data_frame("swim_grid"),

                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        records = reactive.Value([])
        swim_passed_val = reactive.Value(False)
        military = reactive.Value("No selection")
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        selected_swim_id = reactive.Value("")

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
            _write_form({"serialnr": "", "swim_passed": False})

        async def _refresh_session_choices():
            sessions = await self.controller.load_sessions()
            items = {str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}" for s in (sessions or [])}
            current = (input.swim_session_id() or "").strip()
            selected = current if current in items else None
            ui.update_select("swim_session_id", choices=items, selected=selected)

        @reactive.effect
        @reactive.event(input.swim_search, ignore_none=False)
        async def swim_search():
            if not (input.swim_serialnr() or "").strip():
                ui.update_action_button("swim_add_btn", disabled=True)
                ui.update_action_button("swim_update_btn", disabled=True)
                return
            try:
                val = await self.controller.search_military(input.swim_serialnr() or "")
                self.selected_military = val
                if val is None:
                    ui.update_text("swim_serialnr", value="Not found")
                    return
                military.set(f"{val.rank} {val.service_number} {val.first_name} {val.last_name}")
                ui.update_action_button("swim_add_btn", disabled=False)
                ui.update_action_button("swim_update_btn", disabled=False)
            except Exception:
                ui.update_text("swim_serialnr", value="Not found")

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
                return await self.controller.list_swim_df(int(session_id))
            except Exception as e:
                print(f"Error fetching Swimming test data: {e}")
                return pd.DataFrame()

        @output
        @render.data_frame
        async def swim_grid():
            df = await sessions_swim_data()
            df = self.controller.decorate_grid(df)
            return render.DataGrid(df, filters=False, selection_mode="rows", width="100%",)

        @reactive.Effect
        async def _init():
            await _refresh_session_choices()

        @reactive.Effect
        async def _on_session_change():
            val = (input.swim_session_id() or "").strip()
            selected_session_id.set(val)
            if val:
                self.selected_session = await self.controller.get_session_by_id(int(val))
                status.set(f"Session is set to {val}")

        @reactive.Effect
        @reactive.event(input.swim_grid_selected_rows)
        async def _on_swim_row_selected():
            try:
                sel = input.swim_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    return
                ui.update_action_button("swim_add_btn", disabled=True)
                ui.update_action_button("swim_update_btn", disabled=True)
                row_idx = sel[0]
                df = await sessions_swim_data()
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    return

                row = df.iloc[row_idx]
                selected_swim_id.set(row["ID"] or "")
                selected_session_id.set(input.swim_session_id() or "")
                serial = str(row.get("Serial", "") or "")
                self.selected_military = await self.controller.search_military(serial)

                swim_passed = row.get("Result", "FAILED") == "PASSED"
                ui.update_text("swim_serialnr", value=serial)
                ui.update_checkbox("swim_passed", value=swim_passed)
                status.set(f"Selected Swimming Test: {serial}")
            except Exception as e:
                status.set(f"Selection error: {e}")

        def _validate(data):
            return self.controller.validate_form(data)

        @reactive.Effect
        @reactive.event(input.swim_add_btn)
        async def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return
            payload = {
                "id": data["session_id"],
                "serialnr": data["serialnr"],
                "swim_passed": res["swim_passed"],
            }
            added = await self.controller.add_swim(int(payload["id"]), payload,session=self.selected_session,military=self.selected_military)
            if not added:
                status.set(f"Failed to add Swimming test for {payload['serialnr']} in session {str(payload['id'])}.")
                return

            self.refresh_tick.set(self.refresh_tick.get() + 1)
            records.set(records.get() + [payload])
            status.set(f"Added Swimming test for {payload['serialnr']} in session {str(payload['id'])}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_update_btn)
        async def _on_update():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return
            payload = {**data, **res}
            updated = await self.controller.update_swim(int(selected_swim_id.get()), payload)
            if not updated:
                status.set(f"Failed to update Swimming test for {payload['serialnr']}.")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(f"Updated Swimming test for {payload['serialnr']}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.swim_delete_btn)
        async def _on_delete():
            sel = input.swim_grid_selected_rows()
            sel_session_id = input.swim_session_id()
            if not sel or not sel_session_id:
                status.set("Select a row to delete.")
                return
            ok = await self.controller.delete_swim(int(sel_session_id), int(selected_swim_id.get()))
            if not ok:
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


# Public API
_page = SwimTestPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)