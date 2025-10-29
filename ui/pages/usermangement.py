# Python
from __future__ import annotations
import pandas as pd
from shiny import ui, render, reactive
from ui.controllers.usermanagement_controller import UserManagementController, UserForm

class UserManagementPage:
    COLUMN_SERIAL = "Serial"
    NO_SELECTION_MESSAGE = "No row selected"

    def __init__(self) -> None:
        self.controller = UserManagementController()
        self.status = reactive.Value("Ready.")
        self.refresh_tick = reactive.Value(0)
        self.selected_serial = reactive.Value(None)
        self.selected_id = reactive.Value(0)

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
                        choices=self.controller.role_choices(),
                    ),
                    ui.input_checkbox("um_is_active", "Active"),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button("um_create_btn", "Create"),
                        ui.input_action_button("um_update_btn", "Update"),
                        ui.input_action_button("um_clear_btn", "Clear Form"),
                        col_widths=(3, 3, 3),
                    ),
                    ui.br(),
                    ui.output_text("um_status"),
                    ui.output_text("selected_user"),
                    full_screen=False,
                ),
                col_widths=(7, 5),
                id="user_management",
            ),
        )

    def _read_form(self, input_form) -> UserForm:
        return UserForm(
            serial=(input_form.um_serial() or "").strip(),
            username=(input_form.um_username() or "").strip(),
            password=(input_form.um_password() or "").strip(),
            email=(input_form.um_email() or "").strip(),
            role=(input_form.um_role() or "").strip(),
            is_active=(input_form.um_is_active())

        )

    def _write_form(self, session, u: dict):
        session.send_input_message("um_serial", {"value": u.get("serial", "")})
        session.send_input_message("um_username", {"value": u.get("username", "")})
        session.send_input_message("um_password", {"value": u.get("password", "")})
        session.send_input_message("um_email", {"value": u.get("email", "")})
        session.send_input_message("um_role", {"value": u.get("role", "")})
        session.send_input_message("um_is_active", {"value": u.get("is_active", "")})

    def _clear_form(self, session):
        self.selected_serial.set(None)
        #self.selected_id.set(0)
        self._write_form(session, {"serial": "", "username": "", "password": "", "email": "", "role": "", "is_active": ""})

    def server(self, input, output, session):
        @output
        @render.text
        def um_status():
            return self.status.get()

        @reactive.calc
        async def users_list():
            _ = self.refresh_tick.get()
            return await self.controller.list_users_df()

        @output
        @render.data_frame
        async def um_grid():
            df = await users_list()
            to_drop = [c for c in ["Password", "ID"] if c in df.columns]
            if to_drop:
                df = df.drop(columns=to_drop)
            return render.DataGrid(df, filters=True, selection_mode="rows", width="100%")

        @output
        @render.text
        async def selected_user():
            sel = input.um_grid_selected_rows()
            if not sel:
                return self.NO_SELECTION_MESSAGE
            row_idx = sel[0]
            df = await users_list()
            if row_idx < 0 or row_idx >= len(df):
                return self.NO_SELECTION_MESSAGE
            row = df.iloc[row_idx]
            serial = row[self.COLUMN_SERIAL]
            self.selected_serial.set(serial)
            self.controller.set_selected_user(UserForm(serial=row[self.COLUMN_SERIAL], username=row.get("Username", ""), email=row.get("Email", ""), role=row.get("Role", ""),password=row.get("Password", ""), is_active=row.get("Active", "")))
            self.selected_id.set(row.get("ID"))
            self.status.set(f"Selected user '{serial}'.")
            self._write_form(
                session,
                {
                    "serial": row[self.COLUMN_SERIAL],
                    "username": row.get("Username", ""),
                    "password": row.get("Password", ""),
                    "email": row.get("Email", ""),
                    "role": row.get("Role", ""),
                    "is_active": (bool(row.get("Active")) if pd.notna(row.get("Active")) else False),
                },
            )
            return serial

        @reactive.Effect
        @reactive.event(input.um_create_btn)
        async def _on_create():
            form = self._read_form(input)
            ok, msg = await self.controller.validate(form, is_update=False)
            if not ok:
                self.status.set(msg)
                return
            created = await self.controller.create_user(form)
            if created:
                self.status.set(f"Created user '{form.serial}'.")
                self.refresh_tick.set(self.refresh_tick.get() + 1)
                self._clear_form(session)
            else:
                self.status.set(f"Failed to create user '{form.serial}'.")

        @reactive.Effect
        @reactive.event(input.um_update_btn)
        async def _on_update():
            if not self.selected_id.get():
                self.status.set("Select a user to update.")
                return
            form = self._read_form(input)
            ok, msg = await self.controller.validate(form, is_update=True)
            if not ok:
                self.status.set(msg)
                return
            updated = await self.controller.update_user(int(self.selected_id.get()), form)
            if not updated:
                self.status.set("Failed to update user.")
                return
            self.status.set(f"Updated user '{form.serial}'.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self._clear_form(session)

        @reactive.Effect
        @reactive.event(input.um_delete_btn)
        async def _on_delete():
            sel_serial = self.selected_serial.get()
            if not sel_serial:
                self.status.set("Select a user to delete.")
                return
            deleted = await self.controller.delete_user_by_serial(sel_serial)
            if not deleted:
                self.status.set(f"No user found with serial '{sel_serial}'.")
                return
            self.status.set(f"Deleted user '{sel_serial}'.")
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            self.selected_serial.set(None)
            self._clear_form(session)

        @reactive.Effect
        @reactive.event(input.um_clear_btn)
        def _on_clear():
            self._clear_form(session)
            self.status.set("Form cleared.")


# Public API
_page = UserManagementPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)