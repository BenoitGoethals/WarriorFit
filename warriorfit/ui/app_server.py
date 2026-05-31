import logging
import os
import time
from typing import Any, Callable, Optional

from dependency_injector.wiring import Provide, inject
from shiny import render, ui

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.container import Container
from warriorfit.data.model.db_model import Role  # type: ignore[attr-defined]
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.security.rate_limiter import login_rate_limiter
from warriorfit.services.service_user import UserService
from warriorfit.ui.page_registry import PageSpec, get_pages, pages_for_role
from warriorfit.ui.user_store import UserStore


class _ServicemanSessionUser:
    """Lightweight shim for serviceman-mode sessions.

    Mirrors the subset of User attributes that the rest of the app reads from
    UserStore / session.user.
    """

    def __init__(self, mil: Any) -> None:
        self.id = None
        self.username = mil.last_name + " " + mil.first_name
        self.email = getattr(mil, "mail", "")
        self.role = Role.USER
        self.is_active = True
        self.serial_number = mil.service_number


def build_app_ui() -> Any:
    """
    Constructs and returns the user interface layout for the application.

    The function defines the main structure of the app's UI, including external
    CSS stylesheets that are applied to style the page and JavaScript to handle
    specific tab-related behaviors. The UI is composed of a fillable page with
    a specified HTML head section and a main content container.

    :return: The user interface layout for the application.
    :rtype: Any
    """
    return ui.page_fillable(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="custom.css"),
            # Military theme overrides (loaded second so it wins).
            ui.tags.link(rel="stylesheet", href="military.css"),
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


def _register_pages_server(
    input: Any,
    output: Any,
    session: Any,
) -> None:
    """
    Registers and mounts page servers dynamically based on the currently active navigation tab.

    This function manages the lifecycle of server initialization for individual pages of the
    application. Page-specific server instances are created and mounted only when the associated
    navigation tab is activated. It ensures that necessary server logic is executed for both
    tab-specific pages and the calendar modal, which operates outside the main navigation structure.

    :param input: Reactive input object for listening to changes in user interaction.
    :type input: Any
    :param output: Reactive output object for rendering user interface updates.
    :type output: Any
    :param session: Current session object providing context for the reactive environment.
    :type session: Any
    :return: None
    :rtype: None
    """
    from shiny import reactive  # noqa: I001
    from warriorfit.ui.pages import calendar_events

    servers_by_tab: dict[str, Callable[[Any, Any, Any], Any]] = {
        p.tab: p.server_factory for p in get_pages() if p.server_factory is not None
    }
    # Calendar server lives outside the navbar (modal trigger).
    servers_by_tab["CalendarEvents"] = calendar_events.server

    mounted: reactive.Value[set[str]] = reactive.Value(set())  # type: ignore[assignment]

    @reactive.Effect
    def _mount_on_nav_activation():
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


