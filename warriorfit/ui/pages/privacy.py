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
                ui.div(
                    ui.tags.strong("Not available. "),
                    "By organisational regulations, your fitness records and "
                    "service file must be retained for the statutory period and "
                    "cannot be erased on request. Contact your unit admin or "
                    "the Defence DPO for restriction or rectification requests.",
                    class_="alert alert-warning",
                ),
                ui.output_text("privacy_status"),
                class_="container-fluid p-4",
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("")
        export_payload: reactive.Value[str] = reactive.Value("")

        @output
        @render.ui
        async def privacy_consent_block():
            self.refresh_tick.get()
            user = UserStore.get_user()
            if user is None:
                return ui.p("Log in to manage consents.")
            serial = PrivacyController.serviceman_serial(user)
            if serial is None:
                return ui.div(
                    "Privacy actions are only available when logged in as a "
                    "serviceman. Please log out and log in using Serviceman mode.",
                    class_="alert alert-info",
                )
            consents = await self.controller.consents(serial)
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

        for ct in PrivacyController.available_consent_types():
            grant_id = f"grant_{ct}"
            withdraw_id = f"withdraw_{ct}"

            def _bind_grant(ct=ct, grant_id=grant_id):
                @reactive.effect
                @reactive.event(input[grant_id])
                async def _():
                    serial = PrivacyController.serviceman_serial(UserStore.get_user())
                    if serial is None:
                        status.set("Log in as a serviceman to manage consents.")
                        return
                    try:
                        ok = await self.controller.grant(serial, ct)
                    except Exception as e:
                        status.set(f"Grant '{ct}' error: {e}")
                        self.refresh()
                        return
                    status.set(f"Consent '{ct}' granted." if ok else f"Grant '{ct}' failed.")
                    self.refresh()

            def _bind_withdraw(ct=ct, withdraw_id=withdraw_id):
                @reactive.effect
                @reactive.event(input[withdraw_id])
                async def _():
                    serial = PrivacyController.serviceman_serial(UserStore.get_user())
                    if serial is None:
                        status.set("Log in as a serviceman to manage consents.")
                        return
                    try:
                        ok = await self.controller.withdraw(serial, ct)
                    except Exception as e:
                        status.set(f"Withdraw '{ct}' error: {e}")
                        self.refresh()
                        return
                    status.set(
                        f"Consent '{ct}' withdrawn." if ok else f"Withdraw '{ct}' failed."
                    )
                    self.refresh()

            _bind_grant()
            _bind_withdraw()

        @reactive.effect
        @reactive.event(input.privacy_export_btn)
        async def _on_export():
            serial = PrivacyController.serviceman_serial(UserStore.get_user())
            if serial is None:
                status.set("Log in as a serviceman to export your data.")
                return
            try:
                payload = await self.controller.export_json(serial)
            except Exception as e:
                status.set(f"Export error: {e}")
                return
            if payload is None:
                status.set("Export failed (serviceman not found).")
                return
            export_payload.set(payload)
            status.set("Export ready — click Download.")

        @output
        @render.ui
        def privacy_export_download():
            payload = export_payload.get()
            if not payload:
                return ui.div()
            return ui.download_button("privacy_export_dl", "Download JSON")

        @session.download(filename="warriorfit-export.json")
        def privacy_export_dl():
            yield export_payload.get()

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
