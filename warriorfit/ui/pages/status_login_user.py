from shiny import ui, render

from warriorfit.core.role import Role
from warriorfit.ui.controllers.status_log_user_controller import StatusLogUserController
from warriorfit.ui.user_store import UserStore


class StatusLoginUser:

    def __init__(self):
        self.controller = StatusLogUserController()

    def get_ui(self):
        return ui.nav_panel(
            "Welcome",
            ui.div(
                ui.row(
                    ui.column(
                        12,
                        ui.div(
                            ui.h1(ui.output_text("welcome_header"), class_="display-4 fw-bold text-primary mb-2"),
                            ui.p(ui.output_text("welcome_subheader"), class_="lead text-muted"),
                            class_="text-center py-5 bg-light rounded-3 mb-4 shadow-sm"
                        )
                    )
                ),
                ui.output_ui("pti_dashboard_section"),
                class_="container-fluid p-4"
            )
        )

    def server(self, input, output, session):
        
        @render.text
        def welcome_header():
            user = UserStore.get_user()
            if user:
                return f"Welcome back, {user.username}!"
            return "Welcome to WarriorFit"

        @render.text
        def welcome_subheader():
            user = UserStore.get_user()
            if user:
                return f"Logged in as {user.role} | {user.email}"
            return "Please log in to access the system."

        @render.ui
        def pti_dashboard_section():
            user = UserStore.get_user()
            # Check if user is PTI or APTI
            if user and user.role in [Role.PTI, Role.APTI]:
                return ui.row(
                    ui.column(
                        8,
                        ui.card(
                            ui.card_header(
                                ui.div(
                                    ui.span("📅 Upcoming Test Sessions", class_="fs-5 fw-bold"),
                                    class_="d-flex align-items-center"
                                ),
                                class_="bg-white border-bottom-0"
                            ),
                            ui.output_data_frame("sessions_grid"),
                            full_screen=True,
                            class_="shadow-sm h-100"
                        ),
                         offset=2
                    )
                )
            return ui.div()

        @render.data_frame
        async def sessions_grid():
            df = await self.controller.get_upcoming_session(UserStore.get_user().serial_number)
            return render.DataGrid(
                df, 
                width="100%", 
                filters=True, 
                selection_mode="none"
            )


_page = StatusLoginUser()

def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)
