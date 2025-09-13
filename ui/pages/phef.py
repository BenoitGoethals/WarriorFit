from shiny import ui, render, reactive
from .sessions import get_sessions_store

from ui.services.db_service import DBService
from ..user_store import UserStore

db_service = DBService("ui/config/config.yml")


def get_ui():
    if UserStore.get_user() :
        return ui.nav_panel(
            "PHEF Tests",
            ui.h2("🧪 PHEF Tests"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Add / Edit PHEF Test"),
                    ui.input_text("ph_serialnr", "Serial Number"),
                    ui.input_select("ph_session_id", "Session", choices=[]),
                    ui.output_text("ph_session_date_txt"),
                    ui.input_text(
                        "ph_side_bridge",
                        "Side-bridge time (mm:ss or seconds)",
                        placeholder="e.g., 2:30 or 150",
                    ),
                    ui.input_text(
                        "ph_run_2400",
                        "2400m run time (mm:ss or seconds)",
                        placeholder="e.g., 10:45 or 645",
                    ),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button("ph_add_btn", "Add"),
                        ui.input_action_button("ph_update_btn", "Update"),
                        ui.input_action_button("ph_clear_btn", "Clear Form"),
                        col_widths=(3, 3, 3),
                    ),
                    ui.br(),
                    ui.output_text("ph_status"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header("Records"),
                    ui.output_ui("ph_grid"),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_select("ph_select_id", "Select record", choices=[]),
                        ui.input_action_button("ph_load_btn", "Load Selected"),
                        ui.input_action_button("ph_delete_btn", "Delete Selected"),
                        col_widths=(6, 3, 3),
                    ),
                    full_screen=False,
                ),
                col_widths=(6, 6),
            ),
        )

    return None


