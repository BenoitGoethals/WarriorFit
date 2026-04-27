import logging
from typing import Any

import pandas as pd

from warriorfit.data.model.db_model import Runner, ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_cross import ServiceCross
from warriorfit.utils.formaters import Formatter

logger = logging.getLogger(__name__)


class CrossStaticsController:
    """
    Handles the management and processing of cross statistics and extended statistics related
    to running events. Allows the retrieval and formatting of various statistical data points
    such as average times, best times, gender-based statistics, and trends.

    The class interacts with services to load and ensure the availability of data before
    providing accessors to the derived and formatted results.

    :ivar _service: Instance of `ServiceCross` responsible for fetching cross statistics.
    :type _service: ServiceCross
    :ivar _mil_service: Instance of `MilitaryService` responsible for fetching servicemen details.
    :type _mil_service: MilitaryService
    """

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
        """
        Asynchronously loads and initializes statistical data by fetching from the related service.

        This method retrieves cross stats and extended stats using the associated service, and stores
        the results for further use.

        :return: None
        """
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

    async def overview_per_distance_df(self) -> pd.DataFrame:
        """
        Asynchronously processes and formats the overview data per distance into a pandas DataFrame.
        The method ensures the required conditions are met, processes time-related columns with
        specific formatting, renames the columns, and returns the resulting DataFrame.

        :raises KeyError: If the required key "overview_per_distance" is missing in the internal
            structure `_ext`.
        :raises AttributeError: If methods or properties accessed on DataFrame or its columns
            do not exist.
        :raises TypeError: If an operation fails due to type incompatibility during DataFrame
            manipulation.
        :raises ValueError: If invalid values are encountered during DataFrame processing.

        :return: A pandas DataFrame containing the processed and formatted overview data per distance.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        df = self._ext["overview_per_distance"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["best_time"] = df["best_time"].apply(Formatter.format_time)
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        df["median_time"] = df["median_time"].apply(Formatter.format_time)
        df["gap_time"] = df["gap_time"].apply(Formatter.format_time)
        df["std_time"] = df["std_time"].round(1)
        return df.rename(
            columns={
                "distance": "Dist (km)",
                "finishers": "Finishers",
                "unique_runners": "Runners",
                "best_time": "Best",
                "avg_time": "Avg",
                "median_time": "Median",
                "std_time": "Std (s)",
                "gap_time": "Gap",
            }
        )

    async def per_cross_df(self) -> pd.DataFrame:
        """
        Generates and processes a DataFrame with cross-event statistics.

        This asynchronous method ensures the required data is prepared and transforms
        a DataFrame containing cross-event details. It applies formatting and renames
        columns to provide human-readable statistics, including time metrics and
        participant details.

        :return: A processed pandas DataFrame containing formatted cross-event
            statistics, including details such as average, median, and best times,
            along with participant data.
        :rtype: pd.DataFrame
        """
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
        df["avg_pace"] = df["avg_pace"].apply(lambda v: f"{v:.1f} s/km" if pd.notna(v) else "-")
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
        """
        Generates a pandas DataFrame containing per-runner statistics with formatted fields.

        This asynchronous method fetches and processes a DataFrame of runner statistics,
        applying specific formatting to time, pace, and improvement fields. It renames
        columns for better readability and ensures any empty DataFrame is returned unchanged.

        :return: A pandas DataFrame with processed and formatted per-runner statistics.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        df = self._ext["per_runner"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["personal_best"] = df["personal_best"].apply(Formatter.format_time)
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        df["avg_pace"] = df["avg_pace"].apply(lambda v: f"{v:.1f} s/km" if pd.notna(v) else "-")
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
        """
        Asynchronously retrieves, processes, and returns a DataFrame containing the best times
        for different age groups and distances.

        This method ensures the necessary external data is loaded and performs post-processing
        on the external "age_distance_best" DataFrame. If the input data is empty, it returns
        an empty DataFrame. Otherwise, it formats the best times into a human-readable format
        and renames the columns for better clarity.

        :return: A pandas DataFrame containing the best times for combinations of age groups
                 and distances, with formatted times and renamed columns.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        df = self._ext["age_distance_best"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["best_time"] = df["best_time"].apply(Formatter.format_time)
        return df.rename(
            columns={"age_group": "Age group", "distance": "Dist (km)", "best_time": "Best"}
        )

    async def age_distance_avg_df(self) -> pd.DataFrame:
        """
        Fetches and processes a DataFrame containing average age and distance-related data.

        This asynchronous method retrieves a DataFrame, if available, containing data about
        age groups, distances, and their corresponding average times. It processes the DataFrame
        by formatting the average time values for readability and then renames the columns to
        user-friendly titles.

        :return: A pandas DataFrame with processed average age and distance-related data. The
            DataFrame contains formatted and renamed columns: 'Age group', 'Dist (km)', and 'Avg'.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        df = self._ext["age_distance_avg"].copy()  # type: ignore[index]
        if df.empty:
            return df
        df["avg_time"] = df["avg_time"].apply(Formatter.format_time)
        return df.rename(
            columns={"age_group": "Age group", "distance": "Dist (km)", "avg_time": "Avg"}
        )

    async def gender_distance_df(self) -> pd.DataFrame:
        """
        Generate and return a DataFrame with gender and distance statistics, formatted and
        renamed for easier readability.

        This asynchronous method ensures the required data is prepared before processing
        the DataFrame. It:
        - Copies and processes the "gender_distance" data.
        - Formats the average time values for presentation.
        - Renames the columns for improved clarity.

        :return: A Pandas DataFrame containing gender-distance statistics with formatted data
            and renamed columns. The DataFrame contains details such as gender, distance
            (in kilometers), average time, and the number of finishers.
        :rtype: pd.DataFrame
        """
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
        """
        Fetches a DataFrame containing trend data, processes it, and returns a modified version with renamed
        columns and formatted average time.

        This asynchronous method ensures that required dependencies or states are initialized prior to
        processing. The DataFrame is retrieved by copying the "trends" data from an internal source, and
        if it is non-empty, the method applies formatting to the average time column and renames certain
        columns to more user-friendly names.

        :raises RuntimeError: If the method encounters initialization issues during processing.

        :return: A Pandas DataFrame with renamed columns and potentially formatted data.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        assert self._ext is not None
        df = self._ext["trends"].copy()
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
        """
        Fetches and returns a Pandas DataFrame containing podium data with formatted column names.

        The method ensures data is ready before processing. If the DataFrame containing
        podium data is empty, it is returned as-is. Otherwise, specific columns in the
        DataFrame are renamed for better readability, including replacing column names
        such as "serial_number" with "Serial" and "gold" with "🥇".

        :return: A Pandas DataFrame containing podium data with renamed columns. The DataFrame
                 is returned unchanged if it is empty.
        :rtype: pd.DataFrame
        """
        await self._ensure()
        assert self._ext is not None
        df = self._ext["podium"].copy()
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
        """
        Retrieves data quality metrics from the external data source.

        This asynchronous method ensures that the connection or session is
        properly initialized before accessing the stored data quality metrics.

        :return: A dictionary containing data quality metrics.
        :rtype: dict[str, Any]
        """
        await self._ensure()
        assert self._ext is not None
        return self._ext["data_quality"]

    async def distances(self) -> list[float]:
        """
        Retrieve a list of distances.

        This method ensures that the internal state is validated and fetches
        distance values from an internal data structure.

        :return: A list of float values representing distances.
        :rtype: list[float]
        """
        await self._ensure()
        assert self._ext is not None
        return self._ext["distances"]

    # ----- Legacy: per-distance Best-10 (now also dedup-aware in service) -----

    async def best_10_all_df(self) -> dict[int, pd.DataFrame]:
        """
        Retrieves the top 10 runners for all distances represented as pandas DataFrames,
        where each DataFrame contains detailed information about the runners.

        The method processes and organizes runner data into a dictionary of pandas
        DataFrames, indexed by distance as the key. Each DataFrame includes the
        rank, serial number, name, running time, distance, and age of the runners.
        If any runner is not associated with a valid service member, their name
        is recorded as "Unknown" and their age is set to None.

        :return: A dictionary mapping distances (int) to pandas DataFrames containing
                 runners' information for each distance.
        :rtype: dict[int, pd.DataFrame]
        """
        await self._ensure()
        assert self._stats is not None

        data: dict[Any, list[Runner]] = self._stats[5]
        data_panda_dict: dict[int, pd.DataFrame] = {}
        for key, value in data.items():
            if not value:
                continue
            data_p = []
            for rank_idx, runner in enumerate(value, start=1):
                if runner.serial_number is None:
                    continue
                service_men: ServiceMen | None = await self._mil_service.get_servicemen_by_serial(
                    runner.serial_number
                )
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
