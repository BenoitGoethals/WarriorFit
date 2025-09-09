from shiny import ui, render

def get_ui():
    return ui.nav_panel(
        "Settings",
        ui.h2("⚙ Settings"),
        ui.input_checkbox("darkmode", "Enable Dark Mode"),
        ui.output_text("status")
    )

def server(input, output, session):
    @output
    @render.text
    def status():
        return "Dark mode ON" if input.darkmode() else "Dark mode OFF"
