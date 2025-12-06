from shiny import ui, render
from warriorfit.data.repositories.abc_repository import ABCRepository
from warriorfit.ui.pages.page import Page


class StatusApplicationPage(Page):

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Status Application",
            ui.h2("Application Status Dashboard"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Database Connectivity"),
                    ui.output_text("db_status_display")
                ),
                ui.card(
                    ui.card_header("HR Service Ops"),
                    ui.output_text("hr_status_display")
                ),
                ui.card(
                    ui.card_header("Server Status"),
                    ui.output_text("server_status_display")
                ),
            )
        )

    def server(self, input, output, session):
        @output
        @render.text
        async def db_status_display():
            try:
                repo = ABCRepository()
                is_operational = await repo.check_if_db_is_operational()
                return "Operational" if is_operational else "Non-Operational"
            except Exception:
                return "Error Connecting"

        @output
        @render.text
        def hr_status_display():
            # Placeholder for HR service check logic
            return "Operational"

        @output
        @render.text
        def server_status_display():
            return "Running"


# Public API
_page = StatusApplicationPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)