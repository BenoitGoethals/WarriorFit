import os
import time

import psutil
from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.ui.controllers.StatusApplicationController import (
    StatusApplicationController,
)
from warriorfit.ui.pages.page import Page

_process = psutil.Process(os.getpid())
_start_time = time.time()


class StatusApplicationPage(Page):
    @inject
    def __init__(
        self,
        controller: StatusApplicationController = Provide[Container.status_application_controller],
    ):
        super().__init__()
        self._controller = controller

    def refresh(self):
        pass

    @staticmethod
    def _metric_card(label: str, output_id: str, icon: str) -> ui.Tag:
        return ui.card(
            ui.card_header(
                ui.div(ui.tags.span(icon, class_="me-2"), label),
            ),
            ui.output_ui(output_id),
            class_="text-center",
        )

    def get_ui(self):
        return ui.nav_panel(
            "Status Application",
            ui.h2("Application Status Dashboard"),
            # ── Service connectivity ──────────────────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Database Connectivity"),
                    ui.output_text("db_status_display"),
                ),
                ui.card(
                    ui.card_header("HR Service Ops"),
                    ui.output_text("hr_status_display"),
                ),
                ui.card(
                    ui.card_header("Mail Server Status"),
                    ui.output_text("mail_server_status_display"),
                ),
                ui.card(
                    ui.card_header("Server Status"),
                    ui.output_text("server_status_display"),
                ),
            ),
            # ── Runtime memory & process metrics ─────────────────────
            ui.div(
                ui.div("Runtime Metrics", class_="wf-section-label mt-3 mb-2 px-1"),
                ui.layout_columns(
                    self._metric_card("Physical Memory (RSS)", "mem_rss", "🧠"),
                    self._metric_card("Virtual Memory (VMS)", "mem_vms", "💾"),
                    self._metric_card("CPU Usage", "mem_cpu", "⚙️"),
                    self._metric_card("Threads", "mem_threads", "🔀"),
                    self._metric_card("Uptime", "mem_uptime", "⏱️"),
                ),
            ),
            # ── Log file ─────────────────────────────────────────────
            ui.layout_columns(
                ui.card(
                    ui.card_header("Log File"),
                    ui.div(
                        ui.output_text_verbatim("lof_file"),
                        style="max-height: 600px; overflow-y: auto;",
                    ),
                ),
            ),
        )

    def server(self, input, output, session):
        refresh_tick = reactive.Value(0)

        self.refresh_on_nav(input, "Status Application", refresh_tick)

        @output
        @render.text
        async def db_status_display():
            return await self._controller.status_db()

        @output
        @render.text
        async def hr_status_display():
            return await self._controller.status_hr()

        @output
        @render.text
        async def mail_server_status_display():
            return await self._controller.status_mail_server()

        @output
        @render.text
        async def server_status_display():
            return await self._controller.status_server()

        # ── Runtime memory helpers ────────────────────────────────────
        def _big_metric(value: str, unit: str, sub: str = "") -> ui.Tag:
            return ui.div(
                ui.div(
                    ui.tags.span(
                        value,
                        style="font-size:2rem; font-weight:700; color:var(--wf-primary);",
                    ),
                    ui.tags.span(
                        f" {unit}",
                        style="font-size:0.9rem; color:var(--wf-text-muted);",
                    ),
                ),
                (
                    ui.div(sub, style="font-size:0.78rem; color:var(--wf-text-muted);")
                    if sub
                    else ui.div()
                ),
                style="padding:0.5rem 0;",
            )

        @output
        @render.ui
        def mem_rss():
            reactive.invalidate_later(5)
            rss = _process.memory_info().rss / 1024 / 1024
            return _big_metric(f"{rss:.1f}", "MB", "Resident Set Size")

        @output
        @render.ui
        def mem_vms():
            reactive.invalidate_later(5)
            vms = _process.memory_info().vms / 1024 / 1024
            return _big_metric(f"{vms:.1f}", "MB", "Virtual Memory Size")

        @output
        @render.ui
        def mem_cpu():
            reactive.invalidate_later(5)
            cpu = _process.cpu_percent(interval=None)
            return _big_metric(f"{cpu:.1f}", "%", f"{psutil.cpu_count()} cores total")

        @output
        @render.ui
        def mem_threads():
            reactive.invalidate_later(5)
            n = _process.num_threads()
            return _big_metric(str(n), "threads")

        @output
        @render.ui
        def mem_uptime():
            reactive.invalidate_later(5)
            elapsed = int(time.time() - _start_time)
            h, r = divmod(elapsed, 3600)
            m, s = divmod(r, 60)
            return _big_metric(f"{h:02d}:{m:02d}:{s:02d}", "", "hh:mm:ss")

        def check_log_modified():
            return self._controller.check_log_modified()

        @reactive.poll(check_log_modified, 2.0)
        async def read_log():
            return await self._controller.load_log_application()

        @output
        @render.text
        async def lof_file():
            return await read_log()


_page = None


def _get_page():
    global _page
    if _page is None:
        _page = StatusApplicationPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
