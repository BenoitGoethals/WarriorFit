import datetime

from services.service_cross import ServiceCross
from services.service_test import ServiceTest


class CalendarEventsController:
    
    def __init__(self,) -> None:
        self._service_test = ServiceTest()
        self._service_cross = ServiceCross()
    
    async def events(self)-> list:
        events_to_post=[]
        sessions=await self._service_test.get_all_test_sessions()
        
        for session in sessions:
            session_date=session.datetime_start.date()
            session_date_end = session_date + datetime.timedelta(hours=2)
            # {"id": "id1_allday", "title": "Event 1", "start": "2023-07-03", "end": "2023-07-05"},
            events_to_post.append({"id": session.id, "title": session.type_test.name,
                                   "start": session.datetime_start.strftime("%Y-%m-%dT%H:%M:%S"),
                                   "end": session_date_end.strftime("%Y-%m-%dT%H:%M:%S")})
        
        crosses=await self._service_cross.get_all_crosses()
        for cross in crosses:
            cross_date=cross.datetime_start.date()
            cross_date_end=cross_date+ datetime.timedelta(hours=2)
            events_to_post.append({"id": cross.id, "title": "Cross", "start": cross_date.strftime("%Y-%m-%dT%H:%M:%S"), "end": cross_date_end.strftime("%Y-%m-%dT%H:%M:%S")})
        return events_to_post