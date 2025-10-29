
import datetime
from typing import Any, Optional
from shiny import ui, reactive
from shiny_calendar import render_shiny_calendar, shiny_calendar, shiny_calendar_call_js_func

from ui.controllers.calendar_events_controller import CalendarEventsController


class CalendarPage:
    TITLE = "Calendar"

    def __init__(self) -> None:
        self._controller =CalendarEventsController()

    def get_ui(self):
        # Plain page content, not a nav panel/tab item
        return ui.page_fluid(
            ui.h2(CalendarPage.TITLE),
            ui.page_fillable(
                ui.layout_columns(
                    ui.card(
                        ui.card_header(CalendarPage.TITLE),

                        shiny_calendar("my_calendar"),
                    ),
                    col_widths=(12,),
                ),
                fillable=True,
            ),
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        @render_shiny_calendar
        async def my_calendar():
            # IMPORTANT: Always return a list, not a dict
            return [
                {
                    "initialView": "timeGridWeek",
                    "initialDate": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "locale": "en-gb",  # 24h
                    "timeZone": "local",
                    "slotLabelFormat": {"hour": "2-digit", "minute": "2-digit", "hour12": False},
                    "eventTimeFormat": {"hour": "2-digit", "minute": "2-digit", "hour12": False},
                    "editable": False,
                    "selectable": True,
                    "events": await self._controller.events()
                }
            ]

        # Register the output so Shiny calls it
        output.my_calendar = my_calendar

        @reactive.effect
        @reactive.event(input.button_add_event)
        async def _add_event():
            now = datetime.datetime.now()
            date_start = now.strftime("%Y-%m-%dT%H:%M:%S")
            date_end = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
            js_func = (
                f"calendar.addEvent({{id: 'someId', title: 'some event title', "
                f"start: '{date_start}', end: '{date_end}'}});"
            )
            await shiny_calendar_call_js_func(session, "my_calendar", js_func)

        @reactive.effect
        async def _handle_calendar_events():
            msg = input.my_calendar()
            if not isinstance(msg, dict):
                return
            t = msg.get("type")
            if t == "eventClick":
                event_id = msg.get("data", {}).get("event", {}).get("id")
                if not event_id:
                    return
                js_func = f"""
                    const calEvent = calendar.getEventById("{event_id}");
                    if (calEvent) {{
                        calEvent.setProp("backgroundColor", "red");
                        calEvent.setProp("borderColor", "red");
                    }}
                """
                await shiny_calendar_call_js_func(session, "my_calendar", js_func)


_page_instance: Optional[CalendarPage] = None


def _get_page() -> CalendarPage:
    global _page_instance
    if _page_instance is None:
        _page_instance = CalendarPage()
    return _page_instance


def get_ui():
    # Return plain UI so the caller can place it outside any navset
    return _get_page().get_ui()


def server(input, output, session):
    # Properly call the bound instance method
    _get_page().server(input, output, session)