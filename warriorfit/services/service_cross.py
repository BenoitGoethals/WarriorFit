from typing import Any
from numpy import floating
from numpy.ma.extras import average
from warriorfit.core.Gender import Gender
from warriorfit.data.repositories.cross_repository import CrossRepository
from warriorfit.data.model.db_model import Cross, Runner, ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service import Service


class ServiceCross(Service):
    """
    Provides functionality for managing and retrieving data related to crosses
    and their associated runners. This class interfaces with a repository for
    persisting and fetching cross and runner-related information. It also offers
    compute capabilities for cross statistics, runner management, and auditing changes.

    :ivar be_mil_service: An instance of MilitaryService used for fetching
        service-related details.
    :type be_mil_service: MilitaryService
    """
    def __init__(self):
        super().__init__()
        self._cross_repo = CrossRepository()
        self.be_mil_service = MilitaryService()

    async def get_runner(self, runner_id:int) -> Runner | None:
        return await self._cross_repo.get_runner(runner_id)

    async def get_cross(self, cross_id) -> Cross | None:
        return await self._cross_repo.get_cross(cross_id)

    async def add(self, cross:Cross) -> Cross | None:
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
            await self.add_audit_log(details=f"Cross {id} deleted", action="delete")
        return deleted

    async def get_all_crosses(self) -> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_cross_by_id(self, id_nr, lazy=True) -> Cross | None:
        if lazy:
            return await self._cross_repo.get_cross(id_nr)
        else:
            return await self._cross_repo.get_cross_full(id_nr)

    async def get_cross_with_runners(self, id_nr) -> list[Runner]:
        return await self._cross_repo.get_runners_from_a_cross(id_nr)

    async def add_runner_to_cross(self, id_cross, r) -> Runner:
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

    async def remove_runner_from_cross(self, id_nr:int) -> bool:
        removed = await self._cross_repo.remove_runner(id_nr)
        if removed:
            await self.add_audit_log(
                details=f"Runner {id_nr} removed from cross", action="delete"
            )
        return removed

    async def update_cross(self, cross:Cross):
        updated = await self._cross_repo.update_cross(cross)
        if updated:
            await self.add_audit_log(
                details=f"Cross {cross} updated", action="update"
            )
        return updated

    async def exist_in_cross(self, serial, cross_id):
        return await self._cross_repo.exist_in_cross(serial, cross_id)

    async def get_cross_stats(self):
        """
        Asynchronously fetches and processes statistical data for all cross events.

        This method retrieves a list of all cross events and calculates various statistical
        data such as average time, gap time, best time, age group data, gender-based times,
        and the top 10 runners based on running time. Returns a tuple of these statistics.

        :return: A tuple containing the following statistics:
            - Average time across all cross events (float)
            - Gap time across all cross events (float)
            - Best time in all cross events (float)
            - Age group statistics (dict)
            - Gender-based times in cross events as a tuple of (float, float)
            - Top 10 runners based on running time (dict)
        :rtype: tuple
        """
        all_cross: list[Cross] = await self._cross_repo.get_all_cross(lazy=False)
        if len(all_cross) > 0:
            return (
                await self.get_average(all_cross) if all_cross else 0.0,
                await self.get_gap_time(all_cross)if all_cross else 0.0,
                await self.get_best_time(all_cross) if all_cross else 0.0,
                await self.get_age_group(all_cross) if all_cross else {},
                await self.get_gender_time(all_cross) if all_cross else (0.0, 0.0),
                await self.get_top_10_runners_based_on_running_time(all_cross) if all_cross else {},
            )
        else:
          return 0.0, 0.0, 0.0, {}, (0.0, 0.0), {}

    async def get_average(self, all_cross) -> float:
        average = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                average += runner.running_time
        average = average / len(all_cross)
        return average

    async def get_gap_time(self, all_cross):
        """
        Computes the time gap between the fastest and slowest runner across a collection
        of given cross groups. If there are no runners, the gap is defaulted to 0.0.

        :param all_cross: A list of cross objects, each containing a collection of
            runners with their running times
        :type all_cross: list
        :return: The calculated time gap between the fastest and slowest runner's
            running times. Returns 0.0 if no valid runners exist.
        :rtype: float
        """
        worst_time = float("-inf")
        best_time = float("inf")

        for cross in all_cross:
            for runner in cross.runners:
                if runner.running_time > worst_time:
                    worst_time = runner.running_time
                if runner.running_time < best_time:
                    best_time = runner.running_time

        return (
            worst_time - best_time
            if worst_time != float("-inf") and best_time != float("inf")
            else 0.0
        )

    async def get_best_time(self, all_cross):

        best_time = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                if runner.running_time > best_time:
                    best_time = runner.running_time
        return best_time

    async def get_age_group(self, all_cross):
        """
        Calculates age group distributions based on a list of cross objects. The method uses
        a helper function to determine the age group of a serviceman based on their age. The
        distribution is returned as a dictionary where keys are age groups and values are
        counts of servicemen in each group.

        :param all_cross: List of cross objects containing runner information.
        :type all_cross: list
        :return: A dictionary containing age group distribution of servicemen.
        :rtype: dict[str, int]
        """
        age_groups: dict[str, int] = {}

        def bucket(age: int) -> str:
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

        missing: list[str] = []
        for cross in all_cross:
            for r in getattr(cross, "runners", []):
                sm = await self.be_mil_service.get_servicemen_by_serial(r.serial_number)
                if sm is None:
                    missing.append(r.serial_number)
                    continue
                try:
                    g = bucket(sm.age_from_birthdate())
                    age_groups[g] = age_groups.get(g, 0) + 1
                except Exception:
                    missing.append(r.serial_number)

        return age_groups

    async def get_gender_time(self, all_cross) -> tuple[floating[Any], floating[Any]]:
        """
        Calculates the average running times for male and female runners from a list of cross
        sessions.

        :param all_cross: A list of cross session objects. Each cross object should contain
            data about the runners and their performance.
        :type all_cross: list

        :return: A tuple containing the average running time for female runners and the average
            running time for male runners. Each value will be a floating-point number. If no
            female or male runners are found, the corresponding value will default to 0.0.
        :rtype: tuple[float, float]
        """
        all_runners_f = []
        all_runners_m = []
        for cross in all_cross:
            for runner in cross.runners:
                service_man: ServiceMen = (
                    await self.be_mil_service.get_servicemen_by_serial(
                        runner.serial_number
                    )
                )
                if service_man is None:
                    continue
                if service_man.gender == Gender.F:
                    all_runners_f.append(runner.running_time)
                else:
                    all_runners_m.append(runner.running_time)

        return average(all_runners_f) if all_runners_f else 0.0, (
            average(all_runners_m) if all_runners_m else 0.0
        )

    async def get_top_10_runners_based_on_running_time(self, all_cross):
        """
        Asynchronously retrieves the top 10 runners ordered by their running times for
        each unique distance. This function groups runners based on the distance they
        covered, and then sorts them based on their running times in ascending order
        (best times first). Only the top 10 runners for each distance are included
        in the result.

        :param all_cross: List of cross objects. Each cross object contains a distance
            attribute and a list of runners. Each runner must have a running_time
            attribute indicating the running time of the runner.
        :type all_cross: list
        :return: A dictionary where the keys are unique distances and the values
            are lists of the top 10 runners sorted by their running times.
        :rtype: dict
        """
        top_runners_by_distance = {}

        # Group runners by distance
        for cross in all_cross:
            distance = cross.distance
            if distance not in top_runners_by_distance:
                top_runners_by_distance[distance] = []
            top_runners_by_distance[distance].extend(cross.runners)

        # Sort and get top 10 for each distance
        for distance in top_runners_by_distance:
            top_runners_by_distance[distance].sort(
                key=lambda x: x.running_time
            )  # Sort ascending (best times first)
            top_runners_by_distance[distance] = top_runners_by_distance[distance][:10]

        return top_runners_by_distance
