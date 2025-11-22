import pandas as pd

from config.appliccation_config import ApplicationConfig
from services.military_service import MilitaryService
from services.service_test import ServiceTest


class StatusLogUserController:
    def __init__(self) -> None:
        self._service = ServiceTest()
        self.be_mil_service = MilitaryService()
        self.unit_name = ApplicationConfig().own_unit
        self._mils = None
        self._all_military_own_unit = None

    async def get_upcoming_session(self, serial_number_pti)->pd.DataFrame:
        sessions=await self._service.get_upcoming_session_for_pti(serial_number_pti)
        return pd.DataFrame(sessions)


