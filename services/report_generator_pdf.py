import logging
import os
from datetime import datetime
from typing import List, Optional, Callable, Any

from services.data_collector import DataCollector
from services.generator import GeneratorReport, _output_dir
from services.report_type import ReportType
from services.service_cross import ServiceCross


class ReportGeneratorPdf(GeneratorReport):
    def __init__(self):
        super().__init__()
        self._cross_service = ServiceCross()
        self._logger = logging.getLogger(__name__)

    async def generate_report(
        self, report_name: str, report_type: ReportType, own_unit: bool, this_year: bool
    ):
        if report_type is ReportType.PHEF:
            print(f"Generating PHEF report for {report_name}")
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
        try:
            s = int(sec or 0)
            return f"{s // 60}:{s % 60:02d}"
        except Exception:
            return "-"

    @staticmethod
    def _ensure_pdf_deps():
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
        Generate PDFs for PHEF:
        - All FAILED tests (<50 total)
        - All PASSED tests (>=50 total)
        Returns dict with 'failed' and 'passed' -> file paths (or None if not created).
        """

        headers, passed, failed = await self.calculate_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
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
        failed, headers, passed = await self.calculate_functional_score(
            own_unit, this_year
        )

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
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
        Generate PDFs for Combat tests:
        - Failed (any requirement not met)
        - Passed (rope + obstacle passed and running_time <= 7200)
        """

        failed, headers, passed = await self.calculate_combat_score(own_unit, this_year)

        headers = [
            "Session ID",
            "Date",
            "Serial",
            "Rope",
            "Obstacle",
            "Speedmars Time",
            "Result",
        ]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
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

        failed, headers, passed = await self.calculate_swim_score(own_unit, this_year)

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
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

    async def generate_ind_report_current_year(self,serial_number:str):
        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                (
                    "-"
                    if r["session_date"] is None
                    else r["session_date"].strftime("%Y-%m-%d %H:%M")
                ),
                r["serial"],
                r["run_time_s"],
                f"{r['run_score']}",
            ]

        headers=["Session ID","Date","Serial","Running Time","Score"]
        collector=DataCollector()
        current_year=datetime.now().year
        data=await collector.collect_tests_for_serial(serial_number)
        data=list(filter(lambda x:x["year"]==current_year,data))
        self._build_pdf(data,f"{serial_number}","Year report",f"Year_report_{serial_number}",headers,row_builder)



if __name__ == "__main__":
    import asyncio

    async def main():
        gem = ReportGeneratorPdf()
        await gem.generate_run_report("run", 1)

    #  await gem.generate_report("tstasd", ReportType.COMBAT,True,True)
    # await gem.generate_report( "tstwe", ReportType.SWIMMING,True,True)
    # await gem.generate_report( "tstf", ReportType.FUNCTIONAL,True,True)
    # await gem.generate_report( "tstsdf", ReportType.PHEF,True,True)

    asyncio.run(main())
