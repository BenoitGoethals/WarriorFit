import datetime
from typing import Optional, Dict, Any, List

import pandas as pd
from shiny import reactive, ui, render

from config.appliccation_config import ApplicationConfig
from core.role import Role
from core.type_fitness_test import TypeFitnessTest
from services.be_mil_service import BEMILService

from services.mail_service import MailService
from ui.controllers.session_controller import SessionsController


class SessionsPage:
    SESSION_TYPES = [r.name for r in TypeFitnessTest]
    ROLES = [r.name for r in Role]

    NO_SELECTION_MESSAGE = "No row selected"

    def __init__(self, ) -> None:
        self.be_mil_service = BEMILService()
        self.refresh_tick = reactive.Value(0)
        self.controller = SessionsController()

    def _validate(self, data: Dict[str, Any]) -> tuple[bool, str]:
        if not data["datetime_start"]:
            return False, "Date and time are required."
        if not (data["type_test"] or "").strip():
            return False, "Type is required."
        if data["type_test"] not in self.SESSION_TYPES:
            return False, "Invalid session type."
        return True, "OK"



    def get_ui(self):
        return ui.nav_panel(
            "Sessions",
            ui.h2("📅 Test Sessions"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Create / Edit Session"),
                    ui.input_select("se_serial", "Serial Number PTI", choices=[]),
                    ui.input_date("se_date", "Date"),
                    ui.input_text("se_time", "Time (HH:MM)", placeholder="HH:MM", value="09:00"),
                    ui.input_select("se_type", "Type", choices=self.SESSION_TYPES),
                    ui.input_checkbox("se_executed", "Executed", value=False),
                    ui.input_text_area("se_description", "Description", rows=3, width="400px"),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button("se_add_btn", "Add"),
                        ui.input_action_button("se_update_btn", "Update"),
                        ui.input_action_button("se_clear_btn", "Clear Form"),
                        col_widths=(3, 4, 4),
                    ),
                    ui.br(),
                    ui.output_text("se_status"),
                    ui.output_text("selected_session"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header("Sessions"),
                    ui.output_data_frame("se_grid"),
                    ui.layout_columns(
                        ui.input_action_button("se_delete_btn", "Delete Selected"),
                        col_widths=(6, 3, 3),
                    ),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
        )


    def server(self, input, output, session):
        sessions = reactive.Value([])
        next_id = reactive.Value(1)
        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")
        async def all_pti() -> List[str]:
            return await self.controller.get_all_pti_serials()

        async def _populate_pti_choices():
            try:
                choices = await all_pti()
                ui.update_select("se_serial", choices=choices, selected=None)
            except Exception:
                ui.update_select("se_serial", choices=[], selected=None)

        @reactive.Effect
        async def _populate_pti_choices_effect():
            await _populate_pti_choices()

        async def _load_initial():
            items = await self.controller.list_sessions()

            def _to_dict_session(r: Any) -> Dict[str, Any]:
                return {
                    "id": getattr(r, "id", None),
                    "serial_number_pti": getattr(r, "serial_number_pti", None),
                    "datetime_start": getattr(r, "datetime_start", None),
                    "executed": bool(getattr(r, "executed", False)),
                    "description": getattr(r, "description", None),
                    "type_test": getattr(getattr(r, "type_test", None), "name", getattr(r, "type_test", None)),
                }

            converted = [_to_dict_session(r) for r in items]
            sessions.set(converted)
            try:
                max_id = max((rec["id"] for rec in converted if rec["id"] is not None), default=0)
            except ValueError:
                max_id = 0
            next_id.set(max_id + 1)
            return pd.DataFrame(
                [
                    {
                        "ID": r.get("id", ""),
                        "Type": r.get("type_test", "") or "",
                        "Start": r.get("datetime_start", "") or "",
                        "Description": r.get("description", "") or "",
                        "Serial PTI": r.get("serial_number_pti", "") or "",
                        "Executed": "Yes" if r.get("executed", False) else "No",
                    }
                    for r in converted
                ]
            )

        def _read_form() -> Dict[str, Any]:
            dt_date = input.se_date()
            dt_time = input.se_time()
            dt = None
            if dt_date and dt_time:
                try:
                    if isinstance(dt_time, str):
                        parts = [int(x) for x in dt_time.split(":")]
                        while len(parts) < 3:
                            parts.append(0)
                        t = datetime.time(parts[0], parts[1], parts[2])
                    else:
                        t = dt_time
                    dt = datetime.datetime.combine(dt_date, t)
                except Exception:
                    dt = None
            return {
                "serial_number_pti": (input.se_serial() or "").strip() or None,
                "datetime_start": dt,
                "executed": bool(input.se_executed()),
                "description": (input.se_description() or "").strip() or None,
                "type_test": (input.se_type() or "").strip(),
            }

        def _write_form(rec: Dict[str, Any]):
            dt = rec.get("datetime_start", None)
            dt_date = dt.date() if isinstance(dt, datetime.datetime) else None
            dt_time = dt.time().strftime("%H:%M:%S") if isinstance(dt, datetime.datetime) else None
            session.send_input_message("se_serial", {"value": rec.get("serial_number_pti", "") or ""})
            session.send_input_message("se_date", {"value": dt_date})
            session.send_input_message("se_time", {"value": dt_time})
            session.send_input_message("se_type", {"value": rec.get("type_test", "")})
            session.send_input_message("se_executed", {"value": bool(rec.get("executed", False))})
            session.send_input_message("se_description", {"value": rec.get("description", "") or ""})

        async def _clear_form():
            await _populate_pti_choices()
            ui.update_date("se_date", label="Date", value=None)
            ui.update_text("se_time", value="09:00")
            ui.update_select("se_type", choices=self.SESSION_TYPES)
            ui.update_checkbox("se_executed", value=False)
            ui.update_text_area("se_description", value="")
            self.selected_row = None


        async def _refresh_select():
            items = sessions.get() or []
            choices = {
                str(r["id"]): f'{r["id"]}: {r.get("type_test","")} ({r.get("datetime_start","")})'
                for r in items
                if r.get("id") is not None
            }
            session.send_input_message("se_select_id", {"choices": choices, "selected": None})

        @output
        @render.text
        def se_status():
            return status.get()

        @reactive.calc
        async def session_list():
            _ = self.refresh_tick.get()
            return await self.controller.list_sessions_df()

        @output
        @render.data_frame
        async def se_grid():
            df = await session_list()
            df = df.drop(columns=["ID"])
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="row",
                width="100%",
            )

        @output
        @render.text
        async def selected_session():
            sel = input.se_grid_selected_rows()  # list of row indices
            if not sel:
                return self.NO_SELECTION_MESSAGE
            row_idx = sel[0]
            df = await _load_initial()
            if row_idx < 0 or row_idx >= len(df):
                return self.NO_SELECTION_MESSAGE
            row = df.iloc[row_idx]
            selected_session_id.set(row["ID"] or "")
            choices = await all_pti()
            serial = str(row["Serial PTI"])
            ui.update_select("se_serial", choices=choices, selected=serial)
            start_dt = row["Start"]
            try:
                date_value = start_dt.date()
            except Exception:
                date_value = None
            ui.update_date("se_date", label="Date", value=date_value)
            ui.update_text("se_time",
                           value=start_dt.strftime("%H:%M") if getattr(start_dt, "strftime", None) else "09:00")
            type_raw = str(row["Type"]).strip()
            ui.update_select("se_type", choices=self.SESSION_TYPES, selected=type_raw)
            ui.update_checkbox("se_executed", value=(str(row["Executed"]).strip().lower() == "yes"))
            ui.update_text_area("se_description", value=str(row["Description"]))



            return f"Selected session ID: {row['ID']}"

        @reactive.Effect
        async def _init_select():
            await _load_initial()
            await _refresh_select()

        @reactive.Effect
        @reactive.event(input.se_add_btn)
        async def _on_add():
            data = _read_form()
            ok, msg = self._validate(data)
            if not ok:
                status.set(msg)
                return
            try:
                added = await self.controller.add_session(data)
                if not added:
                    status.set("Failed to add session.")
                    return

            except Exception as e:
                status.set(f"Error adding session: {str(e)}")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set("Session added successfully.")
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.se_load_btn)
        def _on_load():
            sel = input.se_select_id()
            if not sel:
                status.set("Select a session to load.")
                return
            sel_id = int(sel)
            rec = next((r for r in (sessions.get() or []) if r.get("id") == sel_id), None)
            if not rec:
                status.set("Selected session not found.")
                return
            _write_form(rec)
            status.set(f"Loaded session #{sel_id}.")

        @reactive.Effect
        @reactive.event(input.se_update_btn)
        async def _on_update():
            payload = _read_form()
            ok, msg = self._validate(payload)
            if not ok:
                status.set(msg)
                return
            updated_ok = await self.controller.update_session(int(selected_session_id.get()), payload)
            if not updated_ok:
                status.set("Failed to update session.")
                return



            await _refresh_select()
            await _clear_form()
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.se_delete_btn)
        async def _on_delete():
            selected_id = input.se_grid_selected_rows()[0]
            if not selected_id:
                status.set("Select a session to delete.")
                return
            ok = await self.controller.delete_session(int(selected_session_id.get()))
            if not ok:
                status.set("Failed to delete session.")
                return
            status.set(f"Deleted session #{selected_id}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            await _refresh_select()
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.se_clear_btn)
        async def _on_clear():
            await _clear_form()
            status.set("Form cleared.")




_page_instance: Optional[SessionsPage] = None


def _get_page() -> SessionsPage:
    global _page_instance
    if _page_instance is None:
        _page_instance = SessionsPage()
    return _page_instance


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)


def get_sessions_store():
    return [None]