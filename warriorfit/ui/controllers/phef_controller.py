from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import PhefTest, ServiceMen, TestSession
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class PhefController:
    """
    Encapsulates all PHEF business logic:
    - Validation and parsing
    - DB queries and commands
    - Grid decoration and email HTML body
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

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> Tuple[bool, int | str]:
        """
        Parses a time value provided as a string and converts it into seconds.

        The time value can either be in the format "mm:ss" or a single numeric value representing
        the number of seconds. The method verifies the validity of the input, ensures that the
        time is positive, and performs the necessary conversion. If the input is invalid, an
        appropriate error message is returned along with a failure status.

        :param val: The time string to be parsed. This can either be in mm:ss format or as a
            numeric value representing seconds.
        :type val: str

        :return: A tuple where the first value is a boolean indicating success, and the
            second value is either the computed time in seconds (if successful) or an
            error message (if unsuccessful).
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
        Formats a given time in seconds into a string representation of minutes and
        seconds. This method accepts both integers and floating point numbers as input,
        and returns a string formatted as 'M:SS', where 'M' represents minutes and 'SS'
        represents seconds (padded with leading zero if needed).

        :param sec: A time duration given in seconds. This value can be either an integer
                    or a float.
        :type sec: float | int
        :return: A formatted string representation of the input time in minutes and
                 seconds.
        :rtype: str
        """
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    @staticmethod
    def validate_form(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        """
        Validates a form with provided data to ensure it adheres to the required format and
        includes necessary fields. Parses specific time-related fields into seconds and
        returns the validation result.

        :param data: Dictionary containing form data with keys such as 'serialnr',
                     'side_bridge_r', 'side_bridge_l', and 'run_2400'.
        :type data: Dict[str, Any]
        :return: A tuple containing a boolean indicating success or failure, and on
                 success, a dictionary with parsed values (in seconds) or, on failure,
                 an error message.
        :rtype: Tuple[bool, Dict[str, Any] | str]
        """
        if not (data.get("serialnr") or "").strip():
            return False, "Serial number is required."

        ok_sbr, sbr = PhefController.parse_time_to_seconds(
            data.get("side_bridge_r") or ""
        )
        if not ok_sbr:
            return False, f"Side-bridge Right: {sbr}"

        ok_sbl, sbl = PhefController.parse_time_to_seconds(
            data.get("side_bridge_l") or ""
        )
        if not ok_sbl:
            return False, f"Side-bridge Left: {sbl}"

        ok_run, run = PhefController.parse_time_to_seconds(data.get("run_2400") or "")
        if not ok_run:
            return False, f"2400m run: {run}"

        return True, {
            "side_bridge_r_s": sbr,
            "side_bridge_l_s": sbl,
            "run2400_s": run,
        }

    # ----- Queries -----
    async def load_sessions(self):
        """
        Asynchronously retrieves all test sessions related to the specified type of fitness test.

        This method invokes a service to fetch all test sessions associated with the
        `TypeFitnessTest.PHEF` fitness test type. It performs the operation asynchronously.

        :return: A coroutine that resolves to the list of all retrieved test sessions.
        :rtype: list
        """
        return await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.PHEF
        )

    async def get_session_by_id(self, session_id: int) -> Optional[TestSession]:
        return await self._service.get_test_session_by_id(int(session_id))

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        """
        Search for a military serviceman using their serial number.

        This asynchronous function checks the provided serial number, ensures it
        is valid, and queries the military service for the corresponding serviceman
        if the serial number is not empty.

        :param serialnr: The serial number of the serviceman to search for.
        :type serialnr: str
        :return: The serviceman object if found, otherwise None.
        :rtype: Optional[ServiceMen]
        """
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_phef_df(self, session_id: int, session_date=None) -> pd.DataFrame:
        """
        Generates a DataFrame containing physical fitness evaluation (PHEF) test results for servicemen
        associated with a given session ID. The method uses age, gender, and physical test results
        to compute detailed scores including running and side bridge performance. It returns a DataFrame
        with structured information including scores and a calculated total score.

        :param session_id: The unique identifier for a testing session
        :param session_date: Optional session date to calculate age-specific results. Defaults to None
        :return: A pandas DataFrame containing computed PHEF test results for the provided session
        :rtype: pd.DataFrame
        :raises Exception: If any error occurs during data processing or calculation
        """
        try:
            phef_tests = await self._service.get_all_phef(int(session_id))
            data = []
            for r in phef_tests:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    continue
                age = (
                    sm.age_from_birthdate()
                    if session_date is None
                    else sm.age_from_birthdate_and_session_date(session_date)
                )
                run = PhefCalculator.running_result(r.running_time, age, sm.gender)
                sbr = PhefCalculator.side_bridge_result(r.sideBridge_r, age, sm.gender)
                sbl = PhefCalculator.side_bridge_result(r.sideBridge_l, age, sm.gender)
                total = (run * (50 / 20.0)) + ((sbr + sbl) * (25 / 20.0))
                data.append(
                    {
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "runningTime": self.format_seconds(r.running_time),
                        "Running Score": f"{run}/20",
                        "Sidebridge R": self.format_seconds(r.sideBridge_r),
                        "Sidebridge R Score": f"{sbr}/20",
                        "Sidebridge L": self.format_seconds(r.sideBridge_l),
                        "Sidebridge L Score": f"{sbl}/20",
                        "Totale Score": f"{total:.1f}/100",
                    }
                )
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        """
        Decorates a pandas DataFrame by adding visual indicators (🟥 or 🟩) based on predefined
        thresholds in specific columns. This function modifies the content of the DataFrame
        to emphasize certain scores that fail or meet the set criteria.

        The method applies formatting to the following columns, if they exist in the DataFrame:
        - "Totale Score": A combination of multiple scores is evaluated. If specific conditions
          are met, it adds an indicator to highlight the total score.
        - "Running Score", "Sidebridge R Score", "Sidebridge L Score": Evaluates individual
          scores, adding an indicator based on a threshold.

        Notes:
        - If the DataFrame is empty, it is immediately returned without modification.
        - The original DataFrame remains unmodified; a copy is returned with changes.

        :param df: Input pandas DataFrame containing the necessary columns for score evaluation.
                   It is expected to contain columns for specific scores if formatting is to
                   be applied.
        :type df: pd.DataFrame
        :return: A copy of the original DataFrame with visual indicators (🟥 or 🟩) added to
                 the evaluated columns based on the threshold conditions.
        :rtype: pd.DataFrame
        """
        if df.empty:
            return df

        def _num(v: str, denom: float) -> Optional[float]:
            try:
                return float(str(v).split("/")[0])
            except Exception:
                return None

        out = df.copy()
        if "Totale Score" in out.columns:

            def _fmt_total_row(row: pd.Series) -> str:
                s = row.get("Totale Score")
                sr = row.get("Sidebridge R Score")
                st = row.get("Sidebridge L Score")
                rtr = row.get("Running Score")
                n = _num(s, 100.0)  # type: ignore[arg-type]
                r = _num(sr, 20.0)  # type: ignore[arg-type]
                t = _num(st, 20.0)  # type: ignore[arg-type]
                rs = _num(rtr, 20.0)  # type: ignore[arg-type]
                if n is None or r is None or t is None or rs is None:
                    return s  # type: ignore[return-value]
                return f"🟥 {s}" if rs < 10 or (r + t) < 20 else f"🟩 {s}"

            out["Totale Score"] = out.apply(_fmt_total_row, axis=1)

        for col in ["Running Score", "Sidebridge R Score", "Sidebridge L Score"]:
            if col in out.columns:

                def _fmt_sc(s: str):
                    n = _num(s, 20.0)
                    if n is None:
                        return s
                    return f"🟥 {s}" if n < 10 else f"🟩 {s}"

                out[col] = out[col].apply(_fmt_sc)
        return out

    # ----- Commands -----
    async def add_phef(
        self,
        session_id: int,
        payload: Dict[str, Any],
        military: ServiceMen | None,
        session: TestSession | None,
    ) -> Optional[PhefTest]:
        """
        Add a PHEF (Physical Health Evaluation Framework) test to a test session.

        This function creates a new instance of `PhefTest` and populates it with details
        from the payload. It then calls the service method to associate the fitness test
        with a specified test session using the provided session ID, optional military
        service member, and session details.

        :param session_id: The unique identifier of the test session. Should be an integer.
        :param payload: A dictionary containing all the relevant data for the fitness test,
            such as serial number, running time, and left/right side bridge times.
        :param military: Optional service member details to associate with the test. Can
            be None or of type ServiceMen.
        :param session: Optional session details to associate with the test. Can
            be None or of type TestSession.
        :return: An instance of `PhefTest` if the addition succeeds; otherwise, None.
        """
        p = PhefTest()
        p.test_session_id = int(session_id)  # type: ignore[attr-defined]
        p.serial_number = payload["serialnr"]
        p.running_time = payload["run2400_s"]
        p.sideBridge_r = payload["side_bridge_r_s"]
        p.sideBridge_l = payload["side_bridge_l_s"]
        return await self._service.add_fitness_test_to_testSession(
            int(session_id), p, military, session
        )

    async def update_phef(
        self, phef_id: int, payload: Dict[str, Any]
    ) -> Optional[PhefTest]:
        """
        Updates an existing PhefTest instance with new data and persists the updates
        using the service layer. The method processes the provided payload, assigns
        the relevant attributes to a PhefTest instance, and passes it to the service
        for update.

        :param phef_id: Identifier for the PhefTest to be updated
        :type phef_id: int
        :param payload: Dictionary containing new PhefTest data to be updated
        :type payload: Dict[str, Any]
        :return: Updated PhefTest instance or None if the update was not successful
        :rtype: Optional[PhefTest]
        """
        p = PhefTest()
        p.id = int(phef_id)
        p.test_session_id = int(payload["session_id"])  # type: ignore[attr-defined]
        p.serial_number = payload["serialnr"]
        p.running_time = payload["run2400_s"]
        p.sideBridge_r = payload["side_bridge_r_s"]
        p.sideBridge_l = payload["side_bridge_l_s"]
        return await self._service.update_fitness_test(int(phef_id), p)

    async def delete_phef(self, session_id: int, phef_id: int) -> bool:
        return await self._service.delete_fitness_test_from_test_session(
            int(session_id), int(phef_id)
        )
