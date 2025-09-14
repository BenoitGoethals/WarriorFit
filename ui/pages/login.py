from shiny import ui, render, reactive, req, Session

from data.db.db_model import User,Role
from ui.user_store import UserStore
from ui.services.db_service import DBService
db_service = DBService("ui/config/config.yml")


def get_ui():
    return ui.nav_panel(
        "Login",
        ui.div(
            {
                "style": (
                    "min-height: 50vh; display: flex; align-items: center; "
                    "justify-content: center; padding: 16px;"                )
            },
            ui.div(
                {"style": "width: 100%; max-width: 480px;"},
                ui.h2("🔐 Login"),
                ui.input_text("username", "Username"),
                ui.input_password("password", "Password"),
                ui.input_action_button("login_btn", "Log in"),
                ui.br(),
                ui.br(),
                ui.output_ui("login_status"),
            ),
        ),
    )


def server(input, output, session: Session):
    status = reactive.Value("Please enter your credentials.")
    is_error = reactive.Value(False)

    @reactive.Effect
    @reactive.event(input.login_btn)
    async def _on_login():
        user = (input.username() or "").strip()
        pw = (input.password() or "").strip()
        if not user or not pw:
            status.set("Please enter both username and password.")
            is_error.set(True)
            return
        user_req = await db_service.check_user(user, pw)
        if not user_req:
            status.set("Invalid username or password.")
            is_error.set(True)
            return
        u = await db_service.get_user_by_username(user)
        UserStore.set_user(u)
        status.set(f"Welcome, {user}. You are now logged in.")
        is_error.set(False)
        # The navbar with main pages is constructed based on login state,
        # so force a client reload after setting the user to rebuild the UI.
        ui.update_navs("main_nav", selected="User Management")
        ui.notification_show("Login successful. Redirecting...", type="message")
        ui.insert_ui(
            selector="body",
            ui=ui.tags.script("setTimeout(function(){ location.reload(); }, 100);"),
        )
    @output
    @render.ui
    def login_status():
        msg = status.get()
        if is_error.get():
            return ui.tags.p(msg, style="color: red;")
        return ui.tags.p(msg)