from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from lxml import etree

import pandas as pd
from numpy import floating  # kept for return type compatibility

from warriorfit.core.Gender import Gender
from warriorfit.data.model.db_model import Cross, Runner, ServiceMen
from warriorfit.data.repositories.cross_repository import CrossRepository
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service import Service


class ServiceCross(Service):
    """
    Handles operations related to cross management and runners.

    The `ServiceCross` class extends the `Service` class, providing methods to
    manage cross events and participants (runners). The operations include adding,
    updating, retrieving, and deleting cross events and runners while maintaining
    audit logs for changes. It offers advanced statistics functionality using
    data processing libraries like `pandas` for faster aggregation and parallel
    processing techniques for performance optimization.

    :ivar be_mil_service: An instance of the `MilitaryService` class used for
        servicemen-related lookups.
    :type be_mil_service: MilitaryService
    """

    def __init__(self, cross_repository: CrossRepository = None,
                 user_repository=None, military_service: MilitaryService = None,
                 config=None) -> None:
        super().__init__(user_repository=user_repository, military_service=military_service, config=config)
        self._cross_repo = cross_repository if cross_repository is not None else CrossRepository()
        self.be_mil_service = military_service if military_service is not None else MilitaryService()

    async def get_runner(self, runner_id: int) -> Runner | None:
        return await self._cross_repo.get_runner(runner_id)

    async def get_cross(self, cross_id: int) -> Cross | None:
        return await self._cross_repo.get_cross(cross_id)

    async def add(self, cross: Cross) -> Cross | None:
        added = await self._cross_repo.add_cross(cross)
        if added:
            await self.add_audit_log(details=f"Cross {cross} added", action="add")
        return added

    async def list_all(self) -> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_all_runners(self) -> list[Runner]:
        return await self._cross_repo.get_all_runners()

    async def delete_cross(self, id_nr: int) -> bool:
        deleted = await self._cross_repo.remove_cross(id_nr)
        if deleted:
            await self.add_audit_log(details=f"Cross {id_nr} deleted", action="delete")
        return deleted

    async def get_all_crosses(self) -> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_cross_by_id(self, id_nr: int, lazy: bool = True) -> Cross | None:
        if lazy:
            return await self._cross_repo.get_cross(id_nr)
        return await self._cross_repo.get_cross_full(id_nr)

    async def get_cross_with_runners(self, id_nr: int) -> list[Runner]:
        return await self._cross_repo.get_runners_from_a_cross(id_nr)

    async def add_runner_to_cross(self, id_cross: int, r: Runner) -> Runner:
        r.cross_id = id_cross
        added = await self._cross_repo.add_runner_to_cross(id_cross, r)
        if added:
            await self.add_audit_log(
                details=f"Runner {r.serial_number} added to cross {id_cross}",
                action="add",
            )
        return added

    async def update_runner(self, id: int, r: Runner) -> Runner:
        updated = await self._cross_repo.update_runner(id, r)
        if updated:
            await self.add_audit_log(
                details=f"Runner {r.serial_number} updated in cross {id}",
                action="update",
            )
        return updated

    async def remove_runner_from_cross(self, id_nr: int) -> bool:
        removed = await self._cross_repo.remove_runner(id_nr)
        if removed:
            await self.add_audit_log(
                details=f"Runner {id_nr} removed from cross", action="delete"
            )
        return removed

    async def update_cross(self, cross: Cross) -> Cross | None:
        updated = await self._cross_repo.update_cross(cross)
        if updated:
            await self.add_audit_log(details=f"Cross {cross} updated", action="update")
        return updated

    async def exist_in_cross(self, serial: str, cross_id: int) -> bool:
        return await self._cross_repo.exist_in_cross(serial, cross_id)

    # ----------------------------
    # Fast stats (pandas + async gather)
    # ----------------------------

    @staticmethod
    def _bucket_age(age: int) -> str:
        if age < 18:
            return "<18"
        if age <= 25:
            return "18-25"
        if age <= 35:
            return "26-35"
        if age <= 45:
            return "36-45"
        if age <= 56:
            return "46-56"
        return "57+"

    @staticmethod
    def _runners_df(all_cross: list[Cross]) -> pd.DataFrame:

        rows: list[dict[str, Any]] = []
        for c in all_cross:
            # If relationship isn't loaded for some reason, this will raise; we fail-safe to empty.
            try:
                runners = c.runners
            except Exception:
                runners = []

            for r in runners:
                rows.append(
                    {
                        "cross_id": c.id,
                        "distance": c.distance,
                        "serial_number": r.serial_number,
                        "running_time": r.running_time,
                        "runner_obj": r,  # keep original objects for output format
                    }
                )
        return pd.DataFrame.from_records(rows)

    async def get_cross_stats(self):

        all_cross: list[Cross] = await self._cross_repo.get_all_cross(lazy=False)
        if not all_cross:
            return 0.0, 0.0, 0.0, {}, (0.0, 0.0), {}

        df = self._runners_df(all_cross)
        if df.empty:
            return 0.0, 0.0, 0.0, {}, (0.0, 0.0), {}

        df["running_time"] = pd.to_numeric(df["running_time"], errors="coerce")
        df = df.dropna(subset=["running_time"])
        if df.empty:
            return 0.0, 0.0, 0.0, {}, (0.0, 0.0), {}

        total_time = float(df["running_time"].sum())
        avg_time = total_time / float(len(all_cross)) if all_cross else 0.0

        best_time = float(df["running_time"].max())
        gap_time = float(df["running_time"].max() - df["running_time"].min())

        # Fetch servicemen once per unique serial, concurrently
        serials = df["serial_number"].dropna().astype(str).unique().tolist()
        servicemen_list = await asyncio.gather(
            *(
                self.be_mil_service.get_servicemen_by_serial(s)
                for s in serials
                if s is not None
            ),
            return_exceptions=True,
        )

        sm_rows: list[dict[str, Any]] = []
        for serial, sm in zip(serials, servicemen_list, strict=False):
            if isinstance(sm, Exception) or sm is None:
                continue
            try:
                sm_rows.append(
                    {
                        "serial_number": str(serial),
                        "gender": sm.gender,
                        "age_group": self._bucket_age(sm.age_from_birthdate()),
                    }
                )
            except Exception:
                continue

        sm_df = pd.DataFrame.from_records(sm_rows)
        if not sm_df.empty:
            df2 = df.copy()
            df2["serial_number"] = df2["serial_number"].astype(str)
            df2 = df2.merge(sm_df, on="serial_number", how="left")
        else:
            df2 = df.copy()
            df2["gender"] = pd.NA
            df2["age_group"] = pd.NA

        # Age groups
        age_group_stats: dict[str, int] = (
            df2["age_group"].dropna().value_counts().astype(int).to_dict()
        )

        # Gender avg times
        female_avg = (
            float(df2.loc[df2["gender"] == Gender.F, "running_time"].mean())
            if (df2["gender"] == Gender.F).any()
            else 0.0
        )
        male_avg = (
            float(df2.loc[df2["gender"] != Gender.F, "running_time"].mean())
            if df2["gender"].notna().any()
            else 0.0
        )

        # Top 10 per distance, ascending running_time (best first), return Runner objects
        top_10_by_distance: dict[Any, list[Runner]] = {}
        df_sorted = df2.sort_values(
            ["distance", "running_time"], ascending=[True, True]
        )
        for distance, group in df_sorted.groupby("distance", dropna=False, sort=False):
            top_10_by_distance[distance] = group["runner_obj"].head(10).tolist()

        return (
            avg_time,
            gap_time,
            best_time,
            age_group_stats,
            (female_avg, male_avg),
            top_10_by_distance,
        )

    async def get_average(self, all_cross: list[Cross]) -> float:
        # Preserves old semantics: sum(all runners) / len(all_cross)
        total = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                total += float(runner.running_time)
        return total / float(len(all_cross)) if all_cross else 0.0

    async def get_gap_time(self, all_cross: list[Cross]) -> float:
        worst_time = float("-inf")
        best_time = float("inf")

        for cross in all_cross:
            for runner in cross.runners:
                rt = float(runner.running_time)
                if rt > worst_time:
                    worst_time = rt
                if rt < best_time:
                    best_time = rt

        if worst_time == float("-inf") or best_time == float("inf"):
            return 0.0
        return worst_time - best_time

    async def get_best_time(self, all_cross: list[Cross]) -> float:
        # Preserves old behavior: returns the MAX running_time
        best_time = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                rt = float(runner.running_time)
                if rt > best_time:
                    best_time = rt
        return best_time

    async def get_age_group(self, all_cross: list[Cross]) -> dict[str, int]:
        age_groups: dict[str, int] = {}

        for cross in all_cross:
            for r in cross.runners:
                if r.serial_number is None:
                    continue
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    continue
                try:
                    g = self._bucket_age(sm.age_from_birthdate())
                    age_groups[g] = age_groups.get(g, 0) + 1
                except Exception:
                    continue

        return age_groups

    async def get_gender_time(
        self, all_cross: list[Cross]
    ) -> tuple[floating[Any], floating[Any]]:
        all_runners_f: list[float] = []
        all_runners_m: list[float] = []

        for cross in all_cross:
            for runner in cross.runners:
                if runner.serial_number is None:
                    continue
                service_man: ServiceMen | None = (
                    await self.be_mil_service.get_servicemen_by_serial(
                        runner.serial_number
                    )
                )
                if service_man is None:
                    continue
                if service_man.gender == Gender.F:
                    all_runners_f.append(float(runner.running_time))
                else:
                    all_runners_m.append(float(runner.running_time))

        # keep return types compatible (numpy floating-ish)
        f_avg = float(pd.Series(all_runners_f).mean()) if all_runners_f else 0.0
        m_avg = float(pd.Series(all_runners_m).mean()) if all_runners_m else 0.0
        return f_avg, m_avg

    async def get_top_10_runners_based_on_running_time(
        self, all_cross: list[Cross]
    ) -> dict[Any, list[Runner]]:
        top_runners_by_distance: dict[Any, list[Runner]] = {}

        for cross in all_cross:
            distance = cross.distance
            top_runners_by_distance.setdefault(distance, []).extend(cross.runners)

        for distance, runners in top_runners_by_distance.items():
            runners.sort(key=lambda x: x.running_time)
            top_runners_by_distance[distance] = runners[:10]

        return top_runners_by_distance

    async def read_xml_chronos(self, xml_file) -> bool:
        _XSD_PATH = Path(__file__).parent.parent / "data" / "chronorace.xsd"
        _logger = logging.getLogger(__name__)

        def _validate_and_parse(file_info) -> bool:
            try:
                file_path = file_info[0]["datapath"]
                schema_doc = etree.parse(str(_XSD_PATH))
                schema = etree.XMLSchema(schema_doc)
                xml_doc = etree.parse(file_path)
                if not schema.validate(xml_doc):
                    _logger.warning("Chronos XML failed XSD validation: %s", schema.error_log)
                    return False
                _logger.info("Chronos XML validated successfully.")
                return True
            except Exception as exc:
                _logger.error("Failed to read/validate Chronos XML: %s", exc)
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _validate_and_parse, xml_file)

