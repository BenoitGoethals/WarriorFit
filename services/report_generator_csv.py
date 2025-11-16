import csv
import logging
import os
from datetime import datetime
from typing import Any, Callable, List, Optional, Generator
from data.db.db_model import PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest, TestSession
from logic.phef_calculator import PhefCalculator
from config.appliccation_config import ApplicationConfig
from core.type_fitness_test import TypeFitnessTest
from services.generator import GeneratorReport, _output_dir
from services.military_service import MilitaryService

from services.report_type import ReportType
from services.service_test import ServiceTest




class ReportGeneratorCsv(GeneratorReport):
    def __init__(self):
        super().__init__()


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
        out_dir = _output_dir()
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
        try:

            headers,passed,failed = await self.calculate_score(own_unit, this_year)

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
        except Exception as e:
            self.__logger.error(f"Error generating PHEF report: {e}")
            return None



    async def generate_functional_report(self, report_name: str,own_unit:bool,this_year:bool):
        failed, headers, passed = await self.calculate_functional_score(own_unit, this_year)

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
        failed, headers, passed = await self.calculate_combat_score(own_unit, this_year)

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
        failed, headers, passed = await self.calculate_swim_score(own_unit, this_year)

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
