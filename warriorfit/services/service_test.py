from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
from warriorfit.core.Gender import Gender
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    MfftEvalTest,
    PhefTest,
    ServiceMen,
    TestSession,
)
from warriorfit.data.repositories.fitness_test_repository import FitnessTestRepository
from warriorfit.logic.Functional_calculator import FunctionalCalculator
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.notify_mail import NotifyMail
from warriorfit.services.service import Service


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

    @staticmethod
    def _assert_can_modify_tests() -> None:
        """Defense-in-depth: verify the current session user holds a role
        permitted to mutate fitness test data. The page-level RBAC already
        hides the relevant UI, but server-side reactive inputs can still be
        invoked by anyone with a session, so we re-check here.

        Raises PermissionError when no privileged user is present.
        """
        from warriorfit.core.role import Role
        from warriorfit.ui.user_store import UserStore

        privileged = {Role.ADMIN, Role.PTI, Role.APTI}
        user = UserStore.get_user()
        role = getattr(user, "role", None)
        if role not in privileged:
            raise PermissionError("Current user is not authorized to modify fitness tests")

    async def get_all_combat_test(self, id):
        """
        Retrieves all combat test data associated with the given identifier.

        This asynchronous method interacts with the test repository to fetch all the
        combat test information corresponding to the provided ``id``.

        :param id: The unique identifier for fetching combat test data.
        :type id: Any
        :return: A collection of combat test data corresponding to the given ``id``.
        :rtype: Any
        """
        return await self._test_repo.get_all_combat_test(id)

    async def get_all_mfft_eval(self, id):
        return await self._test_repo.get_all_mfft_eval(id)

    async def get_all_mfft_eval_mil(self, service_number) -> list[MfftEvalTest]:
        """
        Retrieve all MFFT evaluation tests for the given service number from the current year.

        This method interacts with the test repository to fetch all Military Fitness Test
        (MFFT) evaluations for the specified service number, filtered to include only those
        from the current year.

        :param service_number: The unique identifier representing the service member's record.
        :type service_number: str
        :return: A list of MfftEvalTest instances for the provided service number.
        :rtype: list[MfftEvalTest]
        """
        return await self._test_repo.get_all_mfft_eval_from_mil(
            service_number,
            current_year=True,
        )

    async def get_all_functional_test(self, id):
        """
        Fetches all functional tests associated with a specific identifier.

        This asynchronous method interacts with the repository to retrieve
        all relevant functional tests. It is used to access detailed
        test information for a given ID.

        :param id: The identifier for which to retrieve functional tests.
        :type id: int
        :return: A list of functional tests associated with the given ID.
        :rtype: list
        """
        return await self._test_repo.get_all_functional_test(id)

    async def get_all_phef(self, id):
        """
        Retrieves all PHEF records associated with the provided `id`.

        This asynchronous method interacts with the underlying repository to
        fetch data and returns the result of the query.

        :param id: The unique identifier used to fetch the corresponding
            PHEF records.
        :type id: Any
        :return: A coroutine that resolves to the list of PHEF records
            associated with the provided `id`.
        :rtype: Coroutine[Any, Any, List]
        """
        return await self._test_repo.get_all_phef(
            id,
        )

    async def get_all_phef_mil(self, serial) -> list[PhefTest]:
        """
        Fetches all PHEF test records filtered by the given serial number and the
        current year.

        :param serial: The serial number used to retrieve PHEF test records.
        :type serial: str
        :return: A list of PhefTest instances matching the provided serial number
                 and current year filter.
        :rtype: list[PhefTest]
        """
        return await self._test_repo.get_all_phef_from_mil(
            serial,
            current_year=True,
        )

    async def get_all_combat_swimming_test(self, id):
        """
        Fetches all combat swimming test data for a given identifier.

        This method retrieves information about all combat swimming tests associated
        with the specified identifier by utilizing the repository layer.

        :param id: Unique identifier to query combat swimming test data.
        :type id: int
        :return: List of combat swimming test records associated with the given identifier.
        :rtype: list
        """
        return await self._test_repo.get_all_combat_swimming_test(id)

    async def get_all_test_sessions_type_fitness_test(self, type_test, this_year=True):
        """
        Retrieve all test sessions for a specific type of fitness test.

        This asynchronous method interacts with the repository to fetch all test
        sessions matching the provided test type. By default, it will only consider
        test sessions from the current year unless specified otherwise.

        :param type_test: The type of fitness test to filter the sessions.
        :param this_year: Whether to restrict the sessions to the current year.
            Defaults to True.
        :type this_year: bool
        :return: A list of test sessions matching the specified type, potentially
            filtered by year.
        :rtype: Any
        """
        return await self._test_repo.get_all_test_sessions_type_fitness_test(type_test, this_year)

    async def get_all_test_sessions_type_fitness_test_for_service_men(
        self, serial: str, type_test, this_year=True
    ):
        """
        Fetches all test sessions of a specific fitness test type for service members.

        This asynchronous method retrieves all test sessions of a specific type related
        to fitness tests for a given service member identified by their serial number.
        By default, it focuses on sessions occurring in the current year, unless
        otherwise specified.

        :param serial: A string representing the serial number of the service member.
        :param type_test: The type of fitness test to filter the sessions by.
        :param this_year: A boolean indicating whether to filter sessions only for the
            current year. Defaults to True.
        :return: A list of test sessions matching the specified criteria.
        """
        return await self._test_repo.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, type_test, this_year=this_year
        )

    async def get_all_test_sessions(self):
        """
        Retrieves all test sessions from the test repository.

        This method asynchronously interacts with the test repository to fetch all
        available test session data.

        :return: A list containing all test sessions retrieved from the repository.
        :rtype: list
        """
        return await self._test_repo.get_all_test_sessions()

    async def get_all_test_sessions_for_pti(self, serial_number_pti: str):
        """
        Retrieve all test sessions associated with a given PTI (Product or Testing Identifier).

        This asynchronous function interacts with a test repository to fetch all test sessions
        linked to the provided PTI. It returns the results as retrieved from the repository.

        :param serial_number_pti: The serial number or unique identifier for the specific PTI
                                  whose test sessions are to be retrieved.
        :type serial_number_pti: str
        :return: A collection of test sessions associated with the specified PTI.
        :rtype: Any
        """
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
        from warriorfit.core.container import Container

        add_test = await self._test_repo.add_fitness_test_to_TestSession(fitness_test, test)
        body = ""
        if add_test or military is None or military.unit is None:
            match test.type:
                case "phef_test":
                    body = self.build_email_body_phef(military, session, test)  # type: ignore[arg-type]

                case "combat_swimming_test":
                    body = self.build_email_body_swim(military, session, test)  # type: ignore[arg-type]
                case "functional_test":
                    body = self.build_email_body_functional(military, session, test)  # type: ignore[arg-type]
                case "combat_test":
                    body = self.build_email_body_combat(test)
                case "mfft_eval_test":
                    body = self.build_email_body_mfft_eval(military, session, test)  # type: ignore[arg-type]
            await Container().broker().send_message(test)
            if body:
                notify = self._notify_mail if self._notify_mail is not None else NotifyMail()
                await notify.send_mail(
                    body=body,
                    subject="Result Test",
                    to=str(military.mail if military else ""),
                )
            await self.add_audit_log(
                details=f"Fitness test {test.serial_number} {test.type} added to test session {fitness_test}",
                action="add",
            )

        return add_test

    async def delete_fitness_test_from_test_session(self, param, param1):
        """
        Deletes a fitness test from a specific test session. This operation removes the
        fitness test association with the given test session and logs the action into
        the audit log if the deletion is successful.

        :param param: The identifier of the test session from which the fitness test
                      should be deleted.
        :param param1: The identifier of the fitness test to be deleted.
        :return: A boolean indicating whether the deletion was successful.
        """
        self._assert_can_modify_tests()
        deleted = await self._test_repo.delete_fitness_test_from_test_session(param, param1)
        if deleted:
            await self.add_audit_log(
                details=f"Fitness test {param1} deleted from test session {param}",
                action="delete",
            )
        return deleted

    async def update_fitness_test(self, param, cp):
        """
        Updates a fitness test within the test repository and logs the update if
        successful. This operation also sends a message to the broker when the
        update is completed.

        :param param: The identifier representing the test session during which
            the fitness test is being updated.
        :type param: Any
        :param cp: The object containing the fitness test data to be updated,
            including its serial number and type.
        :type cp: Any
        :return: A boolean indicating whether the fitness test update was
            successful.
        :rtype: bool
        """
        updated = await self._test_repo.update_fitness_test(param, cp)
        from warriorfit.core.container import Container

        if updated:
            await Container().broker().send_message(updated)
            await self.add_audit_log(
                details=f"Fitness test {cp.serial_number}  {cp.type} updated in test session {param}",
                action="update",
            )
        return updated

    async def get_test_session_by_id(self, param):
        """
        Asynchronously retrieves a test session by its unique identifier.

        This method interacts with the repository layer to fetch a test session.
        The test session is fetched based on the identifier provided as input.

        :param param: Unique identifier of the test session.
        :type param: Any
        :return: The fetched test session corresponding to the provided identifier.
        :rtype: Any
        """
        return await self._test_repo.get_test_session_by_id(param)

    async def add_test_session(self, ts):
        """
        Adds a new test session and logs the action.

        This method adds a test session to the repository and creates an
        audit log entry specifying the details of the action. The added
        test session is then returned.

        :param ts: The test session to add.
        :type ts: TestSession
        :return: The added test session if successful.
        :rtype: TestSession
        """
        added_test: TestSession = await self._test_repo.add_test_session(ts)  # type: ignore[assignment]
        if added_test:
            await self.add_audit_log(
                details=f"Test session {ts.id} {added_test.type_test.name} added",
                action="add",
            )
        return added_test

    async def update_test_session(self, data):
        """
        Updates a test session with the provided data and logs the operation in the audit log
        if the update is successful.

        :param data: The data object containing information about the test session to update.
        :type data: Any
        :return: Indicates whether the update operation was successful.
        :rtype: bool
        """
        updated = await self._test_repo.update_test_session(data)
        if updated:
            await self.add_audit_log(
                details=f"Test session {data.id}  {updated}updated", action="update"
            )
        return updated

    async def delete_test_session(self, sel_id):
        """
        Deletes a test session with the specified identifier from the repository. If the session
        is successfully deleted, an audit log entry is added to record the action.

        :param sel_id: Identifier of the test session to delete.
        :type sel_id: int
        :return: A boolean value indicating whether the test session was successfully deleted.
        :rtype: bool
        """
        deleted = await self._test_repo.delete_test_session(sel_id)
        if deleted:
            await self.add_audit_log(details=f"Test session {sel_id} deleted", action="delete")
        return deleted

    async def get_all_pti(self):
        """
        Retrieve all PTI (Presumably Test Information) records asynchronously.

        This method interacts with the test repository to fetch the complete list
        of PTI records. It is designed to handle asynchronous operations and
        returns the results as awaited.

        :return: All PTI records retrieved from the repository.
        :rtype: Any
        """
        return await self._test_repo.get_all_pti()

    @staticmethod
    def format_seconds(sec: float | int) -> str:
        """
        Converts a time duration in seconds to a formatted string representation.

        The method takes in a duration in seconds and converts it into a
        formatted string in the format 'MM:SS'. This can be particularly
        useful for representing durations in media playback or timers.

        :param sec: A duration in seconds. Can be an integer or a floating-point
            value.
        :type sec: float | int
        :return: A formatted string representing the duration in 'MM:SS'
            format. Minutes and seconds are calculated from the given input,
            and seconds are always represented as a zero-padded two-digit
            number.
        :rtype: str
        """
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    def build_email_body_phef(
        self, sm: ServiceMen, session: TestSession, payload: PhefTest | FitnessTest
    ) -> str:
        """
        Builds the email body for a Physical Health Evaluation Framework (PHEF) test.
        This method processes the test payload, calculates individual and total scores
        based on the service member's age, gender, and test performance. It then returns
        a formatted HTML string displaying the test results and service member details.

        :param sm: Service member's information including rank, age, and personal details
        :type sm: ServiceMen
        :param session: Test session details including the test date and time
        :type session: TestSession
        :param payload: Test performance details specific to the PHEF test
        :type payload: PhefTest | FitnessTest
        :return: An HTML string representing the formatted email body with test results
        :rtype: str
        """
        assert isinstance(payload, PhefTest)
        age = (
            sm.age_from_birthdate()
            if session is None
            else sm.age_from_birthdate_and_session_date(session.datetime_start)
        )
        run = PhefCalculator.running_result(payload.running_time, age, sm.gender)
        sbr = PhefCalculator.side_bridge_result(payload.sideBridge_r, age, sm.gender)
        sbl = PhefCalculator.side_bridge_result(payload.sideBridge_l, age, sm.gender)
        total = (run * (50 / 20.0)) + ((sbr + sbl) * (25 / 20.0))
        test_date = str(session.datetime_start)[:10] if session else "-"
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{test_date}</td>
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
        """
        Builds the email body for a swimming test result. This method is specifically designed to process
        instances of `CombatSwimmingTest` to determine the outcome of the test and generate an HTML email
        body summarizing the result, the service member's details, and the key statistics of the test.

        :param sm: The service member who participated in the test.
        :type sm: ServiceMen
        :param session: The session during which the swimming test was conducted.
        :type session: TestSession
        :param payload: The swimming test data containing the performance results. Must be an instance of
            `CombatSwimmingTest`.
        :type payload: CombatSwimmingTest | FitnessTest
        :return: String formatted as an HTML table summarizing the swimming test results.
        :rtype: str
        """
        assert isinstance(payload, CombatSwimmingTest)
        passed = payload.swim_paased
        test_date = str(session.datetime_start)[:10]
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{test_date}</td>
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
        """
        Builds an email body containing functional test results in an HTML format.

        This method formats and summarizes the functional test performance of a service member
        based on the number of repetitions completed in push-ups, sit-ups, and pull-ups. The
        results are calculated using specific scoring logic for each exercise, normalized by
        the service member's age and gender.

        :param sm: The service member whose results will be summarized.
        :type sm: ServiceMen
        :param session: The test session information, including date and time.
        :type session: TestSession
        :param test: The functional or fitness test containing data on push-ups, sit-ups,
            and pull-ups. Must be of type `FunctionalTest`.
        :type test: FunctionalTest | FitnessTest
        :return: A formatted HTML string containing the summarized test results, scores,
            and overall performance percentage.
        :rtype: str
        """
        assert isinstance(test, FunctionalTest)
        test_date = str(session.datetime_start)[:10]

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
              Your functional test results from {test_date} are:
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
        """
        Generates an HTML table representation of the combat test results for a candidate.

        This function takes a test object which contains the results of various components
        of a combat test and creates an HTML-formatted string. The table includes test
        component descriptions, results, and pass/fail statuses for each component as well
        as an overall outcome indicator.

        :param test: The test object containing results for each component of the combat test.
                     Must be an instance of `CombatTestParatrooper` or `FitnessTest`.
        :type test: CombatTestParatrooper | FitnessTest
        :return: An HTML string formatted as a table displaying test results and their statuses.
        :rtype: str
        """
        assert isinstance(test, CombatTestParatrooper)
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
                       <td style="padding: 8px;">{test.obstacle_passed!s}</td>
                       <td style="padding: 8px; color: {"green" if test.obstacle_passed else "red"}">
                           {"PASSED" if test.obstacle_passed else "FAILED"}
                       </td>
                   </tr>
                   <tr>
                       <td style="padding: 8px;">Rope Course</td>
                       <td style="padding: 8px;">{test.rope_passed!s}</td>
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

    def build_email_body_mfft_eval(
        self,
        sm: ServiceMen,
        session: TestSession,
        test: MfftEvalTest | FitnessTest,
    ) -> str:
        """
        Build an HTML-based email body for displaying the evaluation results of an MFFT evaluation test.

        This function processes a fitness test result, calculates the performance metrics, determines the
        pass/fail status based on predefined tiers, and generates a detailed HTML report summarizing the
        test results.

        :param sm: A `ServiceMen` object representing the service member who took the test.
        :param session: A `TestSession` object indicating the test session details, including the test date.
            If no session is provided, the test date will be replaced with a default placeholder.
        :param test: An `MfftEvalTest` object (or `FitnessTest` inheriting from it) containing test input data,
            such as performance in events like pull-ups, push-ups, and other exercises.
        :return: A formatted HTML string summarizing the MFFT evaluation test results.
        :rtype: str
        """
        assert isinstance(test, MfftEvalTest)
        from warriorfit.logic.mfft_eval_calculator import MfftEvalCalculator

        age = (
            sm.age_from_birthdate()
            if session is None
            else sm.age_from_birthdate_and_session_date(session.datetime_start)
        )
        res = MfftEvalCalculator.evaluate(test, sm.cluster, age, sm.gender)
        test_date = str(session.datetime_start)[:10] if session else "-"
        per = res.per_event
        passed_word = "PASSED" if res.passed else "FAILED"
        passed_color = "green" if res.passed else "red"
        return f"""
            <h2>MFFT Eval Test Results</h2>
            <p><strong>{sm.rank} {sm.service_number}</strong> -
               {sm.first_name} {sm.last_name} ({sm.cluster}, age {age})<br>
               Test date: {test_date}</p>
            <table border="1" style="border-collapse: collapse;" cellpadding="5">
              <tr><th>Event</th><th>Result</th><th>Tier</th></tr>
              <tr><td>1. Pull-up</td><td>{test.pull_ups} reps</td><td>{per[0]}</td></tr>
              <tr><td>2. Burpees step-over</td><td>{test.burpees_step_over} reps</td><td>{per[1]}</td></tr>
              <tr><td>3. Farmer walk</td><td>{test.farmer_walk_m} m</td><td>{per[2]}</td></tr>
              <tr><td>4. Push-up & release</td><td>{test.push_ups_release} reps</td><td>{per[3]}</td></tr>
              <tr><td>5. Casualty drag</td><td>{test.casualty_drag_m} m</td><td>{per[4]}</td></tr>
              <tr><td>6. Sandbag carry</td><td>{test.sandbag_carry_m} m</td><td>{per[5]}</td></tr>
              <tr><td>7. Combat run (4800 m)</td><td>{self.format_seconds(test.combat_run_seconds)}</td><td>{per[6]}</td></tr>
              <tr><td>8. Combat swim (200 m)</td><td>{self.format_seconds(test.combat_swim_seconds)}</td><td>{per[7]}</td></tr>
              <tr><th>Overall</th>
                  <th style="color: {passed_color};">{passed_word}</th>
                  <th>{res.overall} (tier info: {res.tier_info})</th></tr>
            </table>
        """

    async def get_all_combat_test_mil(self, service_number):
        """
        Retrieve all combat test data for the specified military service number
        from the current year.

        This method interacts with the test repository to fetch data filtered by
        the provided service number and restricts the results to the current year.

        :param service_number: The unique identifier for a military service.
        :type service_number: str
        :return: A collection of combat test data associated with the given
            service number for the current year.
        :rtype: Any
        """
        return await self._test_repo.get_all_combat_from_mil(
            service_number,
            current_year=True,
        )

    async def get_all_combat_test_swim(self, service_number):
        """
        Fetches all combat test swim records for a specific service number from the
        current year.

        This asynchronous method retrieves data related to all combat test swim
        records associated with the provided service number. The data is fetched
        from the repository that interfaces with the military records database.

        :param service_number: The service number of the individual whose combat
            test swim records are being requested.
        :type service_number: str

        :return: A list of combat test swim records for the specified service number
            from the current year.
        :rtype: list
        """
        return await self._test_repo.get_all_swim_from_mil(
            service_number,
            current_year=True,
        )

    async def get_upcoming_session_for_pti(self, serial_number_pti):
        """
        Fetch the upcoming session details for a specified PTI.

        This asynchronous method retrieves upcoming session details associated with
        the provided PTI serial number. It interacts with the internal test repository
        to perform this operation. The returned data contains relevant session
        information associated with the specified PTI serial number.

        :param serial_number_pti: Serial number of the PTI for which the upcoming
            session details are to be fetched.
        :type serial_number_pti: str
        :return: A dictionary or data object containing details of the upcoming session
            for the given PTI.
        :rtype: Any
        """
        return await self._test_repo.get_upcoming_session_for_pti(serial_number_pti)
