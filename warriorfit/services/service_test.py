from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
from warriorfit.core.Gender import Gender
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    PhefTest,
    ServiceMen,
    TestSession,
)
from warriorfit.data.repositories.fitness_test_repository import FitnessTestRepository
from warriorfit.logic.Functional_calculator import FunctionalCalculator
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.service import Service
from warriorfit.ui.pages.notify_mail import NotifyMail


class ServiceTest(Service):
    """
    ServiceTest class for managing various fitness tests and their sessions.

    This class extends the functionalities of the Service class, providing
    methods to interact with multiple fitness test types, manage test
    sessions, handle notifications, and perform necessary CRUD operations
    on test data. It communicates with repositories for data access and
    executes business logic related to fitness testing.

    :ivar test_repo: The repository used for accessing and managing fitness
        test data.
    :type test_repo: FitnessTestRepository
    """

    def __init__(
        self,
        fitness_test_repository: FitnessTestRepository = None,
        user_repository=None,
        config=None,
        notify_mail=None,
    ):
        super().__init__(user_repository=user_repository, config=config)
        self._test_repo = (
            fitness_test_repository
            if fitness_test_repository is not None
            else FitnessTestRepository()
        )
        self._notify_mail = notify_mail

    async def get_all_combat_test(self, id):
        return await self._test_repo.get_all_combat_test(id)

    async def get_all_functional_test(self, id):
        return await self._test_repo.get_all_functional_test(id)

    async def get_all_phef(self, id):
        return await self._test_repo.get_all_phef(
            id,
        )

    async def get_all_phef_mil(self, serial) -> list[PhefTest]:
        return await self._test_repo.get_all_phef_from_mil(
            serial,
            current_year=True,
        )

    async def get_all_combat_swimming_test(self, id):
        return await self._test_repo.get_all_combat_swimming_test(id)

    async def get_all_test_sessions_type_fitness_test(self, type_test, this_year=True):
        return await self._test_repo.get_all_test_sessions_type_fitness_test(type_test, this_year)

    async def get_all_test_sessions_type_fitness_test_for_service_men(
        self, serial: str, type_test, this_year=True
    ):
        return await self._test_repo.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, type_test, this_year=this_year
        )

    async def get_all_test_sessions(self):
        return await self._test_repo.get_all_test_sessions()

    async def get_all_test_sessions_for_pti(self, serial_number_pti: str):
        return await self._test_repo.get_all_test_sessions_for_a_pti(serial_number_pti)

    async def add_fitness_test_to_testSession(
        self,
        fitness_test,
        test: FitnessTest,
        military: ServiceMen = None,
        session: TestSession = None,
    ):
        """
        Asynchronously adds a fitness test to a test session and handles specific follow-up
        actions such as sending notifications and logging audit details based on the type
        of test. Supports additional handling for various test types like PHEF, combat
        swimming, functional, and combat tests.

        :param fitness_test: A fitness test object to be added to the test session.
        :param test: An instance of FitnessTest representing the test details.
        :param military: An optional ServiceMen object representing the personnel
            associated with the test. Defaults to None.
        :param session: An optional TestSession object representing the test session
            context. Defaults to None.
        :return: Returns a boolean indicating whether the fitness test was successfully
            added to the test session.
        """
        from warriorfit.app import FitnessWarriorApp

        add_test = await self._test_repo.add_fitness_test_to_TestSession(fitness_test, test)
        body = ""
        if add_test or military.unit is None:
            match test.type:
                case "phef_test":
                    body = self.build_email_body_phef(military, session, test)

                case "combat_swimming_test":
                    body = self.build_email_body_swim(military, session, test)
                case "functional_test":
                    body = self.build_email_body_functional(military, session, test)
                case "combat_test":
                    body = self.build_email_body_combat(test)
            await FitnessWarriorApp.get_broker().send_message(test)
            if body:
                notify = self._notify_mail if self._notify_mail is not None else NotifyMail()
                await notify.send_mail(body=body, subject="Result Test", to=str(military.mail))
            await self.add_audit_log(
                details=f"Fitness test {test.serial_number} {test.type} added to test session {fitness_test}",
                action="add",
            )

        return add_test

    async def delete_fitness_test_from_test_session(self, param, param1):
        deleted = await self._test_repo.delete_fitness_test_from_test_session(param, param1)
        if deleted:
            await self.add_audit_log(
                details=f"Fitness test {param1} deleted from test session {param}",
                action="delete",
            )
        return deleted

    async def update_fitness_test(self, param, cp):
        updated = await self._test_repo.update_fitness_test(param, cp)
        from warriorfit.app import FitnessWarriorApp

        await FitnessWarriorApp.get_broker().send_message(updated)
        if updated:
            await self.add_audit_log(
                details=f"Fitness test {cp.serial_number}  {cp.type} updated in test session {param}",
                action="update",
            )
        return updated

    async def get_test_session_by_id(self, param):
        return await self._test_repo.get_test_session_by_id(param)

    async def add_test_session(self, ts):
        added_test: TestSession = await self._test_repo.add_test_session(ts)
        if added_test:
            await self.add_audit_log(
                details=f"Test session {ts.id} {added_test.type_test.name} added",
                action="add",
            )
        return added_test

    async def update_test_session(self, data):
        updated = await self._test_repo.update_test_session(data)
        if updated:
            await self.add_audit_log(
                details=f"Test session {data.id}  {updated}updated", action="update"
            )
        return updated

    async def delete_test_session(self, sel_id):
        deleted = await self._test_repo.delete_test_session(sel_id)
        if deleted:
            await self.add_audit_log(details=f"Test session {sel_id} deleted", action="delete")
        return deleted

    async def get_all_pti(self):
        return await self._test_repo.get_all_pti()

    @staticmethod
    def format_seconds(sec: float | int) -> str:
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    def build_email_body_phef(
        self, sm: ServiceMen, session: TestSession, payload: PhefTest | FitnessTest
    ) -> str:
        age = (
            sm.age_from_birthdate()
            if session is None
            else sm.age_from_birthdate_and_session_date(session.datetime_start)
        )
        run = PhefCalculator.running_result(payload.running_time, age, sm.gender)
        sbr = PhefCalculator.side_bridge_result(payload.sideBridge_r, age, sm.gender)
        sbl = PhefCalculator.side_bridge_result(payload.sideBridge_l, age, sm.gender)
        total = (run * (50 / 20.0)) + ((sbr + sbl) * (25 / 20.0))
        return f"""
            <h2>PHEF Test Results</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Service Member Information</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Service Member:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{sm.rank} {sm.service_number}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Name:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{sm.first_name} {sm.last_name}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Test Date:</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{session.datetime_start.strftime("%Y-%m-%d") if session else "-"}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Test Results</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Running (2400m)</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload.running_time)}<br>
                        Score: {run}/20
                    </td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Right</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload.sideBridge_r)}<br>
                        Score: {sbr}/20
                    </td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Left</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload.sideBridge_l)}<br>
                        Score: {sbl}/20
                    </td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">Total Score</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">{total:.1f}/100</th>
                </tr>
            </table>
        """

    @staticmethod
    def build_email_body_swim(
        sm: ServiceMen, session: TestSession, payload: CombatSwimmingTest | FitnessTest
    ) -> str:
        passed = payload.swim_paased
        result = "PASSED" if passed else "FAILED"
        color = "green" if passed else "red"
        return f"""
            <h2>Swimming Test Result</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Service Member</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Identity</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{sm.rank} {sm.service_number} - {sm.first_name} {sm.last_name}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Test Date</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{session.datetime_start.strftime("%Y-%m-%d")}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Result</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Status</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {color}; font-weight: bold;">{result}</td>
                </tr>
            </table>
        """

    def build_email_body_functional(
        self, sm: ServiceMen, session: TestSession, test: FunctionalTest | FitnessTest
    ) -> str:
        def normalize_gender(g: Gender | str) -> Gender:
            if isinstance(g, str):
                return Gender.M if g.lower().startswith("m") else Gender.F
            return g

        gender = normalize_gender(sm.gender)
        age = sm.age_from_birthdate()
        push_score = FunctionalCalculator.get_score_pushup(gender, age, test.push_ups)
        sit_score = FunctionalCalculator.get_score_situp(gender, age, test.sit_ups)
        pull_score = FunctionalCalculator.get_score_pullup(gender, age, test.pull_ups)
        total_pct = ((push_score + sit_score + pull_score) / 60) * 100
        return f"""
              Dear {sm.rank} {sm.first_name} {sm.last_name},
              <br><br>
              Your functional test results from {session.datetime_start.strftime("%Y-%m-%d")} are:
              <br><br>
              <table border="1" cellpadding="5" style="border-collapse: collapse;">
                  <tr>
                      <th>Exercise</th>
                      <th>Repetitions</th>
                      <th>Score</th>
                  </tr>
                  <tr>
                      <td>Push-ups</td>
                      <td>{test.push_ups}</td>
                      <td>{push_score}</td>
                  </tr>
                  <tr>
                      <td>Sit-ups</td>
                      <td>{test.sit_ups}</td>
                      <td>{sit_score}</td>
                  </tr>
                  <tr>
                      <td>Pull-ups</td>
                      <td>{test.pull_ups}</td>
                      <td>{pull_score}</td>
                  </tr>
                  <tr>
                      <td colspan="2"><strong>Total Score</strong></td>
                      <td><strong>{total_pct:.2f}%</strong></td>
                  </tr>
              </table>
              <br><br>
              Best regards,<br>
              Fitness Test System
              """

    def build_email_body_combat(self, test: CombatTestParatrooper | FitnessTest) -> str:
        return f"""
           <table border="1" style="border-collapse: collapse; width: 100%;">
               <thead>
                   <tr style="background-color: #f2f2f2;">
                       <th style="padding: 8px; text-align: left;">Test Component</th>
                       <th style="padding: 8px; text-align: left;">Result</th>
                       <th style="padding: 8px; text-align: left;">Status</th>
                   </tr>
               </thead>
               <tbody>
                   <tr>
                       <td style="padding: 8px;">Obstacle Course</td>
                       <td style="padding: 8px;">{str(test.obstacle_passed)}</td>
                       <td style="padding: 8px; color: {"green" if test.obstacle_passed else "red"}">
                           {"PASSED" if test.obstacle_passed else "FAILED"}
                       </td>
                   </tr>
                   <tr>
                       <td style="padding: 8px;">Rope Course</td>
                       <td style="padding: 8px;">{str(test.rope_passed)}</td>
                       <td style="padding: 8px; color: {"green" if test.rope_passed else "red"}">
                           {"PASSED" if test.rope_passed else "FAILED"}
                       </td>
                   </tr>
                   <tr>
                       <td style="padding: 8px;">Speed March</td>
                       <td style="padding: 8px;">{self.format_seconds(test.running_time)}</td>
                       <td style="padding: 8px; color: {"green" if test.running_time <= 2400 else "red"}">
                           {"PASSED" if test.running_time <= 2400 else "FAILED"}
                       </td>
                   </tr>
                   <tr>
                       <td style="padding: 8px; font-weight: bold;">Overall Result</td>
                       <td style="padding: 8px;"></td>
                       <td style="padding: 8px; color: {"green" if (test.obstacle_passed and test.rope_passed and test.running_time <= 2400) else "red"}; font-weight: bold">
                           {"PASSED" if (test.obstacle_passed and test.rope_passed and test.running_time <= 2400) else "FAILED"}
                       </td>
                   </tr>
               </tbody>
           </table>
           """

    async def get_all_combat_test_mil(self, service_number):
        return await self._test_repo.get_all_combat_from_mil(
            service_number,
            current_year=True,
        )

    async def get_all_combat_test_swim(self, service_number):
        return await self._test_repo.get_all_swim_from_mil(
            service_number,
            current_year=True,
        )

    async def get_upcoming_session_for_pti(self, serial_number_pti):
        return await self._test_repo.get_upcoming_session_for_pti(serial_number_pti)
