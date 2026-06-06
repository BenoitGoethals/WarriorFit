"""Controller for the 'My Progress' page — USER self-service test history."""

from __future__ import annotations

import re

import pandas as pd

from warriorfit.services.data_collector import DataCollector

_TOTAL_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _extract_numeric(total_str: str) -> float | None:
    """
    Extracts the first numeric value from a given string. If no numeric value is found or if the
    input is not a string, the function returns None.

    :param total_str: A string from which the first numeric value is to be extracted.
    :type total_str: str
    :return: The first numeric value as a float if present, otherwise None.
    :rtype: float | None
    """
    if not isinstance(total_str, str):
        return None
    m = _TOTAL_NUM_RE.search(total_str)
    return float(m.group(0)) if m else None


class MyProgressController:
    """
    Represents a controller for managing progress data, providing functionalities for
    extracting and processing historical and current year data.

    This class utilizes an instance of `DataCollector` for collecting data related to
    certain serials. It provides methods to return corresponding DataFrames and a static
    method for processing and transforming the collected data.

    :ivar _data_collector: Instance of `DataCollector` used for data collection.
    :type _data_collector: DataCollector
    """

    def __init__(self, data_collector: DataCollector | None = None):
        self._data_collector = data_collector if data_collector is not None else DataCollector()

    async def history_df(self, serial: str) -> pd.DataFrame:
        df = await self._data_collector.collect_tests_for_serial(serial, current_year=False)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    async def current_year_df(self, serial: str) -> pd.DataFrame:
        df = await self._data_collector.collect_tests_for_serial(serial, current_year=True)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    @staticmethod
    def progress_series(df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes the input DataFrame, ensuring it contains specific columns, and extracts
        numeric values from the "Total" column to create a new DataFrame with processed data.

        This method is designed to handle DataFrames that contain "Date", "Type", and "Total"
        columns, ensuring the data is properly formatted and sorted. If the required columns
        are missing or the DataFrame is empty,None, it produces an empty dataframe with
        expected columns ["Date", "Type", "Score"].

        :param df: Input DataFrame with a required "Date" column and an optional "Total" column.
                   The DataFrame should represent records with dates and numerical data.
        :type df: pandas.DataFrame
        :return: A DataFrame containing processed and filtered data with columns: "Date", "Type",
                 and "Score". Empty DataFrame is returned if input validation fails or required
                 data is insufficient.
        :rtype: pandas.DataFrame
        """
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
