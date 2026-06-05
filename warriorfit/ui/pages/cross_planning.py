from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.cross_planning_controller import CrossPlanningController
from warriorfit.ui.pages.page import Page


class CrossPlanningPage(Page):
    @inject
    def __init__(
        self,
        controller: CrossPlanningController = Provide[
            Container.cross_planning_controller
        ],
    ):
        super().__init__()
        self._controller = controller
        self.selected_cross_id = reactive.Value("")

    NO_SELECTION_MESSAGE = "No row selected"

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            t("nav.cross_planning"),
            ui.h2(t("cross_plan.title")),
            ui.input_action_button(
                "cr_refresh_btn", t("common.refresh"), class_="btn btn-secondary btn-sm my-2"
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("cross_plan.cross_form")),
                    ui.input_date("cr_date", t("cross_plan.date")),
                    ui.input_text(
                        "cr_time",
                        t("cross_plan.pick_time"),
                        placeholder="Select a time",
                        value="09:30",
                    ),
                    ui.output_text_verbatim("show_time"),
                    ui.input_numeric("cr_distance", t("cross_plan.distance"), value=5, min=0),
                    ui.input_checkbox("cr_executed", t("cross_plan.executed"), value=False),
                    ui.input_text(
                        "cr_desc",
                        t("cross_plan.description"),
                        placeholder=t("cross_plan.optional"),
                    ),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button(
                            "cr_add_btn",
                            t("cross_plan.add"),
                            width="120px",
                            class_="btn-primary w-100",
                        ),
                        ui.input_action_button(
                            "cr_update_btn",
                            t("cross_plan.update"),
                            width="120px",
                            class_="btn-warning w-100",
                        ),
                        ui.input_action_button(
                            "cr_clear_btn",
                            t("cross_plan.clear"),
                            width="120px",
                            class_="btn-secondary w-100",
                        ),
                        ui.input_action_button(
                            "cr_delete_btn",
                            t("cross_plan.delete_selected"),
                            width="170px",
                            class_="btn-danger w-100",
                        ),
                        col_widths=(4,),
                    ),
                    ui.output_text("cr_status"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header(t("cross_plan.crosses")),
                    ui.layout_columns(
                        ui.output_data_frame("cr_grid"),
                    ),
                    full_screen=False,
                ),
                col_widths=(4, 8),
            ),
            value="Cross Planning",
        )

    # ---------------------------
    # Helpers
    # ---------------------------

    @staticmethod
    def _to_datetime(date_str: str | None, time_str: str | None) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # ui.input_date returns 'YYYY-MM-DD'; ui.input_time returns 'HH:MM' (24h)
            date_part = date_str
            time_part = time_str or "00:00"
            return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        except Exception:
            return None

    @staticmethod
    def _format_dt(dt: Optional[datetime]) -> str:
        if not dt:
            return ""
        return dt.strftime("%Y-%m-%d %H:%M")

    def _read_form(self, input) -> Dict[str, Any]:
        date_val = input.cr_date()
        time_val = input.cr_time()
        dt = self._to_datetime(date_val, time_val)
        return {
            "datetime_start": dt,
            "executed": bool(input.cr_executed()),
            "distance": input.cr_distance(),
            "description": (input.cr_desc() or "").strip(),
        }

    def _write_form(self, session, rec: Dict[str, Any]) -> None:
        dt: Optional[datetime] = rec.get("datetime_start")
        date_val = dt.strftime("%Y-%m-%d") if dt else ""
        time_val = dt.strftime("%H:%M") if dt else ""
        session.send_input_message("cr_date", {"value": date_val})
        session.send_input_message("cr_time", {"value": time_val})
        session.send_input_message("cr_distance", {"value": rec.get("distance", 0)})
        session.send_input_message(
            "cr_executed", {"value": bool(rec.get("executed", False))}
        )
        session.send_input_message("cr_desc", {"value": rec.get("description", "")})

    def _clear_form(self, session) -> None:
        session.send_input_message("cr_date", {"value": ""})
        session.send_input_message("cr_time", {"value": ""})
        session.send_input_message("cr_distance", {"value": 0})
        session.send_input_message("cr_executed", {"value": False})
        session.send_input_message("cr_desc", {"value": ""})

    # ---------------------------
    # Server
    # ---------------------------

    def server(self, input, output, session):
        status = reactive.Value(t("common.ready"))

        @output
        @render.text
        def show_time():
            return f"Selected time: {input.cr_date().strftime('%d/%m/%Y')} {input.cr_time()}"

        # Status output
        @output
        @render.text
        def cr_status():
            return status.get()

        # Data (full df keeps ID)
        @reactive.calc
        async def cross_df() -> pd.DataFrame:
            _ = self.refresh_tick.get()
            rows = await self._controller.list_crosses()
            data = [
                {
                    "ID": r["id"],
                    "Start": self._format_dt(r["datetime_start"]),
                    "Executed": r["executed"],
                    "Distance": r.get("distance", 0),
                    "Description": r["description"] or "",
                }
                for r in rows
            ]
            df = (
                pd.DataFrame(data)
                if data
                else pd.DataFrame(
                    columns=["ID", "Start", "Executed", "Description", "Distance"]
                )
            )
            df = df.sort_values(by=["Start"], kind="stable").reset_index(drop=True)
            return df

        # Data shown in the grid (ID hidden, but still present in cross_df)
        @reactive.calc
        async def cross_df_view() -> pd.DataFrame:
            df = await cross_df()
            return df.drop(columns=["ID"])

        @output
        @render.data_frame
        async def cr_grid():
            df_view = await cross_df_view()
            return render.DataGrid(
                df_view,
                selection_mode="rows",
                filters=False,
                width="100%",
            )

        # Row selection -> populate form
        @reactive.Effect
        @reactive.event(input.cr_grid_selected_rows)
        async def _on_row_selected():
            try:
                sel = input.cr_grid_selected_rows()
                if not sel:
                    status.set(self.NO_SELECTION_MESSAGE)
                    self.selected_cross_id.set("")
                    return
                # Await the async calc to get the DataFrame
                df = await cross_df()
                row_idx = sel[0]
                if row_idx < 0 or row_idx >= len(df):
                    status.set(self.NO_SELECTION_MESSAGE)
                    self.selected_cross_id.set("")
                    return
                row = df.iloc[row_idx]
                cross_id = int(row["ID"])
                self.selected_cross_id.set(str(cross_id))
                detail = await self._controller.get_cross_view(cross_id)
                self._write_form(session, detail)
                status.set(f"Selected Cross #{cross_id}")
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                status.set(f"Selection error: {e}")

        # Buttons
        @reactive.Effect
        @reactive.event(input.cr_refresh_btn)
        def _on_cr_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @reactive.Effect
        @reactive.event(input.cr_clear_btn)
        def _on_clear():
            self._clear_form(session)
            self.selected_cross_id.set("")
            status.set("Form cleared.")

        @reactive.Effect
        @reactive.event(input.cr_add_btn)
        async def _on_add():
            data = self._read_form(input)
            if not data["datetime_start"]:
                status.set("Please provide a valid date and time.")
                return
            try:
                detail = await self._controller.create_cross(
                    datetime_start=data["datetime_start"],
                    executed=data["executed"],
                    distance=data["distance"],
                    description=data["description"] or None,
                )
                self.selected_cross_id.set(str(detail["id"]))
                self._write_form(session, detail)

                self.refresh_tick.set(self.refresh_tick.get() + 1)
                status.set(f"Cross #{detail['id']} created.")
                ui.notification_show(
                    f"Cross #{detail['id']} created.", type="message", duration=3
                )
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                status.set(f"Add failed: {e}")
                ui.notification_show(f"Add failed: {e}", type="error", duration=3)

        @reactive.Effect
        @reactive.event(input.cr_update_btn)
        async def _on_update():
            sel = self.selected_cross_id.get()
            if not sel:
                status.set(self.NO_SELECTION_MESSAGE)
                return
            data = self._read_form(input)
            if data["datetime_start"] is None:
                status.set("Please provide a valid date and time.")
                return
            try:
                detail = await self._controller.update_cross(
                    int(sel),
                    datetime_start=data["datetime_start"],
                    executed=data["executed"],
                    distance=data["distance"],
                    description=data["description"] or None,
                )
                self._write_form(session, detail)
                self.refresh_tick.set(self.refresh_tick.get() + 1)
                status.set(f"Cross #{sel} updated.")
                ui.notification_show(
                    f"Cross #{sel} updated.", type="message", duration=3
                )
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                status.set(f"Update failed: {e}")
                ui.notification_show(f"Update failed: {e}", type="error", duration=3)

        @reactive.Effect
        @reactive.event(input.cr_delete_btn)
        async def _on_delete():
            sel = input.cr_grid_selected_rows()
            # cross_df is async -> await it
            df = await cross_df()
            if not sel or df.empty:
                status.set(self.NO_SELECTION_MESSAGE)
                return
            idx = sel[0]
            if idx < 0 or idx >= len(df):
                status.set(self.NO_SELECTION_MESSAGE)
                return
            cross_id = int(df.iloc[idx]["ID"])
            try:
                # delete_cross is sync in controller -> do NOT await
                self._controller.delete_cross(cross_id)
                self.refresh_tick.set(self.refresh_tick.get() + 1)
                self._clear_form(session)
                self.selected_cross_id.set("")
                status.set(f"Cross #{cross_id} deleted.")
                ui.notification_show(
                    f"Cross #{cross_id} deleted.", type="warning", duration=3
                )
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                status.set(f"Delete failed: {e}")
                ui.notification_show(f"Delete failed: {e}", type="error", duration=3)


# Expose singleton-style API compatible with app.py import pattern
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = CrossPlanningPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)
