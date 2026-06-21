import csv
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from warriorfit.services.generator import GeneratorReport, _output_dir
from warriorfit.services.report_type import ReportType


class ReportGeneratorCsv(GeneratorReport):
    """
    Generates various types of CSV reports for performance assessments.

    This class is responsible for generating performance reports in CSV format.
    It provides comprehensive methods to build reports for different categories such as
    PHEF, functional assessments, combat performance, and swimming performance.
    Reports are generated based on inputs provided, and the class handles concise
    formats and error handling during report generation.

    :ivar calculate_score: Method reference to calculate scores for PHEF reports.
    :ivar calculate_functional_score: Method reference to calculate scores for functional assessments.
    :ivar calculate_combat_score: Method reference to calculate scores for combat performance.
    :ivar calculate_swim_score: Method reference to calculate scores for swimming performance.
    """

    def __init__(self, military_service=None, service_test=None, config=None):
        super().__init__(
            military_service=military_service, service_test=service_test, config=config
        )

    async def generate_report(
        self, report_name: str, report_type: ReportType, own_unit: bool, this_year: bool
    ):
        """
        Generates a report based on the specified parameters. The function handles different
        report types such as PHEF, Functional, Combat, and Swimming, and passes the required
        details to the corresponding specific report generation function. If the report type
        is invalid, it raises a ValueError.

        :param report_name: The name of the report.
        :param report_type: Enum value representing the type of the report.
        :param own_unit: Whether the report is specific to the owner's unit.
        :param this_year: Whether the report should focus on the current year.
        :return: A coroutine that resolves to the generated report.
        :rtype: Awaitable
        :raises ValueError: If the report type provided is invalid.
        """
        if report_type is ReportType.PHEF:
            return await self.generate_phef_report(report_name, own_unit, this_year)
        elif report_type is ReportType.FUNCTIONAL:
            return await self.generate_functional_report(report_name, own_unit, this_year)
        elif report_type is ReportType.COMBAT:
            return await self.generate_combat_report(report_name, own_unit, this_year)
        elif report_type is ReportType.SWIMMING:
            return await self.generate_swimming_report(report_name, own_unit, this_year)
        elif report_type is ReportType.MFFT_EVAL:
            return await self.generate_mfft_eval_report(report_name, own_unit, this_year)
        else:
            raise ValueError("Invalid report type")

    @staticmethod
    def _fmt_time(sec: int | float | None) -> str:
        try:
            s = int(sec or 0)
            return f"{s // 60}:{s % 60:02d}"
        except (ValueError, TypeError):
            return "-"

    def _build_csv(
        self,
        rows: list[dict],
        report_name: str,
        file_suffix: str,
        headers: list[str],
        row_builder: Callable[[dict], list[Any]],
    ) -> str | None:
        """
        Builds a CSV file from the provided data rows, headers, and a row builder function.
        Generates a filename based on the specified report name, file suffix, and the current
        timestamp. The file is saved in the output directory. If no rows are provided, no
        file is created, and the function returns None.

        :param rows: List of dictionaries containing data to be written into the CSV file.
        :param report_name: Name of the report to be used in the file name.
        :param file_suffix: Additional suffix to append to the file name.
        :param headers: List of column headers to be written into the CSV file.
        :param row_builder: Function that takes a dictionary (row) as input and returns
            a list representing the corresponding row in the CSV.
        :return: Path to the generated CSV file or None if no rows are provided.
        """
        if not rows:
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{report_name}_{file_suffix}_{timestamp}.csv"
        out_dir = _output_dir(self._config)

        output_path = os.path.join(out_dir, file_name)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(row_builder(r))
        return output_path

    async def generate_phef_report(self, report_name: str, own_unit: bool, this_year: bool):
        """
        Generates a Performance-based Health Evaluation Framework (PHEF) report. The report
        includes two categories: passed and failed results, formatted into CSV files based
        on given parameters and dynamically built row data.

        The method calculates scores using `calculate_score` and utilizes the provided
        `row_builder` function to format data rows for CSV creation. It generates two
        separate CSV files for passed and failed results and returns their file paths.

        :param report_name: Name of the report to be generated.
        :param own_unit: Whether to filter the report data for the user's own unit.
        :param this_year: Whether to filter the report for data from the current year.
        :return: A dictionary with paths to the 'failed' and 'passed' report CSV files,
            or None in case of an error during report generation.
        """
        try:
            headers, passed, failed = await self.calculate_score(own_unit, this_year)

            def row_builder(r: dict) -> list[Any]:
                return [
                    (
                        "-"
                        if r["session_date"] is None
                        else r["session_date"].strftime("%Y-%m-%d %H:%M")
                    ),
                    r["serial"],
                    f"{r['run_score']}",
                    f"{r['side_r_score']}",
                    f"{r['side_l_score']}",
                    f"{r['total']:.1f}",
                    self._fmt_time(r["run_time_s"]),
                    self._fmt_time(r["side_r_s"]),
                    self._fmt_time(r["side_l_s"]),
                ]

            failed_path = self._build_csv(failed, report_name, "phef_failed", headers, row_builder)
            passed_path = self._build_csv(passed, report_name, "phef_passed", headers, row_builder)
            return {"failed": failed_path, "passed": passed_path}
        except (OSError, ValueError) as e:
            self._logger.error("Error generating PHEF report: %s", e)
            return None

    async def generate_functional_report(self, report_name: str, own_unit: bool, this_year: bool):
        """
        Generates a functional report based on the given parameters. The method calculates the
        functional scores for different sessions and creates separate CSV files for failed and
        passed sessions. The generated report paths for both the failed and passed sessions are
        returned in the result.

        :param report_name: The name of the report to be generated.
        :param own_unit: Indicates whether the report is specific to the user's unit.
        :param this_year: Indicates whether the report should focus on the current year.
        :return: A dictionary containing paths to the generated CSV files for both failed and
            passed sessions.
        :rtype: Dict[str, str]

        """
        failed, headers, passed = await self.calculate_functional_score(own_unit, this_year)

        def row_builder(r: dict) -> list[Any]:
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

        failed_path = self._build_csv(
            failed, report_name, "functional_failed", headers, row_builder
        )
        passed_path = self._build_csv(
            passed, report_name, "functional_passed", headers, row_builder
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_combat_report(self, report_name: str, own_unit: bool, this_year: bool):
        """
        Asynchronously generates a combat report based on given parameters and computes the
        results of passed and failed combat scores. The method processes the data, formats it
        into respective CSV files for failed and passed scores, and returns the file paths for
        these reports.

        :param report_name: The name of the combat report to be generated.
        :type report_name: str
        :param own_unit: Flag indicating whether the calculation should be limited to the
            user's own unit.
        :type own_unit: bool
        :param this_year: Flag to specify if the calculation should only consider the
            combat scores of the current year.
        :type this_year: bool
        :return: A dictionary containing paths to the generated CSV files for failed
            and passed scores.
        :rtype: dict
        """
        failed, headers, passed = await self.calculate_combat_score(own_unit, this_year)

        def row_builder(r: dict) -> list[Any]:
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

        failed_path = self._build_csv(failed, report_name, "combat_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "combat_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}

    async def generate_swimming_report(self, report_name: str, own_unit: bool, this_year: bool):
        failed, headers, passed = await self.calculate_swim_score(own_unit, this_year)

        def row_builder(r: dict) -> list[Any]:
            return [
                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                r["result"],
            ]

        failed_path = self._build_csv(failed, report_name, "swimming_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "swimming_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}

    async def generate_mfft_eval_report(self, report_name: str, own_unit: bool, this_year: bool):
        """Generate CSV pass/fail reports for the MFFT Eval test."""
        failed, headers, passed = await self.calculate_mfft_eval_score(own_unit, this_year)

        def row_builder(r: dict) -> list[Any]:
            return [
                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                r["cluster"],
                r["pull_ups"],
                r["burpees"],
                r["farmer_m"],
                r["push_ups"],
                r["drag_m"],
                r["sandbag_m"],
                self._fmt_time(r["run_s"]),
                self._fmt_time(r["swim_s"]),
                r["overall"],
                r["tier"],
                r["result"],
            ]

        failed_path = self._build_csv(failed, report_name, "mfft_eval_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "mfft_eval_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}


# if __name__ == "__main__":
#     import asyncio
#
#     asyncio.run(
#         ReportGeneratorCsv().generate_report("tstsdf", ReportType.PHEF, True, True)
#     )
#     asyncio.run(
#         ReportGeneratorCsv().generate_report("tstasd", ReportType.COMBAT, True, True)
#     )
#     asyncio.run(
#         ReportGeneratorCsv().generate_report("tstwe", ReportType.SWIMMING, True, True)
#     )
#     asyncio.run(
#         ReportGeneratorCsv().generate_report("tstf", ReportType.FUNCTIONAL, True, True)
#     )
