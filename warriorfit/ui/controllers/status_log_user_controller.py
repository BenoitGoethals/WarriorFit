import pandas as pd
from warriorfit.services.service_test import ServiceTest


class StatusLogUserController:
    def __init__(self) -> None:
        self._service = ServiceTest()


    async def get_upcoming_session(self, serial_number_pti)->pd.DataFrame:
        sessions = await self._service.get_upcoming_session_for_pti(serial_number_pti)
        if not sessions:
            return pd.DataFrame(columns=["Date", "Type", "Description"])
        data = []
        for s in sessions:
            type_str = s.type_test.name if hasattr(s.type_test, "name") else str(s.type_test)
            data.append({
                "Date": s.datetime_start.strftime("%Y-%m-%d %H:%M") if s.datetime_start else "",
                "Type": type_str,
                "Description": s.description or ""
            })

        return pd.DataFrame(data)


