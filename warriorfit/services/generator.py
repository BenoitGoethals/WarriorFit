import logging
import os
from abc import ABC

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FunctionalTest,
    PhefTest,
    TestSession,
)
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


def _output_dir(config: ApplicationConfig = None) -> str:
    cfg = config if config is not None else ApplicationConfig()
    path = cfg.pdf_output_path
    if path:
        return path
    else:
        return os.getcwd()


class GeneratorReport(ABC):  # noqa: B024  # base class, subclassed not instantiated
    """
    Handles the generation of various fitness test reports, including calculations of
    scores for physical fitness tests, functional tests, combat tests, and swimming tests.

    This abstract class is designed to process and report data collected from unit-specific
    or general test sessions, utilizing results from multiple test types such as PHEF, combat,
    functional training, and swimming. The implementation process involves score calculation,
    data filtering based on unit affiliation, and result categorization.

    :ivar be_mil_service: Service instance for handling military-related operations, such
        as retrieving military unit data or servicemen details.
    :type be_mil_service: MilitaryService
    """

    def __init__(
        self,
        military_service: MilitaryService = None,
        service_test: ServiceTest = None,
        config: ApplicationConfig = None,
    ):
        self.be_mil_service = (
            military_service if military_service is not None else MilitaryService()
        )
        self._service = service_test if service_test is not None else ServiceTest()
        self._user_service = self._service
        self._config = config if config is not None else ApplicationConfig()
        self._logger = logging.getLogger(__name__)

    async def calculate_score(self, own_unit, this_year):
        """
        Calculates the PHEF (Physical Fitness Efficiency) test scores for participants
        and categorizes them as passed or failed based on their total scores. The
        method retrieves test sessions, filters them based on the provided criteria,
        and computes individual scores for side bridge tests and running time using the
        PhefCalculator.

        The scoring system normalizes results to a standardized scale, where a total
        score of at least 50 constitutes passing. Results are grouped by session
        and include detailed metrics such as individual test scores, participant
        information, and session details. Headers corresponding to the results
        are also generated.

        :param own_unit: Determines if the filtering should be limited to the service
                         member's own unit.
        :type own_unit: bool
        :param this_year: The specific year for which test sessions and scores should
                          be considered.
        :type this_year: int
        :return: A tuple containing the table headers, passed participants,
                 and failed participants.
        :rtype: Tuple[List[str], List[dict], List[dict]]
        """
        failed: list[dict] = []
        passed: list[dict] = []
        sessions: list[TestSession] = await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.PHEF, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(self._config.own_unit)
        for sess in sessions or []:
            phef_tests: list[PhefTest] = await self._service.get_all_phef(sess.id)
            for test in phef_tests or []:
                if own_unit and test.serial_number not in [s.service_number for s in mils]:
                    continue
                sm = await self.be_mil_service.get_servicemen_by_serial(
                    test.serial_number or "",
                    lazy=False,
                )
                if sm is None:
                    continue
                self._logger.info(
                    f"PHEF test: {test.serial_number} - {sm.first_name} {sm.last_name} - {sm.age_from_birthdate()} years old"
                )
                score_r = PhefCalculator.side_bridge_result(
                    test.sideBridge_r,
                    sm.age_from_birthdate(),
                    sm.gender,
                )
                score_l = PhefCalculator.side_bridge_result(
                    test.sideBridge_l,
                    sm.age_from_birthdate(),
                    sm.gender,
                )
                score_run = PhefCalculator.running_result(
                    test.running_time,
                    sm.age_from_birthdate(),
                    sm.gender,
                )
                total = (score_run * (50 / 20.0)) + ((score_r + score_l) * (25 / 20.0))
                phef_passed = (score_r + score_l) >= 20 and score_run >= 10
                row = {
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(test, "serial_number", ""),
                    "run_score": score_run,
                    "run_time_s": getattr(test, "running_time", None),
                    "side_r_score": score_r,
                    "side_r_s": getattr(test, "sideBridge_r", None),
                    "side_l_score": score_l,
                    "side_l_s": getattr(test, "sideBridge_l", None),
                    "total": total,
                }
                (passed if phef_passed else failed).append(row)

        headers = [
            "Date",
            "Serial",
            "Run (pts)",
            "Run Time",
            "Side R (pts)",
            "Side R",
            "Side L (pts)",
            "Side L",
            "Total /100",
        ]
        return headers, passed, failed

    async def calculate_functional_score(self, own_unit, this_year):
        """
        Asynchronously calculates a functional score for military personnel based on
        their performance in fitness tests. The function filters test results for a
        specific year and optionally for a specific unit. It aggregates results,
        categorizing them into passed or failed based on their total score. Each
        aggregate includes detailed test data.

        :param own_unit: Whether to consider only tests belonging to a specific unit
            or include all units.
        :type own_unit: bool
        :param this_year: The year of test sessions to include.
        :type this_year: int
        :return: A tuple containing three elements: a list of failed test results,
            a list of column headers for summarized results, and a list of passed
            test results.
        :rtype: tuple
        """
        failed: list[dict] = []
        passed: list[dict] = []

        sessions: list[TestSession] = await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.PHEF, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(self._config.own_unit)
        for sess in sessions or []:
            tests: list[FunctionalTest] = await self._service.get_all_functional_test(sess.id)
            for t in tests or []:
                if own_unit and t.serial_number not in [s.service_number for s in mils]:
                    continue
                pu = getattr(t, "push_ups", 0) or 0
                su = getattr(t, "sit_ups", 0) or 0
                plu = getattr(t, "pull_ups", 0) or 0
                total = int(pu) + int(su) + int(plu)
                row = {
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "push_ups": pu,
                    "sit_ups": su,
                    "pull_ups": plu,
                    "total": total,
                }
                (passed if total >= 50 else failed).append(row)

        headers = [
            "Date",
            "Serial",
            "Push-ups",
            "Sit-ups",
            "Pull-ups",
            "Total",
        ]
        return failed, headers, passed

    async def calculate_combat_score(self, own_unit, this_year):
        """
        Asynchronously calculates the combat score for paratroopers' test results based on
        certain criteria such as passing a rope course, an obstacle course, and completing
        a running challenge within a specified time limit.

        This function retrieves and processes the results of combat tests conducted during
        test sessions in the current year (or a given year). If the `own_unit` parameter
        is specified, it filters results to include only those for individuals from a specific
        military unit.

        :param own_unit: A boolean indicating whether to filter the results for the own
            unit specified in the application configuration.
        :param this_year: An integer specifying the year for which the combat test
            results are being evaluated.
        :return: A tuple containing:
            - failed: A list of dictionaries with details of individuals who failed the combat test.
            - headers: A list of strings defining the column headers for the test results.
            - passed: A list of dictionaries with details of individuals who passed the combat test.
        """
        failed: list[dict] = []
        passed: list[dict] = []

        sessions: list[TestSession] = await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.COMBAT, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(self._config.own_unit)
        for sess in sessions or []:
            tests: list[CombatTestParatrooper] = await self._service.get_all_combat_test(sess.id)
            for t in tests or []:
                if own_unit and t.serial_number not in [s.service_number for s in mils]:
                    continue
                rope = bool(getattr(t, "rope_passed", False))
                obstacle = bool(getattr(t, "obstacle_passed", False))
                run_s = int(getattr(t, "running_time", 0) or 0)
                is_pass = rope and obstacle and run_s <= 7200
                row = {
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "rope": rope,
                    "obstacle": obstacle,
                    "run_time_s": run_s,
                    "result": "Passed" if is_pass else "Failed",
                }
                (passed if is_pass else failed).append(row)

        headers = [
            "Date",
            "Serial",
            "Rope",
            "Obstacle",
            "Speedmars Time",
            "Result",
        ]
        return failed, headers, passed

    async def calculate_swim_score(self, own_unit, this_year):
        """
        Calculates swimming scores for a set of test sessions within a specified year. It checks
        whether participants pass or fail based on their swimming test results, while optionally
        filtering participants belonging to the specified unit.

        :param own_unit: Whether to filter results to include only participants from the local unit
        :type own_unit: bool
        :param this_year: The year in which to fetch test sessions for swimming tests
        :type this_year: int

        :return: A tuple containing failed test cases, column headers, and passed test cases
        :rtype: Tuple[List[dict], List[str], List[dict]]
        """
        failed: list[dict] = []
        passed: list[dict] = []
        sessions: list[TestSession] = await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.SWIMMING, this_year=this_year
        )
        if own_unit:
            mils = await self.be_mil_service.get_all_be_mil_from_unit(self._config.own_unit)
        for sess in sessions or []:
            tests: list[CombatSwimmingTest] = await self._service.get_all_combat_swimming_test(
                sess.id
            )
            for t in tests or []:
                if own_unit and t.serial_number not in [s.service_number for s in mils]:
                    continue
                ok = bool(getattr(t, "swim_paased", False))
                row = {
                    "session_date": getattr(sess, "datetime_start", None),
                    "serial": getattr(t, "serial_number", ""),
                    "result": "Passed" if ok else "Failed",
                }
                (passed if ok else failed).append(row)

        headers = ["Date", "Serial", "Result"]
        return failed, headers, passed
