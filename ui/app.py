import logging
from typing import Any, Optional
from shiny import App, ui, render
from data.db.db_model import Role
from utils.Os import Os
from config.appliccation_config import ApplicationConfig
from .pages import dashboard, reports, settings, combat_test, own_unit, dashboard_own_unit, ind_test_show
from .pages import usermangement
from .pages import phef
from .pages import sessions
from .pages import functional_test
from .pages import swim_test


class FitnessWarriorApp:
    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000
    LOGIN_MODAL_SIZE = "m"


    @classmethod
    def _create_logger_formatter(cls) -> logging.Formatter:
        return logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @classmethod
    def _ensure_log_file_handler(cls, logger: logging.Logger, formatter: logging.Formatter) -> None:
        project_root = Os.get_project_root()
        if not project_root:
            return
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "application.log", mode="a")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            logger.addHandler(file_handler)

    @classmethod
    def setup_logger(cls) -> None:
        cls.logger = logging.getLogger()
        cls.logger.setLevel(logging.INFO)
        formatter = cls._create_logger_formatter()
        cls._ensure_log_file_handler(cls.logger, formatter)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        if not any(
                isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
                for h in cls.logger.handlers
        ):
            cls.logger.addHandler(console_handler)

    @staticmethod
    def build_app_ui():
        return ui.page_fillable(
            ui.output_ui("main_nav_container"),
        )

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive
        servers_by_tab = {
            "User Management": usermangement.server,
            "PHEF Tests": phef.server,
            "Combat Tests": combat_test.server,
            "Functional Tests": functional_test.server,
            "Swimming Tests": swim_test.server,
            "Sessions": sessions.server,
            "Dashboard": dashboard.server,
            "Reports": reports.server,
            "Settings": settings.server,
            "Own Unit": own_unit.server,
            "Own Dashboard" : dashboard_own_unit.server,
            "Individual" : ind_test_show.server
        }
        mounted = reactive.Value(set())

        @reactive.Effect
        def _mount_on_nav_activation_register_only():
            try:
                active = input.main_nav()
            except Exception:
                return
            if not active:
                return
            already = mounted.get()
            if active in servers_by_tab and active not in already:
                servers_by_tab[active](input, output, session)
                mounted.set({*already, active})

    @staticmethod
    def server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive
        from services.db_service import DBService
        db_service = DBService()


        FitnessWarriorApp.register_pages_server(input, output, session)

        status_text = reactive.Value("")
        login_user_text = reactive.Value("")
        nav_version = reactive.Value(0)

        def _safe_panel(panel: Optional[Any]) -> Optional[Any]:
            return panel if panel is not None else None

        def _build_test_menu() -> ui.nav_menu:
            items = [
                _safe_panel(phef.get_ui()),
                _safe_panel(combat_test.get_ui()),
                _safe_panel(functional_test.get_ui()),
                _safe_panel(swim_test.get_ui()),
            ]
            items = [c for c in items if c is not None]
            return ui.nav_menu("Test", *items)

        def _build_admin_menu(role: Optional[Role]) -> Optional[ui.nav_menu]:
            if role != Role.ADMIN:
                return None
            admin_children = [
                _safe_panel(usermangement.get_ui()),
                _safe_panel(settings.get_ui()),
            ]
            admin_children = [c for c in admin_children if c is not None]
            return ui.nav_menu("Admin", *admin_children) if admin_children else None

        def _get_session_user():
            return getattr(session, "user", None)

        def _set_session_user(user):
            setattr(session, "user", user)

        def _clear_session_user():
            if hasattr(session, "user"):
                delattr(session, "user")

        def build_main_navbar() -> ui.page_navbar:
            user = _get_session_user()
            role = getattr(user, "role", None)
            nav_items: list[Any] = []

            nav_items.extend(
                [i for i in [_safe_panel(dashboard_own_unit.get_ui()),
                             _safe_panel(own_unit.get_ui()), ] if i is not None]
            )
            admin_menu = _build_admin_menu(role)
            if role is Role.ADMIN:
                if admin_menu is not None:
                    nav_items.append(_build_test_menu())
                    nav_items.append(_safe_panel(ind_test_show.get_ui()))
                    nav_items.append(_safe_panel(reports.get_ui()))
                    nav_items.append(_safe_panel(dashboard.get_ui()))
                    nav_items.append(_safe_panel((sessions.get_ui())))
                    nav_items.append(admin_menu)
            elif role is Role.USER:
                nav_items.append(_safe_panel(own_unit.get_ui()))
                nav_items.append(_safe_panel(ind_test_show.get_ui()))
            elif role is Role.PTI:
                nav_items.append(_safe_panel(ind_test_show.get_ui()))
                nav_items.append(_build_test_menu())
                nav_items.append(_safe_panel(dashboard.get_ui()))
                nav_items.append(_safe_panel(reports.get_ui()))
                nav_items.append(admin_menu)
            elif role is Role.APTI:
                nav_items.append(_safe_panel(ind_test_show.get_ui()))
                nav_items.append(_build_test_menu())
                nav_items.append(_safe_panel(dashboard.get_ui()))
                nav_items.append(_safe_panel(reports.get_ui()))
            elif role is Role.PLANNER:
                nav_items.append(_safe_panel(dashboard.get_ui()))
                nav_items.append(_safe_panel((sessions.get_ui())))

            nav_items.append(ui.nav_spacer())
            nav_items.append(
                ui.nav_control(
                    ui.div(ui.output_text("login_user"), style="display: flex; align-items: center; height: 100%;")
                )
            )
            nav_items.append(ui.nav_control(ui.input_action_button("logout_btn", "Logout")))
            nav_items = [i for i in nav_items if i is not None]
            return ui.page_navbar(*nav_items, id="main_nav")

        @output
        @render.ui
        def main_nav_container():
            _ = nav_version.get()
            return build_main_navbar()

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
                ui.div(ui.output_text("login_status", inline=True), style="color: red; font-weight: bold;"),
            )
            ui.modal_show(ui.modal(login, easy_close=False, size=FitnessWarriorApp.LOGIN_MODAL_SIZE, footer=None))

        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login():
            logger = getattr(FitnessWarriorApp, "logger", logging.getLogger(__name__))
            username_login = (input.username_login() or "").lower()
            password_login = input.password_login()
            try:
                if await db_service.check_user(username_login, password_login):
                    user = await db_service.get_user_by_username(username_login)
                    _set_session_user(user)
                    login_user_text.set(f"User: {username_login}  Role: {user.role}  Unit: {ApplicationConfig().own_unit}")
                    status_text.set("")
                    ui.modal_remove()
                    nav_version.set(nav_version.get() + 1)
                    logger.info(f"User {username_login} logged in successfully")
                else:
                    status_text.set("Invalid username or password.")
            except Exception as e:
                logger.error(f"Login error: {e}")
                status_text.set("An error occurred while logging in. Please try again.")

        @reactive.Effect
        def _mount_on_nav_activation():
            try:
                _ = input.main_nav()
            except Exception:
                return

        @reactive.Effect
        def _on_logout_button_click():
            try:
                clicks = input.logout_btn()
            except Exception:
                return
            if clicks and clicks > 0:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You have been logged out.", type="message")
                ui.insert_ui(selector="body", ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"))

        # ===== Auto-logout after 10 minutes of inactivity (no ui.now) =====
        import time
        INACTIVITY_LIMIT_SECONDS = 600  # 10 minutes
        last_activity = reactive.Value(time.time())

        @output
        @render.ui
        def _activity_probe():
            return ui.tags.script(
                """
                (function(){
                  const report = () => Shiny.setInputValue('activity_ping', Date.now(), {priority: 'event'});
                  const events = ['click','keydown','mousemove','scroll','touchstart','touchmove','visibilitychange'];
                  events.forEach(ev => window.addEventListener(ev, report, {passive:true}));
                  setInterval(report, 30000);
                  report();
                })();
                """
            )

        @reactive.Effect
        def _record_activity():
            try:
                _ = input.activity_ping()
            except Exception:
                return
            last_activity.set(time.time())

        @reactive.Effect
        def _reset_on_nav_or_login():
            try:
                _ = input.main_nav()
            except Exception:
                pass
            _ = nav_version.get()
            last_activity.set(time.time())

        @reactive.Effect
        def _auto_logout_timer():
            reactive.invalidate_later(5)  # check every 5s
            user = _get_session_user()
            if not user:
                return
            ts = last_activity.get() or time.time()
            if time.time() - ts >= INACTIVITY_LIMIT_SECONDS:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You were logged out due to 10 minutes of inactivity.", type="warning")
                ui.insert_ui(selector="body", ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"))

# Initialize logging once at import and expose ASGI app
FitnessWarriorApp.setup_logger()
app = App(ui=FitnessWarriorApp.build_app_ui(), server=FitnessWarriorApp.server)
