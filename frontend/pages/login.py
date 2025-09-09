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
                ui.output_text("login_status"),
            ),
        ),
    )

def server(input, output, session):
    status = reactive.Value("Please enter your credentials.")

    @reactive.Effect
    @reactive.event(input.login_btn)
    def _on_login():
        user = (input.username() or "").strip()
        pw = (input.password() or "").strip()
        if not user or not pw:
            status.set("Please enter both username and password.")
            return
        status.set(f"Welcome, {user}! You are now logged in.")

    @output
    @render.text
    def login_status():
        return status.get()