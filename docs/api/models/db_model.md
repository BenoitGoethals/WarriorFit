# Database Models

SQLAlchemy ORM models for the entire data layer. Uses polymorphic inheritance for fitness test types.

## Entity Overview

| Model | Description |
|-------|-------------|
| `User` | Application user with role and credentials |
| `ServiceMen` | Military personnel with rank, unit, and fitness data |
| `FitnessTest` | Polymorphic base for all test types |
| `PhefTest` | PHEF test (running + side-bridge) |
| `FunctionalTest` | Functional test (push-ups, sit-ups, pull-ups) |
| `CombatTestParatrooper` | Combat test (running, obstacle, rope) |
| `CombatSwimmingTest` | Swimming test (pass/fail) |
| `TestSession` | Groups fitness tests into sessions |
| `Cross` | Cross-country running event |
| `Runner` | Participant in a cross event |
| `March` | March test record |
| `Unit` | Military unit |
| `AuditLog` | Audit trail entry |
| `Room` | Sport area / fitness room |
| `Reservation` | Room reservation |
| `HrMessage` | HR system message queue entry |

::: warriorfit.data.model.db_model
    options:
      members_order: source
      show_source: true
      show_docstring_attributes: true
