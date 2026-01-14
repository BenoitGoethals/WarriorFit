# Python
from __future__ import annotations

import logging
from pathlib import Path
from shiny import ui, render, reactive

from warriorfit.ui.controllers.reports_controller import ReportsController, ReportRequest
from warriorfit.ui.pages.page import Page


class ReportsPage(Page):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ReportsController()
        self._status_msg = reactive.Value(("info", "Click 'Generate Report' to create your report."))
        self._last_paths = reactive.Value([])
        self.__logger = logging.getLogger(__name__)

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Reports",
            ui.h2("Reports"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_text("report_title", "Report Title:", "Fitness Test Report"),
                    ui.input_checkbox("own_Unit", "Own Unit", value=True),
                    ui.input_checkbox("this_year", "This Year", value=True),
                    ui.input_select(
                        "test_type",
                        "Test Type:",
                        {
                            "all": "All Tests",
                            "PHEF": "PHEF Tests",
                            "FUNCTIONAL": "Functional Tests",
                            "COMBAT": "Combat Tests",
                            "SWIMMING": "Swimming Tests",
                        },
                    ),
                    ui.input_select(
                        "report_format",
                        "Export Format:",
                        {
                            "pdf": "PDF",
                            "csv": "CSV",
                            "both": "Both (PDF & CSV)",
                        },
                    ),
                    ui.input_action_button("generate_report", "Generate Report", class_="btn-primary"),
                    ui.download_button("download_report", "Download", class_="btn-primary"),

                    width=300,
                ),
                ui.card(
                    ui.output_ui("report_status"),
                    ui.output_ui("report_paths"),
                ),
            ),
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
                ui.tags.h4("Generated files"),
                ui.tags.ul(*items),
                ui.download_button("download_button", "Download Reports", class_="btn-primary"),
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
_page = ReportsPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)
