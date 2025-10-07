import csv
import os
from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple

from data.db.db_model import PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest
from logic.phef_calculator import PhefCalculator
from ui.services.be_mil_service import BEMILService
from ui.services.db_service import DBService
from ui.config.appliccation_config import ApplicationConfig
from core.type_fitness_test import TypeFitnessTest
from api.testsession import TestSession
from ui.services.report_type import ReportType


class ReportGeneratorCsv:
    def __init__(self):
        self.be_mil_service = BEMILService()
        self.db_service: DBService = DBService("ui/config/config.yml")

    async def generate_report(self, report_name: str, report_type: ReportType,own_unit:bool,this_year:bool):
        if report_type is ReportType.PHEF:
            return await self.generate_phef_report(report_name,own_unit,this_year)
        elif report_type is ReportType.FUNCTIONAL:
            return await self.generate_functional_report(report_name,own_unit,this_year)
        elif report_type is ReportType.COMBAT:
            return await self.generate_combat_report(report_name,own_unit,this_year)
        elif report_type is ReportType.SWIMMING:
            return await self.generate_swimming_report(report_name,own_unit,this_year)
        else:
            raise ValueError("Invalid report type")

    def _output_dir(self) -> str:
        try:
            # Prefer a dedicated CSV output path if present, else reuse pdf_output_path, else CWD
            cfg = ApplicationConfig()
            return getattr(cfg, "csv_output_path", None) or getattr(cfg, "pdf_output_path", None) or os.getcwd()
        except Exception:
            return os.getcwd()

    @staticmethod
    def _fmt_time(sec: int | float | None) -> str:
        try:
            s = int(sec or 0)
            return f"{s // 60}:{s % 60:02d}"
        except Exception:
            return "-"

    def _build_csv(
        self,
        rows: List[dict],
        report_name: str,
        file_suffix: str,
        headers: List[str],
        row_builder: Callable[[dict], List[Any]],
    ) -> Optional[str]:
        if not rows:
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{report_name}_{file_suffix}_{timestamp}.csv"
        out_dir = self._output_dir()
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, file_name)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(row_builder(r))
        print(f"CSV generated: {output_path}")
        return output_path

    async def generate_phef_report(self, report_name: str,own_unit:bool,this_year:bool):
        failed: List[dict] = []
        passed: List[dict] = []

        sessions: List[TestSession] = await self.db_service.get_all_test_sessions_type_fitnessTest(
            TypeFitnessTest.PHEF, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        for sess in sessions or []:
            phef_tests: List[PhefTest] = await self.db_service.get_all_phef(sess.id)
            for test in phef_tests or []:
                if own_unit:
                    if not test.serial_number in [s.service_number for s in mils]:
                        continue
                sm = await self.be_mil_service.get_be_mil_by_id(test.serial_number)
                score_r = PhefCalculator.side_bridge_result(test.sideBridge_r, sm.age_from_birthdate(), sm.gender)
                score_l = PhefCalculator.side_bridge_result(test.sideBridge_l, sm.age_from_birthdate(), sm.gender)
                score_run = score_l = PhefCalculator.running_result(test.pointsRunning, sm.age_from_birthdate(),
                                                                    sm.gender)
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

        headers = [
            "Session ID",
            "Date",
            "Serial",
            "Run (pts)",
            "Side R (pts)",
            "Side L (pts)",
            "Total /100",
            "Run Time",
            "Side R",
            "Side L",
        ]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
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

    async def generate_functional_report(self, report_name: str,own_unit:bool,this_year:bool):
        failed: List[dict] = []
        passed: List[dict] = []

        sessions: List[TestSession] = await self.db_service.get_all_test_sessions_type_fitnessTest(
            TypeFitnessTest.PHEF, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        for sess in sessions or []:
            tests: List[FunctionalTest] = await self.db_service.get_all_functional_test(sess.id)
            for t in tests or []:
                if own_unit:
                    if not t.serial_number in [s.service_number for s in mils]:
                        continue
                pu = getattr(t, "push_ups", 0) or 0
                su = getattr(t, "sit_ups", 0) or 0
                plu = getattr(t, "pull_ups", 0) or 0
                total = int(pu) + int(su) + int(plu)
                row = {
                    "session_id": sess.id,
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "push_ups": pu,
                    "sit_ups": su,
                    "pull_ups": plu,
                    "total": total,
                }
                (passed if total >= 50 else failed).append(row)

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

        failed_path = self._build_csv(failed, report_name, "functional_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "functional_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}

    async def generate_combat_report(self, report_name: str,own_unit:bool,this_year:bool):
        failed: List[dict] = []
        passed: List[dict] = []

        sessions: List[TestSession] = await self.db_service.get_all_test_sessions_type_fitnessTest(
            TypeFitnessTest.COMBAT, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        for sess in sessions or []:
            tests: List[CombatTestParatrooper] = await self.db_service.get_all_combat_test(sess.id)
            for t in tests or []:
                if own_unit:
                    if not t.serial_number in [s.service_number for s in mils]:
                        continue
                rope = bool(getattr(t, "rope_passed", False))
                obstacle = bool(getattr(t, "obstacle_passed", False))
                run_s = int(getattr(t, "running_time", 0) or 0)
                is_pass = rope and obstacle and run_s <= 7200
                row = {
                    "session_id": sess.id,
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "rope": rope,
                    "obstacle": obstacle,
                    "run_time_s": run_s,
                    "result": "Passed" if is_pass else "Failed",
                }
                (passed if is_pass else failed).append(row)

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

        failed_path = self._build_csv(failed, report_name, "combat_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "combat_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}

    async def generate_swimming_report(self, report_name: str,own_unit:bool,this_year:bool):
        failed: List[dict] = []
        passed: List[dict] = []
        sessions: List[TestSession] = await self.db_service.get_all_test_sessions_type_fitnessTest(
            TypeFitnessTest.SWIMMING, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        for sess in sessions or []:
            tests: List[CombatSwimmingTest] = await self.db_service.get_all_combat_swimming_test(sess.id)
            for t in tests or []:
                if own_unit:
                    if not t.serial_number in [s.service_number for s in mils]:
                        continue
                ok = bool(getattr(t, "swim_paased", False))
                row = {
                    "session_id": sess.id,
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "result": "Passed" if ok else "Failed",
                }
                (passed if ok else failed).append(row)

        headers = ["Session ID", "Date", "Serial", "Result"]

        def row_builder(r: dict) -> List[Any]:
            return [
                r["session_id"],
                "-" if r["session_date"] is None else r["session_date"].strftime("%Y-%m-%d %H:%M"),
                r["serial"],
                r["result"],
            ]

        failed_path = self._build_csv(failed, report_name, "swimming_failed", headers, row_builder)
        passed_path = self._build_csv(passed, report_name, "swimming_passed", headers, row_builder)
        return {"failed": failed_path, "passed": passed_path}

if __name__ == "__main__":
    import asyncio
    asyncio.run(ReportGeneratorCsv().generate_report( "tstsdf", ReportType.PHEF,True,True))
    asyncio.run(ReportGeneratorCsv().generate_report("tstasd", ReportType.COMBAT,True,True))
    asyncio.run(ReportGeneratorCsv().generate_report( "tstwe", ReportType.SWIMMING,True,True))
    asyncio.run(ReportGeneratorCsv().generate_report( "tstf", ReportType.FUNCTIONAL,True,True))
