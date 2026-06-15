import datetime
from typing import Any, ClassVar

from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.core.role import Role
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.i18n import t
from warriorfit.ui.controllers.session_controller import SessionsController
from warriorfit.ui.pages.page import Page


class SessionsPage(Page):
    TAB_NAME = "Sessions"
    SESSION_TYPES: ClassVar[list[str]] = [r.name for r in TypeFitnessTest]
    ROLES: ClassVar[list[str]] = [r.name for r in Role]

    NO_SELECTION_MESSAGE = "common.no_row_selected"
    _DATE_KEY = "sessions.date"

    @inject
    def __init__(
        self, controller: SessionsController = Provide[Container.sessions_controller]
    ) -> None:
        super().__init__()
        self.controller = controller

    def _validate(self, data: dict[str, Any]) -> tuple[bool, str]:
        if not data["datetime_start"]:
            return False, t("sessions.date_time_required")
        if not (data["type_test"] or "").strip():
            return False, t("sessions.type_required")
        if data["type_test"] not in self.SESSION_TYPES:
            return False, t("sessions.invalid_type")
        return True, "OK"

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            t("nav.sessions"),
            ui.h2(t("sessions.title")),
            ui.input_action_button(
                "se_refresh_btn", t("common.refresh"), class_="btn btn-secondary btn-sm my-2"
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("sessions.edit_header")),
                    ui.input_select("se_serial", t("sessions.pti_serial"), choices=[]),
                    ui.input_date("se_date", t(self._DATE_KEY)),
                    ui.input_text(
                        "se_time",
                        t("sessions.time"),
                        placeholder=t("sessions.time_placeholder"),
                        value="09:00",
                    ),
                    ui.input_select("se_type", t("sessions.type"), choices=self.SESSION_TYPES),
                    ui.input_checkbox("se_canceled", t("sessions.canceled"), value=False),
                    ui.input_text_area(
                        "se_description", t("sessions.description"), rows=3, width="400px"
                    ),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button(
                            "se_add_btn", t("sessions.add"), class_="btn-primary w-100"
                        ),
                        ui.input_action_button(
                            "se_update_btn", t("sessions.update"), class_="btn-warning w-100"
                        ),
                        ui.input_action_button(
                            "se_clear_btn", t("sessions.clear"), class_="btn-secondary w-100"
                        ),
                        ui.input_action_button(
                            "se_delete_btn",
                            t("sessions.delete_selected"),
                            class_="btn-danger w-100",
                        ),
                        col_widths=(4,),
                    ),
                    ui.br(),
                    ui.output_text("se_status"),
                    ui.output_text("selected_session"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header(t("sessions.sessions_label")),
                    ui.output_data_frame("se_grid"),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
            value=self.TAB_NAME,
        )

    def server(self, input, output, session):
        sessions = reactive.Value([])  # type: ignore[var-annotated]
        status = reactive.Value(t("common.ready"))
        selected_session_id = reactive.Value("")

        async def all_pti_choices() -> dict[str, str]:
            return await self.controller.get_all_pti_choices()

        async def _populate_pti_choices():
            try:
                choices = await all_pti_choices()
                ui.update_select("se_serial", choices=choices, selected=None)
            except Exception:
                ui.update_select("se_serial", choices=[], selected=None)

        @reactive.Effect
        async def _populate_pti_choices_effect():
            await _populate_pti_choices()

        def _read_form() -> dict[str, Any]:
            dt_date = input.se_date()
            dt_time = input.se_time()
            dt = None
            if dt_date and dt_time:
                try:
                    if isinstance(dt_time, str):
                        parts = [int(x) for x in dt_time.split(":")]
                        while len(parts) < 3:
                            parts.append(0)
                        _t = datetime.time(parts[0], parts[1], parts[2])
                    else:
                        _t = dt_time
                    dt = datetime.datetime.combine(dt_date, _t)
                except Exception:
                    dt = None
            return {
                "serial_number_pti": (input.se_serial() or "").strip() or None,
                "datetime_start": dt,
                "canceled": bool(input.se_canceled()),
                "description": (input.se_description() or "").strip() or None,
                "type_test": (input.se_type() or "").strip(),
            }

        def _write_form(rec: dict[str, Any]):
            dt = rec.get("datetime_start")
            dt_date = dt.date() if isinstance(dt, datetime.datetime) else None
            dt_time = dt.time().strftime("%H:%M:%S") if isinstance(dt, datetime.datetime) else None
            session.send_input_message(
                "se_serial", {"value": rec.get("serial_number_pti", "") or ""}
            )
            session.send_input_message("se_date", {"value": dt_date})
            session.send_input_message("se_time", {"value": dt_time})
            session.send_input_message("se_type", {"value": rec.get("type_test", "")})
            session.send_input_message("se_canceled", {"value": bool(rec.get("canceled", False))})
            session.send_input_message(
                "se_description", {"value": rec.get("description", "") or ""}
            )

        async def _clear_form():
            await _populate_pti_choices()
            ui.update_date("se_date", label=t(self._DATE_KEY), value=None)
            ui.update_text("se_time", value="09:00")
            ui.update_select("se_type", choices=self.SESSION_TYPES)
            ui.update_checkbox("se_canceled", value=False)
            ui.update_text_area("se_description", value="")
            self.selected_row = None

        async def _refresh_select():
            items = sessions.get() or []
            choices = {
                str(r["id"]): f"{r['id']}: {r.get('type_test', '')} ({r.get('datetime_start', '')})"
                for r in items
                if r.get("id") is not None
            }
            session.send_input_message("se_select_id", {"choices": choices, "selected": None})

        @output
        @render.text
        def se_status():
            return status.get()

        @reactive.calc
        async def session_list():
            _ = self.refresh_tick.get()
            val = await self.controller.list_sessions_df()
            return val.sort_values(by=["Start"])

        @output
        @render.data_frame
        async def se_grid():
            df = await session_list()

            df = df.drop(columns=["ID"])
            if not df.empty:
                return render.DataGrid(
                    df,
                    filters=True,
                    selection_mode="rows",
                    width="100%",
                )
            return None

        @output
        @render.text
        async def selected_session():
            sel = input.se_grid_selected_rows()  # list of row indices
            if not sel:
                status.set(t("sessions.no_row_selected"))
                return
            row_idx = sel[0]
            df = await session_list()
            if row_idx < 0 or row_idx >= len(df):
                status.set(t("sessions.no_row_selected"))
                return
            row = df.iloc[row_idx]
            selected_session_id.set(row["ID"] or "")
            choices = await all_pti_choices()
            serial = str(row["Serial PTI"])
            ui.update_select("se_serial", choices=choices, selected=serial)
            start_dt = row["Start"]
            try:
                date_value = start_dt.date()
            except Exception:
                date_value = None
            ui.update_date("se_date", label=t(self._DATE_KEY), value=date_value)
            ui.update_text(
                "se_time",
                value=(
                    start_dt.strftime("%H:%M") if getattr(start_dt, "strftime", None) else "09:00"
                ),
            )
            type_raw = str(row["Type"]).strip()
            ui.update_select("se_type", choices=self.SESSION_TYPES, selected=type_raw)
            ui.update_checkbox("se_canceled", value=(str(row["Canceled"]).strip().lower() == "yes"))
            ui.update_text_area("se_description", value=str(row["Description"]))
            return f"Selected session ID: {row['ID']}"

        @reactive.Effect
        async def _init_select():
            await _refresh_select()

        @reactive.Effect
        @reactive.event(input.se_add_btn)
        async def _on_add():
            data = _read_form()
            ok, msg = self._validate(data)
            if not ok:
                status.set(msg)
                return
            try:
                added = await self.controller.add_session(data)
                if not added:
                    status.set(t("sessions.failed_add"))
                    return
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                status.set(f"Error adding session: {e!s}")
                return
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("sessions.added"))
            ui.notification_show(t("sessions.session_added"), type="message", duration=3)
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.se_load_btn)
        def _on_load():
            sel = input.se_select_id()
            if not sel:
                status.set(t("sessions.select_to_load"))
                return
            sel_id = int(sel)
            rec = next((r for r in (sessions.get() or []) if r.get("id") == sel_id), None)
            if not rec:
                status.set(t("sessions.not_found"))
                return
            _write_form(rec)
            status.set(t("sessions.loaded").format(id=sel_id))

        @reactive.Effect
        @reactive.event(input.se_update_btn)
        async def _on_update():
            payload = _read_form()
            ok, msg = self._validate(payload)
            if not ok:
                status.set(msg)
                return
            updated_ok = await self.controller.update_session(
                int(selected_session_id.get()), payload
            )
            if not updated_ok:
                status.set(t("sessions.failed_update"))
                return
            await _refresh_select()
            await _clear_form()
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            status.set(t("sessions.updated"))
            ui.notification_show(t("sessions.updated"), type="message", duration=3)

        @reactive.Effect
        @reactive.event(input.se_delete_btn)
        async def _on_delete():
            selected_id = input.se_grid_selected_rows()[0]
            if not selected_id:
                status.set(t("sessions.select_to_delete"))
                return
            ok = await self.controller.delete_session(int(selected_session_id.get()))
            if not ok:
                status.set(t("sessions.failed_delete"))
                return
            status.set(t("sessions.deleted_id").format(id=selected_id))
            ui.notification_show(t("sessions.deleted"), type="warning", duration=3)
            self.refresh_tick.set(self.refresh_tick.get() + 1)
            await _refresh_select()
            await _clear_form()

        @reactive.Effect
        @reactive.event(input.se_refresh_btn)
        def _on_se_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.se_clear_btn)
        async def _on_clear():
            await _clear_form()
            status.set(t("sessions.form_cleared"))


_page_instance: SessionsPage | None = None


def _get_page() -> SessionsPage:
    global _page_instance
    if _page_instance is None:
        _page_instance = SessionsPage()
    return _page_instance


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)


def get_sessions_store():
    return [None]
