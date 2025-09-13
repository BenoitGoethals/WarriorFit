from shiny import ui, render, reactive
import pandas as pd

import data
from data.db.db_model import User,Role
from ui.services.db_service import DBService
db_service = DBService("ui/config/config.yml")



def _get_role_choices():
    # Convert enum members to strings suitable for UI choices.
    # Prefer .value when available; fallback to str(member).
    try:
        return [r.value for r in Role]
    except Exception:
        return [str(r) for r in Role]


def get_ui():
    return ui.nav_panel(
        "User Management",
        ui.h2("👥 User Management"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Users"),

                    ui.output_data_frame("um_grid"),
                    ui.input_action_button("um_delete_btn", "Delete Selected"),
                full_screen=False,
            ),
            ui.card(
                ui.card_header("Create / Edit User"),
                ui.input_text("um_serial", "Serial Number"),
                ui.input_text("um_username", "Username"),
                ui.input_password("um_password", "Password"),
                ui.input_text("um_email", "Email"),
                ui.input_select(
                    "um_role",
                    "Role",
                    choices= _get_role_choices()
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
                ui.output_text("selected")            ,
                full_screen=False,
            ),
            col_widths=(7, 5),
        ),
    )

def server(input, output, session):
    # Reactive store of users: list of dicts with required keys
    users = reactive.Value(db_service.get_all_users())
    # Add a dedicated tick to force grid refreshes
    refresh_tick = reactive.Value(0)
    selected_serial = None
    def _key(u):
        # Use the correct key name used throughout the form ("serial")
        return u.get("serial", "")

    async def _validate_user(u, is_update=False, current_serial=None):
        # Required fields
        required_fields = ["serial", "username", "password", "email", "role"]
        for f in required_fields:
            if not (u.get(f) or "").strip():
                return False, f"Field '{f}' is required."
        # Email simple validation
        email = u["email"].strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Invalid email address."
        # Serial uniqueness
        serial = u["serial"].strip()
        existing_serials = await db_service.serial_exists(serial)
        if is_update:
            # allow same serial if updating same record
            if serial != (current_serial or "") and existing_serials:
                return False, f"Serial '{serial}' already exists."
        else:
            if existing_serials:
                return False, f"Serial '{serial}' already exists."
        return True, "OK"

    async def _refresh_select_choices():
        opts = {u.serial_number: f'{u.serial_number} — {u.username} {u.email}' for u in await db_service.get_all_users()}
        session.send_input_message(
            "um_select_serial",
            {"choices": opts, "selected": None},
        )



    def _read_form():
        return {
            "serial": (input.um_serial() or "").strip(),
            "username": (input.um_username() or "").strip(),
            "password": (input.um_password() or "").strip(),
            "email": (input.um_email() or "").strip(),
            "role": (input.um_role() or "").strip(),
        }

    def _write_form(u):
        # Populate inputs with user values
        session.send_input_message("um_serial", {"value": u.get("serial", "")})

        session.send_input_message("um_username", {"value": u.get("username", "")})
        session.send_input_message("um_password", {"value": u.get("password", "")})

        session.send_input_message("um_email", {"value": u.get("email", "")})
        session.send_input_message("um_role", {"value": u.get("role", "")})

    def _clear_form():
        _write_form({"serial": "","username": "", "password": "",  "email": "", "role": ""})

    status = reactive.Value("Ready.")

    @output
    @render.text
    def um_status():
        return status.get()

    @reactive.calc
    async def users_list():
        users_list_pd = pd.DataFrame([{
            'Serial': u.serial_number,
            'Username': u.username,
            'Email': u.email,

            'Role': str(u.role),
            'Active': str(u.is_active),
            'Created': str(u.created_at.date())
        } for u in await db_service.get_all_users()])
        _ = refresh_tick.get()
        return users_list_pd

    @output
    @render.data_frame
    async def um_grid():
        # Create a dependency so this output re-runs when data changes


        # Fetch the current data (await the reactive calc), then build the DataGrid
        df = await users_list()
        return render.DataGrid(
            df,
            filters=True,
            selection_mode="rows",  # "none" | "rows" | "cells"

        )

    @output
    @render.text
    async def selected():
        sel = input.um_grid_selected_rows()  # returns list of row indices
        if not sel:
            return "No row selected"
        row_idx = sel[0]
        df = await users_list()
        row = df.iloc[row_idx]

        selected_serial = row['Serial']
        status.set(f"Selected user '{row['Serial']}'.")
        return row['Serial']


    @reactive.Effect
    async def _init_choices():
        await _refresh_select_choices()

    @reactive.Effect
    @reactive.event(input.um_create_btn)
    async def _on_create():
        new_user = _read_form()
        ok, msg = await _validate_user(new_user, is_update=False)
        if not ok:
            status.set(msg)
            return
        add_user = User()
        add_user.serial_number = new_user["serial"]
        add_user.username = new_user["username"]
        add_user.password_hash = new_user["password"]
        add_user.email = new_user["email"]
        add_user.role = new_user["role"]
        add_user.is_active = True
        ret_user=await db_service.add_user(add_user)
        if ret_user:
            status.set(f"Created user '{new_user['serial']}'.")
            # Trigger reactivity so um_grid re-renders
            refresh_tick.set(refresh_tick.get() + 1)
            _clear_form()
        else:
            status.set(f"Failed to create user '{new_user['serial']}'.")


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
    async def _on_delete():
        if not selected_serial:
            status.set("Select a user to delete.")
            return
        deleted=await db_service.delete_user_by_serial(selected_serial)
        if not deleted:
            status.set(f"No user found with serial '{selected_serial}'.")
        status.set(f"Deleted user '{selected_serial}'.")
        refresh_tick.set(refresh_tick.get() + 1)

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