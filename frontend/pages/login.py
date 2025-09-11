from shiny import ui, render, reactive, req

def get_ui():
    return ui.nav_panel(
        "Login",
        ui.div(
            {
                "style": (
                    "min-height: 50vh; display: flex; align-items: center; "
                    "justify-content: center; padding: 16px;"
                )
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

def server(input, output, session):
    status = reactive.Value("Please enter your credentials.")
    is_error = reactive.Value(False)

    @reactive.Effect
    @reactive.event(input.login_btn)
    def _on_login():
        user = (input.username() or "").strip()
        pw = (input.password() or "").strip()
        if not user or not pw:
            status.set("Please enter both username and password.")
            is_error.set(True)
            return
        status.set(f"Welcome, {user}! You are now logged in.")
        is_error.set(False)

    @output
    @render.ui
    def login_status():
        msg = status.get()
        if is_error.get():
            return ui.tags.p(msg, style="color: red;")
        return ui.tags.p(msg)