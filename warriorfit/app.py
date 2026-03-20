import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from warriorfit.security.rate_limiter import login_rate_limiter
from dataclasses import dataclass
from typing import Any, Callable, Optional
from shiny import App, ui, render
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.core.container import Container
from warriorfit.data.model.db_model import Role
from warriorfit.mom.broker import Broker
from warriorfit.ui.user_store import UserStore
from warriorfit.utils.Os import Os

# Initialize and wire the container BEFORE importing pages
_container = Container()


# NOW import pages after wiring is complete
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
    _container: Container = _container
    _broker: Broker = _container.broker()

    def __init__(self):
        self.setup_logger()

    @classmethod
    def get_broker(cls):
        return cls._broker

    @classmethod
    def setup_logger(cls) -> None:
        """
        Sets up logging configuration for the application using a YAML-based configuration file
        and handles the creation of necessary log directories and files. If the configuration
        file does not exist, defaults to basic logging with the INFO level.

        :param cls: The class on which the logger will be configured.

        :return: None
        """
        import yaml
        import logging.config

        project_root = Os.get_project_root()
        if not project_root:
            return

        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        config_path = (
            project_root / "warriorfit" / "config" / "logging_configuration.yml"
        )

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                logging.config.dictConfig(config)
                logging.getLogger(__name__)
            except (yaml.YAMLError, KeyError, ValueError) as e:
                logging.basicConfig(level=logging.INFO)
                logging.getLogger().error(f"Failed to load logging config: {e}")
        else:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger()

    # -----------------------------
    # Pages (what exists) + Roles (who can see)
    # -----------------------------

    @staticmethod
    def _pages() -> list[PageSpec]:
        """
        Returns a list of page specifications, defining tabs, menu groups, UI and server factories,
        and allowed roles necessary for visibility and access control. The configuration determines
        the structure of the application's navigation and accessibility for all user roles.

        :param tab: Specifies the name of the tab for the page.
        :param group: Defines the group to which the page belongs, forming menu categories.
        :param ui_factory: A callable that returns the user interface structure for the page.
        :param server_factory: A callable that initializes and manages the server logic for the page.
        :param allowed_roles: A set of roles permitted to view and interact with the defined page.

        :return: A list of `PageSpec` objects representing the configuration of pages in the application.
        :rtype: list[PageSpec]
        """
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
                tab="Reserve Sport Area",
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
        """
        Filters and retrieves a list of pages allowed for the given role.

        This method returns a filtered list of PageSpec objects that are accessible to
        the provided role. If the role is None, it will return an empty list. The method
        analyzes the permissions defined in each page's `allowed_roles` attribute to
        determine accessibility.

        :param role: The role whose allowed pages are to be retrieved. Must be of type
            Role or None.
        :return: A list of PageSpec objects representing the pages that the given role
            is permitted to access.
        :rtype: list[PageSpec]
        """
        if role is None:
            return []
        return [p for p in FitnessWarriorApp._pages() if role in p.allowed_roles]

    @staticmethod
    def build_app_ui():
        return ui.page_fillable(
            ui.tags.head(
                ui.tags.link(rel="stylesheet", href="custom.css"),
            ),
            ui.output_ui("main_content_container"),
            ui.tags.script(
                """
                $(document).on('shown.bs.tab', function() {
                    setTimeout(function() {
                        window.dispatchEvent(new Event('resize'));
                    }, 100);
                });
                """
            ),
        )

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        """
        Defines a static method for registering server logic for different navigation tabs
        within the application. The method dynamically mounts the server logic associated
        with a tab only when the tab is activated through the main navigation component.
        Additionally, a calendar-related server is independently mounted and remains outside
        the main navigation bar.

        The method uses reactive constructs to ensure optimal performance and avoids mounting
        any unnecessary servers until their corresponding navigation tab is activated.

        :param input: Input object containing reactive elements, such as navigation
            component states and triggered events.
        :type input: Any
        :param output: Output object used to handle updates to UI components in
            response to server logic.
        :type output: Any
        :param session: Current user session object containing session-specific
            state and data.
        :type session: Any

        :return: None
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
            """
            Sets up reactive effects that mount server functions on navigation tab activation register
            and ensures that the "CalendarEvents" server is always mounted. This function observes the
            currently active navigation tab and executes the corresponding server function if it is not
            yet mounted. The mounted state is updated appropriately to track which servers are active.

            :param input: Input data or context passed for reactive operations.
            :type input: Any
            :param output: Output data or context associated with reactive operations.
            :type output: Any
            :param session: Session details or context for current user activity.
            :type session: Any

            :return: None
            """
            try:
                active = input.main_nav()
            except (AttributeError, KeyError):
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

        user_service = FitnessWarriorApp._container.user_service()
        FitnessWarriorApp.register_pages_server(input, output, session)

        status_text = reactive.Value("")
        login_user_text = reactive.Value("")
        nav_version = reactive.Value(0)

        # Open/close Calendar panel from app-level button
        show_calendar = reactive.Value(False)

        @reactive.Effect
        @reactive.event(input.open_calendar_modal_global)
        def _toggle_calendar():
            calendar_events.refresh()
            show_calendar.set(not show_calendar.get())
            if show_calendar.get():
                show_personal_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_calendar)
        def _close_calendar():
            show_calendar.set(False)

        show_personal_calendar = reactive.Value(False)

        @reactive.Effect
        @reactive.event(input.open_personal_calendar_modal_global)
        def _toggle_personal_calendar():
            calendar_events.refresh()
            show_personal_calendar.set(not show_personal_calendar.get())
            if show_personal_calendar.get():
                show_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_personal_calendar)
        def _close_personal_calendar():
            show_personal_calendar.set(False)

        @output
        @render.ui
        def main_content_container():
            if show_calendar.get():
                return ui.div(
                    ui.div(
                        ui.h3("📅 Calendar"),
                        ui.input_action_button(
                            "close_calendar", "✕ Close", class_="btn btn-outline-secondary btn-sm"
                        ),
                        class_="wf-calendar-panel-header",
                    ),
                    ui.div(calendar_events.get_ui(), class_="wf-calendar-panel-body"),
                    class_="wf-calendar-panel",
                )
            elif show_personal_calendar.get():
                return ui.div(
                    ui.div(
                        ui.h3("📅 Personal Calendar"),
                        ui.input_action_button(
                            "close_personal_calendar",
                            "✕ Close",
                            class_="btn btn-outline-secondary btn-sm",
                        ),
                        class_="wf-calendar-panel-header",
                    ),
                    ui.div(
                        calendar_events.get_ui(all_test=False), class_="wf-calendar-panel-body"
                    ),
                    class_="wf-calendar-panel",
                )
            else:
                _ = nav_version.get()
                return build_main_navbar()

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
                _safe_panel(p.ui_factory()) for p in pages_for_role if p.group == group
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
                    ui.div(
                        ui.output_text("login_user"),
                        style="display:flex; align-items:center; height:100%; color:rgba(255,255,255,0.7); font-size:0.8rem; padding:0 0.5rem; white-space:nowrap; max-width:280px; overflow:hidden; text-overflow:ellipsis;",
                    )
                )
            )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button(
                        "open_personal_calendar_modal_global",
                        "📅 My Calendar",
                        class_="btn btn-outline-secondary btn-sm",
                        style="color:rgba(255,255,255,0.85); border-color:rgba(255,255,255,0.3);",
                    )
                )
            )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button(
                        "open_calendar_modal_global",
                        "📅 Unit Calendar",
                        class_="btn btn-outline-secondary btn-sm",
                        style="color:rgba(255,255,255,0.85); border-color:rgba(255,255,255,0.3);",
                    )
                )
            )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button(
                        "logout_btn", "Sign Out",
                        class_="btn btn-sm",
                        style="background:rgba(255,255,255,0.12); color:rgba(255,255,255,0.9); border:1px solid rgba(255,255,255,0.25);",
                    )
                )
            )

            nav_items = [i for i in nav_items if i is not None]
            return ui.page_navbar(*nav_items, id="main_nav")

        @output
        @render.text
        def login_status():
            return status_text()

        @output
        @render.ui
        def login_status_ui():
            msg = status_text()
            if not msg:
                return ui.div()
            return ui.div(
                msg,
                style=(
                    "margin-top:0.75rem; padding:0.55rem 0.85rem;"
                    "background:#fff5f5; border:1px solid #feb2b2;"
                    "border-left:4px solid #e53e3e; border-radius:6px;"
                    "color:#742a2a; font-size:0.82rem; font-weight:500; line-height:1.4;"
                ),
            )

        @output
        @render.text
        def login_user():
            return login_user_text()

        @reactive.Effect
        async def login_dialog():
            app_env = os.getenv("APP_ENV", "")

            if app_env == "development":
                if _get_session_user() is None:
                    from warriorfit.data.model.db_model import User as UserModel
                    dev_user = UserModel(
                        id=0,
                        username="admin",
                        email="admin@dev.local",
                        password_hash="",
                        role=Role.ADMIN,
                        is_active=True,
                    )
                    UserStore.set_user(dev_user)
                    _set_session_user(dev_user)
                    login_user_text.set(
                        f"User: admin  Role: {Role.ADMIN}  Unit: {ApplicationConfig().own_unit}"
                    )
                    nav_version.set(nav_version.get() + 1)
                return

            status_text.set("")
            login = ui.div(
                ui.div(
                    ui.div("⚔️ WarriorFit", class_="wf-login-logo"),
                    ui.div("Physical Training Management System", class_="wf-login-subtitle"),
                    ui.tags.label("Username", for_="username_login", class_="form-label"),
                    ui.input_text("username_login", None, placeholder="Enter username"),
                    ui.tags.label("Password", for_="password_login", class_="form-label mt-2"),
                    ui.input_password("password_login", None, placeholder="Enter password"),
                    ui.input_action_button(
                        "handle_login", "Sign In", class_="btn btn-primary w-100 mt-3"
                    ),
                    ui.output_ui("login_status_ui"),
                    class_="wf-login-card",
                ),
            )
            ui.modal_show(ui.modal(login, easy_close=False, size="s", footer=None))

        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login():
            logger = getattr(FitnessWarriorApp, "logger", logging.getLogger(__name__))
            username_login = (input.username_login() or "").lower()
            password_login = input.password_login()

            locked, seconds_left = login_rate_limiter.is_locked(username_login)
            if locked:
                minutes = (seconds_left + 59) // 60
                status_text.set(
                    f"Too many failed attempts. Try again in {minutes} minute(s)."
                )
                return

            client = getattr(session.http_conn, "client", None)
            x_forwarded = session.http_conn.headers.get("x-forwarded-for", "")
            client_ip = (x_forwarded.split(",")[0].strip() if x_forwarded
                         else (client.host if client else None))

            try:
                if await user_service.check_user(username_login, password_login):
                    user = await user_service.get_user_by_username(username_login)
                    if user.is_active is False:
                        status_text.set(
                            "Your account is disabled. Please contact your administrator."
                        )
                        return
                    login_rate_limiter.reset(username_login)
                    UserStore.set_user(user)
                    await user_service.add_audit_log(
                        f"User {username_login} logged in", "login", ip_address=client_ip
                    )
                    _set_session_user(user)
                    login_user_text.set(
                        f"User: {username_login}  Role: {user.role}  Unit: {ApplicationConfig().own_unit}"
                    )
                    status_text.set("")
                    ui.modal_remove()
                    nav_version.set(nav_version.get() + 1)
                    logger.info("User %s logged in successfully", username_login)
                else:
                    login_rate_limiter.record_failure(username_login)
                    await user_service.add_audit_log(
                        f"Failed login attempt for '{username_login}'",
                        "login_failed",
                        ip_address=client_ip,
                    )
                    locked, seconds_left = login_rate_limiter.is_locked(username_login)
                    if locked:
                        minutes = (seconds_left + 59) // 60
                        status_text.set(
                            f"Too many failed attempts. Account locked for {minutes} minute(s)."
                        )
                    else:
                        left = login_rate_limiter.attempts_remaining(username_login)
                        status_text.set(
                            f"Invalid username or password. {left} attempt(s) remaining."
                        )
            except (ValueError, TypeError, AttributeError) as e:
                logger.error("Login error: %s", e)
                status_text.set("An error occurred while logging in. Please try again.")

        @reactive.Effect
        def _mount_on_nav_activation():
            """
            Defines a reactive effect that triggers when the main navigation is activated. This function
            handles potential navigation activation by observing the `input.main_nav` property. If any
            issues such as `AttributeError` or `KeyError` occur during this process, they are gracefully
            handled to prevent application-level errors.

            :return: None
            """
            try:
                _ = input.main_nav()
            except (AttributeError, KeyError):
                return

        @reactive.Effect
        def _on_logout_button_click():
            """
            Handles the effects triggered by the logout button click event. This effect is
            responsible for clearing the session user, updating the navigation state,
            showing a notification to the user, and initiating a page reload after a
            slight delay.

            :param clicks: The number of times the logout button was clicked.
            :type clicks: Optional[int]
            :return: None
            """
            try:
                clicks = input.logout_btn()
            except (AttributeError, KeyError):
                return
            if clicks and clicks > 0:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You have been logged out.", type="message")
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script(
                        "setTimeout(function(){ location.reload(); }, 100);"
                    ),
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
            """
            Tracks user activity by recording the last activity timestamp whenever input
            activity is detected. This function ensures that the 'last_activity' value
            is updated in response to user interactions.

            This effect listens to changes in input activity and updates the
            'last_activity' attribute to the current time whenever such activity is
            triggered. Failed attempts to access or process the input activity (due to
            exceptions like AttributeError or KeyError) will be ignored gracefully.

            :return: None
            """
            try:
                _ = input.activity_ping()
            except (AttributeError, KeyError):
                return
            last_activity.set(time.time())

        @reactive.Effect
        def _reset_on_nav_or_login():
            """
            An internal reactive effect function designed to reset certain state variables when a navigation
            or login event occurs.

            This function reacts to specific conditions such as changes in navigation state or version.
            It ensures that the `last_activity` variable is updated to the current timestamp whenever
            these events take place. Errors during navigation state access are silently handled.

            Note: This function is marked as internal for framework or system-level usage and is
            intended for reactive state-handling flows.

            :raises AttributeError: Silently handled when accessing `input.main_nav` fails due to missing
                attributes.
            :raises KeyError: Silently handled when accessing `input.main_nav` fails due to a key error.
            :return: None
            """
            try:
                _ = input.main_nav()
            except (AttributeError, KeyError):
                pass
            _ = nav_version.get()
            last_activity.set(time.time())

        @reactive.Effect
        def _auto_logout_timer():
            """
            This reactive effect function monitors user activity and automatically logs out
            users after 10 minutes of inactivity. It is triggered every 5 seconds and
            ensures that the user session is cleared if the inactivity timeout occurs.

            During the logout process, it also updates the navigation menu, shows a
            notification to the user, and reloads the page for security purposes.

            :raises KeyError: If session details or user data are not properly managed.

            :return: None
            """
            reactive.invalidate_later(5)
            user = _get_session_user()
            if not user:
                return
            ts = last_activity.get() or time.time()
            if time.time() - ts >= 600:
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show(
                    "You were logged out due to 10 minutes of inactivity.",
                    type="warning",
                )
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script(
                        "setTimeout(function(){ location.reload(); }, 100);"
                    ),
                )


FitnessWarriorApp.setup_logger()
FitnessWarriorApp.get_broker().start()
app = App(ui=FitnessWarriorApp.build_app_ui(), server=FitnessWarriorApp.server, static_assets=Path(__file__).parent / "www")
