from shiny import ui, render, reactive

from ui.services.db_service import DBService
db_service = DBService("ui/config/config.yml")


def get_ui():
    return ui.nav_panel(
        "User Management",
        ui.h2("👥 User Management"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Users"),
                ui.input_text(
                    "um_select_serial",
                    "Select user (by serial)",

                ),
                ui.output_ui("um_grid"),
                ui.br(),
                ui.layout_columns(

                    ui.input_action_button("um_load_btn", "Load Selected"),
                    ui.input_action_button("um_delete_btn", "Delete Selected"),
                    col_widths=(6, 3, 3),
                ),
                full_screen=False,
            ),
            ui.card(
                ui.card_header("Create / Edit User"),
                ui.input_text("um_serial", "Serial Number"),
                ui.input_text("um_forname", "Forname"),
                ui.input_text("um_name", "Name"),
                ui.input_text("um_email", "Email"),
                ui.input_select(
                    "um_role",
                    "Role",
                    choices=["Admin", "Coach", "Member"],
                ),
                ui.br(),
                ui.layout_columns(
                    ui.input_action_button("um_create_btn", "Create"),
                    ui.input_action_button("um_update_btn", "Update"),
                    ui.input_action_button("um_clear_btn", "Clear Form"),
                    col_widths=(3, 3, 3),
                ),
                ui.br(),
                ui.output_text("um_status"),
                full_screen=False,
            ),
            col_widths=(7, 5),
        ),
    )

def server(input, output, session):
    # Reactive store of users: list of dicts with required keys
    users = reactive.Value(db_service.get_all_users())

    def _key(u):
        return u.get("serialnmbr", "")

    def _validate_user(u, is_update=False, current_serial=None):
        # Required fields
        required_fields = ["serialnmbr", "forname", "name", "email", "role"]
        for f in required_fields:
            if not (u.get(f) or "").strip():
                return False, f"Field '{f}' is required."
        # Email simple validation
        email = u["email"].strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Invalid email address."
        # Serial uniqueness
        serial = u["serialnmbr"].strip()
        existing_serials = {x["serialnmbr"] for x in users.get()}
        if is_update:
            # allow same serial if updating same record
            if serial != (current_serial or "") and serial in existing_serials:
                return False, f"Serial '{serial}' already exists."
        else:
            if serial in existing_serials:
                return False, f"Serial '{serial}' already exists."
        return True, "OK"

    async def _refresh_select_choices():
        opts = {u.serial_number: f'{u.serial_number} — {u.username} {u.email}' for u in await db_service.get_all_users()}
        session.send_input_message(
            "um_select_serial",
            {"choices": opts, "selected": None},
        )

    def _to_table(users_list):
        # Build a simple HTML table to simulate a grid
        header = ui.tags.tr(
            ui.tags.th("Serial"),
            ui.tags.th("Name"),
            ui.tags.th("Email"),
            ui.tags.th("Role"),
        )
        rows = []
        for u in users_list:
            role = u.role
            rows.append(
                ui.tags.tr(
                    ui.tags.td(u.serial_number, ""),
                    ui.tags.td(u.username, ""),

                    ui.tags.td(u.email, ""),
                    ui.tags.td(str(role))
                )
            )
        return ui.tags.table(
            {"class": "table table-striped table-sm"},
            ui.tags.thead(header),
            ui.tags.tbody(*rows) if rows else ui.tags.tbody(
                ui.tags.tr(ui.tags.td({"colspan": "5"}, "No users yet."))
            ),
        )

    def _read_form():
        return {
            "serialnmbr": (input.um_serial() or "").strip(),
            "forname": (input.um_forname() or "").strip(),
            "name": (input.um_name() or "").strip(),
            "email": (input.um_email() or "").strip(),
            "role": (input.um_role() or "").strip(),
        }

    def _write_form(u):
        # Populate inputs with user values
        session.send_input_message("um_serial", {"value": u.get("serialnmbr", "")})
        session.send_input_message("um_forname", {"value": u.get("forname", "")})
        session.send_input_message("um_name", {"value": u.get("name", "")})
        session.send_input_message("um_email", {"value": u.get("email", "")})
        session.send_input_message("um_role", {"value": u.get("role", "")})

    def _clear_form():
        _write_form({"serialnmbr": "", "forname": "", "name": "", "email": "", "role": ""})

    status = reactive.Value("Ready.")

    @output
    @render.text
    def um_status():
        return status.get()

    @output
    @render.ui
    async def um_grid():
        return _to_table(await db_service.get_all_users())

    @reactive.Effect
    async def _init_choices():
        await _refresh_select_choices()

    @reactive.Effect
    @reactive.event(input.um_create_btn)
    def _on_create():
        new_user = _read_form()
        ok, msg = _validate_user(new_user, is_update=False)
        if not ok:
            status.set(msg)
            return
        users.set(users.get() + [new_user])
        status.set(f"Created user '{new_user['serialnmbr']}'.")
        _refresh_select_choices()

    @reactive.Effect
    @reactive.event(input.um_update_btn)
    def _on_update():
        sel = input.um_select_serial()
        if not sel:
            status.set("Select a user to update.")
            return
        updated = _read_form()
        ok, msg = _validate_user(updated, is_update=True, current_serial=sel)
        if not ok:
            status.set(msg)
            return
        current = users.get()
        idx = next((i for i, u in enumerate(current) if _key(u) == sel), None)
        if idx is None:
            status.set("Selected user not found.")
            return
        current[idx] = updated
        users.set(current[:])
        status.set(f"Updated user '{sel}'.")
        _refresh_select_choices()

    @reactive.Effect
    @reactive.event(input.um_delete_btn)
    def _on_delete():
        sel = input.um_select_serial()
        if not sel:
            status.set("Select a user to delete.")
            return
        current = users.get()
        if not any(_key(u) == sel for u in current):
            status.set("Selected user not found.")
            return
        users.set([u for u in current if _key(u) != sel])
        status.set(f"Deleted user '{sel}'.")
        _refresh_select_choices()
        _clear_form()

    @reactive.Effect
    @reactive.event(input.um_load_btn)
    def _on_load():
        sel = input.um_select_serial()
        if not sel:
            status.set("Select a user to load.")
            return
        current = users.get()
        user = next((u for u in current if _key(u) == sel), None)
        if not user:
            status.set("Selected user not found.")
            return
        _write_form(user)
        status.set(f"Loaded user '{sel}' into form.")

    @reactive.Effect
    @reactive.event(input.um_clear_btn)
    def _on_clear():
        _clear_form()
        status.set("Form cleared.")