# ... existing code ...
from shiny import ui, render, reactive
from pathlib import Path
from datetime import datetime

from ui.services.db_service import DBService
from ui.services.file_service import FileService


class ReportsPage:
    def __init__(self) -> None:
        self.db_service = DBService()
        self.file_service = FileService()

        self._report_data = reactive.Value([])
        self._status_msg = reactive.Value(("info", "Click 'Generate Report' to create your report."))
        self._last_paths = reactive.Value([])

    def ui(self):
        return ui.nav_panel(
            "Reports",
            ui.h2("Reports"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_text("report_title", "Report Title:", "Fitness Test Report"),
                    ui.input_select(
                        "test_type",
                        "Test Type:",
                        {
                            "all": "All Tests",
                            "phef": "PHEF Tests",
                            "functional": "Functional Tests",
                            "combat": "Combat Tests",
                            "swimming": "Swimming Tests",
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
                    ui.input_text("output_folder", "Output Folder:", "reports"),
                    ui.input_action_button("generate_report", "Generate Report", class_="btn-primary"),
                    width=300,
                ),
                # Shiny for Python uses ui.card() or plain container for main content
                ui.card(
                    ui.output_ui("report_status"),
                    ui.output_table("report_preview"),
                    ui.output_ui("report_paths"),
                ),
            ),
        )

    def server(self, input, output, session):
        @reactive.effect
        @reactive.event(input.generate_report)
        async def _generate_report():
            try:
                test_type = input.test_type()
                if test_type == "all":
                    fitness_tests = await self.db_service.get_all_fitness_tests()
                elif test_type == "phef":
                    fitness_tests = await self.db_service.get_all_phef()
                elif test_type == "functional":
                    fitness_tests = await self.db_service.get_all_functional_test()
                elif test_type == "combat":
                    fitness_tests = await self.db_service.get_all_combat_test()
                elif test_type == "swimming":
                    fitness_tests = await self.db_service.get_all_combat_swimming_test()
                else:
                    fitness_tests = []

                if not fitness_tests:
                    self._report_data.set([])
                    self._last_paths.set([])
                    self._status_msg.set(("warning", "No data found for the selected filters."))
                    return

                data = self.file_service.get_fitness_test_data_dict(fitness_tests)
                self._report_data.set(data)

                output_folder = Path(input.output_folder())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = input.report_title().strip().replace(" ", "_") or "Report"
                base_filename = f"{safe_title}_{test_type}_{timestamp}"

                paths = []
                fmt = input.report_format()

                if fmt in ("pdf", "both"):
                    pdf_path = output_folder / f"{base_filename}.pdf"
                    ok = self.file_service.export_fitness_tests_to_pdf(
                        data=data,
                        file_path=str(pdf_path),
                        title=input.report_title(),
                        test_type=test_type.upper(),
                    )
                    if ok:
                        paths.append(str(pdf_path))

                if fmt in ("csv", "both"):
                    csv_path = output_folder / f"{base_filename}.csv"
                    ok = self.file_service.export_to_csv(
                        data=data,
                        file_path=str(csv_path),
                    )
                    if ok:
                        paths.append(str(csv_path))

                if paths:
                    self._last_paths.set(paths)
                    self._status_msg.set(("success", f"Report generated successfully with {len(data)} records."))
                else:
                    self._last_paths.set([])
                    self._status_msg.set(("danger", "Failed to generate report files."))
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