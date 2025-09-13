from ui.user_store import UserStore
from shiny import ui, render, reactive, req

from shiny import ui, render

def get_ui():
    return ui.nav_panel(
        "Logout",
        ui.input_action_button("Logout",label="Logout",),
    )

def server(input, output, session):
    @output
    @render.text
    def report_title():
        return f"Selected report: {input.title()}"

    @reactive.Effect
    def _logout():
        UserStore.logout()
        session.logout()
