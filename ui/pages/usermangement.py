from shiny import ui, render, reactive
import pandas as pd

import data
from api.auth_service import Auth
from data.db.db_model import User,Role
from ui.services.db_service import DBService
# ... existing code ...

class UserManagementPage:
    COLUMN_SERIAL = "Serial"
    NO_SELECTION_MESSAGE = "No row selected"

    def __init__(self) -> None:
        self.db_service = DBService("ui/config/config.yml")
        self.status = reactive.Value("Ready.")
        self.refresh_tick = reactive.Value(0)
        self.selected_serial = reactive.Value(None)
        self.selected_id = reactive.Value(None)

    @staticmethod
    def _get_role_choices():
        try:
            return [r.value for r in Role]
        except Exception:
            return [str(r) for r in Role]

    def get_ui(self):
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
                        choices=self._get_role_choices()
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
                    ui.output_text("selected"),
                    full_screen=False,
                ),
                col_widths=(7, 5),
                id="user_management",
            ),
        )

    def _key(self, u: dict) -> str:
        return u.get("serial", "")

    async def _validate_user(self, u: dict, is_update: bool = False, current_serial: str | None = None):
        required_fields = ["serial", "username", "password", "email", "role"]
        for f in required_fields:
            if not (u.get(f) or "").strip():
                return False, f"Field '{f}' is required."
        email = u["email"].strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Invalid email address."
        serial = u["serial"].strip()
        existing_serials = await self.db_service.serial_exists(serial)
        if is_update:
            if serial != (current_serial or "") and existing_serials:
                return False, f"Serial '{serial}' already exists."
        else:
            if existing_serials:
                return False, f"Serial '{serial}' already exists."
        return True, "OK"

    async def _refresh_select_choices(self, session):
        opts = {u.serial_number: f'{u.serial_number} — {u.username} {u.email}' for u in await self.db_service.get_all_users()}
        session.send_input_message(
            "um_select_serial",
            {"choices": opts, "selected": None},
        )

    def _read_form(self, input):
        return {
            "serial": (input.um_serial() or "").strip(),
            "username": (input.um_username() or "").strip(),
            "password": (input.um_password() or "").strip(),
            "email": (input.um_email() or "").strip(),
            "role": (input.um_role() or "").strip(),
        }

    def _write_form(self, session, u: dict):
        session.send_input_message("um_serial", {"value": u.get("serial", "")})
        session.send_input_message("um_username", {"value": u.get("username", "")})
        session.send_input_message("um_password", {"value": u.get("password", "")})
        session.send_input_message("um_email", {"value": u.get("email", "")})
        session.send_input_message("um_role", {"value": u.get("role", "")})

    def _clear_form(self, session):
        self.selected_serial = reactive.Value(None)
        self.selected_id = reactive.Value(None)
        self._write_form(session, {"serial": "", "username": "", "password": "", "email": "", "role": ""})

    def server(self, input, output, session):
        users = reactive.Value(self.db_service.get_all_users())

        @output
        @render.text
        def um_status():
            return self.status.get()

        @reactive.calc
        async def users_list():
            users_list_pd = pd.DataFrame([{
                self.COLUMN_SERIAL: u.serial_number,
                'id' : u.id,
                'Username': u.username,
                'Email': u.email,
                'Role': str(u.role),
                'Active': str(u.is_active),
                'Password':  u.password_hash,
                'Created': str(u.created_at.date())
            } for u in await self.db_service.get_all_users()])
            _ = self.refresh_tick.get()
            return users_list_pd

        @output
        @render.data_frame
        async def um_grid():
            df = await users_list()
            # Drop the Password column before displaying
            df = df.drop(columns=['Password','id'])

            return render.DataGrid(
                df,
                filters=True,
                selection_mode="rows",
            )

        @output
        @render.text
        async def selected():
            sel = input.um_grid_selected_rows()  # list of row indices
            if not sel:
                return self.NO_SELECTION_MESSAGE
            row_idx = sel[0]
            df = await users_list()
            if row_idx < 0 or row_idx >= len(df):
                return self.NO_SELECTION_MESSAGE
            row = df.iloc[row_idx]
            serial = row[self.COLUMN_SERIAL]
            self.selected_serial.set(serial)
            self.selected_id.set(row["id"])
            self.status.set(f"Selected user '{serial}'.")
            self._write_form(session, {"serial": row[self.COLUMN_SERIAL], "username": row["Username"], "password": row["Password"], "email": row["Email"], "role":row["Role"]})
            return serial

        @reactive.Effect
        async def _init_choices():
            await self._refresh_select_choices(session)

        @reactive.Effect
        @reactive.event(input.um_create_btn)
        async def _on_create():
            new_user = self._read_form(input)
            ok, msg = await self._validate_user(new_user, is_update=False)
            if not ok:
                self.status.set(msg)
                return
            add_user = User()
            add_user.serial_number = new_user["serial"]
            add_user.username = new_user["username"]
            add_user.password_hash = Auth.hash_password(new_user["password"])
            add_user.email = new_user["email"]
            add_user.role = new_user["role"]
            add_user.is_active = True
            ret_user = await self.db_service.add_user(add_user)
            if ret_user:
                self.status.set(f"Created user '{new_user['serial']}'.")
                self.refresh_tick.set(self.refresh_tick.get() + 1)
                self._clear_form(session)
            else:
                self.status.set(f"Failed to create user '{new_user['serial']}'.")

        @reactive.Effect
        @reactive.event(input.um_update_btn)
        async def _on_update():

            updated = self._read_form(input)
            ok, msg = await self._validate_user(updated, is_update=True, current_serial=updated["serial"]) # type: ignore
            if not ok:
                self.status.set(msg)  # type: ignore
                return
            user= User()
            user.id = self.selected_id.get()
            user.serial_number = updated["serial"]
            user.username = updated["username"]
            user.password_hash = Auth.hash_password(updated["password"])
            user.email = updated["email"]
            user.role = updated["role"]
            updated=await self.db_service.update_user(user.id,user)
            if not updated:
                self.status.set("Failed to update user.")
                return
            self.status.set(f"Updated user '{user.serial_number}'.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self.selected_serial = reactive.Value(None)
            self._clear_form(session)


        @reactive.Effect
        @reactive.event(input.um_delete_btn)
        async def _on_delete():
            sel_serial = self.selected_serial.get()
            if not sel_serial:
                self.status.set("Select a user to delete.")
                return
            deleted = await self.db_service.delete_user_by_serial(sel_serial)
            if not deleted:
                self.status.set(f"No user found with serial '{sel_serial}'.")
                return
            self.status.set(f"Deleted user '{sel_serial}'.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self.selected_serial.set(None)

        @reactive.Effect
        @reactive.event(input.um_load_btn)
        def _on_load():
            sel = input.um_select_serial()
            if not sel:
                self.status.set("Select a user to load.")
                return
            current = users.get()
            user = next((u for u in current if self._key(u) == sel), None)
            if not user:
                self.status.set("Selected user not found.")
                return
            self._write_form(session, user)
            self.status.set(f"Loaded user '{sel}' into form.")

        @reactive.Effect
        @reactive.event(input.um_clear_btn)
        def _on_clear():
            self._clear_form(session)
            self.status.set("Form cleared.")

# Public API preserved for existing imports/usages
_page = UserManagementPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)