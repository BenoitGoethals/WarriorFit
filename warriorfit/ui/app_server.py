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
from warriorfit.i18n import LanguageStore, t
from warriorfit.security.rate_limiter import login_rate_limiter
from warriorfit.services.service_user import UserService
from warriorfit.ui.page_registry import PageSpec, get_pages, pages_for_role
from warriorfit.ui.user_store import UserStore

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
    from shiny import reactive  # noqa: I001
    from warriorfit.ui.pages import calendar_events

    servers_by_tab: dict[str, Callable[[Any, Any, Any], Any]] = {
        p.tab: p.server_factory for p in get_pages() if p.server_factory is not None
    }
    servers_by_tab["CalendarEvents"] = calendar_events.server

    mounted: reactive.Value[set[str]] = reactive.Value(set())

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

    def server(input: Any, output: Any, session: Any) -> None:
        from shiny import reactive

        from warriorfit.ui.pages import calendar_events

        _register_pages_server(input, output, session)

        status_text: reactive.Value[str] = reactive.Value("")
        login_user_text: reactive.Value[str] = reactive.Value("")
        nav_version: reactive.Value[int] = reactive.Value(0)
        lang_version: reactive.Value[int] = reactive.Value(0)

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

        _GROUP_LABELS: dict[str, str] = {
            "Physical Tests": "nav.group.physical_tests",
            "Cross/Runs": "nav.group.cross_runs",
            "Admin": "nav.group.admin",
            "About": "nav.group.about",
        }

        def _safe_panel(panel: Optional[Any]) -> Optional[ui.Tag]:
            return panel if panel is not None else None

        def _build_menu(
            group: str, role_pages: list[PageSpec]
        ) -> Optional[ui.Tag]:
            children = [
                _safe_panel(p.ui_factory()) for p in role_pages if p.group == group
            ]
            children = [c for c in children if c is not None]
            label = t(_GROUP_LABELS.get(group, group))
            return ui.nav_menu(label, *children) if children else None  # type: ignore[arg-type, return-value]

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
                    login_user_text.set(
                        f"User: admin  Role: {Role.ADMIN}  Unit: {config.own_unit}"
                    )
                    nav_version.set(nav_version.get() + 1)
                return

            status_text.set("")

            # Translations for dynamic JS labels
            lbl_username = t("login.username")
            lbl_service = t("login.service_number")
            ph_username = t("login.username_placeholder")
            ph_service = t("login.service_number_placeholder")

            login = ui.div(
                # Language switcher inside the login modal
                ui.div(
                    ui.input_action_button(
                        "lang_en", "EN",
                        class_="btn btn-outline-secondary btn-sm me-1",
                        style="font-size:0.75rem; padding:2px 8px;",
                    ),
                    ui.input_action_button(
                        "lang_nl", "NL",
                        class_="btn btn-outline-secondary btn-sm me-1",
                        style="font-size:0.75rem; padding:2px 8px;",
                    ),
                    ui.input_action_button(
                        "lang_fr", "FR",
                        class_="btn btn-outline-secondary btn-sm",
                        style="font-size:0.75rem; padding:2px 8px;",
                    ),
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
                    ui.tags.label(
                        lbl_username, for_="username_login", class_="form-label"
                    ),
                    ui.input_text(
                        "username_login", None, placeholder=ph_username
                    ),
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
            logger = logging.getLogger(__name__)
            username_login = (input.username_login() or "").lower()
            password_login = input.password_login()

            locked, seconds_left = login_rate_limiter.is_locked(username_login)
            if locked:
                minutes = (seconds_left + 59) // 60
                status_text.set(
                    t("login.error.locked").format(minutes=minutes)
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
                        status_text.set(t("login.error.account_disabled"))
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
                            t("login.error.account_locked").format(minutes=minutes)
                        )
                    else:
                        left = login_rate_limiter.attempts_remaining(username_login)
                        status_text.set(
                            t("login.error.invalid").format(left=left)
                        )
            except (ValueError, TypeError, AttributeError) as e:
                logging.getLogger(__name__).error("Login error: %s", e)
                status_text.set(t("login.error.general"))

        # ── Logout handler ───────────────────────────────────────────────────

        @reactive.Effect
        async def _on_logout_button_click() -> None:
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
                ui.notification_show(t("logout.notification"), type="message")
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
                    t("logout.inactivity"),
                    type="warning",
                )
                ui.insert_ui(
                    selector="body",
                    ui=ui.tags.script(
                        "setTimeout(function(){ location.reload(); }, 100);"
                    ),
                )

    return server
