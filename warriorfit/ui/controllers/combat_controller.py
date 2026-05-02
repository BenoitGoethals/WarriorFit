from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import (
    CombatTestParatrooper,
    ServiceMen,
    TestSession,
)
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class CombatController:
    """
    Represents a controller for managing combat fitness tests.
    """

    def __init__(
        self,
        service: ServiceTest = None,
        mil_service: MilitaryService = None,
    ) -> None:
        self._service = service if service is not None else ServiceTest()
        self.be_mil_service = (
            mil_service if mil_service is not None else MilitaryService()
        )
        self._logger = logging.getLogger(__name__)

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> Tuple[bool, int | str]:
        """
        Accepts:
          - "mm:ss"  (minutes + seconds)  -> returns total seconds (int)
          - "ss"     (numeric seconds)    -> returns total seconds (int)

        Validation:
          - must be > 0
          - must be <= 120 minutes total (<= 7200 seconds)
          - if mm:ss: seconds part must be 0..59
        """
        txt = (val or "").strip()
        if not txt:
            return False, "Time value is required."

        MAX_SECONDS = 120 * 60  # 120 minutes

        try:
            if ":" in txt:
                parts = txt.split(":")
                if len(parts) != 2:
                    return False, "Time must be in mm:ss or seconds."

                m = int(parts[0])  # total minutes
                s = int(parts[1])  # seconds (0..59)

                if m < 0:
                    return False, "Minutes must be >= 0."
                if s < 0 or s >= 60:
                    return False, "Seconds must be between 0 and 59."

                total_seconds = m * 60 + s
            else:
                # numeric input is interpreted as total seconds
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
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    @staticmethod
    def overall_passed(
        obstacle_passed: bool, rope_passed: bool, running_time_s: int
    ) -> bool:
        return obstacle_passed and rope_passed and running_time_s <= 7200

    async def load_sessions(self):
        """
        Asynchronously loads all test sessions of type "COMBAT".

        This method fetches all test sessions for which the type is classified as
        `TypeFitnessTest.COMBAT`. The data is retrieved using the `_service` object's
        `get_all_test_sessions_type_fitness_test` method.

        :return: A coroutine that resolves to the list of test sessions.
        :rtype: listfTime must be <=
        """
        return await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.COMBAT
        )

    async def search_military(self, serial_nr: str) -> Optional[ServiceMen]:
        """
        Asynchronously searches for a serviceman using a provided serial number.

        The method takes a serial number and searches for the corresponding
        serviceman record. If the serial number is empty or invalid, it
        returns None. Otherwise, it queries the relevant service to
        retrieve the serviceman details.

        :param serial_nr: The serial number of the serviceman to be searched.
        :type serial_nr: str
        :return: An instance of ServiceMen if a serviceman is found;
            None otherwise.
        :rtype: Optional[ServiceMen]
        """
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_combat_tests_df(self, session_id: int) -> pd.DataFrame:
        """
        Generates a pandas DataFrame containing details about combat tests for a given session ID. It fetches data
        from the combat test service, performs additional processing such as calculating total scores,
        formatting results, and filtering servicemen records.

        :param session_id: The unique identifier for the session being queried.
        :type session_id: int
        :return: A pandas DataFrame containing combat test results with fields like ID, serial number, running
                 time, and overall scores. If an error occurs during data processing, an empty DataFrame
                 is returned.
        :rtype: pd.DataFrame
        """
        try:
            combat_tests = await self._service.get_all_combat_test(int(session_id))
            data = []
            for r in combat_tests:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    continue
                total = self.overall_passed(
                    r.obstacle_passed, r.rope_passed, r.running_time
                )
                data.append(
                    {
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "speedmarsTime": self.format_seconds(r.running_time),
                        "Speedmars Score": f"{r.running_time <= 7200}",
                        "ObstacleCourse": "Passed" if r.obstacle_passed else "Failed",
                        "RobeCourse": "Passed" if r.rope_passed else "Failed",
                        "Totale Score": "Passed" if total else "Failed",
                    }
                )
            return pd.DataFrame(data)
        except (ValueError, TypeError, AttributeError) as e:
            self._logger.error("Error in list_combat_tests_df: %s", e)
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        """
        Decorates the grid DataFrame by modifying specific column values. This static method
        checks if the DataFrame contains a "Totale Score" column. If the column exists, the
        method applies a transformation to the values in this column, prefixing them with
        colored indicators (green or red) based on the content ("passed" or other). Returns
        the modified DataFrame or the original DataFrame if it is empty.

        :param df: Input pandas DataFrame that may be modified.
        :type df: pd.DataFrame
        :return: A new pandas DataFrame with updated column values if applicable. If the
            input DataFrame is empty, it returns the same empty DataFrame.
        :rtype: pd.DataFrame
        """
        if df.empty:
            return df
        df2 = df.copy()
        if "Totale Score" in df2.columns:
            df2["Totale Score"] = df2["Totale Score"].apply(
                lambda v: f"🟩 {v}" if str(v).lower() == "passed" else f"🟥 {v}"
            )
        return df2

    # ----- Commands -----
    async def add_combat(
        self,
        session_id: int,
        payload: Dict[str, Any],
        session: TestSession,
        military: ServiceMen,
    ) -> Optional[CombatTestParatrooper]:
        """
        Adds a combat test to a specific test session and returns the created combat test
        paratrooper instance.

        This method initializes a `CombatTestParatrooper` object with the information from
        the provided payload and associates the test with the given session and servicemen.

        The combat test parameters such as session ID, serial number, running time, rope test
        status, and obstacle test status are set based on the input payload.

        :param session_id: The unique identifier of the test session to which the combat
                           test will be added.
        :param payload: A dictionary containing the combat test parameters such as
                        serial number, combat running time, rope test status,
                        and obstacle test status.
        :param session: An instance of `TestSession` that represents the test session.
        :param military: An instance of `ServiceMen` representing the servicemen
                         participating in the combat test.
        :return: An instance of `CombatTestParatrooper` representing the newly created
                 combat test, or `None`.
        """
        cp = CombatTestParatrooper()
        cp.test_session_id = int(session_id)  # type: ignore[attr-defined]
        cp.serial_number = payload["serialnr"]
        cp.running_time = payload["combat_speedmars"]
        cp.rope_passed = payload["combat_robe"]
        cp.obstacle_passed = payload["combat_obstacle"]
        return await self._service.add_fitness_test_to_testSession(
            int(session_id), cp, session=session, military=military
        )

    async def update_combat(
        self, combat_id: int, payload: Dict[str, Any]
    ) -> Optional[CombatTestParatrooper]:
        """
        Updates a combat test record with the provided data.

        This asynchronous method updates the combat test details of a specific combat
        test ID based on the given payload. It creates an instance of
        CombatTestParatrooper, sets its attributes with the data from the payload,
        and passes the object to the service for updating the fitness test.

        :param combat_id: The ID of the combat test to be updated.
        :type combat_id: int
        :param payload: A dictionary containing the update data for the combat test.
        :type payload: Dict[str, Any]
        :return: The updated CombatTestParatrooper object or None if the update fails.
        :rtype: Optional[CombatTestParatrooper]
        """
        cp = CombatTestParatrooper()
        cp.id = combat_id
        cp.test_session_id = int(payload["session_id"])  # type: ignore[attr-defined]
        cp.serial_number = payload["serialnr"]
        cp.running_time = payload["combat_speedmars"]
        cp.obstacle_passed = payload["combat_obstacle"]
        cp.rope_passed = payload["combat_robe"]
        return await self._service.update_fitness_test(int(combat_id), cp)

    async def delete_combat(self, session_id: int, combat_id: int) -> bool:
        """
        Deletes a combat from a session using the provided session ID and combat ID.
        This function interacts with an underlying service to perform the deletion.

        :param session_id: Unique identifier for the session
        :param combat_id: Unique identifier for the combat to be deleted
        :return: A boolean indicating whether the deletion was successful
        """
        return await self._service.delete_fitness_test_from_test_session(
            int(session_id), int(combat_id)
        )

    async def get_test_session_by_id(self, param):
        """
        Retrieves a test session by its ID using the associated service.

        :param param: The id of the test session to retrieve.
        :return: An object representing the test session corresponding to the provided
            ID.
        """
        return await self._service.get_test_session_by_id(param)

    def validate_form(dself, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        """
        Validates combat form data and normalizes it for storage.

        Required:
          - serialnr (non-empty)
          - combat_speedmars (mm:ss or seconds)

        Returns:
          - (True, normalized_dict) on success
          - (False, error_message) on failure
        """
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."

        _, run_seconds = CombatController.parse_time_to_seconds(
            (data.get("combat_speedmars") or "").strip()
        )
        if not run_seconds:
            return False, f"combat_speedmars: {run_seconds}"

        return True, {
            "serialnr": serial,
            "combat_speedmars": int(run_seconds),  # total seconds
            "combat_obstacle": bool(data.get("combat_obstacle")),
            "combat_robe": bool(data.get("combat_robe")),
        }
