from typing import Any
from shiny import App, ui, run_app

from data.db.db_model import User
from ui.user_store import UserStore
from .pages import dashboard, reports, settings, logout
from .pages import login
from .pages import usermangement
from .pages import phef
from .pages import sessions

from data.db.db_model import User,Role
class FitnessWarriorApp:
    APP_TITLE = "Fitness Warrior"
    DEFAULT_PORT = 8000

    # Public static user store
    USER_STORE: UserStore = UserStore()

    @staticmethod
    def build_app_ui() -> ui.page_navbar:
        u=User()
        u.username="admin"
        u.password_hash=""
        u.role=Role.ADMIN
        UserStore.set_user(u)
        """
        Construct and return the root UI for the application.
        """
        if  UserStore.get_user():

            return ui.page_navbar(
                usermangement.get_ui(),

                phef.get_ui(),
                sessions.get_ui(),
                dashboard.get_ui(),
                reports.get_ui(),
                settings.get_ui(),
                logout.get_ui(),
                title=FitnessWarriorApp.APP_TITLE,
                id="main_nav",
             )
        else:
            return ui.page_navbar(
                login.get_ui(),
            )

    @staticmethod
    def register_pages_server(input: Any, output: Any, session: Any) -> None:
        """
        Register server logic for each page.
        """
        # All pages will be mounted lazily when their tab becomes active.
        pass

    @staticmethod
    def server(input: Any, output: Any, session: Any) -> None:
        """
        Shiny server entry point. Delegates to per-page servers.
        """
        from shiny import reactive

        FitnessWarriorApp.register_pages_server(input, output, session)

        # Map navbar labels to their page server functions
        servers_by_tab = {
            "User Management": usermangement.server,
            "Login": login.server,
            "PHEF Tests": phef.server,
            "Sessions": sessions.server,
            "Dashboard": dashboard.server,
            "Reports": reports.server,
            "Settings": settings.server,
            "logout": logout.server
        }

        mounted = reactive.Value(set())

        @reactive.Effect
        def _mount_on_nav_activation():
            active = input.main_nav()
            if not active:
                return
            already = mounted.get()
            if active in servers_by_tab and active not in already:
                servers_by_tab[active](input, output, session)
                mounted.set({*already, active})

app = App(FitnessWarriorApp.build_app_ui(), FitnessWarriorApp.server)

if __name__ == "__main__":
    run_app(app, port=FitnessWarriorApp.DEFAULT_PORT, reload=True)