@inject
def make_server(
    user_service: UserService = Provide[Container.user_service],
    servicemen_repository: ServicemenRepository = Provide[Container.servicemen_repository],
    config: ApplicationConfig = Provide[Container.config],
) -> Callable[[Any, Any, Any], None]:
    """
    Creates and configures the server function for managing application state, session
    attributes, user interactions, and reactive elements.

    The server function facilitates interaction between the user interface, session
    handling, calendar events, and page navigation. It defines reactive effects
    for toggling calendars and manages the application's main navigation bar based on
    user roles and session properties.

    :param user_service: Dependency-injected service for user-related operations
    :type user_service: UserService
    :param servicemen_repository: Dependency-injected repository for servicemen data
    :type servicemen_repository: ServicemenRepository
    :param config: Dependency-injected application configuration parameters
    :type config: ApplicationConfig
    :return: The server function to be executed by the reactive framework
    :rtype: Callable[[Any, Any, Any], None]
    """

    def server(input: Any, output: Any, session: Any) -> None:
        """
        Handles server-side initialization and reactive rendering logic for the
        Shiny application. The server function is responsible for registering
        page servers, managing user sessions, handling calendar panels,
        building navigation bars, and rendering the main application content.

        :param input: Reactive input object for capturing user interactions.
        :type input: Any
        :param output: Reactive output object for updating UI components.
        :type output: Any
        :param session: Session object for maintaining user-specific state throughout the
            user interaction session.
        :type session: Any
        :return: None
        """
        from shiny import reactive

        from warriorfit.ui.pages import calendar_events

        _register_pages_server(input, output, session)

        status_text: reactive.Value[str] = reactive.Value("")
        login_user_text: reactive.Value[str] = reactive.Value("")
        nav_version: reactive.Value[int] = reactive.Value(0)

        # ── Session helpers ──────────────────────────────────────────────────

        def _get_session_user() -> Optional[Any]:
            return getattr(session, "user", None)

        def _set_session_user(user: Any) -> None:
            setattr(session, "user", user)

        def _clear_session_user() -> None:
            if hasattr(session, "user"):
                delattr(session, "user")
            if hasattr(session, "login_mode"):
                delattr(session, "login_mode")

        # ── Calendar panel ───────────────────────────────────────────────────

        show_calendar: reactive.Value[bool] = reactive.Value(False)
        show_personal_calendar: reactive.Value[bool] = reactive.Value(False)

        @reactive.Effect
        @reactive.event(input.open_calendar_modal_global)
        def _toggle_calendar() -> None:
            calendar_events.refresh()
            show_calendar.set(not show_calendar.get())
            if show_calendar.get():
                show_personal_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_calendar)
        def _close_calendar() -> None:
            show_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.open_personal_calendar_modal_global)
        def _toggle_personal_calendar() -> None:
            calendar_events.refresh()
            show_personal_calendar.set(not show_personal_calendar.get())
            if show_personal_calendar.get():
                show_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_personal_calendar)
        def _close_personal_calendar() -> None:
            show_personal_calendar.set(False)

        # ── Navbar builder ───────────────────────────────────────────────────

        def _safe_panel(panel: Optional[Any]) -> Optional[ui.Tag]:
            return panel if panel is not None else None

        def _build_menu(
            group: str, role_pages: list[PageSpec]
        ) -> Optional[ui.Tag]:
            children = [
                _safe_panel(p.ui_factory()) for p in role_pages if p.group == group
            ]
            children = [c for c in children if c is not None]
            return ui.nav_menu(group, *children) if children else None  # type: ignore[arg-type, return-value]

        def _build_navbar() -> Any:
            user = _get_session_user()
            role = getattr(user, "role", None)
            mode = getattr(session, "login_mode", "application")
            role_pages = pages_for_role(role)

            nav_items: list[Any] = []

            if mode == "serviceman":
                allowed_tabs = {"My Progress", "About", "Privacy"}
                restricted = [p for p in role_pages if p.tab in allowed_tabs]
                for p in restricted:
                    if p.group == "root":
                        nav_items.append(_safe_panel(p.ui_factory()))
                about_menu = _build_menu("About", restricted)
                if about_menu is not None:
                    nav_items.append(about_menu)
            else:
                # Insert "Physical Tests" menu right after Dashboard.
                physical_menu = _build_menu("Physical Tests", role_pages)
                physical_inserted = False
                for p in role_pages:
                    if p.group == "root" and p.tab != "About":
                        nav_items.append(_safe_panel(p.ui_factory()))
                        if (
                            p.tab == "Dashboard"
                            and physical_menu is not None
                            and not physical_inserted
                        ):
                            nav_items.append(physical_menu)
                            physical_inserted = True

                if physical_menu is not None and not physical_inserted:
                    nav_items.append(physical_menu)

                nav_items.append(_build_menu("Cross/Runs", role_pages))
                nav_items.append(_build_menu("Admin", role_pages))
                about_menu = _build_menu("About", role_pages)
                if about_menu is not None:
                    nav_items.append(about_menu)

            # Global controls
            nav_items.append(ui.nav_spacer())
            nav_items.append(
                ui.nav_control(
                    ui.div(
                        ui.output_text("login_user"),
                        style=(
                            "display:flex; align-items:center; height:100%;"
                            " color:rgba(255,255,255,0.7); font-size:0.8rem;"
                            " padding:0 0.5rem; white-space:nowrap;"
                            " max-width:280px; overflow:hidden; text-overflow:ellipsis;"
                        ),
                    )
                )
            )
            if mode != "serviceman":
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
                        "logout_btn",
                        "Sign Out",
                        class_="btn btn-sm",
                        style=(
                            "background:rgba(255,255,255,0.12);"
                            " color:rgba(255,255,255,0.9);"
                            " border:1px solid rgba(255,255,255,0.25);"
                        ),
                    )
                )
            )

            nav_items = [i for i in nav_items if i is not None]
            return ui.page_navbar(*nav_items, id="main_nav")

        # ── Main content renderer ────────────────────────────────────────────

        @output
        @render.ui
        def main_content_container() -> Any:
            """
            Renders the main content container based on the current state of the application.

            This function dynamically creates and returns the appropriate UI layout
            for the main content container by checking the state of `show_calendar`
            and `show_personal_calendar`. Depending on the state, it either displays
            the calendar view, personal calendar view, or the navigation bar content.

            :return: The dynamically generated UI layout for the main content container.
            """
            if show_calendar.get():
                return ui.div(
                    ui.div(
                        ui.h3("📅 Calendar"),
                        ui.input_action_button(
                            "close_calendar",
                            "✕ Close",
                            class_="btn btn-outline-secondary btn-sm",
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
                        calendar_events.get_ui(all_test=False),
                        class_="wf-calendar-panel-body",
                    ),
                    class_="wf-calendar-panel",
                )
            else:
                _ = nav_version.get()
                return _build_navbar()

        # ── Output renderers ─────────────────────────────────────────────────

        @output
        @render.text
        def login_status() -> str:
            return status_text()

        @output
        @render.ui
        def login_status_ui() -> Any:
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
        def login_user() -> str:
            return login_user_text()

        # ── Login dialog ─────────────────────────────────────────────────────

        @reactive.Effect
        async def login_dialog() -> None:
            """
            Reactively displays and handles a login dialog interface for the application. This function
            determines the current app environment and either initializes a default developer user for
            development environments or displays the login modal interface for other environments. The modal
            offers two login modes and dynamically updates input labels and placeholders based on the selected mode.

            :param login_dialog: Reactively triggered login logic and UI rendering.
            :type login_dialog: asynchronous React effect
            :return: None

            """
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
                        f"User: admin  Role: {Role.ADMIN}  Unit: {config.own_unit}"
                    )
                    nav_version.set(nav_version.get() + 1)
                return

            status_text.set("")
            login = ui.div(
                ui.div(
                    ui.div("⚔️ WarriorFit", class_="wf-login-logo"),
                    ui.div(
                        "Physical Training Management System",
                        class_="wf-login-subtitle",
                    ),
                    ui.input_radio_buttons(
                        "login_mode",
                        "Login as",
                        choices={
                            "application": "Application user (admin, PTI, ...)",
                            "serviceman": "Serviceman (view my own results only)",
                        },
                        selected="application",
                        inline=False,
                    ),
                    ui.tags.label(
                        "Username", for_="username_login", class_="form-label"
                    ),
                    ui.input_text(
                        "username_login", None, placeholder="Enter username"
                    ),
                    ui.tags.label(
                        "Password", for_="password_login", class_="form-label mt-2"
                    ),
                    ui.input_password(
                        "password_login", None, placeholder="Enter password"
                    ),
                    ui.tags.script(
                        """
                        (function() {
                            function updateLoginLabels() {
                                const mode = $('input[name="login_mode"]:checked').val();
                                const usernameLabel = $('label[for="username_login"]');
                                const usernameInput = $('#username_login');
                                if (mode === 'serviceman') {
                                    usernameLabel.text('Service number');
                                    usernameInput.attr('placeholder', 'Enter service number');
                                } else {
                                    usernameLabel.text('Username');
                                    usernameInput.attr('placeholder', 'Enter username');
                                }
                            }
                            $(document).on('change', 'input[name="login_mode"]', updateLoginLabels);
                            setTimeout(updateLoginLabels, 0);
                        })();
                        """
                    ),
                    ui.input_action_button(
                        "handle_login", "Sign In", class_="btn btn-primary w-100 mt-3"
                    ),
                    ui.output_ui("login_status_ui"),
                    class_="wf-login-card",
                ),
            )
            ui.modal_show(ui.modal(login, easy_close=False, size="m", footer=None))

        # ── Login handler ────────────────────────────────────────────────────

        @reactive.Effect
        @reactive.event(input.handle_login)
        async def handle_login() -> None:
            """
            Reactive function to handle user or serviceman login attempts. This function
            processes user-provided credentials, handles multiple invalid login attempts,
            performs user or serviceman authentication, updates session state, resets the
            login rate limiter on successful login, and maintains audit logs for all
            attempts. In the case of serviceman mode, a password is temporarily skipped
            (subject to proper implementation in the future).

            :param input: Reactive input object providing username, password, and login mode.
            :type input: Any
            :param session: The current user session object used for managing session details.
            :type session: Any
            :param status_text: Reactive object containing status information for the
                               login process.
            :type status_text: Any
            :param login_user_text: Reactive object updating session user details on a
                                    successful login.
            :type login_user_text: Any
            :param nav_version: Reactive object updating the navigation version on a
                                successful login.
            :type nav_version: Any
            :param user_service: Service for handling user-related operations, including
                                 authentication and audit logging.
            :type user_service: Any
            :param servicemen_repository: Service for retrieving serviceman data from the
                                           repository.
            :type servicemen_repository: Any
            :param login_rate_limiter: Object managing the rate limiter for login attempts.
            :type login_rate_limiter: Any

            :return: None
            """
            logger = logging.getLogger(__name__)
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
            client_ip = (
                x_forwarded.split(",")[0].strip()
                if x_forwarded
                else (client.host if client else None)
            )

            try:
                mode = (input.login_mode() or "application").strip()

                # TODO: serviceman mode currently skips password verification.
                # Proper serviceman auth (SSO or dedicated credentials) is
                # tracked as a GDPR/security follow-up item.
                if mode == "serviceman":
                    service_number = (input.username_login() or "").strip()
                    mil = await servicemen_repository.get_by_service_number(
                        service_number, lazy=False
                    )
                    if mil is None:
                        status_text.set("Unknown service number.")
                        return
                    shim_user = _ServicemanSessionUser(mil)
                    login_rate_limiter.reset(service_number)
                    setattr(session, "login_mode", mode)
                    UserStore.set_user(shim_user)  # type: ignore[arg-type]
                    await user_service.add_audit_log(
                        f"Serviceman {service_number} logged in (password skipped — TODO)",
                        "login_serviceman",
                        ip_address=client_ip,
                    )
                    _set_session_user(shim_user)
                    login_user_text.set(
                        f"Serviceman: {mil.first_name} {mil.last_name}"
                        f"  Serial: {service_number}"
                    )
                    status_text.set("")
                    ui.modal_remove()
                    nav_version.set(nav_version.get() + 1)
                    logger.info("Serviceman %s logged in (password skipped)", service_number)
                    return

                if await user_service.check_user(username_login, password_login):
                    user = await user_service.get_user_by_username(username_login)
                    if user.is_active is False:
                        status_text.set(
                            "Your account is disabled. Please contact your administrator."
                        )
                        return
                    setattr(session, "login_mode", mode)
                    login_rate_limiter.reset(username_login)
                    UserStore.set_user(user)
                    await user_service.add_audit_log(
                        f"User {username_login} logged in",
                        "login",
                        ip_address=client_ip,
                    )
                    _set_session_user(user)
                    login_user_text.set(
                        f"User: {username_login}  Role: {user.role}"
                        f"  Unit: {config.own_unit}"
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
                logging.getLogger(__name__).error("Login error: %s", e)
                status_text.set("An error occurred while logging in. Please try again.")

        # ── Logout handler ───────────────────────────────────────────────────

        @reactive.Effect
        async def _on_logout_button_click() -> None:
            """
            Handles the logout button click event, performing user logout operations and updating
            the user interface accordingly. It ensures the user's session is cleared, an audit log
            is created for the logout event, and the UI is refreshed to reflect the logout action.

            :return: None
            """
            try:
                clicks = input.logout_btn()
            except (AttributeError, KeyError):
                return
            if clicks and clicks > 0:
                current_user = _get_session_user()
                if current_user is not None:
                    try:
                        await user_service.add_audit_log(
                            f"User {current_user.username} logged out",
                            "logout",
                        )
                    except Exception:
                        pass
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show("You have been logged out.", type="message")
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script(
                        "setTimeout(function(){ location.reload(); }, 100);"
                    ),
                )

        # ── Activity tracking & auto-logout ──────────────────────────────────

        last_activity: reactive.Value[float] = reactive.Value(time.time())

        @output
        @render.ui
        def _activity_probe() -> Any:
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
        def _record_activity() -> None:
            try:
                _ = input.activity_ping()
            except (AttributeError, KeyError):
                return
            last_activity.set(time.time())

        @reactive.Effect
        def _reset_on_nav_or_login() -> None:
            try:
                _ = input.main_nav()
            except (AttributeError, KeyError):
                pass
            _ = nav_version.get()
            last_activity.set(time.time())

        @reactive.Effect
        async def _auto_logout_timer() -> None:
            """
            Automatically logs out an inactive user after 10 minutes of inactivity. This function
            is reactive and triggers the logout process by invalidating later after a set time
            interval. Upon inactivity of 10 minutes or more, the user's session is cleared, a
            notification is shown, and the page is reloaded.

            Raises an audit log entry indicating the auto-logout due to inactivity and provides
            visual feedback via UI changes.

            :raises Exception: If there is an error while adding the audit log entry.

            :returns: None
            """
            reactive.invalidate_later(5)
            user = _get_session_user()
            if not user:
                return
            ts = last_activity.get() or time.time()
            if time.time() - ts >= 600:
                try:
                    await user_service.add_audit_log(
                        f"User {user.username} auto-logged out after 10min inactivity",
                        "logout_inactivity",
                    )
                except Exception:
                    pass
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

    return server