async def server(input, output, session):
    # Reactive list of dicts: {id, serialnr, session_id, session_date, side_bridge_s, run2400_s}
    records = reactive.Value(await db_service.get_all_fitness_tests_full())
    next_id = reactive.Value(1)
    status = reactive.Value("Ready.")

    sessions_store = get_sessions_store()

    def _parse_time_to_seconds(val: str):
        """
        Accepts 'mm:ss' or 'ss' and returns total seconds (int).
        Returns (ok, seconds or error_message)
        """
        txt = (val or "").strip()
        if not txt:
            return False, "Time value is required."
        try:
            if ":" in txt:
                parts = txt.split(":")
                if len(parts) != 2:
                    return False, "Time must be in mm:ss or seconds."
                m = int(parts[0])
                s = int(parts[1])
                total = m * 60 + s
            else:
                total = int(float(txt))
            if total <= 0:
                return False, "Time must be positive."
            return True, int(total)
        except Exception:
            return False, "Time must be numeric (mm:ss or seconds)."

    def _format_seconds(sec: int):
        m = sec // 60
        s = sec % 60
        return f"{m}:{s:02d}"

    def _find_session_by_id_str(id_str: str):
        try:
            sid = int(id_str)
        except Exception:
            return None
        for s in sessions_store.get():
            if s["id"] == sid:
                return s
        return None

    def _validate(data):
        if not (data["serialnr"] or "").strip():
            return False, "Serial number is required."
        if not (data["session_id"] or "").strip():
            return False, "Session selection is required."
        sess = _find_session_by_id_str(data["session_id"])
        if sess is None:
            return False, "Selected session does not exist."
        ok_sb, sb = _parse_time_to_seconds(data["side_bridge"])
        if not ok_sb:
            return False, f"Side-bridge: {sb}"
        ok_run, run = _parse_time_to_seconds(data["run_2400"])
        if not ok_run:
            return False, f"2400m run: {run}"
        return True, {"side_bridge_s": sb, "run2400_s": run, "session_date": sess["date"], "session_id_int": sess["id"]}

    def _read_form():
        return {
            "serialnr": (input.ph_serialnr() or "").strip(),
            "session_id": (input.ph_session_id() or "").strip(),
            "side_bridge": (input.ph_side_bridge() or "").strip(),
            "run_2400": (input.ph_run_2400() or "").strip(),
        }

    def _write_form(rec):
        session.send_input_message("ph_serialnr", {"value": rec.get("serialnr", "")})
        session.send_input_message("ph_session_id", {"value": "" if rec.get("session_id") is None else str(rec.get("session_id"))})
        sb_val = rec.get("side_bridge_s")
        run_val = rec.get("run2400_s")
        session.send_input_message("ph_side_bridge", {"value": "" if sb_val is None else _format_seconds(sb_val)})
        session.send_input_message("ph_run_2400", {"value": "" if run_val is None else _format_seconds(run_val)})

    def _clear_form():
        _write_form({
            "serialnr": "",
            "session_id": None,
            "side_bridge_s": None,
            "run2400_s": None
        })
        _update_session_date_text(None)

    def _refresh_session_choices():
        sess = sessions_store[0]
        choices = {
            str(s["id"]): f'{s["id"]}: {s["type"]} ({s["date"]})'
            for s in sess
        }
        session.send_input_message("ph_session_id", {"choices": choices})

    def _refresh_record_select():
        choices = {
            str(r["id"]): f'{r["id"]}: {r["serialnr"]} / Session {r["session_id"]} ({r["session_date"]})'
            for r in records.get()
        }
        session.send_input_message("ph_select_id", {"choices": choices, "selected": None})

    def _to_table(items):
        header = ui.tags.tr(
            ui.tags.th("ID"),
            ui.tags.th("Serial"),
            ui.tags.th("Session ID"),
            ui.tags.th("Session Date"),
            ui.tags.th("Side-bridge"),
            ui.tags.th("2400m Run"),
        )
        rows = []
        for r in items:
            rows.append(
                ui.tags.tr(
                    ui.tags.td(str(r["id"])),
                    ui.tags.td(r["serialnr"]),
                    ui.tags.td(str(r["session_id"])),
                    ui.tags.td(str(r["session_date"]) if r.get("session_date") else ""),
                    ui.tags.td(_format_seconds(r["side_bridge_s"])),
                    ui.tags.td(_format_seconds(r["run2400_s"])),
                )
            )
        body = (
            ui.tags.tbody(*rows)
            if rows
            else ui.tags.tbody(ui.tags.tr(ui.tags.td({"colspan": "6"}, "No records yet.")))
        )
        return ui.tags.table({"class": "table table-striped table-sm"}, ui.tags.thead(header), body)

    def _update_session_date_text(session_id_str):
        sess = _find_session_by_id_str(session_id_str) if session_id_str else None
        date_txt = f"Session date: {sess['date']}" if sess else "Session date: —"
        session.send_input_message("ph_session_date_txt", {"value": date_txt})

    @output
    @render.text
    def ph_status():
        return status.get()

    @output
    @render.text
    def ph_session_date_txt():
        # default text before selection
        sess = _find_session_by_id_str(input.ph_session_id())
        return f"Session date: {sess['date']}" if sess else "Session date: —"

    @output
    @render.ui
    def ph_grid():

        return _to_table(records.get())

    @reactive.Effect
    def _init():
        _refresh_session_choices()
        _refresh_record_select()

    # Rebuild session choices whenever the sessions store changes
    @reactive.Effect
    def _watch_sessions():
        _ = sessions_store.get()
        _refresh_session_choices()
        _update_session_date_text(input.ph_session_id())

    # Update session date text when user changes the session selection
    @reactive.Effect
    def _on_session_change():
        _ = input.ph_session_id()
        _update_session_date_text(input.ph_session_id())

    @reactive.Effect
    @reactive.event(input.ph_add_btn)
    def _on_add():
        data = _read_form()
        ok, res = _validate(data)
        if not ok:
            status.set(res)
            return
        new_id = next_id.get()
        next_id.set(new_id + 1)
        record = {
            "id": new_id,
            "serialnr": data["serialnr"],
            "session_id": res["session_id_int"],
            "session_date": res["session_date"],
            "side_bridge_s": res["side_bridge_s"],
            "run2400_s": res["run2400_s"],
        }
        records.set(records.get() + [record])
        status.set(f"Added PHEF test #{new_id} for {record['serialnr']} in session {record['session_id']}.")
        _refresh_record_select()
        _clear_form()

    @reactive.Effect
    @reactive.event(input.ph_load_btn)
    def _on_load():
        sel = input.ph_select_id()
        if not sel:
            status.set("Select a record to load.")
            return
        sel_id = int(sel)
        rec = next((r for r in records.get() if r["id"] == sel_id), None)
        if not rec:
            status.set("Selected record not found.")
            return
        _write_form(rec)
        _update_session_date_text(str(rec.get("session_id")))
        status.set(f"Loaded record #{sel_id}.")

    @reactive.Effect
    @reactive.event(input.ph_update_btn)
    def _on_update():
        sel = input.ph_select_id()
        if not sel:
            status.set("Select a record to update.")
            return
        sel_id = int(sel)
        data = _read_form()
        ok, res = _validate(data)
        if not ok:
            status.set(res)
            return
        current = records.get()
        idx = next((i for i, r in enumerate(current) if r["id"] == sel_id), None)
        if idx is None:
            status.set("Selected record not found.")
            return
        current[idx] = {
            "id": sel_id,
            "serialnr": data["serialnr"],
            "session_id": res["session_id_int"],
            "session_date": res["session_date"],
            "side_bridge_s": res["side_bridge_s"],
            "run2400_s": res["run2400_s"],
        }
        records.set(current[:])
        status.set(f"Updated record #{sel_id}.")
        _refresh_record_select()

    @reactive.Effect
    @reactive.event(input.ph_delete_btn)
    def _on_delete():
        sel = input.ph_select_id()
        if not sel:
            status.set("Select a record to delete.")
            return
        sel_id = int(sel)
        current = records.get()
        if not any(r["id"] == sel_id for r in current):
            status.set("Selected record not found.")
            return
        records.set([r for r in current if r["id"] != sel_id])
        status.set(f"Deleted record #{sel_id}.")
        _refresh_record_select()

    @reactive.Effect
    @reactive.event(input.ph_clear_btn)
    def _on_clear():
        _clear_form()
        status.set("Form cleared.")