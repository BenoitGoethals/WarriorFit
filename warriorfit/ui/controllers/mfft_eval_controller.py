from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from warriorfit.core.cluster import Cluster
from warriorfit.core.mfft_level import MfftLevel
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import MfftEvalTest, ServiceMen, TestSession
from warriorfit.logic.mfft_eval_calculator import MfftEvalCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class MfftEvalController:
    """
    Controller responsible for handling operations related to the MFFT (Military Functional Fitness Test) evaluations.

    This class provides methods to manage MFFT sessions, parse and validate related data,
    and interact with the associated services to retrieve and process data for military personnel.
    Use this controller to load, add, update, or delete evaluations, generate summaries, and ensure
    data integrity when processing MFFT-related operations.

    :ivar EVENT_LABELS: A tuple of event labels representing the key components of the MFFT evaluation.
    :type EVENT_LABELS: tuple[str, ...]
    :ivar be_mil_service: A service interface for interacting with military personnel data.
    :type be_mil_service: MilitaryService
    """

    EVENT_LABELS: tuple[str, ...] = (
        "Pull-up",
        "Burpees step-over",
        "Farmer walk (m)",
        "Push-up & release",
        "Casualty drag (m)",
        "Sandbag carry (m)",
        "Combat run",
        "Combat swim",
    )

    def __init__(
        self,
        service: ServiceTest | None = None,
        mil_service: MilitaryService | None = None,
    ) -> None:
        self._service = service if service is not None else ServiceTest()
        self.be_mil_service = mil_service if mil_service is not None else MilitaryService()
        self._logger = logging.getLogger(__name__)

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> tuple[bool, int | str]:
        """
        Parses a time string and converts it into total seconds.

        The method takes a time string in the "mm:ss" format or as a numeric value
        represented as a string indicating total seconds. It validates the input,
        checking for proper formatting, and returns the time in seconds if properly
        formatted. Otherwise, it returns an error message detailing the issue.

        :param val: The time input as a string, either in "mm:ss" format or numeric
            seconds. The value should represent a positive time within an acceptable
            maximum limit.
        :type val: str
        :return: A tuple where the first element is a boolean indicating whether the
            parsing was successful, and the second element is either an error message
            (in case of failed parsing) or the total number of seconds as an integer
            (when parsing is successful).
        :rtype: tuple[bool, int | str]
        """
        txt = (val or "").strip()
        if not txt:
            return False, "Time value is required."
        MAX_SECONDS = 120 * 60
        try:
            if ":" in txt:
                parts = txt.split(":")
                if len(parts) != 2:
                    return False, "Time must be in mm:ss or seconds."
                m = int(parts[0])
                s = int(parts[1])
                if m < 0:
                    return False, "Minutes must be >= 0."
                if s < 0 or s >= 60:
                    return False, "Seconds must be between 0 and 59."
                total_seconds = m * 60 + s
            else:
                total_seconds = int(float(txt))
            if total_seconds <= 0:
                return False, "Time must be positive."
            if total_seconds > MAX_SECONDS:
                return False, total_seconds
            return True, int(total_seconds)
        except (ValueError, TypeError):
            return False, "Time must be numeric (mm:ss or seconds)."

    @staticmethod
    def format_seconds(sec: float | int) -> str:
        """
        Formats a given time in seconds to a human-readable string in the format `MM:SS`.

        :param sec: The time duration in seconds, which can be provided as a float or integer.
        :return: A string representing the time duration in the format `MM:SS`.
        """
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    @staticmethod
    def _parse_int(val: str | int | None, *, field: str) -> tuple[bool, int | str]:
        """
        Parses a value to determine if it can be converted to a positive integer. If the parsing
        fails or the value is invalid, appropriate error messages are returned.

        :param val: The input value to be parsed, which could be of type str, int, or None.
        :param field: The name of the field associated with the value for error messaging.
        :return: A tuple where the first element is a boolean indicating success (True if the
                 value is a valid positive integer, False otherwise), and the second element
                 is either the parsed integer on success or an error message string on failure.
        """
        if val is None or (isinstance(val, str) and not val.strip()):
            return False, f"{field} is required."
        try:
            n = int(float(str(val)))
        except (ValueError, TypeError):
            return False, f"{field} must be a positive integer."
        if n <= 0:
            return False, f"{field} must be greater than 0."
        return True, n

    async def load_sessions(self):
        """
        Loads all test sessions of type "MFFT_EVAL" from the service.

        The method asynchronously retrieves and returns test sessions of a specific type.
        It employs the service's `get_all_test_sessions_type_fitness_test` method to perform
        the operation.

        :return: A list of test sessions retrieved from the service.
        :rtype: list
        """
        return await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.MFFT_EVAL
        )

    async def search_military(self, serial_nr: str) -> ServiceMen | None:
        """
        Searches for a serviceman in the military database by the provided serial number.

        This method performs a lookup in the military service for a serviceman whose serial
        number matches the provided one. If no valid serial number is given, it returns None.

        :param serial_nr: The unique serial number of the serviceman to search.
        :type serial_nr: str
        :return: The serviceman object if found, otherwise None.
        :rtype: ServiceMen | None
        """
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_mfft_tests_df(self, session_id: int) -> pd.DataFrame:
        """
        Asynchronously retrieves a DataFrame containing detailed MFFT (Military Functional Fitness Test)
        evaluation results for a specified session ID. The results include information about individual
        tests, performed calculations, and servicemen details.

        :param session_id: The unique identifier of the session whose MFFT test results are to be
            retrieved.
        :type session_id: int
        :return: A pandas DataFrame containing the aggregated MFFT test data, including calculations
            and evaluations, or an empty DataFrame if an error occurs.
        :rtype: pd.DataFrame
        """
        try:
            tests = await self._service.get_all_mfft_eval(int(session_id))
            data = []
            for r in tests:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    continue
                age = sm.age_from_birthdate()
                res = MfftEvalCalculator.evaluate(r, sm.cluster, age, sm.gender)
                data.append(
                    {
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "Cluster": str(sm.cluster),
                        "PullUps": r.pull_ups,
                        "Burpees": r.burpees_step_over,
                        "FarmerM": r.farmer_walk_m,
                        "PushUps": r.push_ups_release,
                        "DragM": r.casualty_drag_m,
                        "SandbagM": r.sandbag_carry_m,
                        "Run": self.format_seconds(r.combat_run_seconds),
                        "Swim": self.format_seconds(r.combat_swim_seconds),
                        "Overall": str(res.overall),
                        "Tier": str(res.tier_info),
                        "Result": "Passed" if res.passed else "Failed",
                    }
                )
            return pd.DataFrame(data)
        except (ValueError, TypeError, AttributeError) as e:
            self._logger.error("Error in list_mfft_tests_df: %s", e)
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df2 = df.copy()
        if "Result" in df2.columns:
            df2["Result"] = df2["Result"].apply(
                lambda v: f"🟩 {v}" if str(v).lower() == "passed" else f"🟥 {v}"
            )
        return df2

    @staticmethod
    def _tier_color(level: MfftLevel) -> str:
        return {
            MfftLevel.GOLD: "#d4af37",
            MfftLevel.SILVER: "#bdbdbd",
            MfftLevel.BRONZE: "#cd7f32",
            MfftLevel.FIT: "green",
            MfftLevel.UNFIT: "red",
        }.get(level, "black")

    # ----- Commands -----
    async def add_mfft(
        self,
        session_id: int,
        payload: dict[str, Any],
        session: TestSession,
        military: ServiceMen,
    ) -> MfftEvalTest | None:
        """
        Adds an MFFT (Military Functional Fitness Test) evaluation record to a test session.

        This method accepts data related to an MFFT and associates it with a specific
        test session and serviceman. After constructing the MFFT evaluation record from
        provided data, it invokes a service method to store the data.

        :param session_id: ID of the test session where the MFFT should be added.
        :type session_id: int
        :param payload: Dictionary containing performance metrics for the MFFT evaluation.
        :type payload: dict[str, Any]
        :param session: The current test session being processed.
        :type session: TestSession
        :param military: An object representing the serviceman associated with the test.
        :type military: ServiceMen
        :return: An instance of `MfftEvalTest` if successfully added, or `None` otherwise.
        :rtype: MfftEvalTest | None
        """
        test = MfftEvalTest()
        test.test_session_id = int(session_id)  # type: ignore[attr-defined]
        test.serial_number = payload["serialnr"]
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return await self._service.add_fitness_test_to_testSession(
            int(session_id), test, session=session, military=military
        )

    async def update_mfft(self, mfft_id: int, payload: dict[str, Any]) -> bool:
        """
        Asynchronously updates an MFFT (Military Functional Fitness Test) record with the provided
        data and returns the updated test entity if successful.

        The function accepts an MFFT ID and a payload containing the relevant fitness metrics
        to update. The payload is expected to include specific fields with integer values.

        :param mfft_id: The unique identifier for the MFFT test to be updated.
        :type mfft_id: int
        :param payload: A dictionary containing the fitness metrics to update. Required keys
            in the payload include:
            - session_id: The identification number of the test session.
            - serialnr: Serial number associated with the test.
            - pull_ups: Number of pull-ups performed.
            - burpees: Number of burpees completed.
            - farmer_m: Distance covered (in meters) during the farmer walk.
            - push_ups: Number of push-ups (with release) completed.
            - drag_m: Distance covered (in meters) during the casualty drag.
            - sandbag_m: Distance covered (in meters) during the sandbag carry.
            - run_seconds: Time taken (in seconds) to complete a combat run.
            - swim_seconds: Time taken (in seconds) to complete a combat swim.
        :type payload: dict[str, Any]
        :return: An updated `MfftEvalTest` object representing the fitness test record
            if the update is successful, or `None` if the update fails.
        :rtype: MfftEvalTest | None
        """
        test = MfftEvalTest()
        test.id = mfft_id
        test.test_session_id = int(payload["session_id"])  # type: ignore[attr-defined]
        test.serial_number = payload["serialnr"]
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return await self._service.update_fitness_test(int(mfft_id), test)

    async def delete_mfft(self, session_id: int, mfft_id: int) -> bool:
        """
        Deletes a fitness test from a test session.

        This method interacts with the underlying service layer to remove a fitness
        test associated with a specific session and test ID. It returns a boolean
        value indicating if the deletion was successful.

        :param session_id: The unique identifier for the test session.
        :param mfft_id: The unique identifier for the fitness test to be deleted.
        :return: A boolean indicating whether the fitness test was successfully
            deleted.
        """
        return await self._service.delete_fitness_test_from_test_session(
            int(session_id), int(mfft_id)
        )

    async def get_test_session_by_id(self, param):
        """
        Asynchronously retrieves a test session by its identifier.

        This method interacts with the underlying service layer to fetch details
        associated with the given test session identifier.

        :param param: The unique identifier of the test session to be retrieved.
        :return: The details of the test session as returned by the service.
        :rtype: Any
        """
        return await self._service.get_test_session_by_id(param)

    def validate_form(self, data: dict[str, Any]) -> tuple[bool, dict[str, Any] | str]:
        """
        Validate a form by ensuring required fields are present and correctly formatted,
        normalizing the data, and returning the validation results.

        :param data: A dictionary containing the form data to validate. Expected keys include
            "serialnr", "pull_ups", "burpees", "farmer_m", "push_ups", "drag_m", "sandbag_m",
            "combat_run", and "combat_swim". Missing or improperly formatted keys will result
            in validation failure.
        :type data: dict[str, Any]

        :return: A tuple indicating whether the form is valid (True or False), and either a
            dictionary of normalized and validated data or an error message string.
        :rtype: tuple[bool, dict[str, Any] | str]
        """
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."

        int_fields = (
            ("pull_ups", "Pull-ups"),
            ("burpees", "Burpees"),
            ("farmer_m", "Farmer walk meters"),
            ("push_ups", "Push-ups"),
            ("drag_m", "Casualty drag meters"),
            ("sandbag_m", "Sandbag carry meters"),
        )
        normalized: dict[str, Any] = {"serialnr": serial}
        for key, label in int_fields:
            ok, val = self._parse_int(data.get(key), field=label)
            if not ok:
                return False, str(val)
            normalized[key] = val

        ok_run, run_val = self.parse_time_to_seconds(str(data.get("combat_run") or ""))
        if not ok_run:
            return False, f"Combat run: {run_val}"
        ok_swim, swim_val = self.parse_time_to_seconds(str(data.get("combat_swim") or ""))
        if not ok_swim:
            return False, f"Combat swim: {swim_val}"

        normalized["run_seconds"] = int(run_val)
        normalized["swim_seconds"] = int(swim_val)
        return True, normalized

    def evaluate_payload(self, payload: dict[str, Any], cluster: Cluster, age: int, gender: Any):
        """
        Evaluates the physical performance data encapsulated in the payload and calculates
        results using the provided cluster, age, and gender inputs.

        The function processes performance metrics such as pull-ups, burpees, farmer walk
        distance, push-ups, casualty drag distance, sandbag carry distance, combat run time,
        and combat swim time. These values are used to perform an evaluation through the
        `MfftEvalCalculator` utility.

        :param payload: A dictionary containing performance metric values for evaluation.
                        It is expected to have keys: "pull_ups", "burpees", "farmer_m",
                        "push_ups", "drag_m", "sandbag_m", "run_seconds", and
                        "swim_seconds".
        :type payload: dict[str, Any]
        :param cluster: The cluster identifier used for contextual grouping during evaluation.
        :type cluster: Cluster
        :param age: The age of the individual whose performance is being evaluated.
        :type age: int
        :param gender: The gender of the individual whose performance is being evaluated.
        :return: Evaluation results after processing the provided data.
        """
        test = MfftEvalTest()
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return MfftEvalCalculator.evaluate(test, cluster, age, gender)
