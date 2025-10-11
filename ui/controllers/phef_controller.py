from __future__ import annotations
from typing import Optional, Dict, Any, Tuple

import pandas as pd

from core.service_men import ServiceMen
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest, TestSession
from logic.phef_calculator import PhefCalculator
from services.be_mil_service import BEMILService
from services.db_service import DBService


class PhefController:
    """
    Encapsulates all PHEF business logic:
    - Validation and parsing
    - DB queries and commands
    - Grid decoration and email HTML body
    """
    def __init__(self, db: DBService, be_mil_service: Optional[BEMILService] = None) -> None:
        self.db = db
        self.be_mil_service = be_mil_service or BEMILService()

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
    def validate_form(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        if not (data.get("serialnr") or "").strip():
            return False, "Serial number is required."

        ok_sbr, sbr = PhefController.parse_time_to_seconds(data.get("side_bridge_r") or "")
        if not ok_sbr:
            return False, f"Side-bridge Right: {sbr}"

        ok_sbl, sbl = PhefController.parse_time_to_seconds(data.get("side_bridge_l") or "")
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
        return await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.PHEF)

    async def get_session_by_id(self, session_id: int) -> Optional[TestSession]:
        return await self.db.get_test_session_by_id(int(session_id))

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_be_mil_by_id(serial)

    async def list_phef_df(self, session_id: int, session_date=None) -> pd.DataFrame:
        try:
            phef_tests = await self.db.get_all_phef(int(session_id))
            data = []
            for r in phef_tests:
                sm = await self.be_mil_service.get_be_mil_by_id(r.serial_number)
                if sm is None:
                    continue
                age = sm.age_from_birthdate() if session_date is None else sm.age_from_birthdate_and_session_date(session_date)
                run = PhefCalculator.running_result(r.running_time, age, sm.gender)
                sbr = PhefCalculator.side_bridge_result(r.sideBridge_r, age, sm.gender)
                sbl = PhefCalculator.side_bridge_result(r.sideBridge_l, age, sm.gender)
                total = (run * (50 / 20.0)) + ((sbr + sbl) * (25 / 20.0))
                data.append({
                    "ID": r.id,
                    "Serial": r.serial_number,
                    "runningTime": self.format_seconds(r.running_time),
                    "Running Score": f"{run}/20",
                    "Sidebridge R": self.format_seconds(r.sideBridge_r),
                    "Sidebridge R Score": f"{sbr}/20",
                    "Sidebridge L": self.format_seconds(r.sideBridge_l),
                    "Sidebridge L Score": f"{sbl}/20",
                    "Totale Score": f"{total:.1f}/100",
                })
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
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
                n = _num(s, 100.0)
                r = _num(sr, 20.0)
                t = _num(st, 20.0)
                rs = _num(rtr, 20.0)
                if n is None or r is None or t is None or rs is None:
                    return s
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
    async def add_phef(self, session_id: int, payload: Dict[str, Any]) -> Optional[PhefTest]:
        p = PhefTest()
        p.test_session_id = int(session_id)
        p.serial_number = payload["serialnr"]
        p.running_time = payload["run2400_s"]
        p.sideBridge_r = payload["side_bridge_r_s"]
        p.sideBridge_l = payload["side_bridge_l_s"]
        p.pointBridge_r = 0
        p.pointBridge_l = 0
        p.pointsRunning = 0
        return await self.db.add_fitness_test_to_TestSession(int(session_id), p)

    async def update_phef(self, phef_id: int, payload: Dict[str, Any]) -> Optional[PhefTest]:
        p = PhefTest()
        p.id = int(phef_id)
        p.test_session_id = int(payload["session_id"])
        p.serial_number = payload["serialnr"]
        p.running_time = payload["run2400_s"]
        p.sideBridge_r = payload["side_bridge_r_s"]
        p.sideBridge_l = payload["side_bridge_l_s"]
        p.pointBridge_r = 0
        p.pointBridge_l = 0
        p.pointsRunning = 0
        return await self.db.update_fitness_test(int(phef_id), p)

    async def delete_phef(self, session_id: int, phef_id: int) -> bool:
        return await self.db.delete_fitness_test_from_test_session(int(session_id), int(phef_id))

    # ----- Presentation: mail HTML -----
    def build_email_body(self, sm: ServiceMen, session: TestSession, payload: Dict[str, Any]) -> str:
        age = sm.age_from_birthdate() if session is None else sm.age_from_birthdate_and_session_date(session.datetime_start)
        run = PhefCalculator.running_result(payload["run2400_s"], age, sm.gender)
        sbr = PhefCalculator.side_bridge_result(payload["side_bridge_r_s"], age, sm.gender)
        sbl = PhefCalculator.side_bridge_result(payload["side_bridge_l_s"], age, sm.gender)
        total = (run * (50 / 20.0)) + ((sbr + sbl) * (25 / 20.0))
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{session.datetime_start.strftime('%Y-%m-%d') if session else '-'}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;" colspan="2">Test Results</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Running (2400m)</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload["run2400_s"])}<br>
                        Score: {run}/20
                    </td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Right</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload["side_bridge_r_s"])}<br>
                        Score: {sbr}/20
                    </td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Side Bridge Left</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        Time: {self.format_seconds(payload["side_bridge_l_s"])}<br>
                        Score: {sbl}/20
                    </td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">Total Score</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">{total:.1f}/100</th>
                </tr>
            </table>
        """