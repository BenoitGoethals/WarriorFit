from shiny import ui, render, reactive, req

class LoginDialog:
    def __init__(self, id: str = "login"):
        self.id = id
        self.status = reactive.Value("Please enter your credentials.")
        self.is_error = reactive.Value(False)

    def ui(self):
        return ui.div(
            ui.input_action_button(f"{self.id}_open", "Open Login"),
            ui.br(),
            ui.output_ui(f"{self.id}_login_status"),
        )

    def server(self, input, output, session):
        # Persistent status shown below the "Open Login" button
        output[f"{self.id}_login_status"] = render.ui(
            lambda: ui.tags.p(
                self.status.get(),
                style="color: red;" if self.is_error.get() else None,
            )
        )

        # Status area inside the modal (for inline error messages)
        output[f"{self.id}_modal_status"] = render.ui(
            lambda: (
                ui.tags.p(self.status.get(), style="color: red;")
                if self.is_error.get()
                else ui.tags.p("Please enter your username and password.")
            )
        )

        # Show the modal when the open button is clicked
        @reactive.Effect
        @reactive.event(input[f"{self.id}_open"])
        def _open_modal():
            # Reset inline state when opening
            self.status.set("Please enter your credentials.")
            self.is_error.set(False)

            ui.modal_show(
                ui.modal(
                    ui.h2("🔐 Login"),
                    ui.input_text(f"{self.id}_username", "Username"),
                    ui.input_password(f"{self.id}_password", "Password"),
                    ui.br(),
                    ui.output_ui(f"{self.id}_modal_status"),
                    footer=ui.div(
                        ui.input_action_button(f"{self.id}_login_btn", "Log in"),
                        ui.modal_button("Close"),
                        style="display: flex; gap: 8px; align-items: center;",
                    ),
                    easy_close=True,
                )
            )

        # Handle login action from within the modal
        @reactive.Effect
        @reactive.event(input[f"{self.id}_login_btn"])
        def _on_login():
            user = (input[f"{self.id}_username"]() or "").strip()
            pw = (input[f"{self.id}_password"]() or "").strip()

            if not user or not pw:
                self.status.set("Please enter both username and password.")
                self.is_error.set(True)
                return

            self.status.set(f"Welcome, {user}! You are now logged in.")
            self.is_error.set(False)
            ui.modal_remove()

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