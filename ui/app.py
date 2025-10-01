import logging
from typing import Any
from shiny import App, ui, run_app, render

from data.db.db_model import User
from ui.user_store import UserStore
from utils.Os import Os
from .pages import dashboard, reports, settings, combat_test

from .pages import usermangement
from .pages import phef
from .pages import sessions

from data.db.db_model import User, Role


class FitnessWarriorApp:

    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000

    # Public static user store
    USER_STORE: UserStore = UserStore()

    @classmethod
    def setup_logger(cls):
        """
        Sets up logging by adding a console handler and file handler.
        Both handlers will log messages at the informational level and above.
        """
        # Create logger
        cls.logger = logging.getLogger()  # Root logger
        cls.logger.setLevel(logging.INFO)  # Set global logging level


        # Create a formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Ensure logs directory exists
        project_root = Os.get_project_root()
        if project_root:
            log_dir = project_root / "logs"
            log_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist

            # File handler -> Logs to a file
            file_handler = logging.FileHandler(
                log_dir / "application.log", mode="a"
            )  # Append mode
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            # Add file handler to the root logger
            if not any(isinstance(h, logging.FileHandler) for h in cls.logger.handlers):
                cls.logger.addHandler(file_handler)

        # Console handler -> Logs to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Add console handler to the root logger
        if not any(
                isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
                for h in cls.logger.handlers
        ):
            cls.logger.addHandler(console_handler)



    @staticmethod
    def build_app_ui():
        # Render the whole navbar dynamically via render.ui so it can change without reload.
        return ui.page_fillable(
            ui.output_ui("main_nav_container"),
        )

    # ... existing code ...

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        """
        Register server logic for each page.
        """
        # All pages will be mounted lazily when their tab becomes active.
        pass

    @staticmethod
    def server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive
        from ui.services.db_service import DBService  # ensure DB access is available here
        db_service = DBService("ui/config/config.yml")


        FitnessWarriorApp.register_pages_server(input, output, session)

        # Map navbar labels to their page server functions
        servers_by_tab = {
            "User Management": usermangement.server,
            "PHEF Tests": phef.server,
            "Combat Tests": combat_test.server,
            "Sessions": sessions.server,
            "Dashboard": dashboard.server,
            "Reports": reports.server,
            "Settings": settings.server,
            # ... existing code ...
        }

        mounted = reactive.Value(set())

        status_text = reactive.Value("")
        login_user_text = reactive.Value("")
        # Version bump to force navbar re-render on role/user change
        nav_version = reactive.Value(0)

        def build_navbar():
            # Build role-aware navbar elements; never insert None
            user = UserStore.get_user()
            role = getattr(user, "role", None)

            def safe(panel):
                return panel if panel is not None else None

            nav_items = []

            # Admin menu
            if role == Role.ADMIN:
                admin_children = [safe(usermangement.get_ui())]
                admin_children = [c for c in admin_children if c is not None]
                if admin_children:
                    nav_items.append(ui.nav_menu("Admin", *admin_children))

            # Base tabs
            nav_items.extend([i for i in [safe(dashboard.get_ui()), safe(reports.get_ui()), safe(settings.get_ui()),safe(phef.get_ui()),safe(combat_test.get_ui())] if
                              i is not None])

            # Logged-in user tabs (also appear for admin if desired)
            if user is not None:
                nav_items.extend([i for i in [safe(sessions.get_ui())] if i is not None])

            # Right-side controls
            nav_items.append(ui.nav_spacer())
            nav_items.append(
                ui.nav_control(
                    ui.div(ui.output_text("login_user"), style="display: flex; align-items: center; height: 100%;")
                )
            )
            nav_items.append(ui.nav_control(ui.input_action_button("logout_btn", "Logout")))

            nav_items = [i for i in nav_items if i is not None]

            return ui.page_navbar(
                *nav_items,
                title=FitnessWarriorApp.APP_TITLE,
                id="main_nav",
            )

        @output
        @render.ui
        def main_nav_container():
            # Depend on nav_version so we re-render navbar when it changes
            _ = nav_version.get()
            return build_navbar()

        @output
        @render.text
        def login_status():
            return status_text()

        @output
        @render.text
        def login_user():
            return login_user_text()

        @reactive.Effect
        async def login_dialog():
            status_text.set("")

            login = ui.div(
                ui.h2("Login"),
                ui.input_text("username_login", "Username"),
                ui.input_password("password_login", "Password"),
                ui.input_action_button("handle_login", "Login"),
                ui.div(
                    ui.output_text("login_status", inline=True),
                    style="color: red; font-weight: bold;"
                ),
            )
            ui.modal_show(ui.modal(login, easy_close=False, size="m", footer=None))

        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login():
            logger = getattr(FitnessWarriorApp, "logger", logging.getLogger(__name__))
            username_login = input.username_login().lower()
            password_login = input.password_login()
            try:
                if await db_service.check_user(username_login, password_login):
                    user = await db_service.get_user_by_username(username_login)
                    UserStore.set_user(user)
                    login_user_text.set(f"User :{username_login} Role: {user.role}")
                    status_text.set("")
                    ui.modal_remove()
                    # Trigger navbar rebuild without page reload
                    nav_version.set(nav_version.get() + 1)

                    logger.info(f"User {username_login} logged in successfully")

                else:
                    status_text.set("Invalid username or password.")
            except Exception as e:
                logger.error(f"An error occurred while logging in. Please try again. {e}")
                status_text.set(f"An error occurred while logging in. Please try again. {e}")


        @reactive.Effect
        def _mount_on_nav_activation():
            # This will work as long as the current navbar has id="main_nav"
            try:
                active = input.main_nav()
            except Exception:
                # main_nav not yet mounted
                return
            if not active:
                return
            already = mounted.get()
            if active in servers_by_tab and active not in already:
                servers_by_tab[active](input, output, session)
                mounted.set({*already, active})

        @reactive.Effect
        def _on_logout_button_click():
            try:
                clicks = input.logout_btn()
            except Exception:
                return
            if clicks and clicks > 0:
                # Clear the user and re-render by navigating to a known tab and reloading
                try:
                    UserStore.logout()
                except Exception as e:
                    UserStore.set_user(None)
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You have been logged out.", type="message")
                # Rebuild UI (hide/unhide pages) after role change
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )


app = App(FitnessWarriorApp.build_app_ui(), FitnessWarriorApp.server)

if __name__ == "__main__":
    
    run_app(app, host="0.0.0.0", port=FitnessWarriorApp.DEFAULT_PORT, reload=True)
