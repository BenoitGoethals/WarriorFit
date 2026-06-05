import pandas as pd
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.i18n import t
from warriorfit.ui.controllers.cross_statics_controller import CrossStaticsController
from warriorfit.ui.pages.page import Page
from warriorfit.utils.formaters import Formatter


class CrossStaticsPage(Page):
    @inject
    def __init__(
        self,
        controller: CrossStaticsController = Provide[
            Container.cross_statics_controller
        ],
    ):
        super().__init__()
        self._controller = controller

    async def refresh(self):
        await self._controller.load()

    # ----------------------------
    # UI
    # ----------------------------

    def get_ui(self):
        return ui.nav_panel(
            t("nav.cross_statics"),
            ui.div(
                ui.h2(t("cross_stats.title")),
                ui.div(
                    ui.input_action_button(
                        "cs_refresh_btn",
                        t("common.refresh"),
                        class_="btn btn-secondary btn-sm",
                    ),
                    class_="ms-auto",
                ),
                class_="d-flex align-items-center mb-3",
            ),
            # KPI strip — only distance-agnostic counts here.
            # Time KPIs (best/avg/median) live in the per-distance grid below.
            ui.layout_columns(
                ui.value_box(t("cross_stats.crosses"), ui.output_text("kpi_crosses"), theme="primary"),
                ui.value_box(
                    t("cross_stats.finishers"), ui.output_text("kpi_finishers"), theme="primary"
                ),
                ui.value_box(
                    t("cross_stats.unique_runners"), ui.output_text("kpi_unique"), theme="primary"
                ),
                col_widths=[4, 4, 4],
            ),
            ui.br(),
            ui.navset_card_tab(
                # ----- Overview -----
                ui.nav_panel(
                    t("cross_stats.overview"),
                    ui.card(
                        ui.card_header(
                            t("cross_stats.best_avg_median"),
                            class_="bg-primary text-white",
                        ),
                        ui.output_data_frame("overview_per_distance_grid"),
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header(
                                t("cross_stats.gender_averages"), class_="bg-primary text-white"
                            ),
                            ui.output_ui("overview_gender"),
                        ),
                        ui.card(
                            ui.card_header(
                                t("cross_stats.age_groups"),
                                class_="bg-primary text-white",
                            ),
                            ui.output_ui("overview_age_group"),
                        ),
                        col_widths=[6, 6],
                    ),
                ),
                # ----- Per cross -----
                ui.nav_panel(
                    t("cross_stats.per_cross"),
                    ui.card(
                        ui.card_header(
                            t("cross_stats.all_crosses"),
                            class_="bg-success text-white",
                        ),
                        ui.output_data_frame("per_cross_grid"),
                    ),
                ),
                # ----- Best 10 -----
                ui.nav_panel(
                    t("cross_stats.best_10"),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header(
                                t("cross_stats.best_10_5km"), class_="bg-success text-white"
                            ),
                            ui.output_data_frame("best_10_all_grid_5"),
                        ),
                        ui.card(
                            ui.card_header(
                                t("cross_stats.best_10_10km"), class_="bg-success text-white"
                            ),
                            ui.output_data_frame("best_10_all_grid_10"),
                        ),
                        col_widths=[6, 6],
                    ),
                ),
                # ----- Demographics -----
                ui.nav_panel(
                    t("cross_stats.demographics"),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header(
                                t("cross_stats.best_per_age"),
                                class_="bg-info text-white",
                            ),
                            ui.output_data_frame("age_distance_best_grid"),
                        ),
                        ui.card(
                            ui.card_header(
                                t("cross_stats.avg_per_age"),
                                class_="bg-info text-white",
                            ),
                            ui.output_data_frame("age_distance_avg_grid"),
                        ),
                        col_widths=[6, 6],
                    ),
                    ui.card(
                        ui.card_header(
                            t("cross_stats.gender_split"), class_="bg-info text-white"
                        ),
                        ui.output_data_frame("gender_distance_grid"),
                    ),
                ),
                # ----- Runners -----
                ui.nav_panel(
                    t("cross_stats.runners"),
                    ui.card(
                        ui.card_header(
                            t("cross_stats.per_runner"),
                            class_="bg-success text-white",
                        ),
                        ui.output_data_frame("per_runner_grid"),
                    ),
                ),
                # ----- Trends -----
                ui.nav_panel(
                    "Trends",
                    ui.card(
                        ui.card_header(
                            "Average running time per cross over time",
                            class_="bg-warning text-dark",
                        ),
                        ui.output_data_frame("trends_grid"),
                    ),
                ),
                # ----- Podium -----
                ui.nav_panel(
                    "Podium",
                    ui.card(
                        ui.card_header(
                            "Most frequent podium finishers",
                            class_="bg-warning text-dark",
                        ),
                        ui.output_data_frame("podium_grid"),
                    ),
                ),
                # ----- Data quality -----
                ui.nav_panel(
                    "Data quality",
                    ui.layout_columns(
                        ui.value_box(
                            "Rows missing time",
                            ui.output_text("dq_missing_times"),
                            theme="danger",
                        ),
                        ui.value_box(
                            "Unmatched serials",
                            ui.output_text("dq_unmatched_count"),
                            theme="warning",
                        ),
                        ui.value_box(
                            "Never raced",
                            ui.output_text("dq_never_raced_count"),
                            theme="secondary",
                        ),
                        col_widths=[4, 4, 4],
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header(
                                "Serials present in cross data but not in registry",
                                class_="bg-danger text-white",
                            ),
                            ui.output_ui("dq_unmatched_list"),
                        ),
                        ui.card(
                            ui.card_header(
                                "Servicemen registered but never raced",
                                class_="bg-secondary text-white",
                            ),
                            ui.output_ui("dq_never_raced_list"),
                        ),
                        col_widths=[6, 6],
                    ),
                ),
            ),
            value="Cross Statics",
        )

    # ----------------------------
    # Server
    # ----------------------------

    def server(self, input, output, session):
        self.refresh_tick = reactive.Value(0)
        self.refresh_on_nav(input, "Cross Statics", self.refresh_tick)

        @reactive.Effect
        async def _init():
            await self._controller.load()

        @reactive.Effect
        @reactive.event(input.cs_refresh_btn)
        async def _on_cs_refresh():
            await self.refresh()
            self.refresh_tick.set(self.refresh_tick.get() + 1)

        # ----- KPIs -----

        @output
        @render.text
        async def kpi_crosses():
            _ = self.refresh_tick.get()
            ov = await self._controller.overview()
            return str(ov.get("total_crosses", 0))

        @output
        @render.text
        async def kpi_finishers():
            _ = self.refresh_tick.get()
            ov = await self._controller.overview()
            return str(ov.get("total_finishers", 0))

        @output
        @render.text
        async def kpi_unique():
            _ = self.refresh_tick.get()
            ov = await self._controller.overview()
            return str(ov.get("unique_runners", 0))

        # ----- Overview cards -----

        @output
        @render.data_frame
        async def overview_per_distance_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.overview_per_distance_df()
            if df.empty:
                df = pd.DataFrame(
                    columns=[
                        "Dist (km)",
                        "Finishers",
                        "Runners",
                        "Best",
                        "Avg",
                        "Median",
                        "Std (s)",
                        "Gap",
                    ]
                )
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        @output
        @render.ui
        async def overview_gender():
            _ = self.refresh_tick.get()
            f_avg, m_avg = await self._controller.get_gender_time()
            return ui.tags.ul(
                ui.tags.li(f"Female avg: {Formatter.format_time(f_avg)}"),
                ui.tags.li(f"Male avg: {Formatter.format_time(m_avg)}"),
            )

        @output
        @render.ui
        async def overview_age_group():
            _ = self.refresh_tick.get()
            ages: dict[str, int] = await self._controller.get_age_group()
            if not ages:
                return ui.p("No data available.")
            items = [ui.tags.li(f"{key}: {value}") for key, value in ages.items()]
            return ui.tags.ul(*items)

        # ----- Best 10 grids (legacy preserved) -----

        @output
        @render.data_frame
        async def best_10_all_grid_5():
            _ = self.refresh_tick.get()
            dfc = await self._controller.best_10_all_df()
            df = dfc.get(5)
            if df is None or df.empty:
                df = pd.DataFrame(
                    columns=[
                        "rank",
                        "serial_number",
                        "Name",
                        "running_time",
                        "distance",
                        "age",
                    ]
                )
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        @output
        @render.data_frame
        async def best_10_all_grid_10():
            _ = self.refresh_tick.get()
            dfc = await self._controller.best_10_all_df()
            df = dfc.get(10)
            if df is None or df.empty:
                df = pd.DataFrame(
                    columns=[
                        "rank",
                        "serial_number",
                        "Name",
                        "running_time",
                        "distance",
                        "age",
                    ]
                )
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        # ----- Per-cross -----

        @output
        @render.data_frame
        async def per_cross_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.per_cross_df()
            if df.empty:
                df = pd.DataFrame(columns=["Cross", "Date", "Dist (km)", "Finishers"])
            return render.DataGrid(
                df, filters=True, selection_mode="none", width="100%"
            )

        # ----- Demographics -----

        @output
        @render.data_frame
        async def age_distance_best_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.age_distance_best_df()
            if df.empty:
                df = pd.DataFrame(columns=["Age group", "Dist (km)", "Best"])
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        @output
        @render.data_frame
        async def age_distance_avg_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.age_distance_avg_df()
            if df.empty:
                df = pd.DataFrame(columns=["Age group", "Dist (km)", "Avg"])
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        @output
        @render.data_frame
        async def gender_distance_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.gender_distance_df()
            if df.empty:
                df = pd.DataFrame(columns=["Gender", "Dist (km)", "Avg", "Finishers"])
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        # ----- Runners -----

        @output
        @render.data_frame
        async def per_runner_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.per_runner_df()
            if df.empty:
                df = pd.DataFrame(
                    columns=["Serial", "Name", "Races", "PB", "Avg", "Pace", "Δ avg"]
                )
            return render.DataGrid(
                df, filters=True, selection_mode="none", width="100%"
            )

        # ----- Trends -----

        @output
        @render.data_frame
        async def trends_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.trends_df()
            if df.empty:
                df = pd.DataFrame(columns=["Date", "Dist (km)", "Avg"])
            return render.DataGrid(
                df, filters=False, selection_mode="none", width="100%"
            )

        # ----- Podium -----

        @output
        @render.data_frame
        async def podium_grid():
            _ = self.refresh_tick.get()
            df = await self._controller.podium_df()
            if df.empty:
                df = pd.DataFrame(
                    columns=["Serial", "Name", "Podiums", "🥇", "🥈", "🥉"]
                )
            return render.DataGrid(
                df, filters=True, selection_mode="none", width="100%"
            )

        # ----- Data quality -----

        @output
        @render.text
        async def dq_missing_times():
            _ = self.refresh_tick.get()
            dq = await self._controller.data_quality()
            return str(dq.get("rows_missing_time", 0))

        @output
        @render.text
        async def dq_unmatched_count():
            _ = self.refresh_tick.get()
            dq = await self._controller.data_quality()
            return str(len(dq.get("unmatched_serials", [])))

        @output
        @render.text
        async def dq_never_raced_count():
            _ = self.refresh_tick.get()
            dq = await self._controller.data_quality()
            return str(len(dq.get("never_raced_serials", [])))

        @output
        @render.ui
        async def dq_unmatched_list():
            _ = self.refresh_tick.get()
            dq = await self._controller.data_quality()
            serials = dq.get("unmatched_serials", [])
            if not serials:
                return ui.p("✅ All cross serials match a registered serviceman.")
            items = [ui.tags.li(s) for s in serials[:200]]
            return ui.tags.ul(*items)

        @output
        @render.ui
        async def dq_never_raced_list():
            _ = self.refresh_tick.get()
            dq = await self._controller.data_quality()
            serials = dq.get("never_raced_serials", [])
            if not serials:
                return ui.p("✅ All registered servicemen have raced at least once.")
            items = [ui.tags.li(s) for s in serials[:200]]
            return ui.tags.ul(*items)


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = CrossStaticsPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    return _get_page().server(input, output, session)
