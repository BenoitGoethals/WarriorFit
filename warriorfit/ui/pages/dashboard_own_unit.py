from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any, Final

from dependency_injector.wiring import Provide, inject
from htmltools import HTML, Tag
from shiny import reactive, render, ui
from shiny.ui._navs import NavPanel

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.dashboard_own_unit_controller import (
    DashboardOwnUnitController,
)
from warriorfit.ui.pages.page import Page


class DashboardOwnUnitPage(Page):
    TAB_NAME: Final[str] = "Dashboard"

    @inject
    def __init__(
        self,
        controller: DashboardOwnUnitController = Provide[Container.dashboard_own_unit_controller],
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

    def get_ui(self) -> NavPanel:  # type: ignore[override]
        year = datetime.now().year
        unit = getattr(self.controller, "unit_name", "Unit")
        return ui.nav_panel(
            t("nav.dashboard"),
            ui.h2(f"📊 {unit} Dashboard {year}"),
            ui.input_action_button(
                "dashboard_refresh_btn",
                t("common.refresh"),
                class_="btn btn-secondary btn-sm my-2",
            ),
            ui.br(),
            # ----- Stats cards row -----
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("dashboard.unit_personnel"), class_="bg-secondary text-white"),
                    ui.output_ui("own_unit_personnel_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header(t("dashboard.phef_tests"), class_="bg-primary text-white"),
                    ui.output_ui("own_unit_phef_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header(t("dashboard.combat_tests"), class_="bg-success text-white"),
                    ui.output_ui("own_unit_combat_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header(t("dashboard.swimming_tests"), class_="bg-info text-white"),
                    ui.output_ui("own_unit_swimming_stats"),
                    class_="text-center",
                ),
                ui.card(
                    ui.card_header(t("dashboard.march_tests"), class_="bg-info text-white"),
                    ui.output_ui("own_unit_march_stats"),
                    class_="text-center",
                ),
            ),
            ui.br(),
            # ----- Broker / HR System health row -----
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        t("dashboard.broker"),
                        class_="text-dark fw-bold",
                        style=(
                            "background-color:#ffc107;"
                            " border-bottom:2px solid #b88600;"
                            " font-size:1.05rem;"
                        ),
                    ),
                    ui.output_ui("broker_health_card"),
                    full_screen=False,
                ),
            ),
            ui.br(),
            # ----- Charts row: side-by-side -----
            ui.layout_columns(
                ui.card(
                    ui.card_header(t("dashboard.pass_fail_chart")),
                    ui.output_ui("own_unit_pass_fail_chart"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header(t("dashboard.phef_dist_chart")),
                    ui.output_ui("own_unit_phef_score_histogram"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
            ui.br(),
            value=self.TAB_NAME,
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
                    "sub_label": t("dashboard.unavailable").format(error=e),
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
            total_text=t("dashboard.service_members"),
            fetcher=self.controller.personnel_stats,
        )
        _register_stats_output(
            output_id="own_unit_phef_stats",
            total_text=t("dashboard.total_tests"),
            fetcher=self.controller.phef_stats,
        )
        _register_stats_output(
            output_id="own_unit_combat_stats",
            total_text=t("dashboard.total_tests"),
            fetcher=self.controller.combat_stats,
        )
        _register_stats_output(
            output_id="own_unit_swimming_stats",
            total_text=t("dashboard.total_tests"),
            fetcher=self.controller.swimming_stats,
        )
        _register_stats_output(
            output_id="own_unit_march_stats",
            total_text=t("dashboard.total_tests"),
            fetcher=self.controller.march_stats,
        )

        # Register charts (same error/empty handling)
        _register_plotly_html_output(
            output_id="own_unit_pass_fail_chart",
            fetcher=self.controller.pass_fail_bar_html,
            empty_msg=t("dashboard.no_chart"),
            non_div_msg=t("dashboard.no_chart"),
        )
        _register_plotly_html_output(
            output_id="own_unit_phef_score_histogram",
            fetcher=self.controller.phef_hist_html,  # type: ignore[arg-type]
            empty_msg=t("dashboard.no_phef_data"),
            non_div_msg=t("dashboard.no_chart"),
        )

        # Broker / HR System health card.
        # Refreshes on the same tick as the rest of the dashboard so manual refresh works,
        # plus a slow auto-refresh so a fresh outage shows up without a click.
        @output(id="broker_health_card")
        @render.ui
        async def _broker_health() -> ui.Tag:
            _ = refresh_tick.get()
            reactive.invalidate_later(15)
            try:
                h = await self.controller.broker_health()
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                return self._no_data(t("dashboard.unavailable").format(error=e))

            badge = ui.span(
                h.get("badge_label", "Unknown"),
                class_=f"badge {h.get('badge_class', 'bg-secondary')} fs-6",
            )

            details_left = ui.div(
                ui.p(
                    ui.strong(t("dashboard.hr_endpoint")),
                    ui.tags.code(h.get("hr_url", "—")),
                    class_="mb-1",
                ),
                ui.p(
                    ui.strong(t("dashboard.database")),
                    t("dashboard.reachable") if h.get("db_ok") else t("dashboard.unreachable"),
                    class_="mb-1",
                ),
            )

            pending = int(h.get("pending", 0))
            dead = int(h.get("dead_letter", 0))
            details_middle = ui.div(
                ui.p(
                    ui.strong(t("dashboard.pending_msgs")),
                    ui.span(
                        str(pending),
                        class_=("fw-bold " + ("text-warning" if pending > 0 else "text-success")),
                    ),
                    class_="mb-1",
                ),
                ui.p(
                    ui.strong(t("dashboard.dead_letter")),
                    ui.span(
                        str(dead),
                        class_=("fw-bold " + ("text-danger" if dead > 0 else "text-success")),
                    ),
                    class_="mb-1",
                ),
                ui.p(
                    ui.strong(t("dashboard.oldest_pending")),
                    h.get("oldest_pending_age_human", "—"),
                    class_="mb-1",
                ),
            )

            last_err = h.get("last_error")
            details_right = ui.div(
                ui.p(ui.strong(t("dashboard.last_error")), class_="mb-1"),
                (
                    ui.tags.code(
                        str(last_err)[:300],
                        class_="text-danger d-block",
                        style="white-space:pre-wrap; word-break:break-word;",
                    )
                    if last_err
                    else ui.p(t("dashboard.no_recent_errors"), class_="text-muted")
                ),
            )

            return ui.div(
                ui.div(
                    ui.h5(t("dashboard.status"), class_="d-inline me-2 mb-0"),
                    badge,
                    class_="mb-3",
                ),
                ui.layout_columns(
                    details_left, details_middle, details_right, col_widths=[3, 4, 5]
                ),
                class_="p-3",
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
