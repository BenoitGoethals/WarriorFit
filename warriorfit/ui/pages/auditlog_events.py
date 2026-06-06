import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.auditlog_events_controller import (
    AuditLogEventsController,
)
from warriorfit.ui.pages.page import Page


class AuditLogEventsPage(Page):
    @inject
    def __init__(
        self,
        controller: AuditLogEventsController = Provide[Container.auditlog_events_controller],
    ) -> None:
        super().__init__()
        self.ctrl = controller

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            t("nav.audit_logs"),
            ui.h2(t("audit.title")),
            ui.card(
                ui.card_header(t("audit.title")),
                ui.input_action_button(
                    "au_refresh", t("common.refresh"), class_="btn btn-secondary btn-sm my-2"
                ),
                ui.output_data_frame("au_grid"),
                full_screen=False,
            ),
            value="Audit Logs",
        )

    def server(self, input, output, session):
        self.refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, "Audit Logs", self.refresh_tick)

        @reactive.calc
        async def au_df():
            _ = self.refresh_tick.get()
            try:
                df: pd.DataFrame = await self.ctrl.list_audit_logs_df()
                return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                return pd.DataFrame({"Error": [str(e)]})

        @output
        @render.data_frame
        async def au_grid():
            # _ = _tick()
            df = await au_df()
            return render.DataGrid(df, filters=True, selection_mode="rows", width="100%")

        @reactive.Effect
        @reactive.event(input.au_refresh)
        def _on_refresh():
            self.refresh_tick.set(self.refresh_tick.get() + 1)


# Expose singleton-style API compatible with app.py import pattern
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = AuditLogEventsPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
