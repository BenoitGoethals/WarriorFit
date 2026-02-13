import datetime
from typing import Any, Optional
from shiny import ui, reactive
from shiny_calendar import (
    render_shiny_calendar,
    shiny_calendar,
    shiny_calendar_call_js_func,
)

from warriorfit.ui.controllers.calendar_events_controller import (
    CalendarEventsController,
)
from warriorfit.ui.pages.page import Page
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container
from warriorfit.ui.user_store import UserStore


class CalendarPage(Page):
    TITLE = "Calendar"
    TITLE_PERSONAL = "Personal Calendar"

    @inject
    def __init__(self, controller: CalendarEventsController = Provide[Container.calendar_events_controller]) -> None:
        super().__init__()
        self._refresh_counter = reactive.Value(0)
        self._controller = controller
        self._all = True

    def get_ui_all_test(self):
        self._all = True
        return ui.page_fluid(
            ui.page_fillable(
                ui.layout_columns(
                    ui.card(
                        ui.card_header(CalendarPage.TITLE),
                        shiny_calendar("my_calendar"),
                    ),
                ),
            ),
        )

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        self._all = False
        return ui.page_fluid(
            ui.page_fillable(
                ui.layout_columns(
                    ui.card(
                        ui.card_header(CalendarPage.TITLE_PERSONAL),
                        shiny_calendar("my_calendar"),
                    ),
                ),
            ),
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        @render_shiny_calendar
        async def my_calendar():
            # Depend on the refresh counter so this is re-run when it changes
            _ = self._refresh_counter()

            # IMPORTANT: Always return a list, not a dict
            return [
                {
                    "initialView": "timeGridWeek",
                    "initialDate": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "locale": "en-gb",  # 24h
                    "timeZone": "local",
                    "slotLabelFormat": {
                        "hour": "2-digit",
                        "minute": "2-digit",
                        "hour12": False,
                    },
                    "eventTimeFormat": {
                        "hour": "2-digit",
                        "minute": "2-digit",
                        "hour12": False,
                    },
                    "editable": False,
                    "selectable": True,
                    "events": (
                        await self._controller.events(
                            str(UserStore.get_user().serial_number)
                        )
                        if not self._all
                        else await self._controller.events()
                    ),
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


def get_ui(all_test: bool = True):
    if all_test:

        return _get_page().get_ui_all_test()
    return _get_page().get_ui()


def server(input, output, session):
    # Properly call the bound instance method
    _get_page().server(input, output, session)


def refresh():
    """
    Force the calendar to re-evaluate (e.g. when opening the modal/page).
    """
    page = _get_page()
    page._refresh_counter.set(page._refresh_counter() + 1)
