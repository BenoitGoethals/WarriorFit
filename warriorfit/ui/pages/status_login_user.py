import base64
from pathlib import Path

from shiny import ui, render, reactive

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.core.role import Role
from warriorfit.ui.controllers.status_log_user_controller import StatusLogUserController
from warriorfit.ui.pages.page import Page
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container
from warriorfit.ui.user_store import UserStore


class StatusLoginUser(Page):
    @inject
    def __init__(self, controller: StatusLogUserController = Provide[Container.status_log_user_controller]):
        super().__init__()
        self.controller = controller

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            "Welcome",
            ui.div(
                ui.row(
                    ui.column(
                        12,
                        ui.div(
                            ui.h1(
                                ui.output_text("welcome_header"),
                                class_="display-4 fw-bold text-primary mb-2",
                            ),
                            ui.p(
                                ui.output_text("welcome_subheader"),
                                class_="lead text-muted",
                            ),
                            ui.p(
                                ui.output_text("version_header"),
                                class_="lead text-muted",
                            ),
                            ui.output_ui("welcome_image"),
                            class_="text-center py-5 bg-light rounded-3 mb-4 shadow-sm",
                        ),
                    )
                ),
                ui.output_ui("pti_dashboard_section"),
                class_="container-fluid p-4",
            ),
        )

    def server(self, input, output, session):

        @reactive.Effect
        async def _init() -> None:
            # Triggered on init and whenever refresh_tick changes
            self.refresh_tick.get()

        @output
        @render.ui
        def welcome_image():
            img_path = Path(__file__).parent / "sor.png"
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            return ui.img(src=f"data:image/png;base64,{img_data}", class_="img-fluid")

        @render.text
        def welcome_header():
            user = UserStore.get_user()
            if user:
                return f"Welcome back, {user.username}!"
            return "Welcome to WarriorFit."

        @render.text
        def version_header():
            return f"Version : {ApplicationConfig().version}"

        @render.text
        def welcome_subheader():
            user = UserStore.get_user()
            if user:
                return f"Logged in as {user.role} | {user.email}"
            return "Please log in to access the system."

        @render.ui
        def pti_dashboard_section():
            self.refresh_tick.get()
            user = UserStore.get_user()
            # Check if user is PTI or APTI
            if user and user.role in [Role.PTI, Role.APTI]:
                return ui.row(
                    ui.column(
                        8,
                        ui.card(
                            ui.card_header(
                                ui.div(
                                    ui.span(
                                        "📅 Upcoming Test Sessions",
                                        class_="fs-5 fw-bold",
                                    ),
                                    class_="d-flex align-items-center",
                                ),
                                class_="bg-white border-bottom-0",
                            ),
                            ui.output_data_frame("sessions_grid"),
                            full_screen=True,
                            class_="shadow-sm h-100",
                        ),
                        offset=2,
                    )
                )
            return ui.div()

        @output
        @render.data_frame
        async def sessions_grid():
            self.refresh_tick.get()
            df = await self.controller.get_upcoming_session(
                UserStore.get_user().serial_number
            )
            return render.DataGrid(
                df, width="100%", filters=True, selection_mode="none"
            )


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = StatusLoginUser()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
