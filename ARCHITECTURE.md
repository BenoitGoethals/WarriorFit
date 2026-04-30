# WarriorFit Architecture

## Overview

WarriorFit is a military physical fitness test digitization platform. It captures, scores, and reports on PHEF, combat, and functional fitness assessments, and integrates with an HR system via an asynchronous message broker.

## Tech Stack

- **Language:** Python 3.13+
- **Web UI:** Shiny for Python (reactive server)
- **Persistence:** PostgreSQL via SQLAlchemy 2.x async ORM, migrations with Alembic
- **DI:** `dependency-injector` (`DeclarativeContainer`)
- **Auth:** Argon2id password hashing, role-based access (6 roles)
- **Packaging:** `uv` / `pyproject.toml`

## Layered Dependency Flow

Dependencies point downward only. Higher layers never import from below in reverse.

```
UI (Shiny pages)
      |
      v
Controllers
      |
      v
Services
      |
      v
Repositories
      |
      v
ORM Models  --->  Core (Enums, DI Container, Config)
```

## Components

### Entry point — `warriorfit/app.py`
- Initializes the DI container
- Registers Shiny pages with role-based access (`PageSpec.allowed_roles`)
- Manages broker lifecycle (start/stop the background worker)

### Core — `warriorfit/core/`
- `container.py` — `DeclarativeContainer` wiring repositories, services, controllers as singletons
- Enums and shared primitives (roles, test types)

### Config — `warriorfit/config/appliccation_config.py`
- Singleton metaclass loading YAML
- Dev: `config/config_dev.yml`
- Prod: `/etc/WarriorFit/config.yml`
- Secrets sourced from env (`WF_SECRET_KEY`)

### Data — `warriorfit/data/model/db_model.py`
- Polymorphic `FitnessTest` base with subtypes: `PhefTest`, `CombatTestParatrooper`, `FunctionalTest`, …
- All I/O is async — repositories use `async_sessionmaker` with `AsyncSession`

### Services — `warriorfit/services/`
- Business logic (scoring, eligibility, consent, user management)
- Stateless; depend only on repositories and core

### Security — `warriorfit/security/`
- Argon2id password hashing run via `asyncio.to_thread` to avoid blocking the event loop
- Role-based access control at the page level

### Message broker — `warriorfit/mom/broker.py`
- Async background worker polling a DB-backed queue
- Transactional outbox pattern for reliable HR-system integration
- Retry + dead-letter handling

### UI — `warriorfit/ui/`
- Shiny pages following a lazy-instantiation pattern (module-level `_page` cached on first call)
- Pages registered centrally in `app.py` with `allowed_roles`

## Roles

`ADMIN`, `PTI`, `APTI`, `PLANNER`, `GUEST`, `USER` — enforced per page via `PageSpec.allowed_roles`.

## Data Flows

### Test submission
1. User fills a Shiny form → page server callback
2. Controller validates and dispatches to the appropriate service
3. Service computes score, persists via repository
4. Broker enqueues an outbox event for HR sync

### HR integration
1. Broker worker polls outbox table
2. Publishes message to HR system
3. On failure: retry with backoff; exhausted → dead-letter
4. On success: mark outbox row as published

### Authentication
1. Login form → auth service
2. Argon2id verification on a worker thread
3. Role loaded into session; pages gate on `allowed_roles`
4. Dev mode (`APP_ENV=development`) auto-injects an admin user, bypassing auth

## Environments

| `APP_ENV`     | Behavior                                            |
|---------------|-----------------------------------------------------|
| `development` | Auto-admin, no auth, dev YAML config                |
| `test`        | Test fixtures, in-memory or test DB                 |
| `production`  | Full auth, `/etc/WarriorFit/config.yml`, real broker|

## Build & Release

- `version.yaml` is auto-updated by a pre-commit hook (commit count + timestamp)
- `WF_SECRET_KEY` is injected at runtime, never baked into the Docker image
- `APP_PORT` defaults to `8501`

## Testing

- `pytest` with async support
- Singleton isolation: tests clear `Singleton._instances` in fixtures
- Broker has dedicated unit tests for DTO mappings, lifecycle, and messaging
