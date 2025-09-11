from shiny import ui, render, reactive

SESSION_TYPES = ["phef", "combattest", "swimtest", "functional test", "other"]

def get_ui():
    return ui.nav_panel(
        "Sessions",
        ui.h2("📅 Test Sessions"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Create / Edit Session"),
                ui.input_date("se_date", "Date"),
                ui.input_select("se_type", "Type", choices=SESSION_TYPES),
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
                ui.output_ui("se_grid"),
                ui.br(),
                ui.layout_columns(
                    ui.input_select("se_select_id", "Select session", choices=[]),
                    ui.input_action_button("se_load_btn", "Load Selected"),
                    ui.input_action_button("se_delete_btn", "Delete Selected"),
                    col_widths=(6, 3, 3),
                ),
                full_screen=False,
            ),
            col_widths=(6, 6),
        ),
    )

def server(input, output, session):
    # Stored as list of dicts: {id, date, type}
    sessions = reactive.Value([])
    next_id = reactive.Value(1)
    status = reactive.Value("Ready.")

    def _validate(data):
        if not data["date"]:
            return False, "Date is required."
        if not (data["type"] or "").strip():
            return False, "Type is required."
        if data["type"] not in SESSION_TYPES:
            return False, "Invalid session type."
        return True, "OK"

    def _read_form():
        return {
            "date": input.se_date(),
            "type": (input.se_type() or "").strip(),
        }

    def _write_form(rec):
        session.send_input_message("se_date", {"value": rec.get("date", None)})
        session.send_input_message("se_type", {"value": rec.get("type", "")})

    def _clear_form():
        _write_form({"date": None, "type": ""})

    def _refresh_select():
        choices = {str(r["id"]): f'{r["id"]}: {r["type"]} ({r["date"]})' for r in sessions.get()}
        session.send_input_message("se_select_id", {"choices": choices, "selected": None})

    def _to_table(items):
        header = ui.tags.tr(
            ui.tags.th("ID"),
            ui.tags.th("Date"),
            ui.tags.th("Type"),
        )
        rows = []
        for r in items:
            rows.append(
                ui.tags.tr(
                    ui.tags.td(str(r["id"])),
                    ui.tags.td(str(r["date"]) if r["date"] else ""),
                    ui.tags.td(r["type"]),
                )
            )
        body = (
            ui.tags.tbody(*rows)
            if rows
            else ui.tags.tbody(ui.tags.tr(ui.tags.td({"colspan": "3"}, "No sessions yet.")))
        )
        return ui.tags.table({"class": "table table-striped table-sm"}, ui.tags.thead(header), body)

    @output
    @render.text
    def se_status():
        return status.get()

    @output
    @render.ui
    def se_grid():
        return _to_table(sessions.get())

    @reactive.Effect
    def _init_select():
        _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_add_btn)
    def _on_add():
        data = _read_form()
        ok, msg = _validate(data)
        if not ok:
            status.set(msg)
            return
        new_id = next_id.get()
        next_id.set(new_id + 1)
        record = {"id": new_id, "date": data["date"], "type": data["type"]}
        sessions.set(sessions.get() + [record])
        status.set(f"Added session #{new_id}.")
        _refresh_select()
        _clear_form()

    @reactive.Effect
    @reactive.event(input.se_load_btn)
    def _on_load():
        sel = input.se_select_id()
        if not sel:
            status.set("Select a session to load.")
            return
        sel_id = int(sel)
        rec = next((r for r in sessions.get() if r["id"] == sel_id), None)
        if not rec:
            status.set("Selected session not found.")
            return
        _write_form(rec)
        status.set(f"Loaded session #{sel_id}.")

    @reactive.Effect
    @reactive.event(input.se_update_btn)
    def _on_update():
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
        current = sessions.get()
        idx = next((i for i, r in enumerate(current) if r["id"] == sel_id), None)
        if idx is None:
            status.set("Selected session not found.")
            return
        current[idx] = {"id": sel_id, "date": data["date"], "type": data["type"]}
        sessions.set(current[:])
        status.set(f"Updated session #{sel_id}.")
        _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_delete_btn)
    def _on_delete():
        sel = input.se_select_id()
        if not sel:
            status.set("Select a session to delete.")
            return
        sel_id = int(sel)
        current = sessions.get()
        if not any(r["id"] == sel_id for r in current):
            status.set("Selected session not found.")
            return
        sessions.set([r for r in current if r["id"] != sel_id])
        status.set(f"Deleted session #{sel_id}.")
        _refresh_select()

    @reactive.Effect
    @reactive.event(input.se_clear_btn)
    def _on_clear():
        _clear_form()
        status.set("Form cleared.")


def get_sessions_store():
    return [None]