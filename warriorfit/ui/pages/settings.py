# Python
from __future__ import annotations

from shiny import ui, render, reactive

from warriorfit.config.settings_data import SettingsData
from warriorfit.config.smtp_config import SmtpConfig
from warriorfit.ui.controllers.setting_controller import SettingsController
from warriorfit.ui.pages.page import Page


class SettingsPage(Page):
    def __init__(self):
        super().__init__()
        self.controller = SettingsController()
        self._status = reactive.Value("")
        self._unit_status = reactive.Value("")


    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Settings",
            ui.h2("⚙ Settings"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Application Configuration"),
                    ui.h5("Unit Settings"),
                    ui.input_text("own_unit", "Own Unit", placeholder="Enter your unit name"),
                    ui.output_text("unit_status"),

                    ui.h5("Database Configuration"),
                    ui.input_text("db_host", "Host", placeholder="e.g., 78.21.255.25"),
                    ui.input_numeric("db_port", "Port", value=5432, min=1, max=65535),
                    ui.input_text("db_database", "Database", placeholder="e.g., warriorfit"),
                    ui.input_text("db_username", "Username", placeholder="e.g., mike"),
                    ui.input_password("db_password", "Password"),

                    ui.h5("HR Configuration"),
                    ui.input_text("hr_url", "HR URL", placeholder="e.g., http://hr-system/api"),
                ),
                ui.card(
                    ui.card_header("Mail & Paths"),
                    ui.h5("Mail Configuration"),
                    ui.input_text("mail_host", "SMTP Host", placeholder="e.g., smtp.gmail.com"),
                    ui.input_numeric("mail_port", "SMTP Port", value=587, min=1, max=65535),
                    ui.input_text("mail_username", "Mail Username", placeholder="e.g., user@example.com"),
                    ui.input_password("mail_password", "Mail Password"),
                    ui.input_text("sender_email", "Sender Email", placeholder="e.g., no-reply@warriorfit.com"),
                    ui.layout_columns(
                        ui.input_checkbox("mail_use_ssl", "Use SSL", value=False),
                        ui.input_checkbox("mail_use_tls", "Use TLS", value=True),
                    ),

                    ui.h5("Path Configuration"),
                    ui.input_text("pdf_path", "PDF Path", placeholder="e.g., c:/temp"),
                    ui.br(),
                    ui.input_action_button("save_config", "Save All Configuration", width="100%", class_="btn-primary"),
                    ui.output_text("config_status"),
                    full_screen=False,
                ),
                col_widths=(6, 6),
            )
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

            if data.mail_server:
                ui.update_text("mail_host", value=data.mail_server.host)
                ui.update_numeric("mail_port", value=data.mail_server.port)
                ui.update_text("mail_username", value=data.mail_server.username or "")
                ui.update_text("mail_password", value=data.mail_server.password or "")
                ui.update_text("sender_email", value=data.mail_server.sender_email or "")
                ui.update_checkbox("mail_use_ssl", value=data.mail_server.use_ssl)
                ui.update_checkbox("mail_use_tls", value=data.mail_server.use_tls)

            self._unit_status.set(f"✓ Unit set to: {data.own_unit}" if data.own_unit else "")


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
            )
            ok, msg = self.controller.save(data)
            self._status.set(("✅ " if ok else "❌ ") + msg)

        @output
        @render.text
        def unit_status():
            return self._unit_status.get()


        @output
        @render.text
        def config_status():
            return self._status.get()


# Public API: keep same signatures
_page = SettingsPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)