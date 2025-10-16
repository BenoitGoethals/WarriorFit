import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional, Callable, Any
from logic.phef_calculator import PhefCalculator
from config.appliccation_config import ApplicationConfig
from services.be_mil_service import BEMILService

from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import TestSession, PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest
from services.report_type import ReportType
from services.service_cross import ServiceCross
from services.service_test import ServiceTest


class ReportGeneratorPdf:

    def __init__(self):
        self._user_service=ServiceTest()
        self._cross_service=ServiceCross()
        self.be_mil_service=BEMILService()
        self.__logger = logging.getLogger(__name__)

    async def generate_report(self,  report_name: str, report_type: ReportType,own_unit:bool,this_year:bool):
        if report_type is ReportType.PHEF:
            print(f"Generating PHEF report for {report_name}")
            return await self.generate_phef_report(report_name,own_unit,this_year)
        elif report_type is ReportType.FUNCTIONAL:
            return await self.generate_functional_report(report_name,own_unit,this_year)
        elif report_type is ReportType.COMBAT:
            return await self.generate_combat_report(report_name,own_unit,this_year)
        elif report_type is ReportType.SWIMMING:
            return await self.generate_swimming_report(report_name,own_unit,this_year)
        else:
            raise ValueError("Invalid report type")
    
    async def generate_run_report(self,report_name:str,cross:int):
        result = await self._cross_service.get_cross_by_id(cross,lazy=False)

        if not result or not result.runners:
            return None

        headers = ["order","Serial Number", "Name", "Running Time","Age","Unit"]

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
            runner_det = await self.be_mil_service.get_be_mil_by_id(runner.serial_number)
            if runner_det:
                rows.append({
                    "order": None,
                    "serial_number": runner.serial_number or "",
                    "Name": runner_det.first_name + " " + runner_det.last_name or "",
                    "running_time": runner.running_time,
                    "Age": runner_det.age_from_birthdate() or "",
                    "Unit": runner_det.unit or "",
                })
        rows = sorted(rows, key=lambda r: (r.get("running_time") is None, r.get("running_time") or float("inf")))
        for idx, r in enumerate(rows, start=1):
            r["order"] = idx
            
                
        

        return self._build_pdf(
            rows,
            report_name,
            f"Cross Report - {result.datetime_start.strftime("%Y-%m-%d %H:%M:%S")}  {len(rows)} runners",
            "cross_runners",
            headers,
            row_builder
        )

    def _output_dir(self) -> str:
        """
        Centralized resolver for PDF output directory.
        """
        try:
            return ApplicationConfig().pdf_output_path
        except Exception:
            return os.getcwd()

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
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
            raise RuntimeError("reportlab is required to generate PDF. Install it with 'uv add reportlab'.") from e

    def _build_pdf(self, rows: List[dict], report_name: str, title: str, file_suffix: str,
                   headers: List[str], row_builder: Callable[[dict], List[Any]]) -> Optional[str]:
        if not rows:
            return None
        deps = self._ensure_pdf_deps()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{report_name}_{file_suffix}_{timestamp}.pdf"
        out_dir = self._output_dir()

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
        self.__logger.info(f"Generating PDF: {output_path}")
        return output_path

    async def generate_phef_report(self, report_name: str,own_unit:bool,this_year:bool):
        """
        Generate PDFs for PHEF:
        - All FAILED tests (<50 total)
        - All PASSED tests (>=50 total)
        Returns dict with 'failed' and 'passed' -> file paths (or None if not created).
        """

        async def _collect_rows(own_unit:bool,this_year:bool) -> tuple[List[dict], List[dict]]:
            failed: List[dict] = []
            passed: List[dict] = []
            sessions: List[TestSession] = await self._user_service.get_all_test_sessions_type_fitnessTest(
                TypeFitnessTest.PHEF,this_year=this_year
            )
            if own_unit:
                mils=await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
            for sess in sessions or []:
                phef_tests: List[PhefTest] = await self._user_service.get_all_phef(sess.id)
                for test in phef_tests or []:
                    if own_unit:
                        if not test.serial_number in [s.service_number for s in mils]:
                            continue

                    sm=await self.be_mil_service.get_be_mil_by_id(test.serial_number)
                    score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, sm.age_from_birthdate(), sm.gender)
                    score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, sm.age_from_birthdate(), sm.gender)
                    score_run =  score_l = PhefCalculator.running_result(test.pointsRunning, sm.age_from_birthdate(), sm.gender)
                    total = (score_run * (50 / 20.0)) + ((score_r + score_l) * (25 / 20.0))
                    row = {
                        "session_id": sess.id,
                        "session_date": getattr(sess, "datetime_start", None),
                        "serial": getattr(test, "serial_number", ""),
                        "run_score": score_run,
                        "side_r_score": score_r,
                        "side_l_score": score_l,
                        "total": total,
                        "run_time_s": getattr(test, "running_time", None),
                        "side_r_s": getattr(test, "sideBridge_r", None),
                        "side_l_s": getattr(test, "sideBridge_l", None),
                    }
                    (passed if total >= 50 else failed).append(row)
            return failed, passed

        failed_rows, passed_rows = await _collect_rows(own_unit,this_year)

        headers = [
            "Session ID",
            "Date",
            "Serial",
            "Run Time",
            "Run (pts)",
            "Side R",
            "Side R (pts)",
            "Side L",
            "Side L (pts)",
            "Total /100",
        ]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
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
            failed_rows, report_name, f"PHEF Failed Tests Report ({len(failed_rows)} records)", "phef_failed",
            headers, row_builder
        )
        passed_path = self._build_pdf(
            passed_rows, report_name, f"PHEF Passed Tests Report ({len(passed_rows)} records)", "phef_passed",
            headers, row_builder
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_functional_report(self, report_name: str,own_unit:bool,this_year:bool):

        async def _collect_rows(own_unit:bool,this_year:bool) -> Tuple[List[dict], List[dict]]:
            try:
                failed, passed = [], []
                sessions: List[TestSession] = await self._user_service.get_all_test_sessions_type_fitnessTest(
                    TypeFitnessTest.PHEF, this_year=this_year
                )
                if own_unit:
                    mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
                for sess in sessions or []:
                    tests: List[FunctionalTest] = await self._user_service.get_all_functional_test(sess.id)
                    for test in tests or []:
                        if own_unit:
                            if not test.serial_number in [s.service_number for s in mils]:
                                continue
                        pu = getattr(test, "push_ups", 0) or 0
                        su = getattr(test, "sit_ups", 0) or 0
                        plu = getattr(test, "pull_ups", 0) or 0
                        total = int(pu) + int(su) + int(plu)
                        row = {
                            "session_id": sess.id,
                            "session_date": getattr(sess, "datetime_start", None),
                            "serial": getattr(test, "serial_number", ""),
                            "push_ups": pu,
                            "sit_ups": su,
                            "pull_ups": plu,
                            "total": total,
                        }
                        (passed if total >= 50 else failed).append(row)
                return failed, passed
            except Exception as e:
                self.__logger.error(f"Error collecting functional tests: {e}")
                return [], []

        failed, passed = await _collect_rows(own_unit,this_year)

        headers = ["Session ID", "Date", "Serial", "Push-ups", "Sit-ups", "Pull-ups", "Total"]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
                r["serial"],
                r["push_ups"],
                r["sit_ups"],
                r["pull_ups"],
                r["total"],
            ]

        failed_path = self._build_pdf(
            failed, report_name, f"Functional Failed Tests ({len(failed)} records)", "functional_failed",
            headers, row_builder
        )
        passed_path = self._build_pdf(
            passed, report_name, f"Functional Passed Tests ({len(passed)} records)", "functional_passed",
            headers, row_builder
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_combat_report(self, report_name: str, own_unit:bool,this_year:bool):
        """
        Generate PDFs for Combat tests:
        - Failed (any requirement not met)
        - Passed (rope + obstacle passed and running_time <= 7200)
        """

        async def _collect_rows(own_unit:bool,this_year:bool) -> Tuple[List[dict], List[dict]]:
            failed, passed = [], []
            sessions: List[TestSession] = await self._user_service.get_all_test_sessions_type_fitnessTest(
                TypeFitnessTest.COMBAT, this_year=this_year
            )
            if own_unit:
                mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
            for sess in sessions or []:
                tests: List[CombatTestParatrooper] = await self._user_service.get_all_combat_test(sess.id)
                for test in tests or []:
                    if own_unit:
                        if not test.serial_number in [s.service_number for s in mils]:
                            continue
                    rope = bool(getattr(test, "rope_passed", False))
                    obstacle = bool(getattr(test, "obstacle_passed", False))
                    run_s = int(getattr(test, "running_time", 0) or 0)
                    is_pass = rope and obstacle and run_s <= 7200
                    row = {
                        "session_id": sess.id,
                        "session_date": getattr(sess, "datetime_start", None),
                        "serial": getattr(test, "serial_number", ""),
                        "rope": rope,
                        "obstacle": obstacle,
                        "run_time_s": run_s,
                        "result": "Passed" if is_pass else "Failed",
                    }
                    (passed if is_pass else failed).append(row)
            return failed, passed

        failed, passed = await _collect_rows(own_unit,this_year)

        headers = ["Session ID", "Date", "Serial", "Rope", "Obstacle", "Speedmars Time", "Result"]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
                r["serial"],
                "Passed" if r["rope"] else "Failed",
                "Passed" if r["obstacle"] else "Failed",
                self._fmt_time(r["run_time_s"]),
                r["result"],
            ]

        failed_path = self._build_pdf(
            failed, report_name, f"Combat Failed Tests ({len(failed)} records)", "combat_failed",
            headers, row_builder
        )
        passed_path = self._build_pdf(
            passed, report_name, f"Combat Passed Tests ({len(passed)} records)", "combat_passed",
            headers, row_builder
        )
        return {"failed": failed_path, "passed": passed_path}

    async def generate_swimming_report(self, report_name: str,own_unit:bool,this_year:bool):


        async def _collect_rows(own_unit:bool,this_year:bool) -> Tuple[List[dict], List[dict]]:
            failed, passed = [], []
            sessions: List[TestSession] = await self._user_service.get_all_test_sessions_type_fitnessTest(
                TypeFitnessTest.SWIMMING, this_year=this_year
            )
            if own_unit:
                mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
            for sess in sessions or []:
                tests: List[CombatSwimmingTest] = await self._user_service.get_all_combat_swimming_test(sess.id)
                for test in tests or []:
                    if own_unit:
                        if not test.serial_number in [s.service_number for s in mils]:
                            continue
                    ok = bool(getattr(test, "swim_paased", False))
                    row = {
                        "session_id": sess.id,
                        "session_date": getattr(sess, "datetime_start", None),
                        "serial": getattr(test, "serial_number", ""),
                        "result": "Passed" if ok else "Failed",
                    }
                    (passed if ok else failed).append(row)
            return failed, passed

        failed, passed = await _collect_rows(own_unit,this_year)

        headers = ["Session ID", "Date", "Serial", "Result"]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
                r["serial"],
                r["result"],
            ]

        failed_path = self._build_pdf(
            failed, report_name, f"Swimming Failed Tests ({len(failed)} records)", "swimming_failed",
            headers, row_builder
        )
        passed_path = self._build_pdf(
            passed, report_name, f"Swimming Passed Tests ({len(passed)} records)", "swimming_passed",
            headers, row_builder
        )
        return {"failed": failed_path, "passed": passed_path}


if __name__ == "__main__":
    import asyncio

    async def main():
        gem = ReportGeneratorPdf()
        await gem.generate_run_report("run",1)
      #  await gem.generate_report("tstasd", ReportType.COMBAT,True,True)
       # await gem.generate_report( "tstwe", ReportType.SWIMMING,True,True)
       # await gem.generate_report( "tstf", ReportType.FUNCTIONAL,True,True)
       # await gem.generate_report( "tstsdf", ReportType.PHEF,True,True)

    asyncio.run(main())
