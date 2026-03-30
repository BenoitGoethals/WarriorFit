from shiny import ui
from dependency_injector.wiring import inject, Provide
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.core.container import Container
from warriorfit.ui.pages.page import Page


class AboutPage(Page):

    @inject
    def __init__(self, config: ApplicationConfig = Provide[Container.config]):
        super().__init__()
        self._config = config

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "About",
            ui.div(
                ui.div(
                    ui.tags.h2("About WarriorFit", class_="mb-1"),
                    ui.tags.p(
                        "WarriorFit is an application for managing and tracking physical fitness tests "
                        "and training activities within the Belgian Defence.",
                        class_="text-muted mb-4",
                    ),
                    class_="mb-4",
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header(
                            ui.div(
                                ui.tags.span("👤", class_="me-2"),
                                "Development Team",
                            )
                        ),
                        ui.div(
                            ui.tags.h5("Goethals Benoit", class_="mb-1"),
                            ui.tags.p(
                                ui.tags.span(
                                    "Adjudant Majoor", class_="badge bg-secondary me-2"
                                ),
                                ui.tags.span("OR-9", class_="badge bg-dark"),
                                class_="mb-2",
                            ),
                            ui.tags.ul(
                                ui.tags.li(
                                    ui.tags.span("💻", class_="me-2"),
                                    "Programmer",
                                ),
                                ui.tags.li(
                                    ui.tags.span("🎨", class_="me-2"),
                                    "Designer",
                                ),
                                ui.tags.li(
                                    ui.tags.span("📊", class_="me-2"),
                                    "Analyst",
                                ),
                                class_="list-unstyled",
                            ),
                            class_="py-2",
                        ),
                    ),
                    ui.card(
                        ui.card_header(
                            ui.div(
                                ui.tags.span("ℹ️", class_="me-2"),
                                "Application Info",
                            )
                        ),
                        ui.div(
                            ui.tags.table(
                                ui.tags.tbody(
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Application", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td("WarriorFit"),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Organisation", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td("Belgian Defence"),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Purpose", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(
                                            "Physical fitness tracking & management"
                                        ),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Version", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[1]),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Status", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[0]),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            "Release Date", class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[2]),
                                    ),
                                ),
                                class_="table table-sm table-borderless mb-0",
                            ),
                            class_="py-2",
                        ),
                    ),
                    col_widths=(6, 6),
                ),
            ),
        )

    def server(self, input, output, session):
        pass


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = AboutPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
