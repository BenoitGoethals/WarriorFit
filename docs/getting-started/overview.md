# Overview

WarriorFit is a military physical fitness test digitization platform built with **Shiny for Python**, **SQLAlchemy async ORM** on **PostgreSQL**, and **dependency-injector** for DI.

## What is WarriorFit?

Each unit within Belgian Defence has a physical training cell responsible for preparing soldiers for operational deployment. Annually, every soldier must complete:

- **PHEF** — Physical Fitness Evaluation Defence (side-bridge + 2400m run)
- **Combat Tests** — Speed march, rope course, obstacle course
- **Functional Tests** — Pull-ups, sit-ups, push-ups
- **Combat Swimming** — 100m in combat uniform
- **March Tests** — Endurance marches

WarriorFit digitizes the entire workflow: test recording, scoring, reporting, and HR integration.

## Roles

| Role | Description |
|------|-------------|
| **ADMIN** | Full system access, user management |
| **PTI** | Physical Training Instructor — records tests for own unit |
| **APTI** | Assistant PTI — limited recording capabilities |
| **PLANNER** | Plans and schedules events |
| **GUEST** | Read-only access |
| **USER** | View own results |

## Quick Start

```bash
# Install dependencies
uv sync

# Run the application
shiny run --host 0.0.0.0 --port 8501 --reload warriorfit/app.py

# Run tests
pytest tests/ -v
```

See the [Installation Guide](install.md) for full setup instructions.
