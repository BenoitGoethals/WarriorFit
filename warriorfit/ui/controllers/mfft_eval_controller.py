from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from warriorfit.core.cluster import Cluster
from warriorfit.core.mfft_level import MfftLevel
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import MfftEvalTest, ServiceMen, TestSession
from warriorfit.logic.mfft_eval_calculator import MfftEvalCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class MfftEvalController:
    """Controller for the MFFT Eval Shiny page.

    Wraps `ServiceTest` for CRUD on `MfftEvalTest` rows and drives the
    `MfftEvalCalculator` for per-event tiers and overall verdict.
    """

    EVENT_LABELS: tuple[str, ...] = (
        "Pull-up",
        "Burpees step-over",
        "Farmer walk (m)",
        "Push-up & release",
        "Casualty drag (m)",
        "Sandbag carry (m)",
        "Combat run",
        "Combat swim",
    )

    def __init__(
        self,
        service: ServiceTest | None = None,
        mil_service: MilitaryService | None = None,
    ) -> None:
        self._service = service if service is not None else ServiceTest()
        self.be_mil_service = mil_service if mil_service is not None else MilitaryService()
        self._logger = logging.getLogger(__name__)

    # ----- Helpers -----
    @staticmethod
    def parse_time_to_seconds(val: str) -> tuple[bool, int | str]:
        """Same shape as CombatController.parse_time_to_seconds (mm:ss or seconds)."""
        txt = (val or "").strip()
        if not txt:
            return False, "Time value is required."
        MAX_SECONDS = 120 * 60
        try:
            if ":" in txt:
                parts = txt.split(":")
                if len(parts) != 2:
                    return False, "Time must be in mm:ss or seconds."
                m = int(parts[0])
                s = int(parts[1])
                if m < 0:
                    return False, "Minutes must be >= 0."
                if s < 0 or s >= 60:
                    return False, "Seconds must be between 0 and 59."
                total_seconds = m * 60 + s
            else:
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
    def _parse_int(val: str | int | None, *, field: str) -> tuple[bool, int | str]:
        """Strict positive-integer parse.

        Accepts an int or a numeric string. Rejects empty, non-numeric, and 0.
        Returns ``(True, n)`` on success or ``(False, error_message)`` otherwise.
        """
        if val is None or (isinstance(val, str) and not val.strip()):
            return False, f"{field} is required."
        try:
            n = int(float(str(val)))
        except (ValueError, TypeError):
            return False, f"{field} must be a positive integer."
        if n <= 0:
            return False, f"{field} must be greater than 0."
        return True, n

    async def load_sessions(self):
        return await self._service.get_all_test_sessions_type_fitness_test(
            TypeFitnessTest.MFFT_EVAL
        )

    async def search_military(self, serial_nr: str) -> ServiceMen | None:
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)

    async def list_mfft_tests_df(self, session_id: int) -> pd.DataFrame:
        """Build a DataFrame summarising MFFT Eval results for one session."""
        try:
            tests = await self._service.get_all_mfft_eval(int(session_id))
            data = []
            for r in tests:
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    continue
                age = sm.age_from_birthdate()
                res = MfftEvalCalculator.evaluate(r, sm.cluster, age, sm.gender)
                data.append(
                    {
                        "ID": r.id,
                        "Serial": r.serial_number,
                        "Cluster": str(sm.cluster),
                        "PullUps": r.pull_ups,
                        "Burpees": r.burpees_step_over,
                        "FarmerM": r.farmer_walk_m,
                        "PushUps": r.push_ups_release,
                        "DragM": r.casualty_drag_m,
                        "SandbagM": r.sandbag_carry_m,
                        "Run": self.format_seconds(r.combat_run_seconds),
                        "Swim": self.format_seconds(r.combat_swim_seconds),
                        "Overall": str(res.overall),
                        "Tier": str(res.tier_info),
                        "Result": "Passed" if res.passed else "Failed",
                    }
                )
            return pd.DataFrame(data)
        except (ValueError, TypeError, AttributeError) as e:
            self._logger.error("Error in list_mfft_tests_df: %s", e)
            return pd.DataFrame()

    @staticmethod
    def decorate_grid(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df2 = df.copy()
        if "Result" in df2.columns:
            df2["Result"] = df2["Result"].apply(
                lambda v: f"🟩 {v}" if str(v).lower() == "passed" else f"🟥 {v}"
            )
        return df2

    @staticmethod
    def _tier_color(level: MfftLevel) -> str:
        return {
            MfftLevel.GOLD: "#d4af37",
            MfftLevel.SILVER: "#bdbdbd",
            MfftLevel.BRONZE: "#cd7f32",
            MfftLevel.FIT: "green",
            MfftLevel.UNFIT: "red",
        }.get(level, "black")

    # ----- Commands -----
    async def add_mfft(
        self,
        session_id: int,
        payload: dict[str, Any],
        session: TestSession,
        military: ServiceMen,
    ) -> MfftEvalTest | None:
        test = MfftEvalTest()
        test.test_session_id = int(session_id)  # type: ignore[attr-defined]
        test.serial_number = payload["serialnr"]
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return await self._service.add_fitness_test_to_testSession(
            int(session_id), test, session=session, military=military
        )

    async def update_mfft(
        self, mfft_id: int, payload: dict[str, Any]
    ) -> MfftEvalTest | None:
        test = MfftEvalTest()
        test.id = mfft_id
        test.test_session_id = int(payload["session_id"])  # type: ignore[attr-defined]
        test.serial_number = payload["serialnr"]
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return await self._service.update_fitness_test(int(mfft_id), test)

    async def delete_mfft(self, session_id: int, mfft_id: int) -> bool:
        return await self._service.delete_fitness_test_from_test_session(
            int(session_id), int(mfft_id)
        )

    async def get_test_session_by_id(self, param):
        return await self._service.get_test_session_by_id(param)

    def validate_form(
        self, data: dict[str, Any]
    ) -> tuple[bool, dict[str, Any] | str]:
        """Normalize the 8-event form.

        Returns ``(True, normalized)`` on success or ``(False, error)`` otherwise.
        """
        serial = (data.get("serialnr") or "").strip()
        if not serial:
            return False, "Serial number is required."

        int_fields = (
            ("pull_ups", "Pull-ups"),
            ("burpees", "Burpees"),
            ("farmer_m", "Farmer walk meters"),
            ("push_ups", "Push-ups"),
            ("drag_m", "Casualty drag meters"),
            ("sandbag_m", "Sandbag carry meters"),
        )
        normalized: dict[str, Any] = {"serialnr": serial}
        for key, label in int_fields:
            ok, val = self._parse_int(data.get(key), field=label)
            if not ok:
                return False, str(val)
            normalized[key] = val

        ok_run, run_val = self.parse_time_to_seconds(str(data.get("combat_run") or ""))
        if not ok_run:
            return False, f"Combat run: {run_val}"
        ok_swim, swim_val = self.parse_time_to_seconds(str(data.get("combat_swim") or ""))
        if not ok_swim:
            return False, f"Combat swim: {swim_val}"

        normalized["run_seconds"] = int(run_val)
        normalized["swim_seconds"] = int(swim_val)
        return True, normalized

    def evaluate_payload(
        self, payload: dict[str, Any], cluster: Cluster, age: int, gender: Any
    ):
        """Run the calculator on already-validated form values.

        Returns the `MfftResult`. The caller is expected to render
        per-event tiers and the overall verdict.
        """
        test = MfftEvalTest()
        test.pull_ups = int(payload["pull_ups"])
        test.burpees_step_over = int(payload["burpees"])
        test.farmer_walk_m = int(payload["farmer_m"])
        test.push_ups_release = int(payload["push_ups"])
        test.casualty_drag_m = int(payload["drag_m"])
        test.sandbag_carry_m = int(payload["sandbag_m"])
        test.combat_run_seconds = int(payload["run_seconds"])
        test.combat_swim_seconds = int(payload["swim_seconds"])
        return MfftEvalCalculator.evaluate(test, cluster, age, gender)
