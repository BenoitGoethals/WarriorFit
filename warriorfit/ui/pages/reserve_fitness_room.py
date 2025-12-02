from shiny import ui, render, reactive
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
import calendar

from warriorfit.data.model.db_model import Room, Reservation
from warriorfit.ui.controllers.reserve_fitness_room_controller import ReserveFitnessRoomController
from warriorfit.ui.pages.page import Page



class ReserveFitnessRoomPage(Page):

    def __init__(self):
        # Define available rooms
        # self.rooms = [
        #     Room(id=1, name="Sports Hall A", capacity=20, location="Floor 1"),
        #     Room(id=2, name="Sports Hall B", capacity=15, location="Floor 1"),
        #     Room(id=3, name="Fitness Studio", capacity=10, location="Floor 2"),
        #     Room(id=4, name="Yoga Room", capacity=12, location="Floor 2")
        # ]
        self.rooms:List[Room]=[]
        self._controller:ReserveFitnessRoomController = ReserveFitnessRoomController()




        # Time slots
        self.time_slots = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00",
                           "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Reserve Room",
            ui.tags.style("""
                .card { margin-bottom: 20px; }
                .room-card { 
                    border: 2px solid #e5e7eb; 
                    border-radius: 8px; 
                    padding: 15px; 
                    margin-bottom: 10px;
                    background-color: #f9fafb;
                }
                .room-card.selected { 
                    border-color: #4f46e5; 
                    background-color: #eef2ff;
                }
                .reservation-card {
                    background-color: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 10px;
                    margin-bottom: 8px;
                }
                .calendar-container {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .calendar-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .calendar-table th {
                    background-color: #4f46e5;
                    color: white;
                    padding: 12px;
                    text-align: center;
                    font-weight: 600;
                }
                .calendar-table td {
                    border: 1px solid #e5e7eb;
                    padding: 8px;
                    text-align: center;
                    height: 100px;
                    vertical-align: top;
                    cursor: pointer;
                    position: relative;
                }
                .calendar-table td:hover {
                    background-color: #f3f4f6;
                }
                .calendar-table td.other-month {
                    background-color: #f9fafb;
                    color: #9ca3af;
                }
                .calendar-table td.today {
                    background-color: #fef3c7;
                    font-weight: bold;
                }
                .calendar-table td.selected {
                    background-color: #dbeafe;
                    border: 2px solid #3b82f6;
                }
                .day-number {
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 5px;
                }
                .reservation-dot {
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    margin: 2px;
                }
                .calendar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .calendar-month {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #1f2937;
                }
                .btn-success { background-color: #10b981; color: white; }
                .btn-danger { background-color: #ef4444; color: white; }
                .btn-primary { background-color: #4f46e5; color: white; }
                h2 { color: #1f2937; margin-top: 20px; }
                .room-color-1 { background-color: #ef4444; }
                .room-color-2 { background-color: #3b82f6; }
                .room-color-3 { background-color: #10b981; }
                .room-color-4 { background-color: #f59e0b; }
                .reservation-badge {
                    font-size: 0.7rem;
                    padding: 2px 6px;
                    border-radius: 4px;
                    color: white;
                    display: inline-block;
                    margin: 2px;
                }
                .modal-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .modal-content {
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: #6b7280;
                }
                .modal-close:hover {
                    color: #1f2937;
                }
                .week-calendar {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.85rem;
                }
                .week-calendar th {
                    background-color: #4f46e5;
                    color: white;
                    padding: 10px 5px;
                    text-align: center;
                    font-weight: 600;
                    position: sticky;
                    top: 0;
                    z-index: 10;
                }
                .week-calendar td {
                    border: 1px solid #e5e7eb;
                    padding: 2px;
                    height: 60px;
                    vertical-align: top;
                    position: relative;
                }
                .week-calendar td.time-label {
                    background-color: #f9fafb;
                    font-weight: 600;
                    text-align: center;
                    width: 80px;
                    padding: 5px;
                }
                .week-calendar td.day-cell {
                    cursor: pointer;
                    background-color: white;
                }
                .week-calendar td.day-cell:hover {
                    background-color: #f3f4f6;
                }
                .week-calendar td.day-cell.past {
                    background-color: #f9fafb;
                }
                .reservation-block {
                    position: absolute;
                    left: 2px;
                    right: 2px;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 0.75rem;
                    overflow: hidden;
                    cursor: pointer;
                    border-left: 3px solid;
                }
                .reservation-block:hover {
                    opacity: 0.8;
                }
                .reservation-block.room-1 {
                    background-color: #fecaca;
                    border-color: #ef4444;
                    color: #7f1d1d;
                }
                .reservation-block.room-2 {
                    background-color: #bfdbfe;
                    border-color: #3b82f6;
                    color: #1e3a8a;
                }
                .reservation-block.room-3 {
                    background-color: #bbf7d0;
                    border-color: #10b981;
                    color: #064e3b;
                }
                .reservation-block.room-4 {
                    background-color: #fed7aa;
                    border-color: #f59e0b;
                    color: #78350f;
                }
                .week-header-date {
                    font-size: 0.75rem;
                    display: block;
                    color: #d1d5db;
                }
            """),

            ui.h2("🗓️ PTI Room Booking System"),

            ui.navset_tab(
                ui.nav_panel(
                    "📅 Weekly Calendar",
                    ui.div(
                        ui.layout_columns(
                            ui.input_action_button("prev_week", "◀ Previous Week", class_="btn-primary"),
                            ui.output_text("current_week"),
                            ui.input_action_button("next_week", "Next Week ▶", class_="btn-primary"),
                            col_widths=[3, 6, 3]
                        ),
                        ui.layout_columns(
                            ui.input_action_button("open_modal", "➕ New Reservation", class_="btn-success mt-3"),
                            col_widths=[12]
                        ),
                        ui.hr(),
                        ui.output_ui("weekly_calendar_view"),
                        ui.output_ui("reservation_modal"),
                        class_="calendar-container"
                    )
                ),

                ui.nav_panel(
                    "📅 Monthly Calendar",
                    ui.div(
                        ui.layout_columns(
                            ui.input_action_button("prev_month", "◀ Previous", class_="btn-primary"),
                            ui.output_text("current_month"),
                            ui.input_action_button("next_month", "Next ▶", class_="btn-primary"),
                            col_widths=[2, 8, 2]
                        ),
                        ui.hr(),
                        ui.output_ui("calendar_view"),
                        class_="calendar-container"
                    )
                ),

                ui.nav_panel(
                    "📋 List View",
                    ui.card(
                        ui.card_header("Reservations by Date"),
                        ui.input_date("filter_date", "Filter date:", value=datetime.now().date()),
                        ui.output_ui("reservations_list")
                    )
                )
            )
        )

    def server(self, input, output, session):
        # Reactive values
        reservations: reactive.Value[List[Reservation]] = reactive.Value([])
        selected_room = reactive.Value(None)
        current_month_val = reactive.Value(datetime.now().month)
        current_year_val = reactive.Value(datetime.now().year)
        current_week_start = reactive.Value(datetime.now().date() - timedelta(days=datetime.now().weekday()))
        selected_calendar_date = reactive.Value(None)
        show_modal = reactive.Value(False)


        @reactive.Effect
        async def _load_rooms():
            self.rooms=await self._controller.rooms()

        @output
        @render.text
        def current_week():
            week_start = current_week_start()
            week_end = week_start + timedelta(days=6)
            return f"Week: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"

        @output
        @render.text
        def current_month():
            month_names = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            return f"{month_names[current_month_val() - 1]} {current_year_val()}"

        @reactive.Effect
        @reactive.event(input.prev_week)
        def _():
            current_week_start.set(current_week_start() - timedelta(days=7))

        @reactive.Effect
        @reactive.event(input.next_week)
        def _():
            current_week_start.set(current_week_start() + timedelta(days=7))

        @output
        @render.ui
        def weekly_calendar_view():
            week_start = current_week_start()
            all_res = reservations.get()
            today = datetime.now().date()

            # Generate week days (Monday to Sunday)
            week_days = [week_start + timedelta(days=i) for i in range(7)]

            # Create header with days
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            header_cells = [ui.tags.th("Time")]
            for i, day in enumerate(week_days):
                is_today = day == today
                day_class = "font-weight-bold" if is_today else ""
                header_cells.append(
                    ui.tags.th(
                        ui.div(
                            day_names[i],
                            ui.span(day.strftime("%d/%m"), class_="week-header-date")
                        ),
                        class_=day_class
                    )
                )

            # Create rows for each hour
            rows = []
            for time_slot in self.time_slots:
                cells = [ui.tags.td(time_slot, class_="time-label")]

                for day in week_days:
                    date_str = str(day)
                    is_past = day < today

                    # Find reservations for this day and time slot
                    slot_idx = self.time_slots.index(time_slot)
                    day_reservations = [
                        r for r in all_res
                        if r.date == date_str and
                           self.time_slots.index(r.start_time) <= slot_idx < self.time_slots.index(r.end_time)
                    ]

                    # Create cell with reservations
                    cell_class = "day-cell"
                    if is_past:
                        cell_class += " past"

                    reservation_blocks = []
                    for res in day_reservations:
                        # Calculate position and height based on time
                        start_idx = self.time_slots.index(res.start_time)
                        end_idx = self.time_slots.index(res.end_time)

                        # Only show block at the start time
                        if slot_idx == start_idx:
                            duration = end_idx - start_idx
                            height = (duration * 60) - 4  # 60px per hour minus padding

                            reservation_blocks.append(
                                ui.div(
                                    ui.div(f"{res.serial_number}", style="font-weight: bold;"),
                                    ui.div(f"{res.room.name}", style="font-size: 0.7rem;"),
                                    ui.div(f"{res.start_time}-{res.end_time}", style="font-size: 0.65rem;"),
                                    class_=f"reservation-block room-{res.room_id}",
                                    style=f"height: {height}px; top: 2px;",
                                    onclick=f"Shiny.setInputValue('reservation_click', {res.id}, {{priority: 'event'}})"
                                )
                            )

                    cells.append(
                        ui.tags.td(
                            *reservation_blocks,
                            class_=cell_class,
                            onclick=f"Shiny.setInputValue('week_cell_click', '{date_str}_{time_slot}', {{priority: 'event'}})"
                        )
                    )

                rows.append(ui.tags.tr(*cells))

            return ui.div(
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(*header_cells)),
                    ui.tags.tbody(*rows),
                    class_="week-calendar"
                ),
                style="overflow-x: auto;"
            )

        @reactive.Effect
        @reactive.event(input.prev_month)
        def _():
            month = current_month_val()
            year = current_year_val()
            if month == 1:
                current_month_val.set(12)
                current_year_val.set(year - 1)
            else:
                current_month_val.set(month - 1)

        @reactive.Effect
        @reactive.event(input.next_month)
        def _():
            month = current_month_val()
            year = current_year_val()
            if month == 12:
                current_month_val.set(1)
                current_year_val.set(year + 1)
            else:
                current_month_val.set(month + 1)

        @output
        @render.ui
        def calendar_view():
            month = current_month_val()
            year = current_year_val()

            # Create calendar
            cal = calendar.monthcalendar(year, month)

            # Get reservations for this month
            all_res = reservations.get()

            # Create table header
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            header = [ui.tags.th(day) for day in days]

            # Create table rows
            rows = []
            today = datetime.now().date()

            for week in cal:
                cells = []
                for day in week:
                    if day == 0:
                        cells.append(ui.tags.td("", class_="other-month"))
                    else:
                        date = datetime(year, month, day).date()
                        date_str = str(date)

                        # Count reservations for this day
                        day_reservations = [r for r in all_res if r.date == date_str]

                        # Group by room
                        room_counts = {}
                        for res in day_reservations:
                            room_id = res.room_id
                            room_counts[room_id] = room_counts.get(room_id, 0) + 1

                        # Create badges
                        badges = []
                        for room_id, count in room_counts.items():
                            room = next((r for r in self.rooms if r.id == room_id), None)
                            if room:
                                badges.append(
                                    ui.span(
                                        f"{room.name[:8]}: {count}",
                                        class_=f"reservation-badge room-color-{room_id}"
                                    )
                                )

                        # Determine CSS classes
                        css_classes = []
                        if date == today:
                            css_classes.append("today")
                        if selected_calendar_date() == date_str:
                            css_classes.append("selected")

                        cell_content = ui.div(
                            ui.div(str(day), class_="day-number"),
                            *badges
                        )

                        cells.append(
                            ui.tags.td(
                                cell_content,
                                class_=" ".join(css_classes),
                                onclick=f"Shiny.setInputValue('calendar_click', '{date_str}', {{priority: 'event'}})"
                            )
                        )

                rows.append(ui.tags.tr(*cells))

            return ui.div(
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(*header)),
                    ui.tags.tbody(*rows),
                    class_="calendar-table"
                ),
                ui.hr(),
                ui.output_ui("selected_day_info")
            )

        @output
        @render.ui
        def selected_day_info():
            date_str = selected_calendar_date()
            if not date_str:
                return ui.p("Click on a date in the calendar to view reservations",
                            style="text-align: center; color: #6b7280;")

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%B %d, %Y")

            all_res = reservations.get()
            day_res = [r for r in all_res if r.date == date_str]

            if not day_res:
                return ui.div(
                    ui.h4(f"📅 {date_formatted}"),
                    ui.p("No reservations for this day", style="color: #6b7280; font-style: italic;")
                )

            # Group by room
            res_cards = []
            for room in self.rooms:
                room_res = [r for r in day_res if r.room_id == room.id]
                if room_res:
                    items = []
                    for res in sorted(room_res, key=lambda x: x.start_time):
                        items.append(
                            ui.div(
                                f"🕐 {res.start_time} - {res.end_time} | 👤 {res.serial_number} | {res.activity}",
                                ui.input_action_button(
                                    f"del_cal_{res.id}",
                                    "❌",
                                    class_="btn-danger btn-sm float-end"
                                ),
                                class_="reservation-card"
                            )
                        )

                    res_cards.append(
                        ui.div(
                            ui.strong(f"📍 {room.name} - {room.location}"),
                            *items,
                            class_="mb-3"
                        )
                    )

            return ui.div(
                ui.h4(f"📅 {date_formatted}"),
                *res_cards
            )

        @reactive.Effect
        @reactive.event(input.calendar_click)
        def _():
            selected_calendar_date.set(input.calendar_click())

        @reactive.Effect
        @reactive.event(input.open_modal)
        def _():
            show_modal.set(True)

        @reactive.Effect
        @reactive.event(input.close_modal)
        def _():
            show_modal.set(False)
            selected_room.set(None)

        @output
        @render.ui
        def reservation_modal():
            if not show_modal():
                return ui.div()

            return ui.div(
                ui.div(
                    ui.div(
                        ui.div(
                            ui.h3("New Reservation"),
                            ui.input_action_button("close_modal", "✕", class_="modal-close"),
                            class_="modal-header"
                        ),
                        ui.input_text("pti_name", "PTI Name *", placeholder="Your name"),
                        ui.input_text("activity", "Activity", placeholder="E.g. Personal Training"),
                        ui.input_date("date", "Date *", value=datetime.now().date()),
                        ui.layout_columns(
                            ui.input_select("start_time", "Start Time *", choices=[""] + self.time_slots),
                            ui.input_select("end_time", "End Time *", choices=[""] + self.time_slots),
                            col_widths=[6, 6]
                        ),
                        ui.h4("Select Room *", style="margin-top: 20px;"),
                        ui.output_ui("room_choice"),
                        ui.input_action_button("reserve", "Confirm Reservation", class_="btn-success w-100 mt-3"),
                        class_="modal-content"
                    ),
                    class_="modal-backdrop",
                    onclick="if(event.target === this) Shiny.setInputValue('close_modal', Math.random())"
                )
            )

        @output
        @render.ui
        def room_choice():
            room_buttons = []
            self._controller.rooms()
            for room in self.rooms:
                is_selected = selected_room.get() == room.id
                card_class = "room-card selected" if is_selected else "room-card"

                room_buttons.append(
                    ui.div(
                        ui.input_action_button(
                            f"room_{room.id}",
                            ui.div(
                                ui.strong(room.name),
                                ui.br(),
                                ui.tags.small(room.location),
                                ui.br(),
                                ui.tags.small(f"Max. {room.capacity} people")
                            ),
                            class_="w-100"
                        ),
                        class_=card_class,
                        style="cursor: pointer;"
                    )
                )
            return ui.div(*room_buttons)

        # Event handlers for room selection
        @reactive.Effect
        @reactive.event(input.room_1)
        def _():
            selected_room.set(1)

        @reactive.Effect
        @reactive.event(input.room_2)
        def _():
            selected_room.set(2)

        @reactive.Effect
        @reactive.event(input.room_3)
        def _():
            selected_room.set(3)

        @reactive.Effect
        @reactive.event(input.room_4)
        def _():
            selected_room.set(4)

        @reactive.Effect
        @reactive.event(input.reserve)
        def _():
            # Validation
            if not input.pti_name():
                ui.notification_show("Please enter your name", type="error")
                return

            if not input.start_time():
                ui.notification_show("Please select a start time", type="error")
                return

            if not input.end_time():
                ui.notification_show("Please select an end time", type="error")
                return

            # Validate that end time is after start time
            start_idx = self.time_slots.index(input.start_time()) if input.start_time() in self.time_slots else -1
            end_idx = self.time_slots.index(input.end_time()) if input.end_time() in self.time_slots else -1

            if start_idx >= end_idx:
                ui.notification_show("End time must be after start time", type="error")
                return

            if selected_room.get() is None:
                ui.notification_show("Please select a room", type="error")
                return

            # Check if time is already booked (check for overlaps)
            date_str = str(input.date())
            current_reservations = reservations.get()

            for res in current_reservations:
                if res.room_id == selected_room.get() and res.date == date_str:
                    # Check for time overlap
                    res_start_idx = self.time_slots.index(res.start_time)
                    res_end_idx = self.time_slots.index(res.end_time)

                    # Overlap occurs if: new start < existing end AND new end > existing start
                    if start_idx < res_end_idx and end_idx > res_start_idx:
                        ui.notification_show(f"This room is already booked from {res.start_time} to {res.end_time}",
                                             type="error")
                        return

            # Find room object
            room_obj = next((r for r in self.rooms if r.id == selected_room.get()), None)

            # Create new reservation
            new_reservation = Reservation(
                id=len(current_reservations) + 1,
                room_id=selected_room.get(),
                room_name=room_obj.name,
                room_location=room_obj.location,
                date=date_str,
                start_time=input.start_time(),
                end_time=input.end_time(),
                serial_number=input.pti_name(),
                activity=input.activity() or "Training"
            )

            current_reservations.append(new_reservation)
            reservations.set(current_reservations)

            ui.notification_show("✅ Reservation created successfully!", type="message", duration=3)

            # Reset fields and close modal
            ui.update_text("activity", value="")
            ui.update_text("pti_name", value="")
            selected_room.set(None)
            show_modal.set(False)

            # Force calendar refresh by triggering reactive dependencies
            # This ensures the calendar updates immediately
            reservations.set(list(current_reservations))

        @output
        @render.ui
        def reservations_list():
            filter_date_str = str(input.filter_date())
            all_reservations = reservations.get()

            filtered_reservations = [
                r for r in all_reservations
                if r.date == filter_date_str
            ]

            if not filtered_reservations:
                return ui.div(
                    ui.p("No reservations found for this date",
                         style="text-align: center; color: #6b7280; padding: 40px;")
                )

            room_divs = []
            for room in self.rooms:
                room_reservations = [r for r in filtered_reservations if r.room_id == room.id]

                reservation_cards = []
                for res in sorted(room_reservations, key=lambda x: x.start_time):
                    reservation_cards.append(
                        ui.div(
                            ui.layout_columns(
                                ui.div(
                                    ui.strong(f"🕐 {res.start_time} - {res.end_time}"),
                                    ui.br(),
                                    f"👤 {res.serial_number}",
                                    ui.br(),
                                    ui.tags.small(res.activity, style="color: #6b7280;")
                                ),
                                ui.input_action_button(
                                    f"delete_{res.id}",
                                    "❌",
                                    class_="btn-danger btn-sm"
                                ),
                                col_widths=[10, 2]
                            ),
                            class_="reservation-card"
                        )
                    )

                if room_reservations:
                    room_content = ui.div(
                        ui.strong(f"📍 {room.name} - {room.location}"),
                        ui.hr(),
                        *reservation_cards,
                        class_="room-card",
                        style="margin-bottom: 15px;"
                    )
                    room_divs.append(room_content)

            return ui.div(*room_divs)

        # Delete handlers for all reservations
        @reactive.Effect
        def _():
            all_reservations = reservations.get()
            for res in all_reservations:
                # For list view
                button_id = f"delete_{res.id}"

                @reactive.Effect
                @reactive.event(input[button_id], ignore_none=True)
                def remove(res_id=res.id):
                    current = reservations.get()
                    new = [r for r in current if r.id != res_id]
                    reservations.set(new)
                    ui.notification_show("Reservation cancelled", type="warning")

                # For calendar view
                button_id_cal = f"del_cal_{res.id}"

                @reactive.Effect
                @reactive.event(input[button_id_cal], ignore_none=True)
                def remove_cal(res_id=res.id):
                    current = reservations.get()
                    new = [r for r in current if r.id != res_id]
                    reservations.set(new)
                    ui.notification_show("Reservation cancelled", type="warning")


# Public API
_page = ReserveFitnessRoomPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)