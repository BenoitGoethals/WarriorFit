from __future__ import annotations

from datetime import datetime
from typing import Any, Final, Mapping, Awaitable, Callable

from htmltools import HTML, Tag
from shiny import ui, render, reactive
from shiny.ui._navs import NavPanel

from warriorfit.ui.controllers.dashboard_own_unit_controller import (
    DashboardOwnUnitController,
)
from warriorfit.ui.pages.page import Page
from dependency_injector.wiring import inject, Provide
from warriorfit.core.container import Container


class DashboardOwnUnitPage(Page):
    TAB_NAME: Final[str] = "Dashboard"

    @inject
    def __init__(
        self,
        controller: DashboardOwnUnitController = Provide[
            Container.dashboard_own_unit_controller
        ],
    ) -> None:
        super().__init__()
        self.controller = controller

    def refresh(self) -> None:
        # Dashboard is cache-heavy; refresh should clear controller caches.
        self.controller.reset_cache()
        reactive.invalidate_later(0.5)

    @staticmethod
    def _ui_stats_card(
        *,
        total_text: str,
        total_value: int | float,
        sub_value: str | None,
        sub_label: str,
        sub_class: str,
    ) -> ui.Tag:
        return ui.div(
            ui.h1(str(total_value), class_="display-4 fw-bold"),
            ui.p(total_text),
            ui.hr(),
            (ui.h4(sub_value, class_=sub_class) if sub_value is not None else ui.div()),
            (ui.p(sub_label) if sub_value is not None else ui.div()),
        )

    @staticmethod
    def _no_data(msg: str) -> ui.Tag:
        return ui.div(
            ui.p(msg, class_="text-muted"),
            ui.p(
                "Tip: check server logs for exceptions and confirm Plotly HTML is generated with full_html=False.",
                class_="text-muted",
            ),
        )

    def get_ui(self) -> NavPanel:
        year = datetime.now().year
        unit = getattr(self.controller, "unit_name", "Unit")
        return ui.nav_panel(
            self.TAB_NAME,
            ui.h2(f"📊 {unit} Dashboard {year}"),
            ui.input_action_button(
                "dashboard_refresh_btn",
                "🔄 Refresh",
                class_="btn btn-secondary btn-sm my-2",
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "👥 Unit Personnel", class_="bg-secondary text-white"
                    ),
                    ui.output_ui("own_unit_personnel_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🏃 PHEF Tests", class_="bg-primary text-white"),
                    ui.output_ui("own_unit_phef_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🪖 Combat Tests", class_="bg-success text-white"),
                    ui.output_ui("own_unit_combat_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🏊 Swimming Tests", class_="bg-info text-white"),
                    ui.output_ui("own_unit_swimming_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header("🥾 March Tests", class_="bg-info text-white"),
                    ui.output_ui("own_unit_march_stats"),
                    class_="text-center",
                ),
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Pass/Fail Rates by Test Type (Own Unit)"),
                    ui.output_ui("own_unit_pass_fail_chart"),
                    full_screen=True,
                ),
            ),
            ui.br(),
            ui.layout_columns(
                ui.card(
                    ui.card_header("PHEF Score Distribution (Own Unit)"),
                    ui.output_ui("own_unit_phef_score_histogram"),
                    full_screen=True,
                ),
            ),
            ui.br(),
        )

    def server(self, input: Any, output: Any, session: Any) -> None:
        refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, self.TAB_NAME, refresh_tick)

        def _get(stats: Mapping[str, Any], key: str, default: Any) -> Any:
            try:
                return stats.get(key, default)
            except Exception:
                return default

        async def _safe_stats(
            fetcher: Callable[[], Awaitable[Mapping[str, Any]]],
        ) -> dict[str, Any]:
            try:
                return dict(await fetcher())
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                # Don't crash dashboard cards; show muted error
                return {
                    "total": 0,
                    "sub_value": None,
                    "sub_label": f"Unavailable: {e}",
                    "sub_class": "text-muted",
                }

        def _register_stats_output(
            *,
            output_id: str,
            total_text: str,
            fetcher: Callable[[], Awaitable[Mapping[str, Any]]],
        ) -> None:
            @output(id=output_id)
            @render.ui
            async def _stats_card() -> ui.Tag:
                reactive.invalidate_later(0.5)
                _ = refresh_tick.get()
                stats = await _safe_stats(fetcher)
                return self._ui_stats_card(
                    total_text=total_text,
                    total_value=int(_get(stats, "total", 0) or 0),
                    sub_value=_get(stats, "sub_value", None),
                    sub_label=str(_get(stats, "sub_label", "")),
                    sub_class=str(_get(stats, "sub_class", "text-muted")),
                )

        def _register_plotly_html_output(
            *,
            output_id: str,
            fetcher: Callable[[], Awaitable[str]],
            empty_msg: str,
            non_div_msg: str,
        ) -> None:
            @output(id=output_id)
            @render.ui
            async def _plot() -> Tag | HTML:
                _ = refresh_tick.get()
                reactive.invalidate_later(0.5)
                try:
                    html = await fetcher()
                    if not html:
                        return self._no_data(empty_msg)
                    if "<div" not in html:
                        return self._no_data(non_div_msg)
                    return ui.HTML(html)
                except (KeyError, TypeError, ValueError, AttributeError) as e:
                    return self._no_data(f"No data available: {e}")

        # Register stat cards (no duplicated output bodies)
        _register_stats_output(
            output_id="own_unit_personnel_stats",
            total_text="Service members in unit",
            fetcher=self.controller.personnel_stats,
        )
        _register_stats_output(
            output_id="own_unit_phef_stats",
            total_text="Total Tests (Own Unit)",
            fetcher=self.controller.phef_stats,
        )
        _register_stats_output(
            output_id="own_unit_combat_stats",
            total_text="Total Tests (Own Unit)",
            fetcher=self.controller.combat_stats,
        )
        _register_stats_output(
            output_id="own_unit_swimming_stats",
            total_text="Total Tests (Own Unit)",
            fetcher=self.controller.swimming_stats,
        )
        _register_stats_output(
            output_id="own_unit_march_stats",
            total_text="Total Tests (Own Unit)",
            fetcher=self.controller.march_stats,
        )

        # Register charts (same error/empty handling)
        _register_plotly_html_output(
            output_id="own_unit_pass_fail_chart",
            fetcher=self.controller.pass_fail_bar_html,
            empty_msg="No chart HTML was generated.",
            non_div_msg="No chart HTML was generated.",
        )
        _register_plotly_html_output(
            output_id="own_unit_phef_score_histogram",
            fetcher=self.controller.phef_hist_html,
            empty_msg="No PHEF data available for your unit.",
            non_div_msg="No histogram HTML was generated.",
        )

        @reactive.Effect
        @reactive.event(input.dashboard_refresh_btn)
        def _on_dashboard_refresh():
            self.refresh()
            refresh_tick.set(refresh_tick.get() + 1)


# Public API
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = DashboardOwnUnitPage()
    return _page


def get_ui() -> NavPanel:
    return _get_page().get_ui()


def server(input: Any, output: Any, session: Any) -> None:
    _get_page().server(input, output, session)
