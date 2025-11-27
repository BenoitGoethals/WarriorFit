from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.db.db_model import March
from warriorfit.data.db.march_repository import MarchRepository

from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service import Service


class ServiceMarch(Service):
    """
    Provides functionalities to manage and interact with military march records.

    The ServiceMarch class provides various methods for retrieving, adding,
    updating, and deleting march records. It serves as an intermediary layer
    that interacts with a repository to perform database operations.

    :ivar be_mil_service: Represents the military service instance this class
        interacts with.
    :type be_mil_service: MilitaryService
    """
    def __init__(self):
        super().__init__()
        self.__repo=MarchRepository()
        self.be_mil_service = MilitaryService()


    async def get_all_march(self):
        return await self.__repo.get_all_march()

    async def get_all_march_from_unit(self):
        return await self.__repo.get_all_march_by_unit_name(ApplicationConfig().own_unit)

    async def get_march_by_id(self, ind_id):
        return await self.__repo.get_march_by_id(ind_id)

    async def get_march_from_service_men(self,serial_number,this_year=True)->list[March]:
        return await self.__repo.get_all_march_form_service_men(serial_number,this_year)

    async def add_march(self, march):
        return await self.__repo.add_march(march)

    async def delete_march(self, ind_march):
        return await self.__repo.delete_march(ind_march)

    async def update_march(self,march):
        return await self.__repo.update_march(march)