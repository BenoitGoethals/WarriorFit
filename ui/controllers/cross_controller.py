from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

from services.service_cross import ServiceCross  # assumed service layer for Cross domain
from services.be_mil_service import BEMILService
from data.db.db_model import Runner, Cross  # Runner model given in prompt


class CrossController:
    def __init__(self) -> None:
        self._service = ServiceCross()
        self.be_mil_service = BEMILService()

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> Tuple[bool, int | str]:
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
        m = int(sec) // 60
        s = int(sec) % 60
        return f"{int(m)}:{int(s):02d}"


    async def validate_form(self, data: Dict[str, Any],update=False) -> Tuple[bool, Dict[str, Any] | str]:
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

        elif await self._service.exist_in_cross(data.get("serialnr"),data.get("cross_id")):
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
        return await self.be_mil_service.get_be_mil_by_id(serialnr.strip())

    async def list_runners_df(self, cross_id: int) -> pd.DataFrame:
        try:
            cross = await self._service.get_cross_with_runners(int(cross_id))
            if cross is None:
                return pd.DataFrame()
            data = []
            for r in cross:
                data.append({
                    "Order" : 0,
                    "ID": r.id,
                    "Serial": r.serial_number or "",
                    "Running Time": self.format_seconds(r.running_time),
                    "Running seconds": (r.running_time)

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
        r = Runner()
        r.serial_number = payload["serialnr"]
        r.running_time = payload["running_time_s"]
        # attach to cross
        return await self._service.add_runner_to_cross(int(cross_id), r)

    async def update_runner(self, runner_id: int, payload: Dict[str, Any]) -> Optional[Runner]:
        r = Runner()
        r.id = int(runner_id)
        r.serial_number = payload["serialnr"]
        r.running_time = payload["running_time_s"]
        return await self._service.update_runner(int(runner_id), r)

    async def delete_runner(self,  runner_id: int) -> bool:
        return await self._service.remove_runner_from_cross(runner_id)