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
        return await self._test_repo.add_fitness_test_to_TestSession(param, cp)

    async def delete_fitness_test_from_test_session(self, param, param1):
        return await self._test_repo.delete_fitness_test_from_test_session(param, param1)

    async def update_fitness_test(self, param, cp):
        return await self._test_repo.update_fitness_test(param, cp)

    async def get_test_session_by_id(self, param):
        return await self._test_repo.get_test_session_by_id(param)

    async def add_test_session(self, ts):
        return await self._test_repo.add_test_session(ts)

    async def update_test_session(self, data):
        return await self._test_repo.update_test_session(data)

    async def delete_test_session(self, sel_id):
        return await self._test_repo.delete_test_session(sel_id)

    async def get_all_pti(self):
        return await self._test_repo.get_all_pti()
