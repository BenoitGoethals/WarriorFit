# Python
from __future__ import annotations

from shiny import ui, render, reactive

from ui.controllers.setting_controller import SettingsController, SettingsData


class SettingsPage:
    def __init__(self):
        self.controller = SettingsController()
        self._status = reactive.Value("")
        self._unit_status = reactive.Value("")
        self._darkmode_status = reactive.Value("Dark mode is OFF")

    def get_ui(self):
        return ui.nav_panel(
            "Settings",
            ui.h2("⚙ Settings"),
            ui.card(
                ui.card_header("Application Configuration"),

                ui.h5("Unit Settings"),
                ui.input_text("own_unit", "Own Unit", placeholder="Enter your unit name"),
                ui.output_text("unit_status"),

                ui.h5("Database Configuration"),
                ui.layout_columns(
                    ui.input_text("db_host", "Host", placeholder="e.g., 78.21.255.210"),
                    ui.input_numeric("db_port", "Port", value=5432, min=1, max=65535),
                    ui.input_text("db_database", "Database", placeholder="e.g., warriorfit"),
                    ui.input_text("db_username", "Username", placeholder="e.g., benoi"),
                    ui.input_password("db_password", "Password"),
                ),

                ui.h5("Path Configuration"),
                ui.input_text("pdf_path", "PDF Path", placeholder="e.g., c:/temp"),

                ui.h5("Display Settings"),
                ui.input_checkbox("darkmode", "Enable Dark Mode"),
                ui.output_text("darkmode_status"),

                ui.layout_columns(
                    ui.input_action_button("save_config", "Save All Configuration", width="200px", class_="btn-primary"),
                    col_widths=(12,),
                ),
                ui.output_text("config_status"),

                full_screen=False,
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
            ui.update_checkbox("darkmode", value=data.darkmode)
            self._unit_status.set(f"✓ Unit set to: {data.own_unit}" if data.own_unit else "")
            self._darkmode_status.set("Dark mode is ON" if data.darkmode else "Dark mode is OFF")

        @reactive.Effect
        @reactive.event(input.own_unit)
        def _on_unit_change():
            unit = (input.own_unit() or "").strip()
            self._unit_status.set(f"✓ Unit set to: {unit}" if unit else "")

        @reactive.Effect
        @reactive.event(input.darkmode)
        def _on_darkmode_change():
            self._darkmode_status.set("Dark mode is ON" if input.darkmode() else "Dark mode is OFF")

        @reactive.Effect
        @reactive.event(input.save_config)
        def _on_save_config():
            data = SettingsData(
                db_host=input.db_host() or "",
                db_port=input.db_port() or 5432,
                db_database=input.db_database() or "",
                db_username=input.db_username() or "",
                db_password=input.db_password() or "",
                pdf_path=input.pdf_path() or "",
                own_unit=(input.own_unit() or "").strip(),
                darkmode=bool(input.darkmode()),
            )
            ok, msg = self.controller.save(data)
            self._status.set(("✅ " if ok else "❌ ") + msg)

        @output
        @render.text
        def unit_status():
            return self._unit_status.get()

        @output
        @render.text
        def darkmode_status():
            return self._darkmode_status.get()

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
