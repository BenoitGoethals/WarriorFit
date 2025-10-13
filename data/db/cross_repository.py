from data.db.abc_repository import ABCRepository


class CrossRepository(ABCRepository):
    def __init__(self):
        super().__init__()