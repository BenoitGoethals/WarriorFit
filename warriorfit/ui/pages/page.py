import inspect
from abc import ABC, abstractmethod

from shiny import reactive, ui


class Page(ABC):
    """
    Abstract base class representing a web application page.

    This class serves as a blueprint for implementing specific pages in a web
    application. It enforces the implementation of methods for user interface
    generation, server-side logic, and page refresh functionalities. Additionally,
    it contains utility methods to enhance user experience, such as a password
    input with a toggle button and automatic refresh behavior when navigating to
    specific tabs.

    :ivar refresh_tick: Reactive value to track refresh ticks for the page.
    :type refresh_tick: reactive.Value
    """
    toggle_disabled_registered_func = """
                (function () {
                  if (window.__wf_toggle_disabled_registered) return;
                  window.__wf_toggle_disabled_registered = true;

                  Shiny.addCustomMessageHandler("wf_toggle_disabled", function (payload) {
                    try {
                      const ids = (payload && payload.ids) ? payload.ids : [];
                      const disabled = !!(payload && payload.disabled);
                      ids.forEach((id) => {
                        const el = document.getElementById(id);
                        if (el) el.disabled = disabled;
                      });
                    } catch (e) {
                      // no-op
                    }
                  });
                })();
                """

    def __init__(self):
        self.refresh_tick = reactive.Value(0)

    @abstractmethod
    def get_ui(self) -> ui.Tag:
        raise NotImplementedError

    @abstractmethod
    def server(self, input, output, session):
        raise NotImplementedError

    @abstractmethod
    def refresh(self):
        pass

    @staticmethod
    def input_password_with_toggle(input_id: str, label: str | None = None) -> ui.Tag:
        """Password input with a show/hide toggle button."""
        btn_js = (
            f"var i=document.getElementById('{input_id}');"
            "if(i.type==='password'){i.type='text';this.textContent='🙈';}"
            "else{i.type='password';this.textContent='👁';}"
        )
        input_group = ui.div(
            ui.tags.input(
                id=input_id,
                type="password",
                class_="form-control",
                value="",
                autocomplete="off",
            ),
            ui.tags.button(
                "👁",
                type="button",
                class_="btn btn-outline-secondary",
                title="Show/hide password",
                onclick=btn_js,
            ),
            class_="input-group",
        )
        children: list = [input_group]
        if label:
            children = [
                ui.tags.label(label, for_=input_id, class_="form-label")
            ] + children
        return ui.div(*children, class_="form-group shiny-input-container")

    def refresh_on_nav(self, input, tab_name: str, refresh_tick=None):
        """
        Sets up a reactive effect to refresh the page when the specific tab is selected.
        Requires 'self.refresh_tick' (reactive.Value) to be present on the instance
        OR 'refresh_tick' passed as an argument.
        """

        @reactive.Effect
        @reactive.event(input.main_nav)
        async def _refresh_on_nav():
            try:
                # Check if the current tab matches the tab_name
                if input.main_nav() == tab_name:
                    if inspect.iscoroutinefunction(self.refresh):
                        await self.refresh()
                    else:
                        self.refresh()
                    target_tick = (
                        refresh_tick
                        if refresh_tick is not None
                        else getattr(self, "refresh_tick", None)
                    )

                    if target_tick is not None:
                        # Increment to trigger reactive dependencies
                        # We use .get() inside an isolate if we want to avoid dependency loop
                        # but @reactive.event handles the trigger isolation.
                        # However, reading the value is fine.
                        current = target_tick.get()
                        target_tick.set(current + 1)
            except Exception:
                # input.main_nav might not be ready
                pass
