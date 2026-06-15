"""Test Analytics page — cohort-level diagnostic charts under Physical Tests.

Four sections:

1. Coverage gauges (how much of the unit completed each test this year)
2. Pass rate per age bracket (grouped bar across all 5 test types)
3. Monthly pass-rate trend (line per test type)
4. MFFT deep dive: bottleneck bar + per-event histograms
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Final

from dependency_injector.wiring import Provide, inject
from htmltools import HTML, Tag
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.test_analytics_controller import (
    TestAnalyticsController,
)
from warriorfit.ui.pages.page import Page


class TestAnalyticsPage(Page):
    TAB_NAME: Final[str] = "Analytics"

    @inject
    def __init__(
        self,
        controller: TestAnalyticsController = Provide[Container.test_analytics_controller],
    ) -> None:
        super().__init__()
        self.controller = controller

    def refresh(self) -> None:
        self.controller.reset_cache()
        reactive.invalidate_later(0.5)

    @staticmethod
    def _no_data(msg: str) -> ui.Tag:
        return ui.div(
            ui.p(msg, class_="text-muted text-center py-4 mb-0"),
        )

    def get_ui(self) -> NavPanel:  # type: ignore[override]
        year = datetime.now().year
        unit = getattr(self.controller, "unit_name", "Unit")
        return ui.nav_panel(
            t("nav.analytics"),
            ui.h2(f"📈 {unit} Analytics {year}"),
            ui.p(t("analytics.intro"), class_="text-muted"),
            ui.input_action_button(
                "analytics_refresh_btn",
                t("common.refresh"),
                class_="btn btn-secondary btn-sm my-2",
            ),
            ui.br(),
            # ----- Coverage gauges -----
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("analytics.coverage_title")),
                    ui.p(t("analytics.coverage_help"), class_="text-muted small mb-2"),
                    ui.output_ui("analytics_coverage"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
            ui.br(),
            # ----- Age bracket + monthly trend side-by-side -----
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("analytics.age_bracket_title")),
                    ui.p(t("analytics.age_bracket_help"), class_="text-muted small mb-2"),
                    ui.output_ui("analytics_age_bracket"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header(t("analytics.monthly_title")),
                    ui.p(t("analytics.monthly_help"), class_="text-muted small mb-2"),
                    ui.output_ui("analytics_monthly"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            ui.br(),
            # ----- MFFT deep-dive -----
            ui.h3(f"🎖 {t('analytics.mfft_section')}"),
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("analytics.mfft_bottleneck_title")),
                    ui.p(t("analytics.mfft_bottleneck_help"), class_="text-muted small mb-2"),
                    ui.output_ui("analytics_mfft_bottleneck"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("analytics.mfft_histograms_title")),
                    ui.p(t("analytics.mfft_histograms_help"), class_="text-muted small mb-2"),
                    ui.output_ui("analytics_mfft_histograms"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
            ui.br(),
            value=self.TAB_NAME,
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, self.TAB_NAME, refresh_tick)

        no_chart_msg = t("dashboard.no_chart")

        def _register_plot(
            output_id: str,
            fetcher: Callable[[], Awaitable[str | None]],
            empty_msg: str,
        ) -> None:
            @output(id=output_id)
            @render.ui
            async def _plot() -> Tag | HTML:
                _ = refresh_tick.get()
                try:
                    html = await fetcher()
                except (KeyError, TypeError, ValueError, AttributeError) as e:
                    return self._no_data(t("dashboard.unavailable").format(error=e))
                if not html:
                    return self._no_data(empty_msg)
                if "<div" not in html:
                    return self._no_data(no_chart_msg)
                return ui.HTML(html)

        _register_plot(
            "analytics_coverage",
            self.controller.coverage_html,
            t("analytics.no_coverage_data"),
        )
        _register_plot(
            "analytics_age_bracket",
            self.controller.pass_rate_by_age_html,
            t("analytics.no_pass_rate_data"),
        )
        _register_plot(
            "analytics_monthly",
            self.controller.monthly_pass_rate_html,
            t("analytics.no_monthly_data"),
        )
        _register_plot(
            "analytics_mfft_bottleneck",
            self.controller.mfft_bottleneck_html,
            t("analytics.no_mfft_data"),
        )
        _register_plot(
            "analytics_mfft_histograms",
            self.controller.mfft_event_histograms_html,
            t("analytics.no_mfft_data"),
        )

        @reactive.Effect
        @reactive.event(input.analytics_refresh_btn)
        def _on_refresh() -> None:
            self.refresh()
            refresh_tick.set(refresh_tick.get() + 1)


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = TestAnalyticsPage()
    return _page


def get_ui() -> NavPanel:
    return _get_page().get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _get_page().server(input, output, session)
