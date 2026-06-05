# Python
from __future__ import annotations

import logging
from pathlib import Path

from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.reports_controller import (
    ReportRequest,
    ReportsController,
)
from warriorfit.ui.pages.page import Page


class ReportsPage(Page):
    TAB_NAME = "Reports"

    @inject
    def __init__(
        self, controller: ReportsController = Provide[Container.reports_controller]
    ) -> None:
        super().__init__()
        self.controller = controller
        self._status_msg = reactive.Value(
            ("info", t("reports.click_to_generate"))
        )
        self._last_paths = reactive.Value([])  # type: ignore[var-annotated]
        self.__logger = logging.getLogger(__name__)

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            t("nav.reports"),
            ui.h2(t("reports.title")),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_text(
                        "report_title", t("reports.report_title_label"), t("reports.fitness_test_report")
                    ),
                    ui.input_checkbox("own_Unit", t("reports.own_unit"), value=True),
                    ui.input_checkbox("this_year", t("reports.this_year"), value=True),
                    ui.input_select(
                        "test_type",
                        t("reports.test_type"),
                        {
                            "all": t("reports.all_tests"),
                            "PHEF": t("reports.phef_tests"),
                            "FUNCTIONAL": t("reports.functional_tests"),
                            "COMBAT": t("reports.combat_tests"),
                            "SWIMMING": t("reports.swimming_tests"),
                        },
                    ),
                    ui.input_select(
                        "report_format",
                        t("reports.export_format"),
                        {
                            "pdf": t("reports.pdf"),
                            "csv": t("reports.csv"),
                            "both": t("reports.both"),
                        },
                    ),
                    ui.input_action_button(
                        "generate_report", t("common.generate_report"), class_="btn-primary"
                    ),
                    ui.download_button(
                        "download_report", t("common.download"), class_="btn-primary"
                    ),
                    width=300,
                ),
                ui.card(
                    ui.output_ui("report_status"),
                    ui.output_ui("report_paths"),
                ),
            ),
            value=self.TAB_NAME,
        )

    def server(self, input, output, session):
        @reactive.effect
        @reactive.event(input.generate_report)
        async def _on_generate():
            req = ReportRequest(
                title=(input.report_title() or "Report").strip(),
                test_type=input.test_type(),
                own_unit=bool(input.own_Unit()),
                this_year=bool(input.this_year()),
                format=input.report_format(),
            )
            paths, status = await self.controller.generate(req)
            self._last_paths.set(paths)
            self._status_msg.set(status)

        @output
        @render.ui
        def report_status():
            level, message = self._status_msg.get()
            cls = {
                "success": "alert alert-success",
                "info": "alert alert-info",
                "warning": "alert alert-warning",
                "danger": "alert alert-danger",
            }.get(level, "alert alert-info")
            return ui.div(ui.tags.div(message, class_=cls))

        @output
        @render.ui
        def report_paths():
            paths = self._last_paths.get()
            if not paths:
                return ui.div()
            items = [ui.tags.li(ui.tags.code(Path(p).name)) for p in paths]
            return ui.div(
                ui.tags.h4(t("reports.generated_files")),
                ui.tags.ul(*items),
            )

        @render.download(filename=lambda: "reports.zip")
        def download_report():
            import io
            import zipfile

            paths = [p for p in self._last_paths.get() or [] if p]
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in paths:
                    try:
                        path_obj = Path(p)
                        if path_obj.is_file():
                            zf.write(path_obj, arcname=path_obj.name)
                    except Exception:
                        logging.exception("Failed to add file to zip")
            buf.seek(0)
            data = buf.read()

            # Return an iterator yielding bytes (not text, not int)
            def _iter():
                yield data

            return _iter()


# Public API: keep same signatures
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = ReportsPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
