"""Privacy / GDPR self-service page.

Provides each logged-in user with:
- Art. 15/20: download a JSON export of their personal data
- Art. 17: request account + data erasure
- Art. 7:  view and manage consents
- Art. 13: link to the privacy notice
"""

from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.core.container import Container
from warriorfit.ui.controllers.privacy_controller import PrivacyController
from warriorfit.ui.pages.page import Page
from warriorfit.ui.user_store import UserStore


class PrivacyPage(Page):
    @inject
    def __init__(
        self,
        controller: PrivacyController = Provide[Container.privacy_controller],
    ):
        super().__init__()
        self.controller = controller
        self._export_payload: reactive.Value[str] = reactive.Value("")

    def refresh(self):
        self.refresh_tick.set(self.refresh_tick.get() + 1)

    def get_ui(self):
        return ui.nav_panel(
            "Privacy",
            ui.div(
                ui.h2("Privacy & Your Data", class_="mb-3"),
                ui.p(
                    "WarriorFit processes your personal and fitness data under "
                    "the EU General Data Protection Regulation (GDPR). "
                    "Use this page to exercise your rights.",
                    class_="text-muted",
                ),
                ui.hr(),
                ui.h4("Your consents"),
                ui.output_ui("privacy_consent_block"),
                ui.hr(),
                ui.h4("Export your data (Art. 15 / 20)"),
                ui.p(
                    "Download a machine-readable copy of all personal data "
                    "WarriorFit holds about you."
                ),
                ui.input_action_button(
                    "privacy_export_btn",
                    "Prepare export",
                    class_="btn btn-primary me-2",
                ),
                ui.output_ui("privacy_export_download"),
                ui.hr(),
                ui.h4("Erase your account (Art. 17)"),
                ui.p(
                    ui.tags.strong("Warning:"),
                    " this permanently deletes your user account, serviceman "
                    "profile, fitness results, marches and reservations.",
                    class_="text-danger",
                ),
                ui.input_action_button(
                    "privacy_erase_btn",
                    "Permanently delete my data",
                    class_="btn btn-danger",
                ),
                ui.output_text("privacy_status"),
                class_="container-fluid p-4",
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("")

        @output
        @render.ui
        async def privacy_consent_block():
            self.refresh_tick.get()
            user = UserStore.get_user()
            if user is None:
                return ui.p("Log in to manage consents.")
            consents = await self.controller.consents(user.id)
            rows = []
            for ct in PrivacyController.available_consent_types():
                active = next(
                    (c for c in consents if c["type"] == ct and c["withdrawn_at"] is None),
                    None,
                )
                label = ct.replace("_", " ").title()
                if active:
                    rows.append(
                        ui.div(
                            ui.span(f"{label} — granted {active['given_at']}"),
                            ui.input_action_button(
                                f"withdraw_{ct}",
                                "Withdraw",
                                class_="btn btn-sm btn-outline-warning ms-2",
                            ),
                            class_="mb-2",
                        )
                    )
                else:
                    rows.append(
                        ui.div(
                            ui.span(f"{label} — not granted"),
                            ui.input_action_button(
                                f"grant_{ct}",
                                "Grant",
                                class_="btn btn-sm btn-outline-primary ms-2",
                            ),
                            class_="mb-2",
                        )
                    )
            return ui.div(*rows)

        def _register_consent_buttons():
            for ct in PrivacyController.available_consent_types():

                def _make_grant(ct=ct):
                    @reactive.Effect
                    @reactive.event(getattr(input, f"grant_{ct}"))
                    async def _grant():
                        user = UserStore.get_user()
                        if user is None:
                            return
                        ok = await self.controller.grant(user.id, ct)
                        status.set(f"Consent '{ct}' granted." if ok else "Grant failed.")
                        self.refresh()

                    return _grant

                def _make_withdraw(ct=ct):
                    @reactive.Effect
                    @reactive.event(getattr(input, f"withdraw_{ct}"))
                    async def _withdraw():
                        user = UserStore.get_user()
                        if user is None:
                            return
                        ok = await self.controller.withdraw(user.id, ct)
                        status.set(
                            f"Consent '{ct}' withdrawn." if ok else "Withdraw failed."
                        )
                        self.refresh()

                    return _withdraw

                _make_grant()
                _make_withdraw()

        _register_consent_buttons()

        @reactive.Effect
        @reactive.event(input.privacy_export_btn)
        async def _on_export():
            user = UserStore.get_user()
            if user is None:
                status.set("Not logged in.")
                return
            payload = await self.controller.export_json(user.id)
            if payload is None:
                status.set("Export failed.")
                return
            self._export_payload.set(payload)
            status.set("Export ready — click Download.")

        @output
        @render.ui
        def privacy_export_download():
            payload = self._export_payload.get()
            if not payload:
                return ui.div()
            return ui.download_button("privacy_export_dl", "Download JSON")

        @session.download(filename="warriorfit-export.json")
        def privacy_export_dl():
            yield self._export_payload.get()

        @reactive.Effect
        @reactive.event(input.privacy_erase_btn)
        async def _on_erase():
            user = UserStore.get_user()
            if user is None:
                status.set("Not logged in.")
                return
            ok = await self.controller.erase(user.id)
            if ok:
                status.set("Your data has been erased. Please log out.")
            else:
                status.set("Erasure failed.")

        @output
        @render.text
        def privacy_status():
            return status.get()


_page: PrivacyPage | None = None


def _get_page() -> PrivacyPage:
    global _page
    if _page is None:
        _page = PrivacyPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
