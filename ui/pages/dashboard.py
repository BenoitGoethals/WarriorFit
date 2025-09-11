from shiny import ui, render

def get_ui():
    return ui.nav_panel(
        "Dashboard",
        ui.h2("📊 Dashboard"),
        ui.output_text("msg")
    )

def server(input, output, session):
    @output
    @render.text
    def msg():
        return "Welcome to the Dashboard!"
