"""Controller for the 'My Progress' page — USER self-service test history."""

from __future__ import annotations

import re

import pandas as pd

from warriorfit.services.data_collector import DataCollector

_TOTAL_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _extract_numeric(total_str: str) -> float | None:
    if not isinstance(total_str, str):
        return None
    m = _TOTAL_NUM_RE.search(total_str)
    return float(m.group(0)) if m else None


class MyProgressController:
    def __init__(self, data_collector: DataCollector = None):  # type: ignore[assignment]
        self._data_collector = data_collector if data_collector is not None else DataCollector()

    async def history_df(self, serial: str) -> pd.DataFrame:
        df = await self._data_collector.collect_tests_for_serial(serial, current_year=False)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    async def current_year_df(self, serial: str) -> pd.DataFrame:
        df = await self._data_collector.collect_tests_for_serial(serial, current_year=True)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    @staticmethod
    def progress_series(df: pd.DataFrame) -> pd.DataFrame:
        """Return a normalized (Date, Type, Score) DataFrame for plotting."""
        if df is None or df.empty or "Date" not in df.columns:
            return pd.DataFrame(columns=["Date", "Type", "Score"])

        out = df.copy()

        if "Total" not in out.columns:
            return pd.DataFrame(columns=["Date", "Type", "Score"])

        out["Score"] = out["Total"].apply(_extract_numeric)
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce")

        out = out.dropna(subset=["Date", "Score"]).sort_values("Date")

        out["Date"] = out["Date"].dt.strftime("%Y-%m-%d %H:%M")
        return out[["Date", "Type", "Score"]]