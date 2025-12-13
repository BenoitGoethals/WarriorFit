## High-level architecture (Markdown)

### Summary
**WarriorFit (fletTestCase)** is a **Python + Flet** client application that provides a simple UI for timing “cross/running” events, recording results, and persisting those results locally (and typically syncing them to a backend service).

## Goals
- Provide a simple, easy-to-use UI for timing and recording cross/running events.
- Persist recorded timings locally (for offline/unstable network scenarios).
- Allow for auditing of recorded timings (e.g.,)
- Allow for syncing recorded timings with a backend service.

### Key components

#### 1) UI / Presentation (Flet)
- A **Flet-based user interface** that drives the user workflow:
  - start screen / navigation
  - event selection
  - timer and recording actions
  - results / status views

**Responsibility:** Render screens, collect user actions, and display the current timing/session state.

---

#### 2) Application Logic (Workflow + State)
- Centralized in-app state representing:
  - selected event/session
  - timer running status and timing values
  - list of recorded times (splits/finishes)

**Responsibility:** Orchestrate the workflow from “select event” → “time & record” → “save”.

---

#### 3) Persistence Layer (Local Storage)
- **SQLite database file** stored under `storage/` (e.g., `storage/recordings.db`).

**Responsibility:** Local durability of recorded timings (useful for offline/unstable network scenarios and auditing).

---

#### 4) Integration Layer (External API)
- Communicates with an **external HTTP API** (via `requests`) to:
  - fetch event metadata (available events)
  - submit recorded results

**Responsibility:** Sync and retrieve authoritative event/result data from a backend system.

---

#### 5) Assets
- Static resources stored in `src/assets/` (e.g., app image).

**Responsibility:** Branding/UI visuals.

---

### Data flow (end-to-end)

1. **App launches** → UI initializes and shows the entry screen.
2. **User selects an event** → app requests event list from the backend API.
3. **Timing session**
   - user starts timer
   - user records one or more timestamps
4. **Save**
   - recordings are written to **local SQLite** in `storage/`
   - recordings are sent to the **remote API**
5. **Feedback**
   - UI shows success/error and allows returning to start.

---

### Deployment / packaging view
- Managed as a Python project (`pyproject.toml`) with **Flet** as the UI framework and `requests` for HTTP.
- The app source lives in `src/`, and runtime artifacts live under `storage/`.

---

### Architecture diagram (conceptual)

```plain text
+-------------------+        HTTP (requests)        +----------------------+
|   Flet UI (Client)| <---------------------------> |   Backend API Server |
|  screens + inputs |                                | (events + results)   |
+---------+---------+                                +----------------------+
          |
          | in-process calls (state/workflow)
          v
+-------------------+
| Application Logic |
|  timer + records  |
+---------+---------+
          |
          | SQLite writes
          v
+-------------------+
| Local Storage     |
| storage/recordings|
+-------------------+
```
