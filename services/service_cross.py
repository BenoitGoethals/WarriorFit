from services.service import Service


class ServiceCross(Service):
    def __init__(self):
        super().__init__()

    def get(self, Runner, runner_id):
        pass

    def add(self, cross):
        pass

    def list_all(self, Cross):
        pass

    def delete(self, runner):
        pass

    async def get_all_crosses(self):
        pass

    async def get_cross_by_id(self, param):
        pass

    async def get_cross_with_runners(self, param):
        pass

    async def add_runner_to_cross(self, param, r):
        pass

    async def update_runner(self, param, r):
        pass

    async def remove_runner_from_cross(self, param, param1):
        pass