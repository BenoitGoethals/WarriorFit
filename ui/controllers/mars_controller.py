from services.service_mars import ServiceMars


class MarsController:

    def __init__(self,) -> None:
        self._service = ServiceMars()

    async def get_all_mars(self):
        return await self._service.get_all_mars()

    async def add_mars(self, new_mars):
        pass

    async def update_mars(self, updated_mars):
        pass

    async def delete_mars(self, current_id):
        pass