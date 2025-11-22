import logging
import os
from datetime import datetime
from typing import List, Optional, Callable, Any, Dict

import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from core.type_fitness_test import TypeFitnessTest
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

    async def generate_ind_report_current_year(self, serial_number: str):
        
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

            # Helper to filter DataFrame by Type
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




if __name__ == "__main__":
    import asyncio

    async def main():
        gem = ReportGeneratorPdf()
        #await gem.generate_run_report("run", 1)
        await gem.generate_ind_report_current_year("BE-20250001")

    #  await gem.generate_report("tstasd", ReportType.COMBAT,True,True)
    # await gem.generate_report( "tstwe", ReportType.SWIMMING,True,True)
    # await gem.generate_report( "tstf", ReportType.FUNCTIONAL,True,True)
    # await gem.generate_report( "tstsdf", ReportType.PHEF,True,True)

    asyncio.run(main())
