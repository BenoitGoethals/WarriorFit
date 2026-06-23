import contextlib
import logging
import os
import time
from collections.abc import Callable
from typing import Any

from dependency_injector.wiring import Provide, inject
from shiny import render, ui

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.container import Container
from warriorfit.data.model.db_model import Role  # type: ignore[attr-defined]
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.i18n import LanguageStore, t
from warriorfit.security.rate_limiter import login_rate_limiter
from warriorfit.services.service_user import UserService
from warriorfit.ui.page_registry import PageSpec, get_pages, pages_for_role
from warriorfit.ui.user_store import UserStore

_LOGIN_LANG_BTN_STYLE = "font-size:0.75rem; padding:2px 8px;"


class _ServicemanSessionUser:
    """Lightweight shim for serviceman-mode sessions."""

    def __init__(self, mil: Any) -> None:
        self.id = None
        self.username = mil.last_name + " " + mil.first_name
        self.email = getattr(mil, "mail", "")
        self.role = Role.USER
        self.is_active = True
        self.serial_number = mil.service_number


def build_app_ui() -> Any:
    return ui.page_fillable(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="custom.css"),
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
    Registers page-specific server logic for the given list of pages and sets up
    reactive effects for mounting server components upon navigation activation.
    This function dynamically associates server factories with their corresponding
    page tabs and ensures that each server is mounted only once during its
    lifecycle.

    :param input: The input object holding Shiny reactive inputs.
    :param output: The output object to manage Shiny reactive outputs.
    :param session: The session object representing the current Shiny session.
    :return: None
    """
    from shiny import reactive

    from warriorfit.ui.pages import calendar_events

    servers_by_tab: dict[str, Callable[[Any, Any, Any], Any]] = {
        p.tab: p.server_factory for p in get_pages() if p.server_factory is not None
    }
    servers_by_tab["CalendarEvents"] = calendar_events.server

    mounted: reactive.Value[set[str]] = reactive.Value(set())

    @reactive.Effect
    def _mount_on_nav_activation():
        """
        Reactive effect function that handles the activation of navigation tabs and their corresponding
        server-side logic. When a navigation tab is activated, this function ensures the relevant server
        logic is mounted and executed if not already active. Additionally, it ensures that the
        "CalendarEvents" tab logic is mounted if not already present.

        :param input: An object providing reactive observation of user input or state changes.
        :param output: An object responsible for handling output and reactive state updates.
        :param session: An object managing the current application session context.
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


def _lang_switcher() -> Any:
    """
    Creates a language switching UI control.

    This function generates a navigation control component that includes a dropdown
    menu for selecting a language. The menu allows users to choose between English ('EN'),
    Dutch ('NL'), and French ('FR'). The currently selected language is dynamically fetched
    from the LanguageStore. The entire control is styled to display flexibly and align
    its items to the center.

    :return: A navigation control UI component that provides a language selection interface
    :rtype: ui.Tag
    """
    return ui.nav_control(
        ui.div(
            ui.input_select(
                "lang_select",
                label=None,
                choices={"en": "EN", "nl": "NL", "fr": "FR"},
                selected=LanguageStore.get_language(),
                width="auto",
            ),
            class_="wf-lang-select",
            style="display:flex; align-items:center;",
        )
    )


