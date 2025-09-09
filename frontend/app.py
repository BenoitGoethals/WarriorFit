from typing import Any
from shiny import App, ui, run_app
from .pages import dashboard, reports, settings
from .pages import login
from .pages import usermangement
from .pages import phef
from .pages import sessions

APP_TITLE = "My Multi-Page Shiny App"
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
    )


def register_pages_server(input: Any, output: Any, session: Any) -> None:
    """
    Register server logic for each page.
    """
    login.server(input, output, session)
    usermangement.server(input, output, session)
    phef.server(input, output, session)
    sessions.server(input, output, session)
    dashboard.server(input, output, session)
    reports.server(input, output, session)
    settings.server(input, output, session)


def server(input: Any, output: Any, session: Any) -> None:
    """
    Shiny server entry point. Delegates to per-page servers.
    """
    register_pages_server(input, output, session)


app = App(build_app_ui(), server)



if __name__ == "__main__":
    run_app(app, port=DEFAULT_PORT, reload=True)
