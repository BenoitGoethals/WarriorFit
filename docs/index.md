# WarriorFit

## Digitization of Physical Military Tests at SOR-Unit Level

**Author:** Benoit Goethals | **Academic Year:** 2025–2026 | **Language:** Python 3.13+

---

WarriorFit is a comprehensive fitness and military management application designed to track physical performance, manage personnel data, and generate analytical reports. The system integrates data collection, statistical analysis, and reporting capabilities tailored for military fitness standards.

Each unit within Defence has a **physical training cell** aimed at preparing soldiers physically for operational deployment. Annually, every soldier must complete the **PHEF** (Physical Fitness Evaluation Defence). In addition, combat units carry out **functional** and **combat tests**, while paracommandos must endure additional **combat evaluations**.

## Key Features

- **Test Management** — Record and manage PHEF, Combat, Functional, Swimming, and March tests
- **Cross Events** — Full cross-running event management with Chronos XML import
- **PDF/CSV Reports** — Generate individual and unit-level fitness reports
- **Role-Based Access** — 6 roles: Admin, PTI, APTI, Planner, Guest, User
- **HR Integration** — Async message broker for HR system synchronization
- **Audit Logging** — Complete audit trail of all security events and CRUD operations
- **Room Reservations** — Sport area booking with calendar view

## Technology Stack

| Layer | Technology |
|-------|-----------|
| UI | Shiny for Python |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL |
| DI | dependency-injector |
| Security | Argon2id, RBAC |
| Reports | ReportLab (PDF), Pandas (CSV) |
| Charts | Plotly |

## Architecture

```
UI (Shiny pages) → Controllers → Services → Repositories → ORM Models
                                                    ↓
                                              Core (Enums, DI Container)
```

## Quick Links

- [Installation Guide](getting-started/install.md)
- [User Manual](getting-started/user-manual.md)
- [System Architecture](architecture/architecture.md)
- [API Reference](api/app.md)
- [Security](security.md)
- [Changelog](project/changelog.md)

## Project Roadmap

| Phase | Period | Status |
|-------|--------|--------|
| Phase 1 — Initiation | Sept 2025 | Done |
| Phase 2 — Architecture | Oct 2025 | Done |
| Phase 3 — Development | Oct 2025 – Apr 2026 | Done |
| Phase 4 — Testing | Apr 2026 | In Progress |
| Phase 5 — Delivery | Jun 2026 | Planned |

## License

Copyright (c) 2026 Goethals Benoit. All rights reserved.
