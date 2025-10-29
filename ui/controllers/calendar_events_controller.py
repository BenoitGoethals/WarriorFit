import datetime

from core.type_fitness_test import TypeFitnessTest
from services.service_cross import ServiceCross
from services.service_test import ServiceTest


class CalendarEventsController:
    
    def __init__(self,) -> None:
        self._service_test = ServiceTest()
        self._service_cross = ServiceCross()
    
    async def events(self)-> list:
        """
        Asynchronously retrieves and processes event data for fitness tests and cross-training sessions.
        This method categorizes sessions by type, calculates their duration, and formats the event
        details in preparation for posting. Events for both fitness tests and cross-training are
        aggregated into a single list.

        :return: A list of dictionaries, each representing an event with details such as
                event ID, title, start time, end time, background color, border color, and text color.
        :rtype: list
        """
        events_to_post=[]
        sessions=await self._service_test.get_all_test_sessions()
        for session in sessions:
            session_date=session.datetime_start
            if session.type_test == TypeFitnessTest.PHEF or session.type_test == TypeFitnessTest.FUNCTIONAL:
                x=3
                color_bg, color_border, color_text = "#28a745", "#28a745", "white"
            elif session.type_test == TypeFitnessTest.COMBAT:
                x=5
                color_bg, color_border, color_text = "#dc3545", "#dc3545", "white"
            else:
                x=1
                color_bg, color_border, color_text = "#6c757d", "#6c757d", "white"
            session_date_end = session_date + datetime.timedelta(hours=x)
            if session.serial_number_pti:
                pti=session.serial_number_pti
            else:
                pti="N/A"

            events_to_post.append({"id": session.id, "title": session.type_test.name + "  PTI : "+pti ,
                                   "start": session.datetime_start.strftime("%Y-%m-%dT%H:%M:%S"),
                                   "end": session_date_end.strftime("%Y-%m-%dT%H:%M:%S"),
                                   "backgroundColor": color_bg,
                                   "borderColor": color_border,
                                   "textColor": color_text,
                                   })
        
        crosses=await self._service_cross.get_all_crosses()
        for cross in crosses:
            cross_date=cross.datetime_start
            cross_date_end=cross_date+ datetime.timedelta(hours=2)
            events_to_post.append({"id": cross.id, "title": "Cross", "start": cross_date.strftime("%Y-%m-%dT%H:%M:%S"), "end": cross_date_end.strftime("%Y-%m-%dT%H:%M:%S")})
        return events_to_post