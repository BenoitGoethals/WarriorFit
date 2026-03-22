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
        """
        Calculate and return various statistical metrics for a set of cross events.

        This function processes data related to cross events, including computing the
        average time, time gap, and best time across all events. It also aggregates
        demographic statistics, such as age group distributions and gender-based average
        times. Furthermore, the function identifies and organizes the top 10 runners
        per distance in ascending order of running time.

        :return: A tuple containing the following:
            - Average running time across all cross events.
            - Time gap between the maximum and minimum running times.
            - Best (minimum) running time across all events.
            - Dictionary mapping age groups to their respective counts.
            - Tuple containing the average running times for female and male participants.
            - Dictionary mapping distances to a list of the top 10 Runner objects
              (ordered by ascending running time) for each distance.
        :rtype: tuple[float, float, float, dict[str, int], tuple[float, float], dict[Any, list[Runner]]]
        """
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
        """
        Calculates the average running time across all provided 'Cross' objects.

        This method iterates through a list of 'Cross' objects, which contain multiple runners,
        and computes the average running time by summing the running times of all runners and
        dividing the result by the number of 'Cross' objects provided.

        :param all_cross: A list of 'Cross' objects. Each 'Cross' object contains runners with
            individual running times.
        :type all_cross: list[Cross]
        :return: The average running time as a float. If the input list is empty, returns 0.0.
        :rtype: float
        """
        # Preserves old semantics: sum(all runners) / len(all_cross)
        total = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                total += float(runner.running_time)
        return total / float(len(all_cross)) if all_cross else 0.0

    async def get_gap_time(self, all_cross: list[Cross]) -> float:
        """
        Computes the difference between the maximum and minimum running times of runners
        in a given list of Cross objects. This function is designed to evaluate the "gap
        time," which represents the disparity between the slowest and fastest runners’
        performance.

        :param all_cross: A list of Cross objects. Each Cross object contains a collection
            of runners, and each runner has a `running_time` attribute representing their
            running time.
        :type all_cross: list[Cross]
        :return: The gap time as a floating-point number. If no valid times are present
            in the input, 0.0 is returned.
        :rtype: float
        """
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
        """
        Determines the best (maximum) running time among all runners in the provided
        list of Cross objects. Iterates through each Cross and its associated runners
        to find the highest recorded running time.

        :param all_cross: A list of Cross objects. Each Cross contains runners with
                          running times to evaluate.
        :type all_cross: list[Cross]
        :return: The maximum running time among all runners in the provided Cross
                 objects.
        :rtype: float
        """
        # Preserves old behavior: returns the MAX running_time
        best_time = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                rt = float(runner.running_time)
                if rt > best_time:
                    best_time = rt
        return best_time

    async def get_age_group(self, all_cross: list[Cross]) -> dict[str, int]:
        """
        Asynchronously retrieves age group distribution based on the provided list of cross entries.
        For each runner in the cross entries with a valid serial number, the serviceman's age is determined,
        then categorized into predefined age groups.

        :param all_cross: A list containing Cross objects, where each Cross contains runners to process.
        :type all_cross: list[Cross]
        :return: A dictionary mapping age group identifiers to the count of servicemen in each group.
        :rtype: dict[str, int]
        """
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
        """
        Calculate and return the average running times for female and male runners from
        the provided list of crosses. The function asynchronously processes the list of
        runners, determines the gender of each by querying a service, and computes the
        average running time for each gender. If no times are available for a gender,
        a default value of 0.0 is returned.

        :param all_cross: A list of Cross objects, each representing a running event.
            Each Cross contains a list of runners, where each runner has attributes
            such as serial number and running time.
        :type all_cross: list[Cross]
        :return: A tuple containing the average running time for female runners
            (first element) and the average running time for male runners (second
            element). Each element is a floating-point number (numpy floating-like)
            or 0.0 if no times exist for that gender.
        :rtype: tuple[floating[Any], floating[Any]]
        """
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
        """
        Asynchronously retrieves the top 10 runners for each unique distance across a list of Cross objects,
        based on their running times. For each distance, the runners are sorted in ascending order of their
        running times, and the top 10 runners are selected.

        :param all_cross: A list of Cross objects, where each Cross object contains a distance and a list
            of runners.
        :type all_cross: list[Cross]
        :return: A dictionary where keys are distances (unique to each Cross object) and values are lists
            of the top 10 runners for that distance, sorted by running time.
        :rtype: dict[Any, list[Runner]]
        """
        top_runners_by_distance: dict[Any, list[Runner]] = {}

        for cross in all_cross:
            distance = cross.distance
            top_runners_by_distance.setdefault(distance, []).extend(cross.runners)

        for distance, runners in top_runners_by_distance.items():
            runners.sort(key=lambda x: x.running_time)
            top_runners_by_distance[distance] = runners[:10]

        return top_runners_by_distance

    async def  read_xml_chronos_and_save(self, xml_file, cross_id: int) -> bool:
        """
        Reads and validates a Chronos XML file against a predefined XSD schema and processes the data to
        add runners to a specified cross event. This function ensures that the XML data conforms to the
        Chronos format and extracts the relevant details about athletes, including their bib numbers
        and net running times. The processed data is then saved to the cross repository.

        :param xml_file: The XML file containing Chronos data. It should be in the format expected by the
            XSD schema. Typically, this is provided as a list with a "datapath" key containing the path
            to the temporary XML file.
        :type xml_file: list[dict[str, str]]
        :param cross_id: The unique identifier of the cross event to which the runners will be added.
        :return: A boolean value indicating whether the XML file was successfully read, validated, and
            processed. Returns True if all operations succeeded, and False if any step failed.
        :rtype: bool
        :raises Exception: If an error occurs during file reading, validation, or data processing.
        """
        _XSD_PATH = Path(__file__).parent.parent / "data" / "chronorace.xsd"
        _logger = logging.getLogger(__name__)

        try:
            # xml_file is Shiny's input.file() list — extract the temp path
            file_path = xml_file[0]["datapath"]

            schema_doc = etree.parse(str(_XSD_PATH))
            schema = etree.XMLSchema(schema_doc)
            xml_doc = etree.parse(file_path)

            if not schema.validate(xml_doc):
                _logger.warning("Chronos XML failed XSD validation: %s", schema.error_log)
                return False
            _logger.info("Chronos XML validated successfully.")
            runners = []
            for athlete in xml_doc.xpath("//athlete"):
                bib = (athlete.findtext("bib") or "").strip()
                net = (athlete.findtext("net") or "0:00:00").strip()

                # Convert net time "hh:mm:ss" to total seconds (float)
                parts = net.split(":")
                if len(parts) == 3:
                    running_time = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                elif len(parts) == 2:
                    running_time = int(parts[0]) * 60 + float(parts[1])
                else:
                    running_time = float(parts[0])

                runner = Runner(serial_number=bib, running_time=running_time)
                runners.append(runner)

            ok_save = await self._cross_repo.add_runners_to_cross(cross_id, runners)
            if not ok_save:
                _logger.error("Failed to save runners to cross %d", cross_id)
                return False
            _logger.info("Added %d runners to cross %d", len(runners), cross_id)
            await self.add_audit_log(details=f"Added {len(runners)} runners to cross {cross_id}", action="add")
            return True

        except Exception as exc:
            _logger.error("Failed to read/validate Chronos XML: %s", exc)
            return False




