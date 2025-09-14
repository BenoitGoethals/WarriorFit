from ui.user_store import UserStore
from shiny import ui, reactive, render


def get_ui():
    return ui.nav_panel(
        "Logout",
        ui.input_action_button("logout", label="Logout"),
    )

def server(input, output, session):

    @reactive.Effect
    @reactive.event(input.logout)
    def _logout():
        print("Logging out...")
        UserStore.set_user(None)
        # Optionally give user feedback:
        ui.notification_show("You have been logged out.", type="message")
        ui.update_navs("main_nav")



        # If you need to close the session, consider session.close() or a redirect flow depending on your app design.
