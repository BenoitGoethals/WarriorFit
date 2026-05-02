import logging
import logging.config
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from shiny import App

from warriorfit.core.container import Container
from warriorfit.utils.Os import Os

# ── 1. Wire the DI container (must happen before any page module is imported) ──
_container = Container()

# ── 2. Import UI factories (after wiring) ─────────────────────────────────────
from warriorfit.ui.app_server import build_app_ui, make_server


# ── 3. Logging setup ──────────────────────────────────────────────────────────
def _setup_logger() -> None:
    import yaml

    project_root = Os.get_project_root()
    if not project_root:
        return

    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    config_path = project_root / "warriorfit" / "config" / "logging_configuration.yml"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        except (yaml.YAMLError, KeyError, ValueError) as e:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger().error("Failed to load logging config: %s", e)
    else:
        logging.basicConfig(level=logging.INFO)


_setup_logger()

# ── 4. Start the message broker ───────────────────────────────────────────────
_container.broker().start()

# ── 5. Assemble the Shiny app ─────────────────────────────────────────────────
app = App(
    ui=build_app_ui(),
    server=make_server(),
    static_assets=Path(__file__).parent / "www",
)
