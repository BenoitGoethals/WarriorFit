from __future__ import annotations
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import html

from core.type_fitness_test import TypeFitnessTest
from core.service_men import ServiceMen
from data.db.db_model import CombatTestParatrooper, TestSession
from services.be_mil_service import BEMILService
from services.service_test import ServiceTest


class CombatController:
    def __init__(self) -> None:
        self._service = ServiceTest()
        self.be_mil_service =BEMILService()

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

    @staticmethod
    def overall_passed(obstacle_passed: bool, rope_passed: bool, running_time_s: int) -> bool:
        # Business rule: <= 7200s (placeholder threshold)
        return obstacle_passed and rope_passed and running_time_s <= 7200

    @staticmethod
    def validate_form(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
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

    # ----- Queries -----
    async def load_sessions(self):
        return await self._service.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.COMBAT,True)

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_be_mil_by_id(serial)

    async def list_combat_tests_df(self, session_id: int) -> pd.DataFrame:
        try:
            combat_tests = await self._service.get_all_combat_test(int(session_id))
            data = []
            for r in combat_tests:
                sm = await self.be_mil_service.get_be_mil_by_id(r.serial_number)
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
        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
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
        cp = CombatTestParatrooper()
        cp.test_session_id = int(session_id)
        cp.serial_number = payload["serialnr"]
        cp.running_time = payload["combat_speedmars"]
        cp.rope_passed = payload["combat_robe"]
        cp.obstacle_passed = payload["combat_obstacle"]
        return await self._service.add_fitness_test_to_TestSession(int(session_id), cp,session=session,military=military)

    async def update_combat(self, combat_id: int, payload: Dict[str, Any]) -> Optional[CombatTestParatrooper]:
        cp = CombatTestParatrooper()
        cp.id = combat_id
        cp.test_session_id = int(payload["session_id"])
        cp.serial_number = payload["serialnr"]
        cp.running_time = payload["combat_speedmars"]
        cp.obstacle_passed = payload["combat_obstacle"]
        cp.rope_passed = payload["combat_robe"]
        return await self._service.update_fitness_test(int(combat_id), cp)

    async def delete_combat(self, session_id: int, combat_id: int) -> bool:
        return await self._service.delete_fitness_test_from_test_session(int(session_id), int(combat_id))

    # ----- Presentation bits -----


    async def get_test_session_by_id(self, param):
        return await self._service.get_test_session_by_id(param)
