from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import CombatSwimmingTest, ServiceMen, TestSession
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class SwimmingController:
    """
    Encapsulates all Swimming test business logic:
    - Validation
    - DB queries and commands
    - Grid decoration and email HTML body
    """

    def __init__(
        self,
        service: ServiceTest = None,
        mil_service: MilitaryService = None,
    ) -> None:
        self._service = service if service is not None else ServiceTest()
        self.be_mil_service = mil_service if mil_service is not None else MilitaryService()

    # ----- Validation -----
    @staticmethod
    def validate_form(data: Dict[str, Any]) -> tuple[bool, Dict[str, Any] | str]:
        """
        Validates the provided form data for required and optional fields.

        This static method ensures the presence of a serial number (`serialnr`) in the
        provided dictionary. It also processes the `swim_passed` field, returning
        it as a boolean. If the serial number is not provided, the method will
        return an error message.

        :param data: The dictionary containing form data to validate.
        :type data: dict[str, Any]
        :return: A tuple containing a boolean indicating validation success and either
            the processed data or an error message string.
        :rtype: tuple[bool, dict[str, Any] | str]
        """
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."
        return True, {
            "swim_passed": bool(data.get("swim_passed", False)),
        }

    # ----- Queries -----
    async def load_sessions(self):
        """
        Asynchronously loads all test sessions for swimming fitness tests.

        This method retrieves all test sessions of type `SWIMMING` by interacting with
        the underlying service. It's intended for use cases where operations on swimming
        fitness test sessions are required.

        :return: A list of all test sessions of type `SWIMMING`.
        :rtype: list
        """
        return await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.SWIMMING)

    async def get_session_by_id(self, session_id: int) -> Optional[TestSession]:
        return await self._service.get_test_session_by_id(int(session_id))

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_swim_df(self, session_id: int) -> pd.DataFrame:
        """
        Retrieves and processes combat swimming test data for a specific session and
        organizes it into a structured DataFrame format.

        :param session_id: Session identifier for which to retrieve combat swimming test
            data. Must be an integer value.
        :return: A pandas DataFrame containing the processed combat swimming test data
            for the provided session ID. Includes the following columns:
            - "ID": The unique identifier for each test record.
            - "Serial": The serial number of the serviceman associated with the test.
            - "Name": The full name (first name and last name) of the serviceman.
            - "Result": Indicates whether the test result was "PASSED" or "FAILED".
        """
        try:
            swim_tests = await self._service.get_all_combat_swimming_test(int(session_id))
            rows = []
            for r in swim_tests or []:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if not sm:
                    continue
                rows.append(
                    {
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "Name": f"{sm.first_name} {sm.last_name}",
                        "Result": ("PASSED" if getattr(r, "swim_paased", False) else "FAILED"),
                    }
                )
            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the "Result" column in a DataFrame by decorating its values
        with colored symbols based on specific conditions. This is primarily
        used for enhancing the readability of a grid-style display. If the
        DataFrame is empty or does not contain a "Result" column, the function
        returns the DataFrame unchanged.

        :param df: The input DataFrame which may or may not contain a "Result" column.
        :type df: pd.DataFrame
        :return: A copy of the DataFrame with the "Result" column decorated,
        or the original DataFrame if no decorations are made.
        :rtype: pd.DataFrame
        """
        if df.empty:
            return df
        out = df.copy()
        if "Result" in out.columns:

            def _fmt(v: str):
                return f"🟩 {v}" if str(v).upper() == "PASSED" else f"🟥 {v}"

            out["Result"] = out["Result"].apply(_fmt)
        return out

    # ----- Commands -----
    async def add_swim(
        self,
        session_id: int,
        payload: Dict[str, Any],
        session: TestSession,
        military: ServiceMen,
    ) -> Optional[CombatSwimmingTest]:
        """
        Add a combat swimming test to a test session.

        This asynchronous method creates a `CombatSwimmingTest` instance based on the given
        parameters and adds it to the specified test session via a service function.

        :param session_id: The unique identifier for the test session.
        :param payload: A dictionary containing the details of the combat swimming test. Must
            include keys such as `serialnr` and `swim_passed`.
        :param session: The test session object to which the fitness test belongs.
        :param military: The serviceman associated with the current test session.
        :return: An optional `CombatSwimmingTest` object if the addition is successful,
            otherwise None.
        """
        st = CombatSwimmingTest()
        st.test_session_id = int(session_id)  # type: ignore[attr-defined]
        st.serial_number = payload["serialnr"]
        st.swim_paased = bool(payload["swim_passed"])
        return await self._service.add_fitness_test_to_testSession(
            int(session_id), st, session=session, military=military
        )

    async def update_swim(
        self, swim_id: int, payload: Dict[str, Any]
    ) -> Optional[CombatSwimmingTest]:
        """
        Updates a swimming test record with the given information. This method asynchronously updates
        a swim test record, utilizing the provided swim test ID and payload data. The operation integrates
        the new data into the `CombatSwimmingTest` model and sends it for updating the fitness test
        through the relevant service.

        :param swim_id: The unique identifier for the swimming test that needs to be updated.
        :param payload: A dictionary containing the data to update the swimming test with. Expected fields
            include "session_id" (the session linked to the test), "serialnr" (a serial number for the test),
            and "swim_passed" (a boolean indicating test success).
        :return: Updated `CombatSwimmingTest` object, or `None` if the update operation fails.
        """
        st = CombatSwimmingTest()
        st.id = int(swim_id)
        st.test_session_id = int(payload["session_id"])  # type: ignore[attr-defined]
        st.serial_number = payload["serialnr"]
        st.swim_paased = bool(payload["swim_passed"])
        return await self._service.update_fitness_test(int(swim_id), st)

    async def delete_swim(self, session_id: int, swim_id: int) -> bool:
        """
        Deletes a swim entry associated with a specific session ID and swim ID.

        The function interacts with the internal service layer to remove a swim entry
        from a fitness test session. The operation is asynchronous.

        :param session_id: The ID of the session containing the swim entry.
        :type session_id: int
        :param swim_id: The ID of the specific swim entry to delete from the session.
        :type swim_id: int
        :return: A boolean indicating whether the swim entry was successfully deleted.
        :rtype: bool
        """
        return await self._service.delete_fitness_test_from_test_session(
            int(session_id), int(swim_id)
        )
