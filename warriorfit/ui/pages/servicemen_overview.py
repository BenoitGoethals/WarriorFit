"""Admin page: Servicemen overview with consent / privacy granted status."""

from __future__ import annotations

import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.servicemen_overview_controller import (
    ServicemenOverviewController,
)
from warriorfit.ui.pages.page import Page


class ServicemenOverviewPage(Page):
    TAB_NAME = "Servicemen Overview"

    @inject
    def __init__(
        self,
        controller: ServicemenOverviewController = Provide[
            Container.servicemen_overview_controller
        ],
    ):
        super().__init__()
        self.ctrl = controller

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            t("nav.servicemen_overview"),
            ui.div(
                ui.h2(t("servicemen.title"), class_="mb-3"),
                ui.p(
                    t("servicemen.description"),
                    class_="text-muted",
                ),
                ui.input_action_button(
                    "so_refresh", t("common.refresh"), class_="btn btn-secondary btn-sm mb-3"
                ),
                ui.card(
                    ui.card_header(t("servicemen.title")),
                    ui.output_data_frame("so_grid"),
                    full_screen=True,
                ),
                class_="container-fluid p-4",
            ),
            value=self.TAB_NAME,
        )

    def server(self, input, output, session):
        self.refresh_on_nav(input, self.TAB_NAME, self.refresh_tick)

        @reactive.calc
        async def df_val():
            _ = self.refresh_tick.get()
            try:
                return await self.ctrl.overview_df()
            except Exception as e:
                return pd.DataFrame({"Error": [str(e)]})

        @output
        @render.data_frame
        async def so_grid():
            df = await df_val()
            return render.DataGrid(df, filters=True, selection_mode="none", width="100%")

        @reactive.effect
        @reactive.event(input.so_refresh)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)


_page: ServicemenOverviewPage | None = None


def _get_page() -> ServicemenOverviewPage:
    global _page
    if _page is None:
        _page = ServicemenOverviewPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
