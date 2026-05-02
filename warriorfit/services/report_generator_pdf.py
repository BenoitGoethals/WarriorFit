import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from warriorfit.services.data_collector import DataCollector
from warriorfit.services.generator import GeneratorReport, _output_dir
from warriorfit.services.report_type import ReportType
from warriorfit.services.service_cross import ServiceCross


class ReportGeneratorPdf(GeneratorReport):
    """
    Class responsible for generating PDF reports of various types. The generated reports can include
    PHEF (Physical Efficiency and Fitness), Functional, Combat, Swimming, and Cross Runner data.

    The purpose of this class is to provide specialized methods that handle data transformation and PDF
    generation for the reports, leveraging utility services for data retrieval and formatting where needed.

    :ivar be_mil_service: Responsible for retrieving servicemen's details.
    :type be_mil_service: Service or similar object, implementation-specific
    :ivar logger: Logger instance for logging report generation and relevant activity.
    :type logger: logging.Logger
    """

    # PDF Table Style Constants
    _TABLE_STYLE_CONFIG = [
        ("BACKGROUND", (0, 0), (-1, 0)),  # Header background
        ("TEXTCOLOR", (0, 0), (-1, 0)),  # Header text color
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("INNERGRID", (0, 0), (-1, -1), 0.25),  # Inner grid
        ("BOX", (0, 0), (-1, -1), 0.5),  # Outer box
    ]

    def __init__(
        self,
        cross_service: ServiceCross = None,
        military_service=None,
        service_test=None,
        config=None,
    ):
        super().__init__(military_service=military_service, service_test=service_test, config=config)
        self._cross_service = (
            cross_service if cross_service is not None else ServiceCross()
        )
        self._report_generators = {
            ReportType.PHEF: self.generate_phef_report,
            ReportType.FUNCTIONAL: self.generate_functional_report,
            ReportType.COMBAT: self.generate_combat_report,
            ReportType.SWIMMING: self.generate_swimming_report,
        }

    async def generate_report(
        self, report_name: str, report_type: ReportType, own_unit: bool, this_year: bool
    ):
        """Generate a report based on the specified type using dictionary dispatch."""
        generator = self._report_generators.get(report_type)
        if not generator:
            raise ValueError(f"Invalid report type: {report_type}")
        return await generator(report_name, own_unit, this_year)

    async def generate_run_report(self, report_name: str, cross: int):
        """
        Generates a PDF report for a cross run event by fetching runners' details,
        sorting them based on their running time, and formatting the result into a
        report layout.

        :param report_name: The name of the report to be generated.
        :type report_name: str
        :param cross: An identifier for the cross run event.
        :type cross: int
        :return: A PDF file representing the generated report, or None if no data is available.
        :rtype: Any
        """
        result = await self._cross_service.get_cross_by_id(cross, lazy=False)

        if not result or not result.runners:
            return None

        rows = await self._fetch_runner_details(result.runners)
        sorted_rows = self._sort_and_rank_runners(rows)

        headers = ["order", "Serial Number", "Name", "Running Time", "Age", "Unit"]
        title = f"Cross Report - {result.datetime_start.strftime('%Y-%m-%d %H:%M:%S')}  {len(sorted_rows)} runners"  # type: ignore[attr-defined]

        return self._build_pdf(
            sorted_rows,
            report_name,
            title,
            "cross_runners",
            headers,
            self._build_runner_row,
        )

    async def _fetch_runner_details(self, runners) -> List[dict]:
        """Fetches and builds runner detail dictionaries from runner objects."""
        rows = []
        for runner in runners:
            runner_det = await self.be_mil_service.get_servicemen_by_serial(
                runner.serial_number, lazy=False
            )
            if runner_det:
                rows.append(
                    {
                        "order": None,
                        "serial_number": runner.serial_number or "",
                        "Name": f"{runner_det.first_name} {runner_det.last_name}",
                        "running_time": runner.running_time,
                        "Age": runner_det.age_from_birthdate() or "",
                        "Unit": runner_det.unit or "",
                    }
                )
        return rows

    @staticmethod
    def _sort_and_rank_runners(rows: List[dict]) -> List[dict]:
        """Sorts runners by time and assigns ranking order."""
        sorted_rows = sorted(
            rows,
            key=lambda r: (
                r.get("running_time") is None,
                r.get("running_time") or float("inf"),
            ),
        )
        for idx, row in enumerate(sorted_rows, start=1):
            row["order"] = idx
        return sorted_rows

    def _build_runner_row(self, runner: dict) -> List[Any]:
        """Builds a table row from runner dictionary."""
        return [
            runner["order"],
            runner["serial_number"],
            runner["Name"],
            self._fmt_time(runner["running_time"]),
            runner["Age"],
            runner["Unit"],
        ]

    @staticmethod
    def _fmt_time(sec: int | float | None) -> str:
        """
        Formats a given time in seconds into a string formatted as "MM:SS".

        This method takes an integer, float, or None as input, representing a duration
        in seconds. It converts this duration into a string format with minutes and
        seconds (MM:SS). If the input is None or invalid, it will return a fallback
        placeholder string "-" instead.

        :param sec: The duration in seconds to format. It can be an integer, float,
                    or None.
        :return: A string representing the duration formatted as "MM:SS". If the
                 input is invalid or None, returns "-".
        """
        try:
            s = int(sec or 0)
            return f"{s // 60}:{s % 60:02d}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_date(date_obj) -> str:
        """Formats a date object or returns '-' if None."""
        return "-" if date_obj is None else date_obj.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _fmt_pass_fail(result: str) -> str:
        """
        Formats a pass/fail result with colored icons.
        Returns green checkmark (✓) for passed, red X (✗) for failed.

        :param result: The result string (e.g., "Passed", "Failed")
        :return: Formatted string with color markup for PDF
        """
        if not result or result == "-":
            return "-"

        result_lower = str(result).lower()
        if "pass" in result_lower:
            return '<font color="green">✓ Passed</font>'
        elif "fail" in result_lower:
            return '<font color="red">✗ Failed</font>'
        return result

    @staticmethod
    def _ensure_pdf_deps():
        """
        Ensures that the required dependencies for generating PDFs are available.

        Attempts to import the necessary modules from the `reportlab` library and
        returns them encapsulated in a dictionary for ease of access. If the required
        dependency `reportlab` is not installed, a `RuntimeError` is raised.

        This static method provides a centralized approach to check for and manage
        dependencies related to PDF generation.

        :raises RuntimeError: If the `reportlab` library is not installed, an error
            is raised prompting the user to install the dependency.
        :return: A dictionary containing the `reportlab` dependencies required
            for PDF generation. Keys include "A4", "colors", "getSampleStyleSheet",
            "SimpleDocTemplate", "Paragraph", "Spacer", "Table", and "TableStyle".
        :rtype: dict
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            return {
                "A4": A4,
                "colors": colors,
                "getSampleStyleSheet": getSampleStyleSheet,
                "SimpleDocTemplate": SimpleDocTemplate,
                "Paragraph": Paragraph,
                "Spacer": Spacer,
                "Table": Table,
                "TableStyle": TableStyle,
            }
        except ImportError as e:
            raise RuntimeError(
                "reportlab is required to generate PDF. Install it with 'uv add reportlab'."
            ) from e

    def _create_table_style(self, deps: Dict):
        """Creates a standardized table style for PDF reports."""
        return deps["TableStyle"](
            [
                ("BACKGROUND", (0, 0), (-1, 0), deps["colors"].lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), deps["colors"].black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, deps["colors"].grey),
                ("BOX", (0, 0), (-1, -1), 0.5, deps["colors"].black),
            ]
        )

    def _build_pdf(
        self,
        rows: List[dict],
        report_name: str,
        title: str,
        file_suffix: str,
        headers: List[str],
        row_builder: Callable[[dict], List[Any]],
    ) -> Optional[str]:
        """Builds a PDF file from structured data with standardized formatting."""
        if not rows:
            return None

        deps = self._ensure_pdf_deps()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{report_name}_{file_suffix}_{timestamp}.pdf"
        output_path = os.path.join(_output_dir(self._config), file_name)

        doc = deps["SimpleDocTemplate"](output_path, pagesize=deps["A4"])
        styles = deps["getSampleStyleSheet"]()
        story = [
            deps["Paragraph"](title, styles["Title"]),
            deps["Spacer"](1, 12),
        ]

        # Build table data and convert markup strings to Paragraphs
        data = [headers]
        for r in rows:
            row_data = row_builder(r)
            # Convert any string with markup to Paragraph for colored text
            processed_row = []
            for cell in row_data:
                if isinstance(cell, str) and "<font" in cell:
                    processed_row.append(deps["Paragraph"](cell, styles["Normal"]))
                else:
                    processed_row.append(cell)
            data.append(processed_row)

        tbl = deps["Table"](data, repeatRows=1)
        tbl.setStyle(self._create_table_style(deps))
        story.append(tbl)
        doc.build(story)
        self._logger.info("Generating PDF: %s", output_path)
        return output_path

    def _build_report_row_with_date(self, r: dict, *fields) -> List[Any]:
        """Helper to build report rows that start with a date field."""
        return [self._fmt_date(r["session_date"])] + list(fields)

    async def generate_phef_report(
        self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a PHEF (Performance Health Evaluation Framework) report containing the
        details of passed and failed tests as two separate PDF files.

        :param report_name: Name of the report to be generated.
        :param own_unit: Whether to process data only for the current unit.
        :param this_year: Flag to filter data for the current year only.
        :return: A dictionary containing paths to the two generated PDF files.
        """
        headers, passed, failed = await self.calculate_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [
                self._fmt_date(r["session_date"]),
                r["serial"],
                self._fmt_time(r["run_time_s"]),
                f"{r['run_score']}",
                self._fmt_time(r["side_r_s"]),
                f"{r['side_r_score']}",
                self._fmt_time(r["side_l_s"]),
                f"{r['side_l_score']}",
                f"{r['total']:.1f}",
            ]

        return self._generate_pass_fail_reports(
            report_name, "PHEF", passed, failed, headers, row_builder
        )

    async def generate_functional_report(
        self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a functional report based on passed and failed test data.

        :param report_name: The name of the report.
        :param own_unit: Flag indicating whether to filter data for the user's own unit.
        :param this_year: Flag indicating whether to filter data for the current year.
        :return: A dictionary containing file paths to the generated failed and passed reports.
        """
        failed, headers, passed = await self.calculate_functional_score(
            own_unit, this_year
        )

        def row_builder(r: dict) -> List[Any]:
            return [
                self._fmt_date(r["session_date"]),
                r["serial"],
                r["push_ups"],
                r["sit_ups"],
                r["pull_ups"],
                r["total"],
            ]

        return self._generate_pass_fail_reports(
            report_name, "Functional", passed, failed, headers, row_builder
        )

    async def generate_combat_report(
        self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a combat report by calculating combat scores, segregating data into
        failed and passed records, and exporting the results to PDF files.

        :param report_name: The name of the report to be generated.
        :param own_unit: Boolean indicating whether to filter records by the unit's own data.
        :param this_year: Boolean indicating whether to filter records to only include data from the current year.
        :return: A dictionary with paths to the generated PDFs for failed and passed records.
        """
        failed, headers, passed = await self.calculate_combat_score(own_unit, this_year)

        headers = [
            "Date",
            "Serial",
            "Rope",
            "Obstacle",
            "Speedmars Time",
            "Result",
        ]

        def row_builder(r: dict) -> List[Any]:
            return [
                self._fmt_date(r["session_date"]),
                r["serial"],
                self._fmt_pass_fail("Passed" if r["rope"] else "Failed"),
                self._fmt_pass_fail("Passed" if r["obstacle"] else "Failed"),
                self._fmt_time(r["run_time_s"]),
                self._fmt_pass_fail(r["result"]),
            ]

        return self._generate_pass_fail_reports(
            report_name, "Combat", passed, failed, headers, row_builder
        )

    async def generate_swimming_report(
        self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a swimming test report in PDF format for failed and passed tests.

        :param report_name: The name of the report to be generated.
        :param own_unit: Indicates whether to include only the current unit in the report.
        :param this_year: Specifies whether the report covers only the current year's data.
        :return: A dictionary containing file paths of the generated PDF reports.
        """
        failed, headers, passed = await self.calculate_swim_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [
                self._fmt_date(r["session_date"]),
                r["serial"],
                self._fmt_pass_fail(r["result"]),
            ]

        return self._generate_pass_fail_reports(
            report_name, "Swimming", passed, failed, headers, row_builder
        )

    def _generate_pass_fail_reports(
        self,
        report_name: str,
        test_type: str,
        passed: List[dict],
        failed: List[dict],
        headers: List[str],
        row_builder: Callable[[dict], List[Any]],
    ) -> Dict[str, Optional[str]]:
        """
        Generates both passed and failed PDF reports for a given test type.

        :param report_name: Base name for the report files.
        :param test_type: Type of test (e.g., "PHEF", "Functional").
        :param passed: List of passed test records.
        :param failed: List of failed test records.
        :param headers: Table headers.
        :param row_builder: Function to build rows from records.
        :return: Dictionary with 'passed' and 'failed' file paths.
        """
        failed_path = self._build_pdf(
            failed,
            report_name,
            f"{test_type} Failed Tests ({len(failed)} records)",
            f"{test_type.lower()}_failed",
            headers,
            row_builder,
        )
        passed_path = self._build_pdf(
            passed,
            report_name,
            f"{test_type} Passed Tests ({len(passed)} records)",
            f"{test_type.lower()}_passed",
            headers,
            row_builder,
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_ind_report(self, serial_number: str):
        """
        Generate an individual report for all years, including a summary of a serviceman's
        details and test results, outputted as a PDF document.

        :param serial_number: A string representing the serviceman's serial number.
        :return: The file path to the generated PDF report as a string.
        """
        return await self._generate_individual_report(
            serial_number, current_year_only=False
        )

    async def generate_ind_report_current_year(self, serial_number: str):
        """
        Generate an individual report for the current year, including a summary of a serviceman's
        details and test results, outputted as a PDF document.

        :param serial_number: A string representing the serviceman's serial number.
        :return: The file path to the generated PDF report as a string.
        """
        return await self._generate_individual_report(
            serial_number, current_year_only=True
        )

    async def _generate_individual_report(
        self, serial_number: str, current_year_only: bool
    ):
        """
        Core method to generate individual reports with or without year filtering.

        :param serial_number: Serviceman's serial number.
        :param current_year_only: If True, only include current year data.
        :return: Path to generated PDF file.
        """
        current_year = datetime.now().year
        serviceman = await self.be_mil_service.get_servicemen_by_serial(
            serial_number, lazy=False
        )

        deps = self._ensure_pdf_deps()
        year_suffix = f"_{current_year}" if current_year_only else ""
        file_name = f"Report_{serial_number}{year_suffix}.pdf"
        output_path = os.path.join(_output_dir(self._config), file_name)

        doc = deps["SimpleDocTemplate"](output_path, pagesize=deps["A4"])
        styles = deps["getSampleStyleSheet"]()

        title_year = f" - {current_year}" if current_year_only else ""
        story = [
            deps["Paragraph"](f"Individual Report{title_year}", styles["Title"]),
            deps["Spacer"](1, 12),
        ]

        if not serviceman:
            story.append(deps["Paragraph"]("Serviceman not found", styles["Normal"]))
        else:
            story.extend(self._build_serviceman_info(serviceman, styles, deps))
            story.append(deps["Spacer"](1, 12))

            collector = DataCollector()
            data_df = await collector.collect_tests_data_for_serial(
                serial_number, current_year=current_year_only
            )

            self._add_test_tables_to_story(story, data_df, deps, styles)
            story.append(deps["Spacer"](1, 20))

        doc.build(story)
        self._logger.info("Generating PDF: %s", output_path)
        return output_path

    def _build_serviceman_info(self, serviceman, styles, deps) -> List:
        """Builds serviceman information paragraph for PDF."""
        return [
            deps["Paragraph"](
                f"Name: {serviceman.first_name} {serviceman.last_name}\n"
                f"Serial: {serviceman.service_number}\n"
                f"Unit: {serviceman.unit}\n"
                f"Age: {serviceman.age_from_birthdate()}",
                styles["Normal"],
            )
        ]

    def _add_test_tables_to_story(
        self, story: List, data_df: pd.DataFrame, deps: Dict, styles
    ):
        """Adds all test type tables to the PDF story."""
        test_configs = [
            (
                "PHEF Tests",
                "PHEF",
                ["Date", "Run", "Side R", "Side L", "Total"],
                self._phef_mapper,
            ),
            (
                "Functional Tests",
                "Functional",
                ["Date", "Push-Ups", "Sit-Ups", "Pull-Ups", "Total"],
                self._func_mapper,
            ),
            (
                "Combat Tests",
                "Combat",
                ["Date", "Run Time", "Rope", "Obstacle"],
                self._combat_mapper,
            ),
            ("Swimming Tests", "Swimming", ["Date", "Result"], self._swim_mapper),
            ("Mars Tests", "Mars", ["Date", "Distance", "Result"], self._mars_mapper),
        ]

        for title, test_type, headers, mapper in test_configs:
            self._process_table(
                story,
                title,
                self._get_type_data(data_df, test_type),
                headers,
                mapper,
                deps,
                styles,
            )

    def _process_table(
        self,
        story: List,
        title: str,
        data,
        headers: List[str],
        row_mapper: Callable,
        deps: Dict,
        styles,
    ):
        """Processes and adds a single test type table to the story."""
        if data is None:
            return

        records = []
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return
            records = data.to_dict("records")
        elif isinstance(data, list):
            if not data:
                return
            records = data

        if not records:
            return

        story.append(deps["Paragraph"](title, styles["Heading3"]))
        story.append(deps["Spacer"](1, 6))

        # Build table data with markup support
        tbl_data = [headers]
        for r in records:
            row_data = row_mapper(r)
            # Convert any string with markup to Paragraph for colored text
            processed_row = []
            for cell in row_data:
                if isinstance(cell, str) and "<font" in cell:
                    processed_row.append(deps["Paragraph"](cell, styles["Normal"]))
                else:
                    processed_row.append(cell)
            tbl_data.append(processed_row)

        t = deps["Table"](tbl_data, repeatRows=1)
        t.setStyle(self._create_table_style(deps))
        story.append(t)
        story.append(deps["Spacer"](1, 12))

    @staticmethod
    def _get_type_data(df: pd.DataFrame, t_type: str):
        """Filters dataframe by test type."""
        if df is None or df.empty:
            return []
        filtered = df[df["Type"] == t_type]
        return filtered.to_dict("records")

    def _phef_mapper(self, r: dict) -> List[Any]:
        """Maps PHEF test record to table row."""
        return [
            r.get("Date", "-"),
            self._fmt_time(float(r.get("Run") or 0)),
            self._fmt_time(float(r.get("SBR") or 0)),
            self._fmt_time(float(r.get("SBL") or 0)),
            r.get("Total", "-"),
        ]

    @staticmethod
    def _func_mapper(r: dict) -> List[Any]:
        """Maps Functional test record to table row."""
        return [
            r.get("Date", "-"),
            str(r.get("PU", "-")),
            str(r.get("SU", "-")),
            str(r.get("PLU", "-")),
            str(r.get("Total", "-")),
        ]

    def _combat_mapper(self, r: dict) -> List[Any]:
        """Maps Combat test record to table row."""
        return [
            r.get("Date", "-"),
            self._fmt_time(float(r.get("Speed") or 0)),
            r.get("Rop_scores", "-"),
            r.get("Obs_scores", "-"),
        ]

    def _swim_mapper(self, r: dict) -> List[Any]:
        """Maps Swimming test record to table row."""
        return [r.get("Date", "-"), self._fmt_pass_fail(r.get("Result", "-"))]

    def _mars_mapper(self, r: dict) -> List[Any]:
        """Maps Mars test record to table row."""
        return [
            r.get("Date", "-"),
            r.get("Details", "-"),
            self._fmt_pass_fail(r.get("Result", "-")),
        ]

    def _create_test_results_table(self, df: pd.DataFrame, deps: Dict):
        """Creates a table with test results for unit members."""
        headers = [
            "Rank",
            "Serial",
            "Name",
            "Phef",
            "Combat",
            "Swimming",
            "Functional",
            "Mars",
        ]
        df_mapped = df.rename(columns={"Service Number": "Serial", "PHEF": "Phef"})
        for h in headers:
            if h not in df_mapped.columns:
                df_mapped[h] = "-"
        data_rows = df_mapped[headers].fillna("-").astype(str).values.tolist()
        table_data = [headers] + data_rows
        table = deps["Table"](table_data, repeatRows=1)
        table.setStyle(self._create_table_style(deps))
        return table

    async def generate_total_report_current_year_own_unit(self):
        """Generates a unit-wide report for the current year."""
        data_collector = DataCollector()
        df = await data_collector.collect_tests_data_for_own_unit()

        deps = self._ensure_pdf_deps()
        file_name = f"Report_Own_unit_{datetime.now().year}.pdf"
        output_path = os.path.join(_output_dir(self._config), file_name)

        doc = deps["SimpleDocTemplate"](output_path, pagesize=deps["A4"])
        styles = deps["getSampleStyleSheet"]()

        story = [
            deps["Paragraph"](f"Unit Report - {datetime.now().year}", styles["Title"]),
            deps["Spacer"](1, 12),
        ]

        if df is None or df.empty:
            story.append(deps["Paragraph"]("No data available", styles["Normal"]))
        else:
            table = self._create_test_results_table(df, deps)
            story.append(table)
            story.append(deps["Spacer"](1, 12))

        doc.build(story)
        self._logger.info("Generating PDF: %s", output_path)
        return output_path


if __name__ == "__main__":
    import asyncio

    async def main():
        gem = ReportGeneratorPdf()
        # await gem.generate_run_report("run", 1)
        # await gem.generate_ind_report_current_year("BE-20250001")
        await gem.generate_total_report_current_year_own_unit()

    #  await gem.generate_report("tstasd", ReportType.COMBAT,True,True)
    # await gem.generate_report( "tstwe", ReportType.SWIMMING,True,True)
    # await gem.generate_report( "tstf", ReportType.FUNCTIONAL,True,True)
    # await gem.generate_report( "tstsdf", ReportType.PHEF,True,True)

    asyncio.run(main())