@inject
def make_server(
    user_service: UserService = Provide[Container.user_service],
    servicemen_repository: ServicemenRepository = Provide[Container.servicemen_repository],
    config: ApplicationConfig = Provide[Container.config],
) -> Callable[[Any, Any, Any], None]:
    """
    Provides a mechanism to create and initialize the server logic of a reactive application.

    This function wires up components for user interaction, event handling, and dynamic updates to UI
    elements. It integrates a user service, repository, and application configuration, ensuring that
    session-specific behavior is properly handled, and components like language switchers and calendars
    respond to user events smoothly.

    :param user_service: The user service used for managing user-related operations.
    :type user_service: UserService
    :param servicemen_repository: The servicemen repository used for data access related to servicemen.
    :type servicemen_repository: ServicemenRepository
    :param config: The application-level configuration settings.
    :type config: ApplicationConfig
    :return: A callable function that represents the reactive server logic for the application.
    :rtype: Callable[[Any, Any, Any], None]
    """
    def server(input: Any, output: Any, session: Any) -> None:
        """
        Initializes the server-side reactive logic and event handling for the application.

        This function sets up language switchers, calendar modals, and navigation menus. It
        uses reactive programming principles to handle events and update the UI and
        backend data accordingly. The server function is the core logic for managing
        session interactions, user-specific configurations, and dynamic updates to the
        application interface.

        :param input: The reactive input signals used to trigger events in the server.
        :type input: Any
        :param output: The reactive output signals used to bind with UI updates.
        :type output: Any
        :param session: The session object containing user metadata and session-specific configurations.
        :type session: Any
        :return: None
        """
        from shiny import reactive

        from warriorfit.ui.pages import calendar_events

        _register_pages_server(input, output, session)

        status_text: reactive.Value[str] = reactive.Value("")
        login_user_text: reactive.Value[str] = reactive.Value("")
        nav_version: reactive.Value[int] = reactive.Value(0)
        lang_version: reactive.Value[int] = reactive.Value(0)

        # ── Session helpers ──────────────────────────────────────────────────

        def _get_session_user() -> Any | None:
            return getattr(session, "user", None)

        def _set_session_user(user: Any) -> None:
            session.user = user

        def _clear_session_user() -> None:
            if hasattr(session, "user"):
                delattr(session, "user")
            if hasattr(session, "login_mode"):
                delattr(session, "login_mode")

        # ── Language switcher handlers ────────────────────────────────────────

        def _change_lang(lang: str) -> None:
            LanguageStore.set_language(lang)
            lang_version.set(lang_version.get() + 1)
            nav_version.set(nav_version.get() + 1)

        @reactive.Effect
        @reactive.event(input.lang_select)
        def _set_lang_from_select() -> None:
            lang = input.lang_select()
            if lang and lang != LanguageStore.get_language():
                _change_lang(lang)

        @reactive.Effect
        @reactive.event(input.lang_en)
        def _set_lang_en() -> None:
            _change_lang("en")

        @reactive.Effect
        @reactive.event(input.lang_nl)
        def _set_lang_nl() -> None:
            _change_lang("nl")

        @reactive.Effect
        @reactive.event(input.lang_fr)
        def _set_lang_fr() -> None:
            """
            Sets the application's language to French.

            This function is invoked when the `lang_fr` event is triggered. It modifies
            the language setting by calling the `_change_lang` function with the language
            code "fr".

            :return: None
            """
            _change_lang("fr")

        # ── Calendar panel ───────────────────────────────────────────────────

        show_calendar: reactive.Value[bool] = reactive.Value(False)
        show_personal_calendar: reactive.Value[bool] = reactive.Value(False)

        @reactive.Effect
        @reactive.event(input.open_calendar_modal_global)
        def _toggle_calendar() -> None:
            """
            Toggle the global calendar visibility and refresh calendar events.

            This reactive effect is triggered by the event linked to the
            `input.open_calendar_modal_global`. It updates the visibility of the
            global calendar, refreshing its events and ensuring that the
            personal calendar is hidden when the global calendar is displayed.

            :return: None
            """
            calendar_events.refresh()
            show_calendar.set(not show_calendar.get())
            if show_calendar.get():
                show_personal_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_calendar)
        def _close_calendar() -> None:
            """
            Closes the calendar by setting the show_calendar state to False when the
            close_calendar event is triggered.

            This reactive effect listens to the close_calendar event and modifies the
            show_calendar state to hide the calendar.

            :param: None
            :return: None
            """
            show_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.open_personal_calendar_modal_global)
        def _toggle_personal_calendar() -> None:
            """
            Toggle the visibility of the personal calendar modal and refresh calendar events.

            This reactive effect monitors the global signal to open the personal calendar modal
            and toggles its visibility state. When the personal calendar modal is shown, it ensures
            that the regular calendar modal is hidden.

            :param input.open_personal_calendar_modal_global: Signal that triggers the state toggle
                for the personal calendar modal.
            :type input.open_personal_calendar_modal_global: reactive.Signal

            :return: None
            """
            calendar_events.refresh()
            show_personal_calendar.set(not show_personal_calendar.get())
            if show_personal_calendar.get():
                show_calendar.set(False)

        @reactive.Effect
        @reactive.event(input.close_personal_calendar)
        def _close_personal_calendar() -> None:
            """
            Closes the personal calendar by setting the visibility state to ``False``.

            This effect reacts to the event triggered by the user interaction with the
            `close_personal_calendar` input. When activated, it modifies the state of
            `show_personal_calendar` to ensure that the calendar is hidden.

            :return: None
            """
            show_personal_calendar.set(False)

        # ── Navbar builder ───────────────────────────────────────────────────

        _GROUP_LABELS: dict[str, str] = {
            "Physical Tests": "nav.group.physical_tests",
            "Cross/Runs": "nav.group.cross_runs",
            "Admin": "nav.group.admin",
            "About": "nav.group.about",
        }

        def _safe_panel(panel: Any | None) -> ui.Tag | None:
            """
            Determines whether a panel value is safe to return or falls back to None if
            the input is None.

            :param panel: The input value to check. It can be of any type or None.
            :type panel: Any | None
            :return: Returns the provided panel if it is not None, otherwise returns None.
            :rtype: ui.Tag | None
            """
            return panel if panel is not None else None

        def _build_menu(group: str, role_pages: list[PageSpec]) -> ui.Tag | None:
            """
            Builds a navigation menu based on the specified group and role pages. This function filters the
            provided role pages by their group, generates UI panels for the filtered pages, and constructs
            a navigation menu if there are valid child elements. If no valid children are found,
            the function returns None.

            :param group: The group name used to filter the role pages.
            :type group: str
            :param role_pages: A list of PageSpec objects representing the role pages to be processed.
            :type role_pages: list[PageSpec]
            :return: A UI navigation menu as a `ui.Tag` instance if valid child elements exist; otherwise, None.
            :rtype: ui.Tag | None
            """
            children = [_safe_panel(p.ui_factory()) for p in role_pages if p.group == group]
            children = [c for c in children if c is not None]
            label = t(_GROUP_LABELS.get(group, group))
            return ui.nav_menu(label, *children) if children else None  # type: ignore[arg-type, return-value]

        def _build_navbar() -> Any:
            """
            Constructs and returns the main navigation bar for the application.

            This function dynamically builds the navigation bar based on the user's role,
            login mode, and available pages for the role. It ensures that only relevant
            navigation items are shown to the user. The navigation bar may include menus,
            tabs, widgets, and actions such as sign-out, calendar access, and language
            switching.

            :returns: The main navigation bar UI component.
            :rtype: Any
            """
            user = _get_session_user()
            role = getattr(user, "role", None)
            mode = getattr(session, "login_mode", "application")
            role_pages = pages_for_role(role)

            nav_items: list[Any] = []

            if mode == "serviceman":
                allowed_tabs = {"My Progress", "About", "Privacy"}
                restricted = [p for p in role_pages if p.tab in allowed_tabs]
                nav_items.extend(
                    _safe_panel(p.ui_factory()) for p in restricted if p.group == "root"
                )
                about_menu = _build_menu("About", restricted)
                if about_menu is not None:
                    nav_items.append(about_menu)
            else:
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
                            t("common.my_calendar"),
                            class_="btn btn-outline-secondary btn-sm",
                            style="color:rgba(255,255,255,0.85); border-color:rgba(255,255,255,0.3);",
                        )
                    )
                )
                nav_items.append(
                    ui.nav_control(
                        ui.input_action_button(
                            "open_calendar_modal_global",
                            t("common.unit_calendar"),
                            class_="btn btn-outline-secondary btn-sm",
                            style="color:rgba(255,255,255,0.85); border-color:rgba(255,255,255,0.3);",
                        )
                    )
                )
            nav_items.append(
                ui.nav_control(
                    ui.input_action_button(
                        "logout_btn",
                        t("common.sign_out"),
                        class_="btn btn-sm",
                        style=(
                            "background:rgba(255,255,255,0.12);"
                            " color:rgba(255,255,255,0.9);"
                            " border:1px solid rgba(255,255,255,0.25);"
                        ),
                    )
                )
            )
            nav_items.append(_lang_switcher())

            nav_items = [i for i in nav_items if i is not None]
            return ui.page_navbar(*nav_items, id="main_nav")

        # ── Main content renderer ────────────────────────────────────────────

        @output
        @render.ui
        def main_content_container() -> Any:
            if show_calendar.get():
                return ui.div(
                    ui.div(
                        ui.h3(t("common.calendar_title")),
                        ui.input_action_button(
                            "close_calendar",
                            t("common.close_btn"),
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
                        ui.h3(t("common.personal_calendar")),
                        ui.input_action_button(
                            "close_personal_calendar",
                            t("common.close_btn"),
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
            An effect function that handles the display and functionality of the login dialog.
            This function dynamically constructs the login modal based on the current application
            state and environment, including support for multiple languages and modes (application
            and serviceman modes). It also handles developer environment login bypass for ease
            of testing during development.

            :param None:
                This function does not take any parameters.

            :raises:
                This function does not explicitly raise any exceptions.

            :return:
                None
            """
            _ = lang_version.get()  # rebuild on language change

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
                    login_user_text.set(f"User: admin  Role: {Role.ADMIN}  Unit: {config.own_unit}")
                    nav_version.set(nav_version.get() + 1)
                return

            if _get_session_user() is not None:
                return  # already logged in — don't re-show the modal

            status_text.set("")

            # Translations for dynamic JS labels
            lbl_username = t("login.username")
            lbl_service = t("login.service_number")
            ph_username = t("login.username_placeholder")
            ph_service = t("login.service_number_placeholder")

            _cur_lang = LanguageStore.get_language()

            def _lang_btn(code: str, label: str, extra_class: str = "") -> Any:
                active = "btn-secondary" if _cur_lang == code else "btn-outline-secondary"
                return ui.input_action_button(
                    f"lang_{code}",
                    label,
                    class_=f"btn {active} btn-sm {extra_class}",
                    style=_LOGIN_LANG_BTN_STYLE,
                )

            login = ui.div(
                # Language switcher inside the login modal
                ui.div(
                    _lang_btn("en", "EN", "me-1"),
                    _lang_btn("nl", "NL", "me-1"),
                    _lang_btn("fr", "FR"),
                    style="display:flex; justify-content:flex-end; margin-bottom:0.5rem;",
                ),
                ui.div(
                    ui.div(t("login.logo"), class_="wf-login-logo"),
                    ui.div(t("login.subtitle"), class_="wf-login-subtitle"),
                    ui.input_radio_buttons(
                        "login_mode",
                        t("login.as"),
                        choices={
                            "application": t("login.mode.application"),
                            "serviceman": t("login.mode.serviceman"),
                        },
                        selected="application",
                        inline=False,
                    ),
                    ui.tags.label(lbl_username, for_="username_login", class_="form-label"),
                    ui.input_text("username_login", None, placeholder=ph_username),
                    ui.tags.label(
                        t("login.password"), for_="password_login", class_="form-label mt-2"
                    ),
                    ui.input_password(
                        "password_login", None, placeholder=t("login.password_placeholder")
                    ),
                    ui.tags.script(
                        f"""
                        (function() {{
                            var _lbl_username = {lbl_username!r};
                            var _lbl_service  = {lbl_service!r};
                            var _ph_username  = {ph_username!r};
                            var _ph_service   = {ph_service!r};
                            function updateLoginLabels() {{
                                var mode = $('input[name="login_mode"]:checked').val();
                                var usernameLabel = $('label[for="username_login"]');
                                var usernameInput = $('#username_login');
                                if (mode === 'serviceman') {{
                                    usernameLabel.text(_lbl_service);
                                    usernameInput.attr('placeholder', _ph_service);
                                }} else {{
                                    usernameLabel.text(_lbl_username);
                                    usernameInput.attr('placeholder', _ph_username);
                                }}
                            }}
                            $(document).on('change', 'input[name="login_mode"]', updateLoginLabels);
                            setTimeout(updateLoginLabels, 0);
                        }})();
                        """
                    ),
                    ui.input_action_button(
                        "handle_login", t("common.sign_in"), class_="btn btn-primary w-100 mt-3"
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
            Handles the login process for users and servicemen, ensuring validation, session setup,
            and auditing of login events. The function enforces rate limiting to prevent brute-force
            attacks and provides detailed auditing for login attempts.

            :raises ValueError: If an unexpected value is encountered during processing.
            :raises TypeError: If a type mismatch occurs during execution.
            :raises AttributeError: If an access to an attribute of None or an invalid object occurs.

            :param input.handle_login: A trigger for the login event.
            :param input.username_login: The username entered by the user, converted to lowercase.
            :param input.password_login: The password entered by the user.
            :param input.login_mode: Optional mode of login, either "application" or "serviceman".
            :param status_text: An observable object used to update status messages for the user.
            :param session.http_conn: HTTP connection details, including headers and client information.
            :param nav_version: Session-specific version management observable.
            :param ui.modal_remove: Removes the modal dialog upon successful login.
            :param user_service: Service managing user-related operations.
            :param servicemen_repository: Repository for fetching servicemen-related data.
            :param login_rate_limiter: Manages and enforces rate-limiting for login attempts.
            :param UserStore: Facilitates user session persistence and management.
            :param t: Translator function for internationalized message retrieval.
            :param logger: Logger object for activity logging.

            :return: None
            """
            logger = logging.getLogger(__name__)
            username_login = (input.username_login() or "").lower()
            password_login = input.password_login()

            locked, seconds_left = login_rate_limiter.is_locked(username_login)
            if locked:
                minutes = (seconds_left + 59) // 60
                status_text.set(t("login.error.locked").format(minutes=minutes))
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

                if mode == "serviceman":
                    service_number = (input.username_login() or "").strip()
                    mil = await servicemen_repository.get_by_service_number(
                        service_number, lazy=False
                    )
                    if mil is None:
                        status_text.set(t("login.error.unknown_service"))
                        return
                    shim_user = _ServicemanSessionUser(mil)
                    login_rate_limiter.reset(service_number)
                    session.login_mode = mode
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
                        status_text.set(t("login.error.account_disabled"))
                        return
                    session.login_mode = mode
                    login_rate_limiter.reset(username_login)
                    UserStore.set_user(user)
                    await user_service.add_audit_log(
                        f"User {username_login} logged in",
                        "login",
                        ip_address=client_ip,
                    )
                    _set_session_user(user)
                    login_user_text.set(
                        f"User: {username_login}  Role: {user.role}" f"  Unit: {config.own_unit}"
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
                        status_text.set(t("login.error.account_locked").format(minutes=minutes))
                    else:
                        left = login_rate_limiter.attempts_remaining(username_login)
                        status_text.set(t("login.error.invalid").format(left=left))
            except (ValueError, TypeError, AttributeError) as e:
                logging.getLogger(__name__).error("Login error: %s", e)
                status_text.set(t("login.error.general"))

        # ── Logout handler ───────────────────────────────────────────────────

        @reactive.Effect
        async def _on_logout_button_click() -> None:
            """
            Handles the logout button click event, logging user activity, updating the user
            interface, and clearing session data.

            This reactive effect is triggered when the logout button is clicked. It verifies
            if the button was clicked, retrieves the current session user, logs the logout event
            if applicable, clears user session information, updates the navigation menu, shows
            a logout notification, and reloads the page content.

            :raises AttributeError: When the `logout_btn` method is not available in the input object.
            :raises KeyError: When the `logout_btn` method does not return a valid value.
            :return: None
            """
            try:
                clicks = input.logout_btn()
            except (AttributeError, KeyError):
                return
            if clicks and clicks > 0:
                current_user = _get_session_user()
                if current_user is not None:
                    with contextlib.suppress(Exception):
                        await user_service.add_audit_log(
                            f"User {current_user.username} logged out",
                            "logout",
                        )
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show(t("logout.notification"), type="message")
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )

        # ── Activity tracking & auto-logout ──────────────────────────────────

        last_activity: reactive.Value[float] = reactive.Value(time.time())

        @output
        @render.ui
        def _activity_probe() -> Any:
            """
            Generates a UI script element for tracking user activity and reporting it to the backend.
            The script listens for various user interactions such as mouse movement, clicks,
            scrolling, key presses, and touch events. It also periodically sends activity pings
            to the backend every 30 seconds to indicate user activity. Additionally, it reacts
            to visibility changes of the page for reporting purposes.

            :return: A UI script element that includes the JavaScript function for monitoring
                and reporting user activity.
            :rtype: Any
            """
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
            """
            Tracks user activity and updates the last recorded activity time.

            This function monitors activity by invoking the `activity_ping` method
            from the input source. If the method call is successful, it sets the
            current timestamp as the last recorded activity. If an `AttributeError`
            or `KeyError` is encountered during the invocation, the function handles
            these exceptions gracefully without raising errors.

            :raises AttributeError: If the `activity_ping` method is not available on
                the input object.
            :raises KeyError: If there is an issue accessing the required attribute from
                the input source.
            :return: None
            """
            try:
                _ = input.activity_ping()
            except (AttributeError, KeyError):
                return
            last_activity.set(time.time())

        @reactive.Effect
        def _reset_on_nav_or_login() -> None:
            """
            Defines a reactive effect to reset state upon navigation or login.

            This effect listens for navigation or login events and responds by resetting
            the last activity timestamp and checking for main navigation state. It also
            attempts to access versioning information to ensure the application's state
            is synchronized.

            :raises AttributeError: Suppressed if accessing an attribute fails during
                execution.
            :raises KeyError: Suppressed when attempting to access a missing key.

            :return: None
            """
            with contextlib.suppress(AttributeError, KeyError):
                _ = input.main_nav()
            _ = nav_version.get()
            last_activity.set(time.time())

        @reactive.Effect
        async def _auto_logout_timer() -> None:
            """
            An asynchronous effect function that tracks user inactivity and automatically logs out
            the user after a period of inactivity. The function checks the user's last activity timestamp
            and performs necessary operations to manage expiration of the user's session.

            :raises Exception: if an error occurs while adding an audit log for the user's logout event.
            :rtype: None
            """
            reactive.invalidate_later(5)
            user = _get_session_user()
            if not user:
                return
            ts = last_activity.get() or time.time()
            if time.time() - ts >= 600:
                with contextlib.suppress(Exception):
                    await user_service.add_audit_log(
                        f"User {user.username} auto-logged out after 10min inactivity",
                        "logout_inactivity",
                    )
                _clear_session_user()
                ui.update_navs("main_nav", selected="Dashboard")
                ui.notification_show(
                    t("logout.inactivity"),
                    type="warning",
                )
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
                )

    return server
