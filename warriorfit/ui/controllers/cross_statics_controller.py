import logging
from typing import Any

import pandas as pd

from warriorfit.data.model.db_model import Runner, ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_cross import ServiceCross
from warriorfit.utils.formaters import Formatter

logger = logging.getLogger(__name__)


class CrossStaticsController:
    def __init__(
        self,
        service: ServiceCross = None,
        mil_service: MilitaryService = None,
    ) -> None:
        self._service = service if service is not None else ServiceCross()
        self._mil_service = mil_service if mil_service is not None else MilitaryService()
        self._stats: tuple | None = None
        self._ext: dict[str, Any] | None = None

    async def load(self):
        self._stats = await self._service.get_cross_stats()
        self._ext = await self._service.get_extended_stats()

    async def _ensure(self):
        if self._stats is None or self._ext is None:
            await self.load()

    # ----- Legacy accessors (kept for backwards compatibility) -----

    async def get_average_time(self) -> float:
        await self._ensure()
        return self._stats[0]  # type: ignore[index]

    async def get_gap_time(self):
        await self._ensure()
        return self._stats[1]  # type: ignore[index]

    async def get_best_time(self):
        await self._ensure()
        return self._stats[2]  # type: ignore[index]

    async def get_age_group(self):
        await self._ensure()
        return self._stats[3]  # type: ignore[index]

    async def get_gender_time(self):
        await self._ensure()
        return self._stats[4]  # type: ignore[index]

    # ----- Extended stats accessors -----

    async def overview(self) -> dict[str, Any]:
        await self._ensure()
        return self._ext["overview"]  # type: ignore[index]

    async def per_cross_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["per_cross"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        df["median_time"] = df["median_time"].apply(Formatter.format_time)
        df["best_time"] = df["best_time"].apply(Formatter.format_time)
        df["worst_time"] = df["worst_time"].apply(Formatter.format_time)
        df["gap_time"] = df["gap_time"].apply(Formatter.format_time)
        df["std_time"] = df["std_time"].round(1)
        df["avg_pace"] = df["avg_pace"].apply(
            lambda v: f"{v:.1f} s/km" if pd.notna(v) else "-"
        )
        df = df.rename(
            columns={
                "cross_id": "Cross",
                "distance": "Dist (km)",
                "cross_datetime": "Date",
                "participants": "Finishers",
                "avg_time": "Avg",
                "median_time": "Median",
                "std_time": "Std (s)",
                "best_time": "Best",
                "worst_time": "Worst",
                "gap_time": "Gap",
                "avg_pace": "Pace",
            }
        )
        return df

    async def per_runner_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["per_runner"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["personal_best"] = df["personal_best"].apply(Formatter.format_time)
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        df["avg_pace"] = df["avg_pace"].apply(
            lambda v: f"{v:.1f} s/km" if pd.notna(v) else "-"
        )
        if "avg_improvement" in df.columns:
            df["avg_improvement"] = df["avg_improvement"].apply(
                lambda v: f"{v:+.1f} s" if pd.notna(v) else "-"
            )
        df = df.rename(
            columns={
                "serial_number": "Serial",
                "full_name": "Name",
                "races": "Races",
                "personal_best": "PB",
                "avg_time": "Avg",
                "avg_pace": "Pace",
                "avg_improvement": "Δ avg",
            }
        )
        return df

    async def age_distance_best_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["age_distance_best"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["best_time"] = df["best_time"].apply(Formatter.format_time)
        return df.rename(
            columns={"age_group": "Age group", "distance": "Dist (km)", "best_time": "Best"}
        )

    async def age_distance_avg_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["age_distance_avg"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        return df.rename(
            columns={"age_group": "Age group", "distance": "Dist (km)", "avg_time": "Avg"}
        )

    async def gender_distance_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["gender_distance"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        return df.rename(
            columns={
                "gender": "Gender",
                "distance": "Dist (km)",
                "avg_time": "Avg",
                "count": "Finishers",
            }
        )

    async def trends_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["trends"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        return df.rename(
            columns={
                "cross_datetime": "Date",
                "distance": "Dist (km)",
                "avg_time": "Avg",
            }
        )

    async def podium_df(self) -> pd.DataFrame:
        await self._ensure()
        df = self._ext["podium"].copy()  # type: ignore[index]
        if df.empty:
            return df
        return df.rename(
            columns={
                "serial_number": "Serial",
                "full_name": "Name",
                "podiums": "Podiums",
                "gold": "🥇",
                "silver": "🥈",
                "bronze": "🥉",
            }
        )

    async def data_quality(self) -> dict[str, Any]:
        await self._ensure()
        return self._ext["data_quality"]  # type: ignore[index]

    async def distances(self) -> list[float]:
        await self._ensure()
        return self._ext["distances"]  # type: ignore[index]

    # ----- Legacy: per-distance Best-10 (now also dedup-aware in service) -----

    async def best_10_all_df(self) -> dict[int, pd.DataFrame]:
        """Build per-distance best-10 grids using enriched serviceman info."""
        await self._ensure()

        data: dict[Any, list[Runner]] = self._stats[5]  # type: ignore[index]
        data_panda_dict: dict[int, pd.DataFrame] = {}
        for key, value in data.items():
            if not value:
                continue
            data_p = []
            for rank_idx, runner in enumerate(value, start=1):
                if runner.serial_number is None:
                    continue
                service_men: ServiceMen = await self._mil_service.get_servicemen_by_serial(
                    runner.serial_number
                )  # type: ignore[assignment]
                if service_men:
                    data_p.append(
                        {
                            "rank": rank_idx,
                            "serial_number": runner.serial_number,
                            "Name": f"{service_men.first_name} {service_men.last_name}",
                            "running_time": Formatter.format_time(runner.running_time),
                            "distance": key,
                            "age": service_men.age_from_birthdate(),
                        }
                    )
                else:
                    logger.warning(
                        f"ServiceMen not found for serial_number: {runner.serial_number} (distance: {key})"
                    )
                    data_p.append(
                        {
                            "rank": rank_idx,
                            "serial_number": runner.serial_number,
                            "Name": "Unknown",
                            "running_time": Formatter.format_time(runner.running_time),
                            "distance": key,
                            "age": None,
                        }
                    )
            data_panda_dict[int(key)] = pd.DataFrame(data_p)
        return data_panda_dict
