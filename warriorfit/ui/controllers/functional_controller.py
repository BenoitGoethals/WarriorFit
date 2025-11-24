from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from warriorfit.core.Gender import Gender

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.db.db_model import FunctionalTest, TestSession, ServiceMen
from warriorfit.logic.Functional_calculator import FunctionalCalculator
from warriorfit.services.military_service import MilitaryService

from warriorfit.services.service_test import ServiceTest


class FunctionalController:
    """
    Controller encapsulating all Functional test business logic:
    - Validation and transformations
    - DB queries and commands
    - Presentation helpers (grid decoration, mail body)
    """
    def __init__(self, ) -> None:
        self._service = ServiceTest()
        self.be_mil_service = MilitaryService()

    # ----- Helpers -----
    @staticmethod
    def normalize_gender(g: Gender | str) -> Gender:
        if isinstance(g, str):
            return Gender.M if g.lower().startswith("m") else Gender.F
        return g

    @staticmethod
    def validate_form(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any] | str]:
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."
        try:
            push_ups = int(data.get("push_ups", 0))
            sit_ups = int(data.get("sit_ups", 0))
            pull_ups = int(data.get("pull_ups", 0))
        except Exception:
            return False, "All exercise counts must be valid numbers."
        if push_ups < 0 or sit_ups < 0 or pull_ups < 0:
            return False, "All exercise counts must be non-negative."
        return True, {"push_ups": push_ups, "sit_ups": sit_ups, "pull_ups": pull_ups}

    # ----- Queries (only here) -----
    async def load_sessions(self):
        return await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.FUNCTIONAL)

    async def get_session_by_id(self, session_id: int) -> Optional[TestSession]:
        return await self._service.get_test_session_by_id(int(session_id))

    async def search_military(self, serialnr: str) -> Optional[ServiceMen]:
        serial = (serialnr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_functional_tests_df(self, session_id: int) -> pd.DataFrame:
        try:
            rows = await self._service.get_all_functional_test(int(session_id))
            data = []
            for r in rows:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if not sm:
                    continue
                gender = self.normalize_gender(sm.gender)
                age = sm.age_from_birthdate()
                pull = FunctionalCalculator.get_score_pullup(gender, age, int(r.pull_ups))
                situp = FunctionalCalculator.get_score_situp(gender, age, int(r.sit_ups))
                push = FunctionalCalculator.get_score_pushup(gender, age, int(r.push_ups))
                total = ((pull + situp + push) / 60) * 100
                data.append({
                    "ID": r.id,
                    "Serial": r.serial_number,
                    "Push-ups": r.push_ups,
                    "Push-ups-score": push,
                    "Sit-ups": r.sit_ups,
                    "Sit-ups-score": situp,
                    "Pull-ups": r.pull_ups,
                    "Pull-ups-score": pull,
                    "Total Score": total,
                })
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df.copy()
        if "Total Score" in out.columns:
            def _fmt(v):
                try:
                    n = float(v)
                    return f"🟥 {n:.0f}" if n < 50 else f"🟩 {n:.0f}"
                except Exception:
                    return v
            out["Total Score"] = out["Total Score"].apply(_fmt)
        return out

    # ----- Commands (only here) -----
    async def add_functional(self, session_id: int, payload: Dict[str, Any],session:TestSession,military:ServiceMen) -> Optional[FunctionalTest]:
        ft = FunctionalTest()
        ft.test_session_id = int(session_id)
        ft.serial_number = payload["serialnr"]
        ft.push_ups = payload["push_ups"]
        ft.sit_ups = payload["sit_ups"]
        ft.pull_ups = payload["pull_ups"]
        return await self._service.add_fitness_test_to_testSession(int(session_id), ft,session=session,military=military)

    async def update_functional(self, functional_id: int, payload: Dict[str, Any]) -> Optional[FunctionalTest]:
        ft = FunctionalTest()
        ft.id = int(functional_id)
        ft.test_session_id = int(payload["session_id"])
        ft.serial_number = payload["serialnr"]
        ft.push_ups = payload["push_ups"]
        ft.sit_ups = payload["sit_ups"]
        ft.pull_ups = payload["pull_ups"]
        return await self._service.update_fitness_test(int(functional_id), ft)

    async def delete_functional(self, session_id: int, functional_id: int) -> bool:
        return await self._service.delete_fitness_test_from_test_session(int(session_id), int(functional_id))

