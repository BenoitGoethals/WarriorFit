from data.db.mars_repository import MarsRepository
from services.military_service import MilitaryService
from services.service import Service


class ServiceMars(Service):
    def __init__(self):
        super().__init__()
        self.__repo=MarsRepository()
        self.be_mil_service = MilitaryService()


    def get_all_mars(self):
        return self.__repo.get_all_mars()

    def get_mars_by_id(self, ind_id):
        return self.__repo.get_mars_by_id(ind_id)

    def add_mars(self, mars):
        ...

    def delete_mars(self, ind_mars):
        ...

    def update_mars(self,id_mars):
        ...