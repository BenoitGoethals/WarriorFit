# Python
from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from shiny import reactive, render, ui

from warriorfit.config.settings_data import SettingsData
from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.core.container import Container
from warriorfit.ui.controllers.setting_controller import SettingsController
from warriorfit.ui.pages.page import Page


class SettingsPage(Page):
    @inject
    def __init__(
        self, controller: SettingsController = Provide[Container.settings_controller]
    ):
        super().__init__()
        self.controller = controller
        self._status = reactive.Value("")
        self._unit_status = reactive.Value("")

    def refresh(self):
        pass

    def _inline_label_input(
        self, *, label: str, input_tag: ui.Tag, label_for: str
    ) -> ui.Tag:
        """Render label + input on the same line."""
        return ui.div(
            ui.tags.label(
                label,
                for_=label_for,
                class_="form-label mb-0",
                style="min-width: 170px;",  # adjust to taste
            ),
            ui.div(input_tag, class_="flex-grow-1"),
            class_="d-flex align-items-center gap-2",
        )

    def get_ui(self):
        return ui.nav_panel(
            "Settings",
            ui.h2("⚙ Settings"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Application Configuration"),
                    ui.h5("Unit Settings"),
                    self._inline_label_input(
                        label="Own Unit",
                        label_for="own_unit",
                        input_tag=ui.input_text(
                            "own_unit", None, placeholder="Enter your unit name"
                        ),
                    ),
                    ui.output_text("unit_status"),
                    ui.h5("Database Configuration"),
                    self._inline_label_input(
                        label="Host",
                        label_for="db_host",
                        input_tag=ui.input_text(
                            "db_host", None, placeholder="e.g., 78.21.255.25"
                        ),
                    ),
                    self._inline_label_input(
                        label="Port",
                        label_for="db_port",
                        input_tag=ui.input_numeric(
                            "db_port", None, value=5432, min=1, max=65535
                        ),
                    ),
                    self._inline_label_input(
                        label="Database",
                        label_for="db_database",
                        input_tag=ui.input_text(
                            "db_database", None, placeholder="e.g., warriorfit"
                        ),
                    ),
                    self._inline_label_input(
                        label="Username",
                        label_for="db_username",
                        input_tag=ui.input_text(
                            "db_username", None, placeholder="e.g., mike"
                        ),
                    ),
                    self._inline_label_input(
                        label="Password",
                        label_for="db_password",
                        input_tag=Page.input_password_with_toggle("db_password"),
                    ),
                    ui.h5("HR Configuration"),
                    self._inline_label_input(
                        label="HR URL",
                        label_for="hr_url",
                        input_tag=ui.input_text(
                            "hr_url", None, placeholder="e.g., http://hr-system/api"
                        ),
                    ),
                    self._inline_label_input(
                        label="Key",
                        label_for="hr_key",
                        input_tag=ui.input_text(
                            "hr_key", None, placeholder="e.g., 1234567890"
                        ),
                    ),
                ),
                ui.card(
                    ui.card_header("Mail & Paths"),
                    ui.h5("Mail Configuration"),
                    self._inline_label_input(
                        label="SMTP Host",
                        label_for="mail_host",
                        input_tag=ui.input_text(
                            "mail_host", None, placeholder="e.g., smtp.gmail.com"
                        ),
                    ),
                    self._inline_label_input(
                        label="SMTP Port",
                        label_for="mail_port",
                        input_tag=ui.input_numeric(
                            "mail_port", None, value=587, min=1, max=65535
                        ),
                    ),
                    self._inline_label_input(
                        label="Mail Username",
                        label_for="mail_username",
                        input_tag=ui.input_text(
                            "mail_username", None, placeholder="e.g., user@example.com"
                        ),
                    ),
                    self._inline_label_input(
                        label="Mail Password",
                        label_for="mail_password",
                        input_tag=Page.input_password_with_toggle("mail_password"),
                    ),
                    self._inline_label_input(
                        label="Sender Email",
                        label_for="sender_email",
                        input_tag=ui.input_text(
                            "sender_email",
                            None,
                            placeholder="e.g., no-reply@warriorfit.com",
                        ),
                    ),
                    ui.layout_columns(
                        ui.input_checkbox("mail_use_ssl", "Use SSL", value=False),
                        ui.input_checkbox("mail_use_tls", "Use TLS", value=True),
                    ),
                    ui.h5("Path Configuration"),
                    self._inline_label_input(
                        label="PDF Path",
                        label_for="pdf_path",
                        input_tag=ui.input_text(
                            "pdf_path", None, placeholder="e.g., c:/temp"
                        ),
                    ),
                    ui.br(),
                    ui.input_action_button(
                        "save_config",
                        "Save All Configuration",
                        width="100%",
                        class_="btn-primary",
                    ),
                    ui.output_text("config_status"),
                    full_screen=False,
                ),
                col_widths=(6, 6),
            ),
        )

    def server(self, input, output, session):
        @reactive.Effect
        def _load_initial_config():
            data = self.controller.load()
            ui.update_text("db_host", value=data.db_host)
            ui.update_numeric("db_port", value=data.db_port)
            ui.update_text("db_database", value=data.db_database)
            ui.update_text("db_username", value=data.db_username)
            ui.update_text("db_password", value=data.db_password)
            ui.update_text("pdf_path", value=data.pdf_path)
            ui.update_text("own_unit", value=data.own_unit)
            ui.update_text("hr_url", value=data.hr_url)
            ui.update_text("hr_key", value=data.hr_api_key)

            if data.mail_server:
                ui.update_text("mail_host", value=data.mail_server.host)
                ui.update_numeric("mail_port", value=data.mail_server.port)
                ui.update_text("mail_username", value=data.mail_server.username or "")
                ui.update_text("mail_password", value=data.mail_server.password or "")
                ui.update_text(
                    "sender_email", value=data.mail_server.sender_email or ""
                )
                ui.update_checkbox("mail_use_ssl", value=data.mail_server.use_ssl)
                ui.update_checkbox("mail_use_tls", value=data.mail_server.use_tls)

            self._unit_status.set(
                f"✓ Unit set to: {data.own_unit}" if data.own_unit else ""
            )

        @reactive.Effect
        @reactive.event(input.own_unit)
        def _on_unit_change():
            unit = (input.own_unit() or "").strip()
            self._unit_status.set(f"✓ Unit set to: {unit}" if unit else "")

        @reactive.Effect
        @reactive.event(input.save_config)
        def _on_save_config():
            smtp_config = SmtpConfig(
                host=input.mail_host() or "",
                port=input.mail_port() or 587,
                username=input.mail_username() or "",
                password=input.mail_password() or "",
                sender_email=input.sender_email() or "",
                use_ssl=input.mail_use_ssl(),
                use_tls=input.mail_use_tls(),
            )

            data = SettingsData(
                db_host=input.db_host() or "",
                db_port=input.db_port() or 5432,
                db_database=input.db_database() or "",
                db_username=input.db_username() or "",
                db_password=input.db_password() or "",
                pdf_path=input.pdf_path() or "",
                own_unit=(input.own_unit() or "").strip(),
                mail_server=smtp_config,
                hr_url=input.hr_url() or "",
                hr_api_key=input.hr_key() or "",
            )
            ok, msg = self.controller.save(data)
            self._status.set(("✅ " if ok else "❌ ") + msg)
            if ok:
                ui.notification_show("Settings saved.", type="message", duration=3)
            else:
                ui.notification_show(
                    f"Failed to save settings: {msg}", type="error", duration=3
                )

        @output
        @render.text
        def unit_status():
            return self._unit_status.get()

        @output
        @render.text
        def config_status():
            return self._status.get()


# Public API: keep same signatures
_page = None


def _get_page():
    global _page
    if _page is None:
        _page = SettingsPage()
    return _page


def get_ui():
    return _get_page().get_ui()


def server(input, output, session):
    _get_page().server(input, output, session)
