import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from shiny import App, ui, render

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import Role
from warriorfit.mom.broker import Broker
from warriorfit.services.service_user import UserService
from warriorfit.ui.user_store import UserStore
from warriorfit.utils.Os import Os
from warriorfit.ui.pages import (
    reports,
    settings,
    combat_test,
    own_unit,
    dashboard_own_unit,
    ind_test_show,
    cross,
    cross_planning,
    calendar_events,
    auditlog_events,
    status_tests,
    cross_statics,
    march,
    status_login_user,
    reserve_fitness_room,
    status_application,
)
from warriorfit.ui.pages import usermangement
from warriorfit.ui.pages import phef
from warriorfit.ui.pages import sessions
from warriorfit.ui.pages import functional_test
from warriorfit.ui.pages import swim_test


@dataclass(frozen=True)
class PageSpec:
    """
    A page definition: what it is (UI + server) and who may see it.
    This keeps "roles" separate from "pages".
    """
    tab: str
    group: str  # "root" | "Psychical Tests" | "Cross/Runs" | "Admin"
    ui_factory: Callable[[], Optional[Any]]
    server_factory: Callable[[Any, Any, Any], Any] | None
    allowed_roles: set[Role]


class FitnessWarriorApp:
    """
    Main application class for the Fitness Warrior app.
    """

    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000
    _broker = Broker()

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

    # -----------------------------
    # Pages (what exists) + Roles (who can see)
    # -----------------------------

    @staticmethod
    def _pages() -> list[PageSpec]:
        # If you want to change visibility, do it HERE (roles), not in navbar code.
        return [
            # Root-level pages
            PageSpec(
                tab="Welcome",
                group="root",
                ui_factory=status_login_user.get_ui,
                server_factory=status_login_user.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Dashboard",
                group="root",
                ui_factory=dashboard_own_unit.get_ui,
                server_factory=dashboard_own_unit.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Status Unit",
                group="root",
                ui_factory=own_unit.get_ui,
                server_factory=own_unit.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI, Role.GUEST},
            ),
            PageSpec(
                tab="Individual",
                group="root",
                ui_factory=ind_test_show.get_ui,
                server_factory=ind_test_show.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI, Role.GUEST},
            ),
            PageSpec(
                tab="Reports",
                group="root",
                ui_factory=reports.get_ui,
                server_factory=reports.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Reserve Room",
                group="root",
                ui_factory=reserve_fitness_room.get_ui,
                server_factory=reserve_fitness_room.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Sessions",
                group="root",
                ui_factory=sessions.get_ui,
                server_factory=sessions.server,
                allowed_roles={Role.PLANNER},
            ),
            # Psychical Tests (menu)
            PageSpec(
                tab="PHEF Tests",
                group="Psychical Tests",
                ui_factory=phef.get_ui,
                server_factory=phef.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Combat Tests",
                group="Psychical Tests",
                ui_factory=combat_test.get_ui,
                server_factory=combat_test.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Functional Tests",
                group="Psychical Tests",
                ui_factory=functional_test.get_ui,
                server_factory=functional_test.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Swimming Tests",
                group="Psychical Tests",
                ui_factory=swim_test.get_ui,
                server_factory=swim_test.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="March",
                group="Psychical Tests",
                ui_factory=march.get_ui,
                server_factory=march.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="PHEF Not done",
                group="Psychical Tests",
                ui_factory=status_tests.get_ui,
                server_factory=status_tests.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Sessions",
                group="Psychical Tests",
                ui_factory=sessions.get_ui,
                server_factory=sessions.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            # Cross/Runs (menu)
            PageSpec(
                tab="Cross Statics",
                group="Cross/Runs",
                ui_factory=cross_statics.get_ui,
                server_factory=cross_statics.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Cross Planning",
                group="Cross/Runs",
                ui_factory=cross_planning.get_ui,
                server_factory=cross_planning.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            PageSpec(
                tab="Cross",
                group="Cross/Runs",
                ui_factory=cross.get_ui,
                server_factory=cross.server,
                allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
            ),
            # Admin (menu)
            PageSpec(
                tab="Audit Logs",
                group="Admin",
                ui_factory=auditlog_events.get_ui,
                server_factory=auditlog_events.server,
                allowed_roles={Role.ADMIN},
            ),
            PageSpec(
                tab="User Management",
                group="Admin",
                ui_factory=usermangement.get_ui,
                server_factory=usermangement.server,
                allowed_roles={Role.ADMIN},
            ),
            PageSpec(
                tab="Settings",
                group="Admin",
                ui_factory=settings.get_ui,
                server_factory=settings.server,
                allowed_roles={Role.ADMIN},
            ),
            PageSpec(
                tab="Status Application",
                group="Admin",
                ui_factory=status_application.get_ui,
                server_factory=status_application.server,
                allowed_roles={Role.ADMIN},
            ),
        ]

    @staticmethod
    def _pages_for_role(role: Optional[Role]) -> list[PageSpec]:
        if role is None:
            return []
        return [p for p in FitnessWarriorApp._pages() if role in p.allowed_roles]

    @staticmethod
    def build_app_ui():
        return ui.page_fillable(
            ui.output_ui("main_nav_container"),
        )

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        """
        Mount server logic lazily when a tab is activated.
        """
        from shiny import reactive

        servers_by_tab: dict[str, Callable[[Any, Any, Any], Any]] = {
            p.tab: p.server_factory
            for p in FitnessWarriorApp._pages()
            if p.server_factory is not None
        }

        # Calendar server mounted independently (modal lives outside navbar)
        servers_by_tab["CalendarEvents"] = calendar_events.server

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

        def _get_session_user():
            return getattr(session, "user", None)

        def _set_session_user(user):
            setattr(session, "user", user)

        def _clear_session_user():
            if hasattr(session, "user"):
                delattr(session, "user")

        def _safe_panel(panel: Optional[Any]) -> Optional[ui.Tag]:
            return panel if panel is not None else None

        def _build_menu(group: str, pages_for_role: list[PageSpec]) -> Optional[ui.Tag]:
            children = [
                _safe_panel(p.ui_factory())
                for p in pages_for_role
                if p.group == group
            ]
            children = [c for c in children if c is not None]
            return ui.nav_menu(group, *children) if children else None

        def build_main_navbar():
            user = _get_session_user()
            role = getattr(user, "role", None)
            pages_for_role = FitnessWarriorApp._pages_for_role(role)

            nav_items: list[Any] = []

            # Root pages first (flat)
            for p in pages_for_role:
                if p.group == "root":
                    nav_items.append(_safe_panel(p.ui_factory()))

            # Grouped menus
            nav_items.append(_build_menu("Psychical Tests", pages_for_role))
            nav_items.append(_build_menu("Cross/Runs", pages_for_role))
            nav_items.append(_build_menu("Admin", pages_for_role))

            # Global controls
            nav_items.append(ui.nav_spacer())
            nav_items.append(
                ui.nav_control(
                    ui.div(ui.output_text("login_user"), style="display: flex; align-items: center; height: 100%;")
                )
            )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button(
                        "open_personal_calendar_modal_global",
                        "Personal Calendar",
                        class_="btn btn-primary",
                    )
                )
            )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button("open_calendar_modal_global", "Open Calendar", class_="btn btn-primary")
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
            ui.modal_show(ui.modal(login, easy_close=False, size="m", footer=None))

        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login():
            logger = getattr(FitnessWarriorApp, "logger", logging.getLogger(__name__))
            username_login = (input.username_login() or "").lower()
            password_login = input.password_login()
            try:
                if await user_service.check_user(username_login, password_login):
                    user = await user_service.get_user_by_username(username_login)
                    if user.is_active is False:
                        status_text.set("Your account is disabled. Please contact your administrator.")
                        return
                    UserStore.set_user(user)
                    await user_service.add_audit_log(f"User {username_login} logged in", "login")
                    _set_session_user(user)
                    login_user_text.set(
                        f"User: {username_login}  Role: {user.role}  Unit: {ApplicationConfig().own_unit}"
                    )
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
            except Exception as e:
                logging.error(f"Error mounting nav: {e}")
                return

        @reactive.Effect
        def _on_logout_button_click():
            try:
                clicks = input.logout_btn()
            except Exception as e:
                logging.error(f"Error handling logout button: {e}")
                return
            if clicks and clicks > 0:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You have been logged out.", type="message")
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )

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
            if time.time() - ts >= 600:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You were logged out due to 10 minutes of inactivity.", type="warning")
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )


FitnessWarriorApp.setup_logger()
FitnessWarriorApp.get_broker().start()
app = App(ui=FitnessWarriorApp.build_app_ui(), server=FitnessWarriorApp.server)
