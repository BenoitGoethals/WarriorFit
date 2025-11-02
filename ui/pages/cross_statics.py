from shiny import ui


class CrossStaticsPage:
    def __init__(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "Cross Statics",
            ui.h2("Cross Statics"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("1. Basic Performance Metrics"),
                    ui.p("These are the foundation for everything else:"),
                    ui.tags.table(
                        {"class": "table table-sm"},
                        ui.tags.thead(
                            ui.tags.tr(
                                ui.tags.th("Metric"),
                                ui.tags.th("Description"),
                                ui.tags.th("Example Use"),
                            )
                        ),
                        ui.tags.tbody(
                            ui.tags.tr(
                                ui.tags.td("Average time"),
                                ui.tags.td("Mean time for the cross that week"),
                                ui.tags.td("Track general trend of the platoon/company"),
                            ),
                            ui.tags.tr(
                                ui.tags.td("Best time / slowest time"),
                                ui.tags.td("Range of performance"),
                                ui.tags.td("Detect top and low performers"),
                            ),
                            ui.tags.tr(
                                ui.tags.td("Median time"),
                                ui.tags.td("Middle performer’s time"),
                                ui.tags.td("More stable indicator than average"),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def server(self, input, output, session):
        pass


_page = CrossStaticsPage()

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    return _page.server(input, output, session)