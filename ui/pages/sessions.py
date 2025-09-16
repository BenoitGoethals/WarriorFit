from shiny import ui, render, reactive
from ..services.db_service import DBService
import datetime
import pandas as pd

db_service = DBService("ui/config/config.yml")
SESSION_TYPES = ["phef", "combattest", "swimtest", "functional test", "other"]

def get_ui():
    return ui.nav_panel(
        "Sessions",
        ui.h2("📅 Test Sessions"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Create / Edit Session"),
                ui.input_text("se_serial", "Serial Number PTI"),
                ui.input_date("se_date", "Date"),
                ui.input_text("se_time", "Time (HH:MM)", placeholder="HH:MM"),

                ui.input_select("se_type", "Type", choices=SESSION_TYPES),
                ui.input_checkbox("se_executed", "Executed", value=False),
                ui.input_text_area("se_description", "Description", rows=3),
                ui.br(),
                ui.layout_columns(
                    ui.input_action_button("se_add_btn", "Add"),
                    ui.input_action_button("se_update_btn", "Update"),
                    ui.input_action_button("se_clear_btn", "Clear Form"),
                    col_widths=(3, 3, 3),
                ),
                ui.br(),
                ui.output_text("se_status"),
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
            col_widths=(6, 6),
        ),
    )

def server(input, output, session):
    # Stored as list of dicts with TestSession attributes:
    # {id, serial_number_pti, datetime_start, executed, description, type_test}
    sessions = reactive.Value([])
    next_id = reactive.Value(1)
    status = reactive.Value("Ready.")

    async def _load_initial():
        items = await db_service.get_all_test_sessions()
        # Convert ORM objects to plain dicts with full TestSession attributes
        def _to_dict_session(r):
            return {
                "id": getattr(r, "id", None),
                "serial_number_pti": getattr(r, "serial_number_pti", None),
                "datetime_start": getattr(r, "datetime_start", None),
                "executed": bool(getattr(r, "executed", False)),
                "description": getattr(r, "description", None),
                # If enum-like, use .name; otherwise str/raw
                "type_test": getattr(getattr(r, "type_test", None), "name", getattr(r, "type_test", None)),
            }
        converted = [_to_dict_session(r) for r in items]
        sessions.set(converted)
        # Initialize next_id based on max existing id (fallback to 1)
        try:
            max_id = max((rec["id"] for rec in converted if rec["id"] is not None), default=0)
        except ValueError:
            max_id = 0
        next_id.set(max_id + 1)

    def _validate(data):
        if not data["datetime_start"]:
            return False, "Date and time are required."
        if not (data["type_test"] or "").strip():
            return False, "Type is required."
        if data["type_test"] not in SESSION_TYPES:
            return False, "Invalid session type."
        return True, "OK"

    def _read_form():
        # Combine date + time into a single datetime
        dt_date = input.se_date()
        dt_time = input.se_time()
        dt = None
        if dt_date and dt_time:
            try:
                # dt_date is a date, dt_time is a time string "HH:MM:SS" or "HH:MM"
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

    def _write_form(rec):
        # Split datetime_start into date/time inputs
        dt = rec.get("datetime_start", None)
        dt_date = dt.date() if isinstance(dt, datetime.datetime) else None
        dt_time = dt.time().strftime("%H:%M:%S") if isinstance(dt, datetime.datetime) else None
        session.send_input_message("se_serial", {"value": rec.get("serial_number_pti", "") or ""})
        session.send_input_message("se_date", {"value": dt_date})
        session.send_input_message("se_time", {"value": dt_time})
        session.send_input_message("se_type", {"value": rec.get("type_test", "")})
        session.send_input_message("se_executed", {"value": bool(rec.get("executed", False))})
        session.send_input_message("se_description", {"value": rec.get("description", "") or ""})

    def _clear_form():
        _write_form({
            "serial_number_pti": None,
            "datetime_start": None,
            "executed": False,
            "description": None,
            "type_test": "",
        })

    async def _refresh_select():
        items = sessions.get() or []
        choices = {str(r["id"]): f'{r["id"]}: {r.get("type_test","")} ({r.get("datetime_start","")})' for r in items if r.get("id") is not None}
        session.send_input_message("se_select_id", {"choices": choices, "selected": None})

    @output
    @render.text
    def se_status():
        return status.get()

    @output
    @render.data_frame
    async def se_grid():
        items = sessions.get() or []
        df = pd.DataFrame([
            {
                "ID": r.get("id", ""),
                "Serial PTI": r.get("serial_number_pti", "") or "",
                "Start": str(r.get("datetime_start", "") or ""),
                "Executed": "Yes" if r.get("executed", False) else "No",
                "Type": r.get("type_test", "") or "",
                "Description": r.get("description", "") or "",
            }
            for r in items
        ])
        df = df.drop(columns=[ 'ID'])
        return render.DataGrid(
            df,
            filters=True,
            selection_mode="rows",
        )

    @reactive.Effect
    async def _init_select():
        await _load_initial()
        await _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_add_btn)
    async def _on_add():
        data = _read_form()
        ok, msg = _validate(data)
        if not ok:
            status.set(msg)
            return
        new_id = next_id.get()
        next_id.set(new_id + 1)
        record = {
            "id": new_id,
            "serial_number_pti": data["serial_number_pti"],
            "datetime_start": data["datetime_start"],
            "executed": data["executed"],
            "description": data["description"],
            "type_test": data["type_test"],
        }
        sessions.set((sessions.get() or []) + [record])
        status.set(f"Added session #{new_id}.")
        await _refresh_select()
        _clear_form()

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
        sel = input.se_select_id()
        if not sel:
            status.set("Select a session to update.")
            return
        sel_id = int(sel)
        data = _read_form()
        ok, msg = _validate(data)
        if not ok:
            status.set(msg)
            return
        current = sessions.get() or []
        idx = next((i for i, r in enumerate(current) if r.get("id") == sel_id), None)
        if idx is None:
            status.set("Selected session not found.")
            return
        current[idx] = {
            "id": sel_id,
            "serial_number_pti": data["serial_number_pti"],
            "datetime_start": data["datetime_start"],
            "executed": data["executed"],
            "description": data["description"],
            "type_test": data["type_test"],
        }
        sessions.set(current[:])
        status.set(f"Updated session #{sel_id}.")
        await _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_delete_btn)
    async def _on_delete():
        sel = input.se_select_id()
        if not sel:
            status.set("Select a session to delete.")
            return
        sel_id = int(sel)
        current = sessions.get() or []
        if not any((r.get("id") == sel_id) for r in current):
            status.set("Selected session not found.")
            return
        sessions.set([r for r in current if r.get("id") != sel_id])
        status.set(f"Deleted session #{sel_id}.")
        await _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_clear_btn)
    def _on_clear():
        _clear_form()
        status.set("Form cleared.")


def get_sessions_store():
    return [None]