from typing import Any
from shiny import App, ui, run_app, render

from data.db.db_model import User
from ui.user_store import UserStore
from .pages import dashboard, reports, settings, logout
from .pages import login
from .pages import usermangement
from .pages import phef
from .pages import sessions

from data.db.db_model import User,Role
class FitnessWarriorApp:
    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000

    # Public static user store
    USER_STORE: UserStore = UserStore()

    @staticmethod
    def build_app_ui() -> ui.page_navbar:

        """
        Construct and return the root UI for the application.
        """


        return ui.page_navbar(
            usermangement.get_ui(),
           # phef.get_ui(),
           # sessions.get_ui(),
            dashboard.get_ui(),
            reports.get_ui(),
            settings.get_ui(),

            ui.nav_spacer(),
            ui.nav_control(ui.input_action_button("logout_btn", "Logout")),

            title=FitnessWarriorApp.APP_TITLE,
            id="main_nav",
         )





    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        """
        Register server logic for each page.
        """
        # All pages will be mounted lazily when their tab becomes active.
        pass

    @staticmethod
    def server(input: Any, output: Any, session: Any) -> None:
        """
        Shiny server entry point. Delegates to per-page servers.
        """
        from shiny import reactive
        from ui.services.db_service import DBService  # ensure DB access is available here
        db_service = DBService("ui/config/config.yml")

        FitnessWarriorApp.register_pages_server(input, output, session)

        # Map navbar labels to their page server functions
        servers_by_tab = {
            "User Management": usermangement.server,
            "Login": login.server,
            "PHEF Tests": phef.server,
            "Sessions": sessions.server,
            "Dashboard": dashboard.server,
            "Reports": reports.server,
            "Settings": settings.server,

        }

        mounted = reactive.Value(set())

        status_text = reactive.Value("")
        login_user_text = reactive.Value("")

        @reactive.Effect
        async def login_dialog():
            login = ui.div(
                ui.h2("Login"),
                ui.input_text("username", "Username"),
                ui.input_password("password", "Password"),
                ui.input_action_button("handle_login", "Login"),
                ui.tags.span(
                    ui.output_text("status"), style="color: red; font-weight: bold;"
                ),
            )
            ui.modal_show(ui.modal(login, easy_close=False, size="m", footer=None))
        # ... existing code ...
        @output
        @render.text
        def status():
            return status_text()
        # ... existing code ...
        @output
        @render.text
        def login_user():
            return login_user_text()
        # ... existing code ...
        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login():
            username = input.username()
            password = input.password()
            try:
                if await db_service.check_user(username, password):
                    user = await db_service.get_user_by_username(username)
                    UserStore.set_user(user)
                    login_user_text.set(f"User :{username}")
                    status_text.set("")  # clear any previous error
                    ui.modal_remove()

                else:
                    status_text.set("Invalid username or password.")
            except Exception as e:
                # Surface a friendly message; you can log e server-side
                status_text.set("An error occurred while logging in. Please try again.")
        # ... existing code ...
        @reactive.Effect
        def _mount_on_nav_activation():
            active = input.main_nav()
            if not active:
                return
            already = mounted.get()
            if active in servers_by_tab and active not in already:
                servers_by_tab[active](input, output, session)
                mounted.set({*already, active})
        # ... existing code ...
        @reactive.Effect
        def _on_logout_button_click():
            try:
                clicks = input.logout_btn()
            except Exception:
                return
            if clicks and clicks > 0:
                # Clear the user and re-render by navigating to Login and reloading
                try:
                    UserStore.logout()
                except Exception:
                    # Fallback to explicit None if logout() not available
                    UserStore.set_user(None)
                ui.update_navs("main_nav", selected="Login")
                ui.notification_show("You have been logged out.", type="message")
                # Hard reload to rebuild UI based on logged-out state
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )
        # ... existing code ...

app = App(FitnessWarriorApp.build_app_ui(), FitnessWarriorApp.server)

if __name__ == "__main__":
    run_app(app, port=FitnessWarriorApp.DEFAULT_PORT, reload=True)
