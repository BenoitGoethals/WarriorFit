# WarriorFit Design Document

## 1. Project Overview
WarriorFit is a comprehensive fitness and military management application designed to track physical performance, manage personnel data, and generate analytical reports. The system integrates data collection, statistical analysis, and reporting capabilities tailored for military fitness standards.
Each unit within Defence has a **physical training cell** aimed at preparing soldiers physically for operational deployment.
Annually, every soldier must complete the **PHEF** (Physical Fitness Evaluation Defence). In addition, combat units carry out **functional** and **combat tests**, while paracommandos must endure additional **combat evaluations**.

Currently, much of this process is manual, leading to inefficiency, errors, and administrative delays.

### Purpose

This document serves as a guideline for developers during the implementation of WARRIORFIT.

### Scope

The system includes user management, test input, calculations, PDF reporting, and email notifications. It is designed for local server deployment within Defense.

### References

* Internal Defense standards
* Python Shiny documentation
* PostgreSQL manual
* ReportLab documentation

## 2. Architecture
The project follows a modular **Layered Architecture** ensuring separation of concerns between data access, business logic, and presentation.

### High-Level Structure
- **Presentation Layer (`ui`)**: Handles user interaction, displaying data, and capturing inputs using **Shiny for Python**. It is structured into `pages` (views) and `controllers` (logic for views).
- **Service Layer (`services`)**: Contains the core business logic, orchestrating data flow between the UI and the Data layer.
- **Data Layer (`data`)**: Manages database interactions using the Repository pattern and SQLAlchemy ORM.
- **Core Domain (`core`)**: Defines fundamental domain types, enums, and constants.
### Architecture Principle

Layers are implemented in such a way that the UI can be replaced by another web/desktop framework if needed, and the same applies to the database layer.



## 3. Technology Stack
- **Language**: Python 3.13+
- **Package Manager**: uv
- **UI Framework**: Shiny for Python
- **Database**: SQLAlchemy (ORM), Alembic (Migrations)
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Plotly
- **Utilities**: OpenPyXL (Excel), PyYAML (Config), Jinja2 (Templating)

## 4. Module Descriptions

### 4.1 Configuration (`config`)
Handles application settings, including database connections, SMTP (email) configuration, and general application parameters loaded from `config.yml`.

### 4.2 Core (`core`)
Contains shared domain definitions used across the application to ensure type safety and consistency.
- **Key Components**: `Gender`, `Role`, `fitness_test_types`.

### 4.3 Data Access (`data`)
Implements the persistent storage logic.
- **ORM**: Uses `db_model.py` to define database schemas.
- **Repositories**: Implements the Repository pattern (`abc_repository.py` as base) to abstract database queries for specific entities (e.g., `user_repository.py`, `fitness_test_repository.py`, `servicemen_repository.py`).
- **Migrations**: Managed via Alembic scripts in `data/db/scripts`.

### 4.4 Business Logic (`services`)
The heart of the application logic.
- **Management Services**: `military_service.py`, `service_user.py`.
- **Fitness Services**: `service_test.py`, `service_cross.py`, `service_march.py`.
- **Reporting**: `report_generator_pdf.py`, `report_generator_csv.py`, `mail_service.py`.
- **Calculation**: Algorithms for calculating scores (e.g., PHEF, Functional tests).

### 4.5 User Interface (`ui`)
Organized into **Controllers** and **Pages** using **Shiny**.
- **Application Entry**: `app.py` defines the main `FitnessWarriorApp` class, handling authentication, navigation, and dynamic UI generation based on user roles.
- **Controllers**: Handle the logic for specific UI actions (e.g., `auditlog_events_controller.py`, `combat_controller.py`).
- **Pages**: Define the Shiny UI layout (inputs, outputs, cards) for specific application screens (e.g., `dashboard_own_unit.py`, `cross_planning.py`).

### 4.6 BEMIL Integration (`military_api_rest`)
Handles integration with the internal Belgian Military (BEMIL) personnel database.
- **Serviceman lookup**: retrieves rank, name, gender, birthdate, age, and unit by serial number.
- **Full servicemen list**: retrieves all servicemen for a unit, used for browse modals and dropdown population.
- This integration is consumed by test input pages (PHEF, Combat, Swimming, Functional, March, Cross) and the Individual Test History page.

