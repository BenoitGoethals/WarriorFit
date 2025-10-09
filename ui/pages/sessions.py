from typing import List, Optional, Dict, Any

from shiny import ui, render, reactive

from data.db.db_model import TestSession,Role

import datetime
import pandas as pd

from core.type_fitness_test import TypeFitnessTest
from services.db_service import DBService


class SessionsPage:
    SESSION_TYPES = [r.name for r in TypeFitnessTest]
    ROLES = [r.name for r in Role]

    NO_SELECTION_MESSAGE = "No row selected"

    def __init__(self, db_service: DBService) -> None:
        # Allow DI for testing; default to app config path
        self.db_service = db_service
        self.refresh_tick = reactive.Value(0)
        self.selected_id = reactive.Value(None)
        # Hold the currently selected row (as a dict) for reuse by update/delete
        self.selected_row: Optional[Dict[str, Any]] = None

    def _validate(self, data: Dict[str, Any]) -> tuple[bool, str]:
        # Ensure required fields and valid type
        if not data["datetime_start"]:
            return False, "Date and time are required."
        if not (data["type_test"] or "").strip():
            return False, "Type is required."
        if data["type_test"] not in self.SESSION_TYPES:
            return False, "Invalid session type."
        return True, "OK"

    def _set_selected(self, row: Dict[str, Any]) -> None:
        """
        Track the selected grid row.
        - row: a dictionary with keys like ID, Type, Start, Serial PTI, Executed, Description
        """
        # Keep both an ID and the full row payload for later use
        self.selected_row = {
            "ID": row.get("ID"),
            "Type": row.get("Type"),
            "Start": row.get("Start"),
            "Serial PTI": row.get("Serial PTI"),
            "Executed": row.get("Executed"),
            "Description": row.get("Description"),
        }
        # Sync the reactive ID for any reactive dependencies
        self.selected_id.set(self.selected_row["ID"])

    # ---------- UI ----------
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

    # ---------- Server ----------
    def server(self, input, output, session):
        # Stored as list of dicts with TestSession attributes:
        # {id, serial_number_pti, datetime_start, executed, description, type_test}
        sessions = reactive.Value([])
        next_id = reactive.Value(1)
        status = reactive.Value("Ready.")

        async def all_pti() -> List[str]:
            pts = await self.db_service.get_all_pti()
            return [p.serial_number for p in pts]

        # Populate the Serial Number select once the page/server mounts
        async def _populate_pti_choices():
            # Plain async function that can be awaited from anywhere
            try:
                choices = await all_pti()
                ui.update_select("se_serial", choices=choices, selected=None)
            except Exception:
                ui.update_select("se_serial", choices=[], selected=None)

        @reactive.Effect
        async def _populate_pti_choices_effect():
            # Effect to populate choices on startup
            await _populate_pti_choices()

        async def _load_initial():
            items = await self.db_service.get_all_test_sessions()

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
            # Combine date + time into a single datetime
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
            # Refresh PTI choices and reset the form fields
            await _populate_pti_choices()
            ui.update_date("se_date", label="Date", value=None)
            ui.update_text("se_time", value="09:00")
            ui.update_select("se_type", choices=self.SESSION_TYPES)
            ui.update_checkbox("se_executed", value=False)
            ui.update_text_area("se_description", value="")
            # Reset tracked selection
            self.selected_row = None
            self.selected_id.set(None)

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
            # Make this calc depend on refresh_tick so it re-runs after add/update/delete
            _ = self.refresh_tick.get()
            items = await self.db_service.get_all_test_sessions()
            df = pd.DataFrame(
                [
                    {
                        "ID": r.id,
                        "Type": str(r.type_test.name),
                        "Start": str(r.datetime_start),
                        "Description": r.description,
                        "Serial PTI": r.serial_number_pti,
                        "Executed": "Yes" if r.executed else "No",
                    }
                    for r in items
                ]
            )
            return df

        @output
        @render.data_frame
        async def se_grid():
            df = await session_list()
            df = df.drop(columns=["ID"])
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="rows",
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

            # Track full selection for update/delete flows
            self._set_selected({
                "ID": row["ID"],
                "Type": row["Type"],
                "Start": row["Start"],
                "Serial PTI": row["Serial PTI"],
                "Executed": row["Executed"],
                "Description": row["Description"],
            })

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
            test_session = TestSession()
            # Map type string to Enum; fallback to default if unknown
            try:
                enum_type = getattr(TypeFitnessTest, str(data["type_test"]).upper())
            except Exception:
                enum_type = TypeFitnessTest.PHEF

            test_session.serial_number_pti = data["serial_number_pti"]
            test_session.datetime_start = data["datetime_start"]
            test_session.executed = bool(data["executed"])
            test_session.description = data["description"]
            test_session.type_test = enum_type

            try:
                added = await self.db_service.add_test_session(test_session)
                if not added:
                    status.set("Failed to add session.")
                    return
                self.refresh_tick = reactive.Value(0)
                #render.DataGrid(await session_list(),selection_mode="rows")
                next_id.set(next_id.get() + 1)
                sessions.set(
                    sessions.get() + [
                        {
                            "id": added.id,
                            "serial_number_pti": added.serial_number_pti,
                            "datetime_start": added.datetime_start,
                            "executed": added.executed,
                            "description": added.description,
                        }
                    ]
                )
                status.set("Session added successfully.")
            except Exception as e:
                status.set(f"Error adding session: {str(e)}")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self.selected_id.set(None)
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
            # Use the tracked selected row stored by selected()
            sel_row = self.selected_row
            if not sel_row or not sel_row.get("ID"):
                status.set("Select a session to update.")
                return
            sel_id = int(sel_row["ID"])
            data_form = _read_form()
            ok, msg = self._validate(data_form)
            if not ok:
                status.set(msg)
                return
            data = TestSession(type_test=data_form["type_test"],
                               serial_number_pti=data_form["serial_number_pti"],
                               datetime_start=data_form["datetime_start"],
                               executed=bool(data_form["executed"]),
                               description=data_form["description"],
                               id=sel_id,
                               )
            updated = await self.db_service.update_test_session(data)
            if not updated:
                status.set("Failed to update session.")
                return

            status.set(f"Updated session #{sel_id}.")
            # Bump refresh tick to trigger session_list and re-render se_grid
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.se_delete_btn)
        async def _on_delete():
            # Use the tracked selected row stored by selected()
            selected_id = self.selected_id.get()
            if not selected_id:
                status.set("Select a session to delete.")
                return
            status_deleted = await self.db_service.delete_test_session(selected_id)
            if not status_deleted:
                status.set("Failed to delete session.")
                return
            status.set(f"Deleted session #{selected_id}.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self.selected_id.set(None)
            await _refresh_select()
            await _clear_form()


        @reactive.Effect
        @reactive.event(input.se_clear_btn)
        async def _on_clear():
            await _clear_form()
            status.set("Form cleared.")


# Optional: keep backward-compatible module-level functions
_page_instance: Optional[SessionsPage] = None


def _get_page() -> SessionsPage:
    global _page_instance
    if _page_instance is None:
        _page_instance = SessionsPage(DBService())
    return _page_instance


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)


def get_sessions_store():
    return [None]
