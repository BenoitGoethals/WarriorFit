from shiny import ui, render, reactive
from warriorfit.data.repositories.abc_repository import ABCRepository
from warriorfit.ui.controllers.StatusApplicationController import StatusApplicationController
from warriorfit.ui.pages.page import Page


class StatusApplicationPage(Page):

    def __init__(self):
        super().__init__()
        self._controller=StatusApplicationController()

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
                    ui.card_header("Mail Server Status"),
                    ui.output_text("mail_server_status_display")
                ),
                ui.card(
                    ui.card_header("Server Status"),
                    ui.output_text("server_status_display")
                ),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Log File"),
                    ui.div(
                        ui.output_text_verbatim("lof_file"),
                        style="max-height: 600px; overflow-y: auto;"
                    )
                ),
            )
        )

    def server(self, input, output, session):
        refresh_tick = reactive.Value(0)

        self.refresh_on_nav(input, "Status Application", refresh_tick)

        @output
        @render.text
        async def db_status_display():
            return await self._controller.status_db()


        @output
        @render.text
        async def hr_status_display():
            return await self._controller.status_hr()

        @output
        @render.text
        async def mail_server_status_display():
            return await self._controller.status_mail_server()

        @output
        @render.text
        async def server_status_display():
            return await self._controller.status_server()


        def check_log_modified():
            return self._controller.check_log_modified()

        @reactive.poll(check_log_modified, 2.0)
        async def read_log():
            return await self._controller.load_log_application()


        @output
        @render.text
        async def lof_file():
            return await read_log()


_page = StatusApplicationPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)