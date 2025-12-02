from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

from warriorfit.data.model.db_model import Runner, Cross  # Runner model given in prompt
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.report_generator_pdf import ReportGeneratorPdf
from warriorfit.services.service_cross import ServiceCross  # assumed service layer for Cross domain


class CrossController:
    def __init__(self) -> None:
        self._service = ServiceCross()
        self.be_mil_service = MilitaryService()
        self._pdf_gen = ReportGeneratorPdf()

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> Tuple[bool, int | str]:
        """
        Parses time input into an equivalent duration in seconds.

        The method accepts time in either "mm:ss" format or as a single value representing
        the total number of seconds. It validates the input for correctness, ensuring that
        the time is a positive numeric value. If the input is valid, it computes and returns
        the time in seconds.

        :param val: A string representing the time input. It can be a formatted time string
                    in "mm:ss" format or a numeric value (as seconds).
        :type val: str
        :return: A tuple where the first value is a boolean indicating success (`True`)
                 or failure (`False`), and the second value is the computed time in seconds
                 if successful, or an error message string if validation fails.
        :rtype: tuple[bool, int | str]

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
        Format a time duration in seconds to a string representation of minutes
        and seconds in the format "MM:SS".

        This method takes a numeric value (either integer or float) representing
        time in seconds and converts it into a string formatted as "MM:SS", where
        "MM" represents the number of minutes and "SS" represents the number of
        remaining seconds.

        :param sec: The time duration in seconds, expressed as a float or an int.
        :type sec: float | int
        :return: A string representation of the time in the "MM:SS" format.
        :rtype: str
        """
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"

    async def validate_form(self, data: Dict[str, Any], update=False) -> Tuple[bool, Dict[str, Any] | str]:
        """
        Validates the form data for a cross with a specific serial number and other parameters.
        Checks include validation of the serial number, its existence, uniqueness in the cross
        context, and proper formatting of the running time. Additional conditions are checked
        when updating an existing cross entry.

        :param data: Dictionary containing form data for validation.
        :param update: Boolean indicating if this is an update operation.
        :return: Tuple containing a boolean validation result and a dictionary with additional
                 processed values or an error message.
        """
        if not (data.get("serialnr") or "").strip():
            return False, "Serial number is required."
        if await self.search_military(data.get("serialnr")) is None:
            return (
                False,
                "Serial number does not exist. Please enter a valid serial number.",
            )
        if update:
            if data.get("serialnr") != data.get("old_serialnr"):
                if await self._service.exist_in_cross(data.get("serialnr"), data.get("cross_id")):
                    return False, "Serial number already exists."

        elif await self._service.exist_in_cross(data.get("serialnr"), data.get("cross_id")):
            return False, "Serial number already exists."

        ok_run, run = CrossController.parse_time_to_seconds(data.get("running_time") or "")
        if not ok_run:
            return False, f"Running time: {run}"
        cross_id = (data.get("cross_id") or "").strip()
        if not cross_id:
            return False, "Select a cross first."
        return True, {
            "running_time_s": run,
        }

    # ----- Queries -----
    async def load_crosses(self) -> List[Cross]:
        # Expected to return all Cross objects
        return await self._service.get_all_crosses()

    async def get_cross_by_id(self, cross_id: int) -> Optional[Cross]:
        return await self._service.get_cross_by_id(int(cross_id))

    async def search_military(self, serialnr: str):
        # Optional lookup; runners store serial_number, so we may look up a soldier for UI convenience
        if not (serialnr or "").strip():
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serialnr.strip())

    async def list_runners_df(self, cross_id: int) -> pd.DataFrame:
        """
        Retrieves and formats a list of runners related to a specified cross event into
        a pandas DataFrame. It fetches runner details asynchronously, formats the data,
        and includes additional computed fields such as order, running time, and
        runner-related metadata.

        :param cross_id: ID of the cross event for which the runners need to be listed.
        :type cross_id: int

        :return: A pandas DataFrame containing the runners' details, sorted by running
                 time in ascending order. The DataFrame includes fields such as order,
                 ID, serial, running time, runner name, gender, age, running seconds, and unit.
        :rtype: pd.DataFrame
        """
        try:
            cross = await self._service.get_cross_with_runners(int(cross_id))
            if cross is None:
                return pd.DataFrame()
            data = []
            for r in cross:
                runner = await self.be_mil_service.get_servicemen_by_serial(r.serial_number, lazy=False)
                data.append({
                    "Order": 0,
                    "ID": r.id,
                    "Serial": r.serial_number or "",
                    "Running Time": self.format_seconds(r.running_time),
                    "Runner Name": runner.first_name + " " + runner.last_name if runner else "",
                    "Gender": runner.gender if runner else "",
                    "Age": runner.age_from_birthdate() if runner else "",
                    "Running seconds": r.running_time,
                    "Unit": runner.unit if runner else "",

                })
            df = pd.DataFrame(data)
            if df.empty:
                return df
            # Sort by running time ascending (fastest first)
            df = df.sort_values(by="Running seconds", ascending=True).reset_index(drop=True)
            df["Order"] = df.index + 1  # Add 1 to make it 1-based instead of 0-based

            return df
        except Exception as e:
            return pd.DataFrame()

    # ----- Commands -----
    async def add_runner(self, cross_id: int, payload: Dict[str, Any]) -> Optional[Runner]:
        """
        Asynchronously adds a runner to a cross with the given cross identifier and payload containing runner details.

        :param cross_id: The unique identifier of the cross to which the runner will be added.
        :type cross_id: int
        :param payload: A dictionary containing runner details, such as serial number and running time.
        :type payload: Dict[str, Any]
        :return: The newly created Runner instance, or None if the operation was unsuccessful.
        :rtype: Optional[Runner]
        """
        r = Runner()
        r.serial_number = payload["serialnr"]
        r.running_time = payload["running_time_s"]
        # attach to cross
        return await self._service.add_runner_to_cross(int(cross_id), r)

    async def update_runner(self, runner_id: int, payload: Dict[str, Any]) -> Optional[Runner]:
        """
        Updates the details of a specific runner using the provided runner ID
        and payload. The runner object is created and populated with the payload
        data, and the update operation is performed through the service.

        :param runner_id: The unique identifier of the runner to update
        :type runner_id: int
        :param payload: A dictionary containing the updated data for the runner.
            Must include keys - "serialnr" (serial number of the runner)
            and "running_time_s" (runner's total running time in seconds).
        :type payload: Dict[str, Any]
        :return: The updated Runner object if the operation is successful, or
            None if the update fails.
        :rtype: Optional[Runner]
        """
        r = Runner()
        r.id = int(runner_id)
        r.serial_number = payload["serialnr"]
        r.running_time = payload["running_time_s"]
        return await self._service.update_runner(int(runner_id), r)

    async def delete_runner(self, runner_id: int) -> bool:
        """
        Deletes a runner using their unique identifier.

        This asynchronous method interacts with the service to remove a runner
        from a cross list. It ensures the deletion process is handled
        efficiently.

        :param runner_id: The unique identifier of the runner to be deleted.
        :type runner_id: int
        :return: True if the runner was successfully deleted, False otherwise.
        :rtype: bool
        """
        return await self._service.remove_runner_from_cross(runner_id)

    async def generate_report_cross(self, cross_id: str):
        """
        Generates a run report asynchronously.

        This method generates a PDF run report for the given `cross_id`.

        :param cross_id: The identifier of the cross to generate the report for.
        :type cross_id: str
        :return: A coroutine that produces the generated run report.
        :rtype: Awaitable
        """
        return await self._pdf_gen.generate_run_report("Run report", (int(cross_id)))
