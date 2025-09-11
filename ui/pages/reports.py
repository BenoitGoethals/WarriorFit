from shiny import ui, render

def get_ui():
    return ui.nav_panel(
        "Reports",
        ui.h2("📑 Reports"),
        ui.input_text("title", "Report title:", "Weekly update"),
        ui.output_text("report_title")
    )

def server(input, output, session):
    @output
    @render.text
    def report_title():
        return f"Selected report: {input.title()}"
