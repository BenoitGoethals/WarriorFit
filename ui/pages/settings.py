
from shiny import ui, render, reactive

from ui.config.appliccation_config import ApplicationConfig
from ui.config.configuration_manager import ConfigurationManager
from ui.user_store import UserStore
import yaml
from pathlib import Path


class SettingsPage:
    def __init__(self):
        self.own_unit = reactive.Value("")
        self.config_path = "ui/config/config.yml"

    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            return ApplicationConfig().load_config()
           # with open(self.config_path, 'r') as f:
            #    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def _save_config(self, config):
        """Save configuration to YAML file"""
        try:
            ApplicationConfig().save_config(config)

            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_ui(self):

            return ui.nav_panel(
                "Settings",
                ui.h2("⚙ Settings"),
                ui.card(
                    ui.card_header("Application Configuration"),
                    
                    # Unit Settings Section
                    ui.h5("Unit Settings"),
                    ui.input_text("own_unit", "Own Unit", placeholder="Enter your unit name"),
                    ui.output_text("unit_status"),

                    
                    # Database Configuration Section
                    ui.h5("Database Configuration"),
                    ui.layout_columns(
                        ui.input_text("db_host", "Host", placeholder="e.g., 78.21.255.210"),
                        ui.input_numeric("db_port", "Port", value=5432, min=1, max=65535),
                        ui.input_text("db_database", "Database", placeholder="e.g., warriorfit"),
                        ui.input_text("db_username", "Username", placeholder="e.g., benoi"),
                        ui.input_password("db_password", "Password"),

                    ),


                    
                    # Path Configuration Section
                    ui.h5("Path Configuration"),
                    ui.input_text("pdf_path", "PDF Path", placeholder="e.g., c:/temp"),

                    
                    # Display Settings Section
                    ui.h5("Display Settings"),
                    ui.input_checkbox("darkmode", "Enable Dark Mode"),
                    ui.output_text("darkmode_status"),

                    
                    # Save Button
                    ui.layout_columns(
                        ui.input_action_button("save_config", "Save All Configuration", width="200px", class_="btn-primary"),
                        col_widths=(12,),
                    ),
                    ui.output_text("config_status"),
                    
                    full_screen=False,
                ),
            )


    def server(self, input, output, session):
        config_status_val = reactive.Value("")

        @reactive.Effect
        def _load_initial_config():
            """Load config values into the form on startup"""
            config = self._load_config()
            if config is not None:
                # Load database config
                if 'db' in config:
                    db = config['db']
                    ui.update_text("db_host", value=db.get('host', ''))
                    ui.update_numeric("db_port", value=db.get('port', 5432))
                    ui.update_text("db_database", value=db.get('database', ''))
                    ui.update_text("db_username", value=db.get('username', ''))
                    ui.update_text("db_password", value=db.get('password', ''))

                # Load path config
                if  'path' in config:
                    path = config['path']
                    ui.update_text("pdf_path", value=path.get('pdf_path', ''))

                if 'unit' in config:
                    ui.update_text("own_unit", value=config['unit']['name'])

        @output
        @render.text
        def darkmode_status():
            return "Dark mode is ON" if input.darkmode() else "Dark mode is OFF"

        @output
        @render.text
        def unit_status():
            unit = (input.own_unit() or "").strip()
            if unit:
                return f"✓ Unit set to: {unit}"
            return ""

        @output
        @render.text
        def config_status():
            return config_status_val.get()

        @reactive.Effect
        @reactive.event(input.own_unit)
        def _on_unit_change():
            unit = (input.own_unit() or "").strip()
            if unit:
                self.own_unit.set(unit)

        @reactive.Effect
        @reactive.event(input.save_config)
        def _on_save_config():
            """Save all configuration to YAML"""
            config = self.configManager.load_configuration()
         #   config = self.configManager._load_configuration()
            
            # Update database section
            config['db'] = {
                'host': input.db_host() or "",
                'port': input.db_port() or 5432,
                'database': input.db_database() or "",
                'username': input.db_username() or "",
                'password': input.db_password() or "",
            }
            
            # Update path section
            if 'path' not in config:
                config['path'] = {}
            config['path']['pdf_path'] = input.pdf_path() or ""
            
            if self._save_config(config):
                config_status.set("✅ Configuration saved successfully!")
            else:
                config_status.set("❌ Failed to save configuration.")


# Public API: keep same signatures
_page = SettingsPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)
