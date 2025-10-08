# ... existing code ...
from shiny import ui, render, reactive

from services.db_service import DBService
from services.file_service import FileService

from services.report_generator_csv import ReportGeneratorCsv
from services.report_generator_pdf import ReportGeneratorPdf

from services.report_type import ReportType


class ReportsPage:
    def __init__(self) -> None:
        self.db_service = DBService()
        self.file_service = FileService()

        self._report_data = reactive.Value([])
        self._status_msg = reactive.Value(("info", "Click 'Generate Report' to create your report."))
        self._last_paths = reactive.Value([])
        # New generators
        self._csv_gen = ReportGeneratorCsv()
        self._pdf_gen = ReportGeneratorPdf()

    def ui(self):
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
                    width=300,
                ),
                # Shiny for Python uses ui.card() or plain container for main content
                ui.card(
                    ui.output_ui("report_status"),
                  #  ui.output_table("report_preview"),
                    ui.output_ui("report_paths"),
                ),
            ),
        )

    def server(self, input, output, session):
        @reactive.effect
        @reactive.event(input.generate_report)
        async def _generate_report():
            try:
                # Resolve type
                test_type = input.test_type()
                title = input.report_title().strip() or "Report"



                # Map UI type to generator enums (only used by generators internally)
                def _to_report_type(tt: str):
                    # Generators expect their own ReportType; to keep this file decoupled,
                    # we’ll pass the UI string forward and let generators map internally if needed.
                    return tt

                # Generate files using new generators
                fmt = input.report_format()
                paths: list[str] = []
                report_name = title.replace(" ", "_")

                # For "all" we produce each category
                targets = [ReportType.PHEF, ReportType.FUNCTIONAL, ReportType.COMBAT,
                           ReportType.SWIMMING] if test_type == "all" else [ReportType.from_str(test_type)]

                own_unit = input.own_Unit()
                this_year = input.this_year()

                for t in targets:
                    if fmt in ("csv", "both"):
                        csv_result = await self._csv_gen.generate_report(report_name, t,own_unit,this_year)
                        for v in (csv_result or {}).values():
                            if v:
                                paths.append(v)
                    if fmt in ("pdf", "both"):
                        pdf_result = await self._pdf_gen.generate_report(report_name,t,own_unit,this_year)
                        for v in (pdf_result or {}).values():
                            if v:
                                paths.append(v)

                if paths:
                    self._last_paths.set(paths)
                    self._status_msg.set(("success", f"Report generated successfully with preview records."))
                else:
                    self._last_paths.set([])
                    self._status_msg.set(("warning", "No files were generated."))
            except Exception as e:
                self._last_paths.set([])
                self._status_msg.set(("danger", f"Error generating report: {e}"))

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
        @render.table
        def report_preview():
            data = self._report_data.get()
            return data[:10] if data else []

        @output
        @render.ui
        def report_paths():
            paths = self._last_paths.get()
            if not paths:
                return ui.div()
            items = [ui.tags.li(ui.tags.code(p)) for p in paths]
            return ui.div(
                ui.tags.h4("Saved files"),
                ui.tags.ul(*items),
            )


_page = ReportsPage()

def get_ui():
    return _page.ui()

def server(input, output, session):
    return _page.server(input, output, session)