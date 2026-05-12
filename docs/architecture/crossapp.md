# WarriorFit Cross/Running Event System

## Goal

The Cross/Running Event system is a **three-component architecture** for timing and recording cross-country running events in the field.

| Component | Technology | Role |
|-----------|------------|------|
| **WarriorFit** | Shiny for Python | Planning, results management, statistics |
| **FastAPI Backend** | FastAPI + PostgreSQL | Shared data persistence and REST API |
| **Flet Client** | Flet (mobile/desktop) | On-site runner timing by PTIs |

## Git Repositories

- [Flet Client](https://github.com/BenoitGoethals/fletTestCase) — mobile/desktop timer application
- [Backend API](https://github.com/BenoitGoethals/CrossClientAPIWarriorFit) — FastAPI REST service

---

## System Architecture

```mermaid
flowchart TB
    subgraph Field["On-Site (Field)"]
        Flet["Flet Client<br/>PTI mobile / desktop"]
    end

    subgraph Cloud["Backend Services"]
        API["FastAPI Backend<br/>/api/cross/...<br/>/api/runners/..."]
        DB[(PostgreSQL<br/>Cross · Runner)]
    end

    subgraph Base["WarriorFit (Shiny)"]
        WF["CrossRepository · ServiceCross<br/>Cross Planning · Cross Statistics"]
    end

    Flet <-- "REST · JWT · HTTPS" --> API
    API --- DB
    WF --- DB

    classDef client fill:#e8eaf6,stroke:#3949ab,color:#1a237e;
    classDef api fill:#fff3e0,stroke:#ef6c00,color:#e65100;
    classDef db fill:#fce4ec,stroke:#ad1457,color:#880e4f;
    classDef app fill:#e0f2f1,stroke:#00695c,color:#004d40;
    class Flet client
    class API api
    class DB db
    class WF app
```

### Overview Screenshots

![img_8.png](img_8.png)

![img_7.png](img_7.png)

### Online version
<https://clientcross.bensoft.be/>

---

## Data Models

The backend and WarriorFit share the same PostgreSQL database. The relevant entities are defined in `warriorfit/data/model/db_model.py`.

### Cross (session)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID / int | Primary key |
| `start` | datetime | Event date and time |
| `distance` | float | Distance in km |
| `executed` | bool | Whether the event took place |
| `description` | str | Free-text description |

### Runner (result)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID / int | Primary key |
| `cross_id` | FK → Cross | Which cross session |
| `serial` | str | Serviceman serial number |
| `running_time` | str | Formatted time (hh:mm:ss) |
| `seconds` | int | Running time in seconds (calculated) |
| `order` | int | Finish order (auto-assigned) |

---

## Integration: Flet ↔ FastAPI Backend

The Flet client communicates with the FastAPI backend over HTTPS. Authentication uses JWT tokens obtained at login.

### Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    participant F as Flet Client
    participant B as FastAPI Backend

    F->>B: POST /auth/login<br/>{username, password}
    B-->>F: {access_token, token_type}
    F->>B: GET /api/cross/<br/>Authorization: Bearer <token>
    B-->>F: [Cross session list]
```

### Key API Endpoints (FastAPI Backend)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Obtain JWT access token |
| `GET` | `/api/cross/` | List cross sessions |
| `GET` | `/api/cross/{id}` | Get a single cross session |
| `GET` | `/api/runners/{cross_id}` | List runners for a session |
| `POST` | `/api/runners/` | Submit a runner result |
| `PUT` | `/api/runners/{id}` | Update a runner result |
| `DELETE` | `/api/runners/{id}` | Remove a runner result |

---

## Integration: WarriorFit ↔ PostgreSQL

WarriorFit accesses the cross data directly via its async SQLAlchemy stack. No HTTP hop is needed — it queries the shared database.

```mermaid
flowchart LR
    UI["WarriorFit Shiny UI"]
    UI --> CPC["CrossPlanningController<br/><i>session CRUD</i>"]
    UI --> CC["CrossController<br/><i>runner results CRUD</i>"]
    UI --> CSC["CrossStaticsController<br/><i>Top 10 rankings</i>"]

    CPC --> S[ServiceCross]
    CC  --> S
    CSC --> S
    S --> R[CrossRepository]
    R --> PG[(PostgreSQL)]

    classDef ctrl fill:#ede7f6,stroke:#5e35b1,color:#311b92;
    classDef svc  fill:#e0f7fa,stroke:#00838f,color:#006064;
    classDef repo fill:#fff3e0,stroke:#ef6c00,color:#e65100;
    classDef db   fill:#fce4ec,stroke:#ad1457,color:#880e4f;
    class CPC,CC,CSC ctrl
    class S svc
    class R repo
    class PG db
```

Relevant WarriorFit source files:

| File | Responsibility |
|------|---------------|
| `warriorfit/services/service_cross.py` | Cross business logic |
| `warriorfit/data/repositories/cross_repository.py` | Cross DB queries |
| `warriorfit/ui/controllers/cross_controller.py` | Runner CRUD for the page |
| `warriorfit/ui/controllers/cross_planning_controller.py` | Session CRUD for the page |
| `warriorfit/ui/controllers/cross_statics_controller.py` | Statistics queries |
| `warriorfit/ui/pages/cross.py` | Runner entry page |
| `warriorfit/ui/pages/cross_planning.py` | Session planning page |
| `warriorfit/ui/pages/cross_statics.py` | Statistics page |

---

## End-to-End Workflow

```mermaid
sequenceDiagram
    autonumber
    actor PTI as PTI
    participant WF as WarriorFit (Shiny)
    participant DB as PostgreSQL
    participant Flet as Flet Client
    participant API as FastAPI Backend

    PTI->>WF: Create cross session (Cross Planning)
    WF->>DB: CrossRepository.save()
    PTI->>Flet: Open client on-site
    Flet->>API: POST /auth/login (JWT)
    Flet->>API: GET /api/cross/
    API->>DB: SELECT cross sessions
    API-->>Flet: session list
    PTI->>Flet: Select session, start timing
    loop For each finishing runner
        PTI->>Flet: serial + finish time
        Flet->>API: POST /api/runners/
        API->>DB: INSERT runner result
    end
    PTI->>WF: View results / Top 10
    WF->>DB: read via CrossController / CrossStaticsController
    DB-->>WF: results
    WF-->>PTI: ranking + statistics
```

---

## Screenshots

![Screenshot From 2026-01-24 18-26-31.png](Screenshot%20From%202026-01-24%2018-26-31.png)
![Screenshot From 2026-01-24 18-28-18.png](Screenshot%20From%202026-01-24%2018-28-18.png)