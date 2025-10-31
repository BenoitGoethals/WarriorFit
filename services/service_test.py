from data.db.db_model import TestSession
from data.db.fitness_test_repository import FitnessTestRepository
from services.service import Service


class TestService:
    pass


class ServiceTest(Service):
    def __init__(self):
        super().__init__()
        self._test_repo=FitnessTestRepository()


    async def get_all_combat_test(self, id):
        return await self._test_repo.get_all_combat_test(id)

    async def get_all_functional_test(self, id):
        return await self._test_repo.get_all_functional_test(id)

    async def get_all_phef(self, id):
        return await self._test_repo.get_all_phef(id)



    async def get_all_combat_swimming_test(self, id):
        return await self._test_repo.get_all_combat_swimming_test(id)

    async def get_all_test_sessions_type_fitnessTest(self, type_test, this_year):
        return await self._test_repo.get_all_test_sessions_type_fitnessTest(type_test, True)

    async def get_all_test_sessions(self):
        return await self._test_repo.get_all_test_sessions()

    async def add_fitness_test_to_TestSession(self, param, cp):
        add_test= await self._test_repo.add_fitness_test_to_TestSession(param, cp)
        if add_test:
            await self.add_audit_log(details=f"Fitness test {cp.serial_number} {cp.type} added to test session {param}",action="add")
        return add_test

    async def delete_fitness_test_from_test_session(self, param, param1):
        deleted= await self._test_repo.delete_fitness_test_from_test_session(param, param1)
        if deleted:
            await self.add_audit_log(details=f"Fitness test {param1} deleted from test session {param}",action="delete")
        return deleted

    async def update_fitness_test(self, param, cp):
        updated= await self._test_repo.update_fitness_test(param, cp)
        if updated:
            await self.add_audit_log(details=f"Fitness test {cp.serial_number}  {cp.type} updated in test session {param}",action="update")
        return updated

    async def get_test_session_by_id(self, param):
        return await self._test_repo.get_test_session_by_id(param)

    async def add_test_session(self, ts):
        added_test:TestSession= await self._test_repo.add_test_session(ts)
        if added_test:
            await self.add_audit_log(details=f"Test session {ts.id} {added_test.type_test.name} added",action="add")
        return added_test

    async def update_test_session(self, data):
        updated= await self._test_repo.update_test_session(data)
        if updated:
            await self.add_audit_log(details=f"Test session {data.id}  {updated}updated",action="update")
        return updated

    async def delete_test_session(self, sel_id):
        deleted=  await self._test_repo.delete_test_session(sel_id)
        if deleted:
            await self.add_audit_log(details=f"Test session {sel_id} deleted",action="delete")
        return deleted

    async def get_all_pti(self):
        return await self._test_repo.get_all_pti()
