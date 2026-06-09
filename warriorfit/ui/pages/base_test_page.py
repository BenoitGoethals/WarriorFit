"""Base class for test pages with common functionality."""

from __future__ import annotations

import contextlib
from abc import abstractmethod
from typing import Any

import pandas as pd
from shiny import reactive, ui

from warriorfit.data.model.db_model import ServiceMen, TestSession
from warriorfit.i18n import t
from warriorfit.ui.pages.page import Page


class BaseTestPage(Page):
    """Base class for test pages with session and military selection."""

    def __init__(self):
        super().__init__()
        self.selected_military: ServiceMen | None = None
        self.selected_session: TestSession | None = None

    def refresh(self) -> None:
        """Refresh the page by incrementing the refresh tick."""
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    @abstractmethod
    def get_prefix(self) -> str:
        """Return the input ID prefix for this page (e.g., 'combat', 'swim')."""
        raise NotImplementedError

    @abstractmethod
    def get_tab_name(self) -> str:
        """Return the tab name for this page."""
        raise NotImplementedError

    # -------------------------
    # Session Management
    # -------------------------
    def setup_session_management(
        self,
        input: Any,
        session: Any,
        selected_session_id: reactive.Value,
        status: reactive.Value,
        controller: Any,
    ) -> None:
        """Setup reactive effects for session management."""
        prefix = self.get_prefix()

        @reactive.Effect
        async def _on_session_change() -> None:
            val = (getattr(input, f"{prefix}_session_id")() or "").strip()
            selected_session_id.set(val)
            await self._clear_form_hook(input, session)
            self.selected_session = None
            if not val:
                status.set(t("common.select_session"))
                return
            status.set(t("common.session_selected_confirm"))

        @reactive.Effect
        @reactive.event(getattr(input, f"{prefix}_session_id"))
        async def _load_session_object() -> None:
            val = (getattr(input, f"{prefix}_session_id")() or "").strip()
            if not val:
                self.selected_session = None
                return
            try:
                # Try get_session_by_id first (most controllers), fall back to get_test_session_by_id
                if hasattr(controller, "get_session_by_id"):
                    self.selected_session = await controller.get_session_by_id(int(val))
                else:
                    self.selected_session = await controller.get_test_session_by_id(int(val))
            except Exception:
                self.selected_session = None

    async def refresh_session_choices(self, input: Any, controller: Any) -> None:
        """Refresh the session dropdown choices."""
        prefix = self.get_prefix()
        try:
            test_sessions = await controller.load_sessions()
        except Exception:
            test_sessions = []

        items = {
            str(s.id): f"{s.datetime_start.strftime('%Y-%m-%d %H:%M')} {s.type_test.name}"
            for s in (test_sessions or [])
        }
        current = (getattr(input, f"{prefix}_session_id")() or "").strip()
        ui.update_select(
            f"{prefix}_session_id",
            choices=items,
            selected=(current if current in items else None),
        )

    # -------------------------
    # Serial Number Search
    # -------------------------
    # NOTE: Due to Shiny's @output decorator limitations, each page must implement
    # its own serial search modal (the @render.data_frame grid and selection
    # @reactive.event must register with page-specific input IDs). The data-loading
    # logic below has no decorator dependency, so it is shared here.
    async def fetch_all_servicemen_df(self, controller: Any) -> pd.DataFrame:
        """Build a DataFrame of all servicemen for the serial-search grid.

        Returns columns: service_number, first_name, last_name, gender — sorted
        by service_number. Returns an empty (but correctly-columned) DataFrame
        when there are no servicemen.
        """
        servicemen = await controller.be_mil_service.get_all_service_men()
        if not servicemen:
            return pd.DataFrame(columns=["service_number", "first_name", "last_name", "gender"])

        df = pd.DataFrame(
            [
                {
                    "service_number": s.service_number,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "gender": s.gender,
                }
                for s in servicemen
            ]
        )
        return df.sort_values(by=["service_number"])

    # -------------------------
    # Military Search
    # -------------------------
    async def search_set_military(
        self,
        controller: Any,
        serial: str,
        military_text: reactive.Value,
        status: reactive.Value,
    ) -> ServiceMen | None:
        """Resolve a serviceman by serial and update ``selected_military``.

        Performs the controller lookup (swallowing errors), stores the result on
        ``self.selected_military``, and on a miss sets the not-found ``military_text``
        and ``status`` messages. Returns the serviceman, or ``None`` when not found.

        The caller remains responsible for the page-specific confirmed-state
        presentation (military text format, input toggling, button enabling), which
        differs between pages.
        """
        try:
            val = await controller.search_military(serial)
        except Exception:
            val = None

        self.selected_military = val
        if val is None:
            military_text.set(t("common.not_found"))
            status.set(t("common.serial_not_found"))
        return val

    # -------------------------
    # UI State Helpers
    # -------------------------
    async def toggle_inputs(
        self, session: Any, disable_ids: tuple[str, ...], disabled: bool
    ) -> None:
        """Toggle input disabling via custom message."""
        with contextlib.suppress(Exception):
            await session.send_custom_message(
                "wf_toggle_disabled",
                {"ids": list(disable_ids), "disabled": bool(disabled)},
            )

    def set_buttons(self, prefix: str, can_add: bool, can_update: bool) -> None:
        """Set button states."""
        ui.update_action_button(f"{prefix}_add_btn", disabled=not can_add)
        ui.update_action_button(f"{prefix}_update_btn", disabled=not can_update)

    def require_session_selected(
        self, selected_session_id: reactive.Value, status: reactive.Value
    ) -> bool:
        """Check if session is selected. Returns True if valid."""
        if not (selected_session_id.get() or "").strip():
            status.set(t("common.select_session_first"))
            return False
        return True

    def require_military_selected(self, status: reactive.Value) -> bool:
        """Check if military is selected. Returns True if valid."""
        if self.selected_military is None:
            status.set(t("common.confirm_valid_serial"))
            return False
        return True

    # -------------------------
    # Abstract Methods
    # -------------------------
    @abstractmethod
    async def _clear_form_hook(self, input: Any, session: Any) -> None:
        """Hook for page-specific form clearing logic."""
        raise NotImplementedError
