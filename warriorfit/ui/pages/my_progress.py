"""'My Progress' page — shows the logged-in user their test history, this
year's tests, and a progress chart. Read-only; USER role self-service."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget

from warriorfit.core.container import Container
from warriorfit.ui.controllers.my_progress_controller import MyProgressController
from warriorfit.ui.pages.page import Page
from warriorfit.ui.user_store import UserStore


class MyProgressPage(Page):
    @inject
    def __init__(
        self,
        controller: MyProgressController = Provide[Container.my_progress_controller],
    ):
        super().__init__()
        self.controller = controller
        self.history_df_val: reactive.Value[pd.DataFrame] = reactive.Value(
            pd.DataFrame()
        )
        self.year_df_val: reactive.Value[pd.DataFrame] = reactive.Value(pd.DataFrame())

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            "My Progress",
            ui.div(
                ui.h2("My Test Progress", class_="mb-1"),
                ui.p(
                    ui.output_text("mp_header"),
                    class_="text-muted mb-3",
                ),
                ui.input_action_button(
                    "mp_refresh_btn",
                    "🔄 Refresh",
                    class_="btn btn-secondary btn-sm mb-3",
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("This year"),
                        ui.output_data_frame("mp_year_grid"),
                        full_screen=True,
                    ),
                    ui.card(
                        ui.card_header("All history"),
                        ui.output_data_frame("mp_history_grid"),
                        full_screen=True,
                    ),
                    col_widths=(6, 6),
                ),
                ui.card(
                    ui.card_header("Progress over time"),
                    output_widget("mp_progress_chart"),
                    full_screen=True,
                    class_="mt-3",
                ),
                class_="container-fluid p-4",
            ),
        )

    def server(self, input, output, session):
        @reactive.Effect
        async def _load():
            self.refresh_tick.get()
            user = UserStore.get_user()
            if user is None or not user.serial_number:
                self.history_df_val.set(pd.DataFrame())
                self.year_df_val.set(pd.DataFrame())
                return
            self.history_df_val.set(
                await self.controller.history_df(user.serial_number)
            )
            self.year_df_val.set(
                await self.controller.current_year_df(user.serial_number)
            )

        @reactive.Effect
        @reactive.event(input.mp_refresh_btn)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        @render.text
        def mp_header():
            user = UserStore.get_user()
            if user is None:
                return "Not logged in."
            if not user.serial_number:
                return "Your account has no service number attached — no tests to show."
            return f"{user.username} · {user.serial_number}"

        @output
        @render.data_frame
        def mp_year_grid():
            df = self.year_df_val.get()
            if df is None or df.empty:
                df = pd.DataFrame(columns=["Date", "Type", "Total", "Result"])
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        @output
        @render.data_frame
        def mp_history_grid():
            df = self.history_df_val.get()
            if df is None or df.empty:
                df = pd.DataFrame(columns=["Date", "Type", "Total", "Result"])
            return render.DataGrid(
                df, filters=True, selection_mode="none", width="100%"
            )

        @output
        @render_widget
        def mp_progress_chart():
            df = self.history_df_val.get()
            series = MyProgressController.progress_series(df)
            series = series[series["Type"] == "PHEF"] if not series.empty else series
            if series.empty:
                fig = px.line(title="No PHEF data yet")
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="PHEF score",
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                return fig
            fig = px.line(
                series,
                x="Date",
                y="Score",
                markers=True,
                title="PHEF score over time",
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="PHEF score",
                margin=dict(l=20, r=20, t=40, b=20),
            )
            return fig


_page: MyProgressPage | None = None


def _get_page() -> MyProgressPage:
    global _page
    if _page is None:
        _page = MyProgressPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
