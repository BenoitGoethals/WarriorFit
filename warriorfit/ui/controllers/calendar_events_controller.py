import datetime

from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.services.service_cross import ServiceCross
from warriorfit.services.service_test import ServiceTest


class CalendarEventsController:
    """
    Handles the retrieval and processing of calendar events for fitness tests and cross-training sessions.

    This class provides functionality to gather sessions, categorize them by type, calculate their
    respective durations, and format the event details for external usage. The resulting events
    include details on attributes such as ID, title, start and end times, and display colors, ensuring
    they are properly formatted for posting or rendering in a calendar interface.
    """

    def __init__(
        self,
        test_service: ServiceTest = None,
        cross_service: ServiceCross = None,
    ) -> None:
        self._service_test = test_service if test_service is not None else ServiceTest()
        self._service_cross = (
            cross_service if cross_service is not None else ServiceCross()
        )

    async def events(self, serial_number_pti: str = None) -> list:
        """
        Asynchronously retrieves and processes event data for fitness tests and cross-training sessions.
        This method categorizes sessions by type, calculates their duration, and formats the event
        details in preparation for posting. Events for both fitness tests and cross-training are
        aggregated into a single list.

        :return: A list of dictionaries, each representing an event with details such as
                event ID, title, start time, end time, background color, border color, and text color.
        :rtype: list
        """
        events_to_post = []
        if serial_number_pti:
            sessions = await self._service_test.get_all_test_sessions_for_pti(
                serial_number_pti
            )
        else:
            sessions = await self._service_test.get_all_test_sessions()
        for session in sessions:
            session_date = session.datetime_start
            if (
                session.type_test == TypeFitnessTest.PHEF
                or session.type_test == TypeFitnessTest.FUNCTIONAL
            ):
                x = 3
                color_bg, color_border, color_text = "#28a745", "#28a745", "white"
            elif session.type_test == TypeFitnessTest.COMBAT:
                x = 5
                color_bg, color_border, color_text = "#dc3545", "#dc3545", "white"
            else:
                x = 1
                color_bg, color_border, color_text = "#6c757d", "#6c757d", "white"
            session_date_end = session_date + datetime.timedelta(hours=x)
            if session.serial_number_pti:
                pti = session.serial_number_pti
            else:
                pti = "N/A"

            events_to_post.append(
                {
                    "id": session.id,
                    "title": session.type_test.name + "  PTI : " + pti,
                    "start": session.datetime_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "end": session_date_end.strftime("%Y-%m-%dT%H:%M:%S"),
                    "backgroundColor": color_bg,
                    "borderColor": color_border,
                    "textColor": color_text,
                }
            )

        crosses = await self._service_cross.get_all_crosses()
        for cross in crosses:
            cross_date = cross.datetime_start
            cross_date_end = cross_date + datetime.timedelta(hours=2)  # type: ignore[operator]
            events_to_post.append(
                {
                    "id": cross.id,
                    "title": "Cross",
                    "start": cross_date.strftime("%Y-%m-%dT%H:%M:%S"),  # type: ignore[attr-defined]
                    "end": cross_date_end.strftime("%Y-%m-%dT%H:%M:%S"),  # type: ignore[attr-defined]
                }
            )
        return events_to_post