## 5. Data Flow
1.  **User Action**: User interacts with a **Shiny Page** (e.g., clicks a button, enters text).
2.  **Reactive Event**: Shiny's reactive system triggers an event in the server logic.
3.  **Controller/Server**: The page's server function or associated controller processes the input.
4.  **Service**: The controller calls a **Service** method.
5.  **Repository**: The service delegates data retrieval/persistence to a **Repository**.
6.  **Database**: The repository executes queries against the **Database**.
7.  **Response**: Data flows back up.
8.  **Reactive Update**: Shiny updates the UI components (e.g., `render.text`, `render.data_frame`, `render.ui`) with the new data.

## 6. Roles within the Application

The application has three roles. These roles determine which tabs are visible. PHEF tests are statutory and contain sensitive personal information.

### 1. PTI (Physical Training Instructor)

The PTI can plan sessions, enter test results for their unit, and generate reports.

**Available Tabs:**

* **Welcome** – Personal upcoming sessions dashboard
* **Sessions** – Create, edit, delete test sessions
* **PHEF Tests** – Enter and manage PHEF results (run + side-bridge)
* **Combat Tests** – Enter and manage combat test results (3 components)
* **Swimming Tests** – Enter and manage swimming test results
* **Functional Tests** – Enter and manage functional test results (pull-ups, push-ups, sit-ups)
* **March** – Register and manage march records
* **Cross Planning** – Create and manage cross sessions
* **Cross** – Enter cross runner results
* **Cross Statistics** – View top-10 rankings
* **Individual** – Search individual test history and generate PDF
* **Status Unit** – Unit status grid (PHEF, Combat, Swimming) with unit PDF
* **Dashboard** – Unit statistics and charts (PHEF not-done, pass rates)
* **PHEF Not done** – List of servicemen missing PHEF for current year
* **Calendar** – Personal test session calendar (FullCalendar)
* **Fitness Room** – Reserve and manage fitness room bookings

### 2. APTI (Assistant PTI)

APTI has the same access as PTI.

**Available Tabs:** Same as PTI (see above).

### 3. Administrator

The administrator has access to all PTI/APTI tabs plus system management functions.

**Additional Tabs (beyond PTI/APTI):**

* **User Management** – Create, edit, delete users; assign roles (admin, PTI, APTI)
* **Audit Logs** – Read-only view of all system audit events

## 7. Technological Design Decisions

The technology choices made in the initial project proposal.

### UI Framework

* **Shiny for Python**: UI framework (reactive, server-rendered)
* **shiny_calendar**: FullCalendar integration for calendar views

### Database / ORM

* **SQLAlchemy**: ORM layer
* **PostgreSQL drivers**: asyncpg, psycopg (psycopg-binary), psycopg2-binary
* **Migrations**: alembic, mako (only for development)

### Security / Authentication

* **Hashing**: bcrypt, passlib
* **Crypto**: ecdsa, rsa, pyasn1

### Data / Analysis / Reporting

* **Core**: pandas, numpy, pytz, tzdata
* **Export**: openpyxl (Excel), reportlab (PDF)
* **Visualization**: plotly

### Network / HTTP

* **Clients**: httpx, requests
* **Utilities**: pythonping

### Build / Tools / Formatting (dev)

* **Formatter / linter**: black
* **Testing**: pytest, iniconfig, pluggy


## 8. Diagrams

### 8.1 High-Level Architecture
![overview-WARRIORFIT_Architectuur.png](overview-WARRIORFIT_Architectuur.png)



## 9. Stories (detail see Stories and Epics in stories.md)

Summary tables per epic. For full acceptance criteria see `stories.md`.

## Epic 1: User Management — 18 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 1.1 | Create new user | 5 | Must Have |
| 1.2 | Error handling for user creation | 2 | Must Have |
| 1.3 | Edit user | 5 | Must Have |
| 1.4 | Password reset by admin | 2 | Should Have |
| 1.5 | User list with search/filter | 2 | Should Have |
| 1.6 | Delete user | 2 | Should Have |

