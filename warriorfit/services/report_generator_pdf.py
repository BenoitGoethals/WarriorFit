import logging
import os
from datetime import datetime
from typing import List, Optional, Callable, Any, Dict

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
    def __init__(self):
        super().__init__()
        self._cross_service = ServiceCross()

    async def generate_report(
            self, report_name: str, report_type: ReportType, own_unit: bool, this_year: bool
    ):
        if report_type is ReportType.PHEF:
            return await self.generate_phef_report(report_name, own_unit, this_year)
        elif report_type is ReportType.FUNCTIONAL:
            return await self.generate_functional_report(
                report_name, own_unit, this_year
            )
        elif report_type is ReportType.COMBAT:
            return await self.generate_combat_report(report_name, own_unit, this_year)
        elif report_type is ReportType.SWIMMING:
            return await self.generate_swimming_report(report_name, own_unit, this_year)
        else:
            raise ValueError("Invalid report type")

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

        headers = ["order", "Serial Number", "Name", "Running Time", "Age", "Unit"]

        def row_builder(runner: dict) -> List[Any]:
            return [
                runner["order"],
                runner["serial_number"],
                runner["Name"],
                self._fmt_time(runner["running_time"]),
                runner["Age"],
                runner["Unit"],
            ]

        rows = []

        for runner in result.runners:
            runner_det = await self.be_mil_service.get_servicemen_by_serial(
                runner.serial_number, lazy=False
            )
            if runner_det:
                rows.append(
                    {
                        "order": None,
                        "serial_number": runner.serial_number or "",
                        "Name": runner_det.first_name + " " + runner_det.last_name
                                or "",
                        "running_time": runner.running_time,
                        "Age": runner_det.age_from_birthdate() or "",
                        "Unit": runner_det.unit or "",
                    }
                )
        rows = sorted(
            rows,
            key=lambda r: (
                r.get("running_time") is None,
                r.get("running_time") or float("inf"),
            ),
        )
        for idx, r in enumerate(rows, start=1):
            r["order"] = idx

        return self._build_pdf(
            rows,
            report_name,
            f'Cross Report - {result.datetime_start.strftime("%Y-%m-%d %H:%M:%S")}  {len(rows)} runners',
            "cross_runners",
            headers,
            row_builder,
        )

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
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
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

    def _build_pdf(
            self,
            rows: List[dict],
            report_name: str,
            title: str,
            file_suffix: str,
            headers: List[str],
            row_builder: Callable[[dict], List[Any]],
    ) -> Optional[str]:
        if not rows:
            return None
        deps = self._ensure_pdf_deps()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{report_name}_{file_suffix}_{timestamp}.pdf"
        out_dir = _output_dir()

        output_path = os.path.join(out_dir, file_name)

        doc = deps["SimpleDocTemplate"](output_path, pagesize=deps["A4"])
        styles = deps["getSampleStyleSheet"]()
        story = [
            deps["Paragraph"](title, styles["Title"]),
            deps["Spacer"](1, 12),
        ]

        data = [headers]
        for r in rows:
            data.append(row_builder(r))

        tbl = deps["Table"](data, repeatRows=1)
        tbl.setStyle(
            deps["TableStyle"](
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
        )
        story.append(tbl)
        doc.build(story)
        self._logger.info(f"Generating PDF: {output_path}")
        return output_path

    async def generate_phef_report(
            self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a PHEF (Performance Health Evaluation Framework) report containing the
        details of passed and failed tests as two separate PDF files. The method processes
        data based on the provided criteria, formats it into tables, and generates PDFs
        with comprehensive test details.

        :param report_name: Name of the report to be generated, used as a reference for
                            output files.
        :type report_name: str
        :param own_unit: Whether to process data only for the current unit or include
                         all units.
        :type own_unit: bool
        :param this_year: Flag to filter data for the current year only.
        :type this_year: bool
        :return: A dictionary containing paths to the two generated PDF files, one for
                 passed tests and the other for failed tests.
        :rtype: dict
        """

        headers, passed, failed = await self.calculate_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [

                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                self._fmt_time(r["run_time_s"]),
                f"{r['run_score']}",
                self._fmt_time(r["side_r_s"]),
                f"{r['side_r_score']}",
                self._fmt_time(r["side_l_s"]),
                f"{r['side_l_score']}",
                f"{r['total']:.1f}",
            ]

        failed_path = self._build_pdf(
            failed,
            report_name,
            f"PHEF Failed Tests Report ({len(failed)} records)",
            "phef_failed",
            headers,
            row_builder,
        )
        passed_path = self._build_pdf(
            passed,
            report_name,
            f"PHEF Passed Tests Report ({len(passed)} records)",
            "phef_passed",
            headers,
            row_builder,
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_functional_report(
            self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a functional report based on passed and failed test data. This function
        calculates functional scores and generates PDF reports for both failed and
        passed tests, including detailed records of test sessions.

        :param report_name: The name of the report.
        :param own_unit: Flag indicating whether to filter data for the user's own unit.
        :param this_year: Flag indicating whether to filter data for the current year.
        :return: A dictionary containing file paths to the generated failed and passed
            reports.
        :rtype: dict
        """
        failed, headers, passed = await self.calculate_functional_score(
            own_unit, this_year
        )

        def row_builder(r: dict) -> List[Any]:
            return [

                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                r["push_ups"],
                r["sit_ups"],
                r["pull_ups"],
                r["total"],
            ]

        failed_path = self._build_pdf(
            failed,
            report_name,
            f"Functional Failed Tests ({len(failed)} records)",
            "functional_failed",
            headers,
            row_builder,
        )
        passed_path = self._build_pdf(
            passed,
            report_name,
            f"Functional Passed Tests ({len(passed)} records)",
            "functional_passed",
            headers,
            row_builder,
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_combat_report(
            self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a combat report by calculating combat scores, segregating data into
        failed and passed records, and exporting the results to PDF files.

        :param report_name: The name of the report to be generated.
        :type report_name: str
        :param own_unit: Boolean indicating whether to filter records by the unit's
            own data.
        :type own_unit: bool
        :param this_year: Boolean indicating whether to filter records to only
            include data from the current year.
        :type this_year: bool
        :return: A dictionary with paths to the generated PDFs for failed and passed
            records. The keys are "failed" and "passed", respectively.
        :rtype: dict
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
            """
            Builds a list of values from a given dictionary. Each value in the list is extracted
            or computed from the dictionary keys or their corresponding values. The function
            formats and converts some values, such as dates and times, while keeping specific logic
            for representing certain states (e.g., Passed/Failed). Aimed at constructing rows
            for further processing or data usage.

            :param r: Dictionary containing keys required to build the row. Expected keys include
                      "session_id", "session_date", "serial", "rope", "obstacle", "run_time_s",
                      and "result".
            :type r: dict
            :return: A list of values extracted or computed from the input dictionary.
            :rtype: List[Any]
            """
            return [
                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                "Passed" if r["rope"] else "Failed",
                "Passed" if r["obstacle"] else "Failed",
                self._fmt_time(r["run_time_s"]),
                r["result"],
            ]

        failed_path = self._build_pdf(
            failed,
            report_name,
            f"Combat Failed Tests ({len(failed)} records)",
            "combat_failed",
            headers,
            row_builder,
        )
        passed_path = self._build_pdf(
            passed,
            report_name,
            f"Combat Passed Tests ({len(passed)} records)",
            "combat_passed",
            headers,
            row_builder,
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_swimming_report(
            self, report_name: str, own_unit: bool, this_year: bool
    ):
        """
        Generates a swimming test report in PDF format for failed and passed tests. This method
        calculates swimming test scores and builds two PDF reports: one for the records of
        failed tests and another for passed tests.

        :param report_name: The name of the report to be generated.
        :param own_unit: Indicates whether to include only the current unit in the report.
        :param this_year: Specifies whether the report covers only the current year's data.
        :return: A dictionary containing file paths of the generated PDF reports for failed and
                 passed tests.
        """
        failed, headers, passed = await self.calculate_swim_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [
                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                r["result"],
            ]

        failed_path = self._build_pdf(
            failed,
            report_name,
            f"Swimming Failed Tests ({len(failed)} records)",
            "swimming_failed",
            headers,
            row_builder,
        )
        passed_path = self._build_pdf(
            passed,
            report_name,
            f"Swimming Passed Tests ({len(passed)} records)",
            "swimming_passed",
            headers,
            row_builder,
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_ind_report_current_year(self, serial_number: str):
        """
        Generate an individual report for the current year, including a summary of a serviceman's
        details and test results, outputted as a PDF document.

        :param serial_number: A string representing the serviceman's serial number.
        :return: The file path to the generated PDF report as a string.
        """
        current_year = datetime.now().year

        # Get serviceman details
        serviceman = await self.be_mil_service.get_servicemen_by_serial(serial_number, lazy=False)

        deps = self._ensure_pdf_deps()
        file_name = f"Report_{serial_number}_{current_year}.pdf"
        output_path = os.path.join(_output_dir(), file_name)

        doc = deps["SimpleDocTemplate"](output_path, pagesize=deps["A4"])
        styles = deps["getSampleStyleSheet"]()

        story = [
            deps["Paragraph"](f"Individual Report - {current_year}", styles["Title"]),
            deps["Spacer"](1, 12),
        ]

        if not serviceman:
            story.append(deps["Paragraph"]("Serviceman not found", styles["Normal"]))
        else:
            collector = DataCollector()

            story.append(deps["Paragraph"](
                f"Name: {serviceman.first_name} {serviceman.last_name}\n"
                f"Serial: {serviceman.service_number}\n"
                f"Unit: {serviceman.unit}\n"
                f"Age: {serviceman.age_from_birthdate()}",

                styles["Normal"]
            ))

            story.append(deps["Spacer"](1, 12))
            data_df = await collector.collect_tests_data_for_serial(serial_number)

            def process_table(title, data, headers, row_mapper):
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

                tbl_data = [headers]
                for r in records:
                    tbl_data.append(row_mapper(r))

                t = deps["Table"](tbl_data, repeatRows=1)
                t.setStyle(
                    deps["TableStyle"](
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
                )
                story.append(t)
                story.append(deps["Spacer"](1, 12))


            def get_type_data(df, t_type):
                if df is None or df.empty:
                    return []
                filtered = df[df["Type"] == t_type]
                return filtered.to_dict("records")

            # PHEF
            def phef_mapper(r):
                return [
                    r.get("Date", "-"),
                    self._fmt_time(float(r.get("Run") or 0)),
                    self._fmt_time(float(r.get("SBR") or 0)),
                    self._fmt_time(float(r.get("SBL") or 0)),
                    r.get("Total", "-")
                ]

            process_table(
                "PHEF Tests",
                get_type_data(data_df, "PHEF"),
                ["Date", "Run", "Side R", "Side L", "Total"],
                phef_mapper
            )

            # Functional
            def func_mapper(r):
                return [
                    r.get("Date", "-"),
                    str(r.get("PU", "-")),
                    str(r.get("SU", "-")),
                    str(r.get("PLU", "-")),
                    str(r.get("Total", "-"))
                ]

            process_table(
                "Functional Tests",
                get_type_data(data_df, "Functional"),
                ["Date", "Push-Ups", "Sit-Ups", "Pull-Ups", "Total"],
                func_mapper
            )

            # Combat
            def combat_mapper(r):
                return [
                    r.get("Date", "-"),
                    self._fmt_time(float(r.get("Speed") or 0)),
                    r.get("Rop_scores", "-"),
                    r.get("Obs_scores", "-")
                ]

            process_table(
                "Combat Tests",
                get_type_data(data_df, "Combat"),
                ["Date", "Run Time", "Rope", "Obstacle"],
                combat_mapper
            )

            # Swimming
            def swim_mapper(r):
                return [
                    r.get("Date", "-"),
                    r.get("Result", "-")
                ]

            process_table(
                "Swimming Tests",
                get_type_data(data_df, "Swimming"),
                ["Date", "Result"],
                swim_mapper
            )

            # Mars
            def mars_mapper(r):
                return [
                    r.get("Date", "-"),
                    r.get("Details", "-"),
                    r.get("Result", "-")
                ]

            process_table(
                "Mars Tests",
                get_type_data(data_df, "Mars"),
                ["Date", "Distance", "Result"],
                mars_mapper
            )

            story.append(deps["Spacer"](1, 20))
            doc.build(story)
            self._logger.info(f"Generating PDF: {output_path}")
            return output_path

    def _create_test_results_table(self, df: pd.DataFrame, deps: Dict):
        """Creates a table with test results for unit members"""
        headers = ["Rank", "Serial", "Name", "Phef", "Combat", "Swimming", "Functional", "Mars"]
        df_mapped = df.rename(columns={"Service Number": "Serial", "PHEF": "Phef"})
        for h in headers:
            if h not in df_mapped.columns:
                df_mapped[h] = "-"
        data_rows = df_mapped[headers].fillna("-").astype(str).values.tolist()
        table_data = [headers] + data_rows
        table = deps["Table"](table_data, repeatRows=1)
        table.setStyle(deps["TableStyle"]([
            ("BACKGROUND", (0, 0), (-1, 0), deps["colors"].lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), deps["colors"].black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, deps["colors"].grey),
            ("BOX", (0, 0), (-1, -1), 0.5, deps["colors"].black),
        ]))
        return table

    async def generate_total_report_current_year_own_unit(self):
        data_collector = DataCollector()
        df = await data_collector.collect_tests_data_for_own_unit()

        deps = self._ensure_pdf_deps()
        file_name = f"Report_Own_unit_{datetime.now().year}.pdf"
        output_path = os.path.join(_output_dir(), file_name)

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
        self._logger.info(f"Generating PDF: {output_path}")
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
