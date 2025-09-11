from typing import Any
from shiny import App, ui, run_app
from .pages import dashboard, reports, settings
from .pages import login
from .pages import usermangement
from .pages import phef
from .pages import sessions

APP_TITLE = "Fitness Warrior"
DEFAULT_PORT = 8000


def build_app_ui() -> ui.page_navbar:
    """
    Construct and return the root UI for the application.
    """
    return ui.page_navbar(
        login.get_ui(),
        usermangement.get_ui(),
        phef.get_ui(),
        sessions.get_ui(),
        dashboard.get_ui(),
        reports.get_ui(),
        settings.get_ui(),
        title=APP_TITLE,
        id="main_nav",
    )


def register_pages_server(input: Any, output: Any, session: Any) -> None:
    """
    Register server logic for each page.
    """
    # All pages will be mounted lazily when their tab becomes active.
    pass


def server(input: Any, output: Any, session: Any) -> None:
    """
    Shiny server entry point. Delegates to per-page servers.
    """
    from shiny import reactive

    register_pages_server(input, output, session)

    # Map navbar labels to their page server functions
    servers_by_tab = {
        "Login": login.server,
        "User Management": usermangement.server,
        "PHEF Tests": phef.server,
        "Sessions": sessions.server,
        "Dashboard": dashboard.server,
        "Reports": reports.server,
        "Settings": settings.server,
    }

    mounted = reactive.Value(set())

    @reactive.Effect
    def _mount_on_nav_activation():
        active = input.main_nav()
        if not active:
            return
        already = mounted.get()
        if active in servers_by_tab and active not in already:
            servers_by_tab[active](input, output, session)
            mounted.set({*already, active})


app = App(build_app_ui(), server)



if __name__ == "__main__":
    run_app(app, port=DEFAULT_PORT, reload=True)
