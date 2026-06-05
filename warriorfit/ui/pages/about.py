from dependency_injector.wiring import Provide, inject
from shiny import ui

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.pages.page import Page


class AboutPage(Page):
    TAB_NAME = "About"

    @inject
    def __init__(self, config: ApplicationConfig = Provide[Container.config]):
        super().__init__()
        self._config = config

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            t("nav.about"),
            ui.div(
                ui.div(
                    ui.tags.h2(t("about.title"), class_="mb-1"),
                    ui.tags.p(
                        t("about.description"),
                        class_="text-muted mb-4",
                    ),
                    class_="mb-4",
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header(
                            ui.div(
                                ui.tags.span("👤", class_="me-2"),
                                t("about.dev_team"),
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
                                t("about.app_info"),
                            )
                        ),
                        ui.div(
                            ui.tags.table(
                                ui.tags.tbody(
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.application"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td("WarriorFit"),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.organisation"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(t("about.org_name")),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.purpose"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(
                                            t("about.purpose_desc")
                                        ),
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.version"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[1]),  # type: ignore[index]
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.status"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[0]),  # type: ignore[index]
                                    ),
                                    ui.tags.tr(
                                        ui.tags.td(
                                            t("about.release_date"), class_="fw-bold pe-3 py-1"
                                        ),
                                        ui.tags.td(self._config.version[2]),  # type: ignore[index]
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
            value=self.TAB_NAME,
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