## Epic 2: Test Session Planning — 15 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 2.1 | Create new test session | 5 | Must Have |
| 2.2 | Update session | 3 | Should Have |
| 2.3 | Delete session | 2 | Should Have |
| 2.4 | View session list | 3 | Must Have |
| 2.5 | Upcoming sessions on welcome page | 2 | Should Have |

## Epic 3: PHEF Test Input — 18 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 3.1 | Select PHEF session | 2 | Must Have |
| 3.2 | Lookup serviceman via BEMIL | 2 | Must Have |
| 3.3 | Enter PHEF measurements | 5 | Must Have |
| 3.4 | Add PHEF result | 5 | Must Have |
| 3.5 | Update/delete PHEF result | 2 | Should Have |
| 3.6 | PHEF result grid | 2 | Should Have |

## Epic 4: Combat Test Input — 10 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 4.1 | Enter combat test results | 5 | Must Have |
| 4.2 | Add/update/delete combat result | 3 | Must Have |
| 4.3 | Combat result grid | 2 | Should Have |

## Epic 5: Swimming Test Input — 7 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 5.1 | Enter swimming test result | 4 | Should Have |
| 5.2 | Add/update/delete swim result | 2 | Should Have |
| 5.3 | Swimming result grid | 1 | Should Have |

## Epic 6: Functional Test Input — 12 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 6.1 | Enter functional test measurements | 5 | Must Have |
| 6.2 | Determine GO/NO-GO | 2 | Must Have |
| 6.3 | Add/update/delete functional result | 3 | Must Have |
| 6.4 | Functional result grid | 2 | Should Have |

## Epic 7: March Registration — 13 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 7.1 | Enter march | 5 | Must Have |
| 7.2 | Update march | 3 | Should Have |
| 7.3 | Delete march | 2 | Should Have |
| 7.4 | March list view | 3 | Should Have |

## Epic 8: Cross Session & Runner Management — 18 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 8.1 | Create/edit/delete cross session | 5 | Must Have |
| 8.2 | Enter cross runner results | 5 | Must Have |
| 8.3 | Update/delete cross runner | 3 | Should Have |
| 8.4 | Cross planning list view | 2 | Should Have |
| 8.5 | Cross statistics | 3 | Could Have |

## Epic 9: BEMIL Personnel Lookup — 5 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 9.1 | Lookup serviceman by serial number | 3 | Must Have |
| 9.2 | Browse all servicemen via modal | 2 | Should Have |

## Epic 10: Individual Test History — 15 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 10.1 | Search individual by serial number | 3 | Must Have |
| 10.2 | Display complete test history | 5 | Must Have |
| 10.3 | Generate individual PDF report | 5 | Should Have |
| 10.4 | Download PDF report | 2 | Should Have |

## Epic 11: Unit Status & Dashboard — 12 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 11.1 | View unit status grid | 5 | Must Have |
| 11.2 | View individual history via modal | 2 | Should Have |
| 11.3 | Unit dashboard with statistics | 3 | Should Have |
| 11.4 | PHEF not-done list | 2 | Should Have |

## Epic 12: Calendar Events — 5 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 12.1 | View personal test calendar | 3 | Should Have |
| 12.2 | View all test sessions calendar | 2 | Could Have |

## Epic 13: Fitness Room Reservation — 8 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 13.1 | Create room reservation | 5 | Should Have |
| 13.2 | View reservations (weekly/monthly/list) | 2 | Should Have |
| 13.3 | Delete reservation | 1 | Should Have |

## Epic 14: Audit Logs — 5 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 14.1 | View audit log | 3 | Must Have |
| 14.2 | Filter audit log | 2 | Should Have |

## Epic 15: Welcome Dashboard — 5 points

| Story # | Story Name | Points | Priority |
|---------|------------|--------|----------|
| 15.1 | Welcome page with role-specific info | 3 | Must Have |
| 15.2 | Upcoming sessions for PTI/APTI | 2 | Should Have |