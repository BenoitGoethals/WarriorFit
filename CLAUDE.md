# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WarriorFit is a military physical fitness test digitization platform built with **Shiny for Python** (reactive web UI), **SQLAlchemy async ORM** on **PostgreSQL**, and **dependency-injector** for DI. Python 3.13+.

## Common Commands

```bash
# Install dependencies
uv sync

# Run app (development)
shiny run --host 0.0.0.0 --port 8501 --reload warriorfit/app.py

# Run all tests
pytest tests/ -v

# Run single test
pytest tests/test_phef_calculator.py::TestPhefCalculator::test_method -v

# Lint
ruff check warriorfit/

# Type check
mypy warriorfit/

# Database migrations
.venv/bin/alembic revision --autogenerate -m "description"
.venv/bin/alembic upgrade head
```

## Architecture

**Layered, unidirectional dependency flow:**

```
UI (Shiny pages) → Controllers → Services → Repositories → ORM Models
                                                    ↓
                                              Core (Enums, DI Container)
```

- **Entry point:** `warriorfit/app.py` — initializes DI container, registers pages with role-based access, manages broker lifecycle
- **DI Container:** `warriorfit/core/container.py` — `DeclarativeContainer` wiring all singletons (repos, services, controllers)
- **ORM Models:** `warriorfit/data/model/db_model.py` — polymorphic `FitnessTest` base with subtypes (PhefTest, CombatTestParatrooper, FunctionalTest, etc.)
- **Config:** `warriorfit/config/appliccation_config.py` — Singleton metaclass, loads from `config/config_dev.yml` (dev) or `/etc/WarriorFit/config.yml` (prod)

### Page Pattern

Each page follows a lazy-instantiation pattern with module-level `_page` variable:

```python
_page = None
def _get_page():
    global _page
    if _page is None:
        _page = MyPage()  # DI injection happens here
    return _page

def get_ui():
    return _get_page().get_ui()

def server(input, output, session):
    return _get_page().server(input, output, session)
```

Pages are registered in `app.py` via `PageSpec` with `allowed_roles` for RBAC (6 roles: ADMIN, PTI, APTI, PLANNER, GUEST, USER).

### Key Patterns

- **All I/O is async** — repositories use `async_sessionmaker` with `AsyncSession`
- **Singleton isolation in tests** — clear `Singleton._instances` in fixtures
- **Message broker** (`warriorfit/mom/broker.py`) — async background worker polling DB queue for HR system integration
- **Argon2id** for password hashing, non-blocking via `asyncio.to_thread`
- **Pre-commit hook** auto-updates `version.yaml` with commit count and timestamp

## Code Style

- **Ruff**: line-length 100, rules E/F/W/I
- **mypy**: strict mode
- **Formatting**: black

## Environment

- `APP_ENV`: `development` | `test` | `production` (dev mode auto-injects admin user, no auth)
- `WF_SECRET_KEY`: runtime secret, never baked into Docker image
- `APP_PORT`: application port (default 8501)