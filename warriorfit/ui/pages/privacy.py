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
from warriorfit.i18n import t
from warriorfit.ui.controllers.privacy_controller import PrivacyController
from warriorfit.ui.pages.page import Page
from warriorfit.ui.user_store import UserStore


class PrivacyPage(Page):
    TAB_NAME = "Privacy"

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
            t("nav.privacy"),
            ui.div(
                ui.h2(t("privacy.title"), class_="mb-3"),
                ui.p(
                    t("privacy.description"),
                    class_="text-muted",
                ),
                ui.hr(),
                ui.h4(t("privacy.your_consents")),
                ui.output_ui("privacy_consent_block"),
                ui.hr(),
                ui.h4(t("privacy.export_title")),
                ui.p(t("privacy.export_desc")),
                ui.input_action_button(
                    "privacy_export_btn",
                    t("privacy.prepare_export"),
                    class_="btn btn-primary me-2",
                ),
                ui.output_ui("privacy_export_download"),
                ui.hr(),
                ui.h4(t("privacy.erase_title")),
                ui.div(
                    ui.tags.strong(t("privacy.not_available") + " "),
                    t("privacy.retention_notice"),
                    class_="alert alert-warning",
                ),
                ui.output_text("privacy_status"),
                class_="container-fluid p-4",
            ),
            value=self.TAB_NAME,
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
                return ui.p(t("privacy.login_to_manage"))
            serial = PrivacyController.serviceman_serial(user)
            if serial is None:
                return ui.div(
                    t("privacy.serviceman_only"),
                    class_="alert alert-info",
                )
            consents = await self.controller.consents(serial)
            rows = []
            for ct in PrivacyController.available_consent_types():
                active = next(
                    (
                        c
                        for c in consents
                        if c["type"] == ct and c["withdrawn_at"] is None
                    ),
                    None,
                )
                label = ct.replace("_", " ").title()
                if active:
                    rows.append(
                        ui.div(
                            ui.span(f"{label} — granted {active['given_at']}"),
                            ui.input_action_button(
                                f"withdraw_{ct}",
                                t("privacy.withdraw"),
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
                                t("privacy.grant"),
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
                        status.set(t("privacy.grant_error").format(ct=ct, error=e))
                        self.refresh()
                        return
                    status.set(
                        t("privacy.grant_ok").format(ct=ct)
                        if ok
                        else t("privacy.grant_failed").format(ct=ct)
                    )
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
                        status.set(t("privacy.withdraw_error").format(ct=ct, error=e))
                        self.refresh()
                        return
                    status.set(
                        t("privacy.withdraw_ok").format(ct=ct)
                        if ok
                        else t("privacy.withdraw_failed").format(ct=ct)
                    )
                    self.refresh()

            _bind_grant()
            _bind_withdraw()

        @reactive.effect
        @reactive.event(input.privacy_export_btn)
        async def _on_export():
            serial = PrivacyController.serviceman_serial(UserStore.get_user())
            if serial is None:
                status.set(t("privacy.login_to_export"))
                return
            try:
                payload = await self.controller.export_json(serial)
            except Exception as e:
                status.set(t("privacy.export_error").format(error=e))
                return
            if payload is None:
                status.set(t("privacy.export_not_found"))
                return
            export_payload.set(payload)
            status.set(t("privacy.export_ready"))

        @output
        @render.ui
        def privacy_export_download():
            payload = export_payload.get()
            if not payload:
                return ui.div()
            return ui.download_button("privacy_export_dl", t("privacy.download_json"))

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
