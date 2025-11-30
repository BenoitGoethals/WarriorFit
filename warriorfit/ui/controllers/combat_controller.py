from __future__ import annotations

import logging
from typing import Tuple, Dict, Any, Optional
import pandas as pd
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.db.db_model import CombatTestParatrooper, TestSession, ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest

class CombatController:
    """
    Represents a controller for managing combat fitness tests.

    This class provides functionality for parsing and formatting time values, validating
    form data, and performing CRUD operations related to combat fitness tests. It also
    facilitates interaction with test sessions, military service, and generates data for
    grid representation of combat tests.

    :ivar be_mil_service: Instance of the MilitaryService class used for managing
        servicemen-related operations.
    :type be_mil_service: MilitaryService
    """
    def __init__(self) -> None:
        self._service = ServiceTest()
        self.be_mil_service =MilitaryService()
        self._logger=logging.getLogger(__name__)

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> Tuple[bool, int | str]:
        """
        Parses a provided time string into total seconds.

        This method takes in a time string formatted as either "mm:ss" or a single
        value representing the total seconds. It validates the input to ensure it
        meets the appropriate format and returns a tuple indicating success or failure
        along with a corresponding value or error message.

        :param val: The time string to parse. It should be in the format "mm:ss" or
            a numeric string representing total seconds.
        :type val: str
        :return: A tuple where the first element is a boolean indicating success or
            failure, and the second element is either an integer representing total
            seconds (if successful) or a string containing an error message.
        :rtype: Tuple[bool, int | str]
        """
        txt = (val or "").strip()
        if not txt:
            return False, "Time value is required."
        try:
            if ":" in txt:
                parts = txt.split(":")
                if len(parts) != 2:
                    return False, "Time must be in mm:ss or seconds."
                m = int(parts[0])
                s = int(parts[1])
                total = m * 60 + s
            else:
                total = int(float(txt))
            if total <= 0:
                return False, "Time must be positive."
            return True, int(total)
        except Exception:
            return False, "Time must be numeric (mm:ss or seconds)."

    @staticmethod
    def format_seconds(sec: float | int) -> str:
        """
        Converts a given time in seconds into a formatted string in the "MM:SS" format.

        The static method takes an input number representing seconds, which can be an
        integer or float, and returns a string formatted as minutes and seconds, with
        leading zeros for single-digit seconds.

        :param sec: Time in seconds to be converted.
        :type sec: float | int
        :return: A string representing the time in the "MM:SS" format.
        :rtype: str
        """
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    @staticmethod
    def overall_passed(obstacle_passed: bool, rope_passed: bool, running_time_s: int) -> bool:
        """
        Determines if a participant successfully passes all requirements in a challenge.

        :param obstacle_passed: Indicates if the obstacle course was passed successfully.
        :type obstacle_passed: bool
        :param rope_passed: Indicates if the rope course was passed successfully.
        :type rope_passed: bool
        :param running_time_s: The running time of the participant in seconds, used to
            verify if they completed the challenge within the given limit.
        :type running_time_s: int
        :return: A boolean value that represents whether the participant successfully
            completed the challenge requirements, including both courses and the
            time constraint.
        :rtype: bool
        """
        return obstacle_passed and rope_passed and running_time_s <= 7200

    @staticmethod
    def validate_form(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        """
        Validates form data based on predefined rules and parses specific field values.

        :param data: Contains form values to validate. The dictionary is expected to have
            the following keys:
            - serialnr: str, representing the serial number. This field is mandatory.
            - combat_speedmars: str, representing speed mars value. It should be parseable
              to seconds.
            - combat_obstacle: Any, representing obstacle data. It will be converted to a
              boolean.
            - combat_robe: Any, representing robe data. It will be converted to a boolean.
        :return: A tuple where the first element is a boolean indicating if the validation
            passed or failed, and the second element is a detailed dictionary of the parsed
            data if validation passes, or an error message string if validation fails.
        """
        if not (data.get("serialnr") or "").strip():
            return False, "Serial number is required."
        ok_run, run = CombatController.parse_time_to_seconds(data.get("combat_speedmars") or "")
        if not ok_run:
            return False, f"combat_speedmars: {run}"
        return True, {
            "combat_speedmars": run,
            "combat_obstacle": bool(data.get("combat_obstacle")),
            "combat_robe": bool(data.get("combat_robe")),
        }

   
    async def load_sessions(self):
        """
        Asynchronously loads all test sessions of type "COMBAT".

        This method fetches all test sessions for which the type is classified as
        `TypeFitnessTest.COMBAT`. The data is retrieved using the `_service` object's
        `get_all_test_sessions_type_fitness_test` method.

        :return: A coroutine that resolves to the list of test sessions.
        :rtype: list
        """
        return await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.COMBAT)

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
                total = self.overall_passed(r.obstacle_passed, r.rope_passed, r.running_time)
                data.append({
                    "ID": r.id,
                    "Serial": r.serial_number,
                    "speedmarsTime": self.format_seconds(r.running_time),
                    "Speedmars Score": f"{r.running_time <= 7200}",
                    "ObstacleCourse": "Passed" if r.obstacle_passed else "Failed",
                    "RobeCourse": "Passed" if r.rope_passed else "Failed",
                    "Totale Score": "Passed" if total else "Failed",
                })
            return pd.DataFrame(data)
        except (ValueError, TypeError) as e:
            self._logger.error(f"Error in list_combat_tests_df: {e}")
            return pd.DataFrame()
        except AttributeError as e:
            self._logger.error(f"Error in list_combat_tests_df: {e}")
            return pd.DataFrame()
        except Exception as e:
           self._logger.error(f"Error in list_combat_tests_df: {e}")
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
    async def add_combat(self, session_id: int, payload: Dict[str, Any],session:TestSession,military:ServiceMen) -> Optional[CombatTestParatrooper]:
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
        cp.test_session_id = int(session_id)
        cp.serial_number = payload["serialnr"]
        cp.running_time = payload["combat_speedmars"]
        cp.rope_passed = payload["combat_robe"]
        cp.obstacle_passed = payload["combat_obstacle"]
        return await self._service.add_fitness_test_to_testSession(int(session_id), cp,session=session,military=military)

    async def update_combat(self, combat_id: int, payload: Dict[str, Any]) -> Optional[CombatTestParatrooper]:
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
        cp.test_session_id = int(payload["session_id"])
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
        return await self._service.delete_fitness_test_from_test_session(int(session_id), int(combat_id))

  
    async def get_test_session_by_id(self, param):
        """
        Retrieves a test session by its ID using the associated service.

        :param param: The id of the test session to retrieve.
        :return: An object representing the test session corresponding to the provided
            ID.
        """
        return await self._service.get_test_session_by_id(param)
