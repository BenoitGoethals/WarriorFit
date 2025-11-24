import logging
import os
from abc import ABC
from typing import List
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.db.db_model import (
    TestSession,
    PhefTest,
    FunctionalTest,
    CombatTestParatrooper,
    CombatSwimmingTest,
)
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


def _output_dir() -> str:
    try:
        return ApplicationConfig().pdf_output_path
    except Exception:
        return os.getcwd()


class GeneratorReport(ABC):
    def __init__(self):
        self.be_mil_service = MilitaryService()
        self._service = ServiceTest()
        self._user_service = ServiceTest()
        self.__logger = logging.getLogger(__name__)

    async def calculate_score(self, own_unit, this_year):
        failed: List[dict] = []
        passed: List[dict] = []
        sessions: List[TestSession] = (
            await self._service.get_all_test_sessions_type_fitness_test(
                TypeFitnessTest.PHEF, this_year=this_year
            )
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(
                ApplicationConfig().own_unit
            )
        for sess in sessions or []:
            phef_tests: List[PhefTest] = await self._service.get_all_phef(sess.id)
            for test in phef_tests or []:
                if own_unit:
                    if not test.serial_number in [s.service_number for s in mils]:
                        continue
                sm = await self.be_mil_service.get_servicemen_by_serial(
                    test.serial_number, lazy=False
                )
                self.__logger.info(
                    f"PHEF test: {test.serial_number} - {sm.first_name} {sm.last_name} - {sm.age_from_birthdate()} years old"
                )
                score_r = PhefCalculator.side_bridge_result(
                    test.sideBridge_r, sm.age_from_birthdate(), sm.gender
                )
                score_l = PhefCalculator.side_bridge_result(
                    test.sideBridge_l, sm.age_from_birthdate(), sm.gender
                )
                score_run = PhefCalculator.running_result(
                    test.running_time, sm.age_from_birthdate(), sm.gender
                )
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
        return headers, passed, failed

    async def calculate_functional_score(self, own_unit, this_year):
        failed: List[dict] = []
        passed: List[dict] = []

        sessions: List[TestSession] = (
            await self._service.get_all_test_sessions_type_fitness_test(
                TypeFitnessTest.PHEF, this_year=this_year
            )
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(
                ApplicationConfig().own_unit
            )
        for sess in sessions or []:
            tests: List[FunctionalTest] = await self._service.get_all_functional_test(
                sess.id
            )
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

        headers = [
            "Session ID",
            "Date",
            "Serial",
            "Push-ups",
            "Sit-ups",
            "Pull-ups",
            "Total",
        ]
        return failed, headers, passed

    async def calculate_combat_score(self, own_unit, this_year):
        failed: List[dict] = []
        passed: List[dict] = []

        sessions: List[TestSession] = (
            await self._service.get_all_test_sessions_type_fitness_test(
                TypeFitnessTest.COMBAT, this_year=this_year
            )
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(
                ApplicationConfig().own_unit
            )
        for sess in sessions or []:
            tests: List[CombatTestParatrooper] = (
                await self._service.get_all_combat_test(sess.id)
            )
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

        headers = [
            "Session ID",
            "Date",
            "Serial",
            "Rope",
            "Obstacle",
            "Speedmars Time",
            "Result",
        ]
        return failed, headers, passed

    async def calculate_swim_score(self, own_unit, this_year):
        failed: List[dict] = []
        passed: List[dict] = []
        sessions: List[TestSession] = (
            await self._service.get_all_test_sessions_type_fitness_test(
                TypeFitnessTest.SWIMMING, this_year=this_year
            )
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(
                ApplicationConfig().own_unit
            )
        for sess in sessions or []:
            tests: List[CombatSwimmingTest] = (
                await self._service.get_all_combat_swimming_test(sess.id)
            )
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
        return failed, headers, passed
