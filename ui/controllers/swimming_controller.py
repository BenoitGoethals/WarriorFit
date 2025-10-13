from __future__ import annotations
from typing import Optional, Dict, Any
import pandas as pd
from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import CombatSwimmingTest, TestSession
from services.be_mil_service import BEMILService
from services.service_test import ServiceTest


class SwimmingController:
    """
    Encapsulates all Swimming test business logic:
    - Validation
    - DB queries and commands
    - Grid decoration and email HTML body
    """
    def __init__(self,) -> None:
        self._service = ServiceTest()
        self.be_mil_service =  BEMILService()

    # ----- Validation -----
    @staticmethod
    def validate_form(data: Dict[str, Any]) -> tuple[bool, Dict[str, Any] | str]:
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."
        return True, {
            "swim_passed": bool(data.get("swim_passed", False)),
        }

    # ----- Queries -----
    async def load_sessions(self):
        return await self._service.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.SWIMMING,True)

    async def get_session_by_id(self, session_id: int) -> Optional[TestSession]:
        return await self._service.get_test_session_by_id(int(session_id))

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_be_mil_by_id(serial)

    async def list_swim_df(self, session_id: int) -> pd.DataFrame:
        try:
            swim_tests = await self._service.get_all_combat_swimming_test(int(session_id))
            rows = []
            for r in swim_tests or []:
                sm = await self.be_mil_service.get_be_mil_by_id(r.serial_number)
                if not sm:
                    continue
                rows.append({
                    "ID": r.id,
                    "Serial": r.serial_number,
                    "Name": f"{sm.first_name} {sm.last_name}",
                    "Result": "PASSED" if getattr(r, "swim_paased", False) else "FAILED",
                })
            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df.copy()
        if "Result" in out.columns:
            def _fmt(v: str):
                return f"🟩 {v}" if str(v).upper() == "PASSED" else f"🟥 {v}"
            out["Result"] = out["Result"].apply(_fmt)
        return out

    # ----- Commands -----
    async def add_swim(self, session_id: int, payload: Dict[str, Any]) -> Optional[CombatSwimmingTest]:
        st = CombatSwimmingTest()
        st.test_session_id = int(session_id)
        st.serial_number = payload["serialnr"]
        st.swim_paased = bool(payload["swim_passed"])
        return await self._service.add_fitness_test_to_TestSession(int(session_id), st)

    async def update_swim(self, swim_id: int, payload: Dict[str, Any]) -> Optional[CombatSwimmingTest]:
        st = CombatSwimmingTest()
        st.id = int(swim_id)
        st.test_session_id = int(payload["session_id"])
        st.serial_number = payload["serialnr"]
        st.swim_paased = bool(payload["swim_passed"])
        return await self._service.update_fitness_test(int(swim_id), st)

    async def delete_swim(self, session_id: int, swim_id: int) -> bool:
        return await self._service.delete_fitness_test_from_test_session(int(session_id), int(swim_id))

    # ----- Presentation: mail HTML -----
    @staticmethod
    def build_email_body(sm: ServiceMen, session: TestSession, payload: Dict[str, Any]) -> str:
        passed = bool(payload.get("swim_passed"))
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{session.datetime_start.strftime('%Y-%m-%d')}</td>
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