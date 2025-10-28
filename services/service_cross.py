from watchfiles import awatch

from data.db.cross_repository import CrossRepository
from data.db.db_model import Cross,Runner
from services.service import Service


class ServiceCross(Service):
    def __init__(self):
        super().__init__()
        self._cross_repo = CrossRepository()

    async def get_runner(self,  runner_id)-> Runner | None:
        return await self._cross_repo.get_runner(runner_id)

    async def get_cross(self, cross_id)-> Cross | None:
        return await self._cross_repo.get_cross(cross_id)

    async def add(self, cross)-> Cross | None:
        added = await self._cross_repo.add_cross(cross)
        if added:
            await self.add_audit_log(details=f"Cross {cross.name} added",action="add")
        return added

    async def list_all(self)-> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_all_runners(self)-> list[Runner]:
        return await self._cross_repo.get_all_runners()

    async def delete_cross(self, id: float)-> bool:
        deleted= await self._cross_repo.remove_cross(id)
        if deleted:
            await self.add_audit_log(details=f"Cross {id} deleted",action="delete")
        return deleted

    async def get_all_crosses(self)-> list[Cross]:
        return await self._cross_repo.get_all_cross()

    async def get_cross_by_id(self, id, lazy=True)-> Cross | None:
        if lazy:
            return await self._cross_repo.get_cross(id)
        else:
            return await self._cross_repo.get_cross_full(id)

    async def get_cross_with_runners(self, id)-> list[Runner]:
        return await self._cross_repo.get_runners_from_a_cross(id)

    async def add_runner_to_cross(self, id_cross, r)-> Runner:
        r.cross_id = id_cross
        added= await self._cross_repo.add_runner_to_cross(id_cross,r)
        if added:
            await self.add_audit_log(details=f"Runner {r.serial_number} added to cross {id_cross}",action="add")
        return added

    async def update_runner(self,id:int, r:Runner)->Runner:
        updated= await self._cross_repo.update_runner(id, r)
        if updated:
            await self.add_audit_log(details=f"Runner {r.serial_number} updated in cross {id}",action="update")
        return updated

    async def remove_runner_from_cross(self,id)->bool:
        removed= await self._cross_repo.remove_runner(id)
        if removed:
            await self.add_audit_log(details=f"Runner {id} removed from cross",action="delete")
        return removed

    async def update_cross(self, cross):
        updated = await self._cross_repo.update_cross(cross)
        if updated:
            await self.add_audit_log(details=f"Cross {cross.name} updated",action="update")
        return updated

    async def exist_in_cross(self, serial, cross_id):
        return await self._cross_repo.exist_in_cross(serial, cross_id)