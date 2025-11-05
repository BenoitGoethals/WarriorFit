from typing import Any

from numpy import floating
from numpy.ma.extras import average

from military_api_rest.service_men_be import ServiceMen
from data.db.cross_repository import CrossRepository
from data.db.db_model import Cross, Runner
from services.be_mil_service import BEMILService
from services.service import Service


class ServiceCross(Service):
    def __init__(self):
        super().__init__()
        self._cross_repo = CrossRepository()
        self.be_mil_service = BEMILService()

    async def get_runner(self, runner_id) -> Runner | None:
        return await self._cross_repo.get_runner(runner_id)

    async def get_cross(self, cross_id) -> Cross | None:
        return await self._cross_repo.get_cross(cross_id)

    async def add(self, cross) -> Cross | None:
        added = await self._cross_repo.add_cross(cross)
        if added:
            await self.add_audit_log(details=f"Cross {cross.name} added", action="add")
        return added

    async def list_all(self) -> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_all_runners(self) -> list[Runner]:
        return await self._cross_repo.get_all_runners()

    async def delete_cross(self, id: float) -> bool:
        deleted = await self._cross_repo.remove_cross(id)
        if deleted:
            await self.add_audit_log(details=f"Cross {id} deleted", action="delete")
        return deleted

    async def get_all_crosses(self) -> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_cross_by_id(self, id, lazy=True) -> Cross | None:
        if lazy:
            return await self._cross_repo.get_cross(id)
        else:
            return await self._cross_repo.get_cross_full(id)

    async def get_cross_with_runners(self, id) -> list[Runner]:
        return await self._cross_repo.get_runners_from_a_cross(id)

    async def add_runner_to_cross(self, id_cross, r) -> Runner:
        r.cross_id = id_cross
        added = await self._cross_repo.add_runner_to_cross(id_cross, r)
        if added:
            await self.add_audit_log(details=f"Runner {r.serial_number} added to cross {id_cross}", action="add")
        return added

    async def update_runner(self, id: int, r: Runner) -> Runner:
        updated = await self._cross_repo.update_runner(id, r)
        if updated:
            await self.add_audit_log(details=f"Runner {r.serial_number} updated in cross {id}", action="update")
        return updated

    async def remove_runner_from_cross(self, id) -> bool:
        removed = await self._cross_repo.remove_runner(id)
        if removed:
            await self.add_audit_log(details=f"Runner {id} removed from cross", action="delete")
        return removed

    async def update_cross(self, cross):
        updated = await self._cross_repo.update_cross(cross)
        if updated:
            await self.add_audit_log(details=f"Cross {cross.name} updated", action="update")
        return updated

    async def exist_in_cross(self, serial, cross_id):
        return await self._cross_repo.exist_in_cross(serial, cross_id)

    async def get_cross_stats(self):
        all_cross: list[Cross] = await self._cross_repo.get_all_cross(lazy=False)
        if len(all_cross) > 0:
            return (await self.get_average(all_cross), await self.get_gap_time(all_cross),
                    await self.get_best_time(all_cross), await self.get_age_group(all_cross),
                    await self.get_gender_time(all_cross),
                    await self.get_top_10_runners_based_on_running_time(all_cross))
        else:
            return None

    async def get_average(self, all_cross) -> float:
        average = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                average += runner.running_time
        average = average / len(all_cross)
        return average

    async def get_gap_time(self, all_cross):

        worst_time = float('-inf')
        best_time = float('inf')

        for cross in all_cross:
            for runner in cross.runners:
                if runner.running_time > worst_time:
                    worst_time = runner.running_time
                if runner.running_time < best_time:
                    best_time = runner.running_time

        return worst_time - best_time if worst_time != float('-inf') and best_time != float('inf') else 0.0

    async def get_best_time(self, all_cross):

        best_time = 0.0
        for cross in all_cross:
            for runner in cross.runners:
                if runner.running_time > best_time:
                    best_time = runner.running_time
        return best_time

    async def get_age_group(self, all_cross):

        age: dict = {}
        #group first runners age group by 5 years group getting from self.be_mil_service.get_be_mil_by_id(runner.serial_number)
        for x in all_cross:
            for y in x.runners:
                service_man: ServiceMen = await self.be_mil_service.get_be_mil_by_id(y.serial_number)
                age_s = service_man.age_from_birthdate()
                if age_s not in age:
                    age[age_s] = 1
                else:
                    age[age_s] += 1
        return age

    async def get_gender_time(self, all_cross) -> tuple[floating[Any], floating[Any]]:
        all_runners_f = []
        all_runners_m = []
        for cross in all_cross:
            for runner in cross.runners:
                service_man: ServiceMen = await self.be_mil_service.get_be_mil_by_id(runner.serial_number)
                if service_man.gender == "F":
                    all_runners_f.append(runner.running_time)
                else:
                    all_runners_m.append(runner.running_time)

        return average(all_runners_f) if all_runners_f else 0.0, average(all_runners_m) if all_runners_m else 0.0


    async def get_top_10_runners_based_on_running_time(self, all_cross):
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
                key=lambda x: x.running_time)  # Sort ascending (best times first)
            top_runners_by_distance[distance] = top_runners_by_distance[distance][:10]

        return top_runners_by_distance