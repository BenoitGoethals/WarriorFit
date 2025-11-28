import logging
from typing import Any, Optional
from shiny import App, ui, render

from warriorfit.data.db.abc_repository import ABCRepository
from warriorfit.data.db.db_model import Role
from warriorfit.mom.broker import Broker
from warriorfit.services.service_user import UserService
from warriorfit.ui.user_store import UserStore
from warriorfit.utils.Os import Os
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.ui.pages import reports, settings, combat_test, own_unit, dashboard_own_unit, ind_test_show, cross, \
    cross_planning, calendar_events, auditlog_events, status_tests, cross_statics, march, status_login_user
from warriorfit.ui.pages import usermangement
from warriorfit.ui.pages import phef
from warriorfit.ui.pages import sessions
from warriorfit.ui.pages import functional_test
from warriorfit.ui.pages import swim_test


class FitnessWarriorApp:
    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000
    LOGIN_MODAL_SIZE = "m"
    _broker=Broker()

    def __init__(self):
        self.setup_logger()

    @classmethod
    def get_broker(cls):
        return cls._broker

    @classmethod
    def setup_logger(cls) -> None:
        import yaml
        import logging.config

        project_root = Os.get_project_root()
        if not project_root:
            return

        # Ensure logs directory exists
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        config_path = project_root / "warriorfit" / "config" / "logging_configuration.yml"

        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            if "handlers" in config and "file" in config["handlers"]:
                config["handlers"]["file"]["filename"] = str(log_dir / "application.log")

            logging.config.dictConfig(config)
            cls.logger = logging.getLogger()
        else:
            logging.basicConfig(level=logging.INFO)
            cls.logger = logging.getLogger()

    @staticmethod
    def build_app_ui():
        return ui.page_fillable(
            ui.output_ui("main_nav_container"),
        )

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive
        servers_by_tab = {
            "Cross Planning": cross_planning.server,
            "PHEF Not done": status_tests.server,
            "Audit Logs": auditlog_events.server,
            "Cross": cross.server,
            "User Management": usermangement.server,
            "PHEF Tests": phef.server,
            "Combat Tests": combat_test.server,
            "Functional Tests": functional_test.server,
            "Swimming Tests": swim_test.server,
            "Sessions": sessions.server,
            "Reports": reports.server,
            "Settings": settings.server,
            "Status Unit": own_unit.server,
            "Dashboard": dashboard_own_unit.server,
            "Individual": ind_test_show.server,
            # Calendar server mounted independently (modal lives outside navbar)
            "CalendarEvents": calendar_events.server,
            "Cross Statics": cross_statics.server,
            "March" : march.server,
            "Welcome" : status_login_user.server


        }
        mounted = reactive.Value(set())

        @reactive.Effect
        def _mount_on_nav_activation_register_only():
            try:
                active = input.main_nav()
            except Exception:
                active = None
            already = mounted.get()
            if active and active in servers_by_tab and active not in already:
                servers_by_tab[active](input, output, session)
                mounted.set({*already, active})
            # Ensure calendar server is mounted so modal UI works even if no tab selected
            if "CalendarEvents" not in mounted.get():
                servers_by_tab["CalendarEvents"](input, output, session)
                mounted.set({*mounted.get(), "CalendarEvents"})

    @staticmethod
    def server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive
        user_service = UserService()
        FitnessWarriorApp.register_pages_server(input, output, session)
        status_text = reactive.Value("")
        login_user_text = reactive.Value("")
        nav_version = reactive.Value(0)


        # Open/close Calendar modal from app-level button
        @reactive.Effect
        @reactive.event(input.open_calendar_modal_global)
        def _open_calendar_modal():
            # Force calendar to re-run before showing the modal
            calendar_events.refresh()

            ui.modal_show(
                ui.modal(
                    calendar_events.get_ui(),
                    title="Calendar",
                    easy_close=True,
                    size="xl",
                    footer=ui.input_action_button("close_calendar_modal_global", "Close"),
                )
            )

        @reactive.Effect
        @reactive.event(input.open_personal_calendar_modal_global)
        def _open_personal_calendar_modal():
            # Force personal calendar to re-run before showing the modal
            calendar_events.refresh()

            ui.modal_show(
                ui.modal(
                    calendar_events.get_ui(all_test=False),
                    title="Personal Calendar",
                    easy_close=True,
                    size="xl",
                    footer=ui.input_action_button("close_calendar_modal_global", "Close"),
                )
            )

        @reactive.Effect
        @reactive.event(input.close_calendar_modal_global)
        def _close_calendar_modal():
            ui.modal_remove()

        def _safe_panel(panel: Optional[Any]) -> Optional[ui.Tag]:
            return panel if panel is not None else None

        def _build_test_menu() -> ui.nav_menu:
            items = [
                _safe_panel(phef.get_ui()),
                _safe_panel(combat_test.get_ui()),
                _safe_panel(functional_test.get_ui()),
                _safe_panel(swim_test.get_ui()),
                _safe_panel(ind_test_show.get_ui()),
                _safe_panel(march.get_ui()),
                _safe_panel(status_tests.get_ui()),
                _safe_panel((sessions.get_ui()))
            ]
            items = [c for c in items if c is not None]
            return ui.nav_menu("Psychical Tests", *items)

        def _build_cross_menu() -> ui.nav_menu:
            items = [
                _safe_panel(cross_statics.get_ui()),
                _safe_panel(cross_planning.get_ui()),
                _safe_panel(cross.get_ui()),
            ]
            items = [c for c in items if c is not None]
            return ui.nav_menu("Cross/Runs", *items)

        def _build_admin_menu(role: Optional[Role]) -> Optional[ui.nav_menu]:
            if role != Role.ADMIN:
                return None
            admin_children = [
                _safe_panel(auditlog_events.get_ui()),
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

            admin_menu = _build_admin_menu(role)
            if role is Role.ADMIN:
                if admin_menu is not None:
                    # Calendar removed from navbar; use global button + modal
                    nav_items.append(_safe_panel(status_login_user.get_ui()))
                    nav_items.append(_safe_panel(dashboard_own_unit.get_ui()))
                    nav_items.append(own_unit.get_ui())
                    nav_items.append(_build_test_menu())
                    nav_items.append(_safe_panel(reports.get_ui()))
                    nav_items.append(_build_cross_menu())
                    nav_items.append(admin_menu)
            elif role is Role.GUEST:
                nav_items.append(_safe_panel(own_unit.get_ui()))
                nav_items.append(_safe_panel(ind_test_show.get_ui()))
            elif role is Role.PTI:
                nav_items.append(_safe_panel(status_login_user.get_ui()))
                nav_items.append(dashboard_own_unit.get_ui())
                nav_items.append(own_unit.get_ui())

                nav_items.append(_build_test_menu())
                nav_items.append(_build_cross_menu())
                nav_items.append(_safe_panel(reports.get_ui()))
            elif role is Role.APTI:
                nav_items.append(_safe_panel(status_login_user.get_ui()))
                nav_items.append(dashboard_own_unit.get_ui())
                nav_items.append(own_unit.get_ui())
                nav_items.append(_build_test_menu())
                nav_items.append(_safe_panel(reports.get_ui()))
                nav_items.append(_build_cross_menu())
            elif role is Role.PLANNER:
                nav_items.append(_safe_panel((sessions.get_ui())))
            nav_items.append(ui.nav_spacer())
            nav_items.append(
                ui.nav_control(
                    ui.div(ui.output_text("login_user"), style="display: flex; align-items: center; height: 100%;")
                )
            )
            nav_items.append(ui.nav_control(
            ui.input_action_button("open_personal_calendar_modal_global", "Personal Calendar", class_="btn btn-primary")))
            nav_items.append(ui.nav_control(ui.input_action_button("open_calendar_modal_global", "Open Calendar", class_="btn btn-primary")))
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
                if await user_service.check_user(username_login, password_login):
                    user = await user_service.get_user_by_username(username_login)
                    UserStore.set_user(user)
                    await user_service.add_audit_log(f"User {username_login} logged in", "login")
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

        import time
        INACTIVITY_LIMIT_SECONDS = 600
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
            except Exception as e:
                logging.error(f"Error recording activity: {e}")
                return
            last_activity.set(time.time())

        @reactive.Effect
        def _reset_on_nav_or_login():
            try:
                _ = input.main_nav()
            except Exception as e:
                logging.error(f"Error resetting nav: {e}")
                pass
            _ = nav_version.get()
            last_activity.set(time.time())

        @reactive.Effect
        def _auto_logout_timer():
            reactive.invalidate_later(5)
            user = _get_session_user()
            if not user:
                return
            ts = last_activity.get() or time.time()
            if time.time() - ts >= INACTIVITY_LIMIT_SECONDS:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You were logged out due to 10 minutes of inactivity.", type="warning")
                ui.insert_ui(selector="body", ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"))

FitnessWarriorApp.setup_logger()
FitnessWarriorApp.get_broker().start()
app = App(ui=FitnessWarriorApp.build_app_ui(), server=FitnessWarriorApp.server)
