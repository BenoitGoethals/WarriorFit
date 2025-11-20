# WarriorFit Design Document

## 1. Project Overview
WarriorFit is a comprehensive fitness and military management application designed to track physical performance, manage personnel data, and generate analytical reports. The system integrates data collection, statistical analysis, and reporting capabilities tailored for military fitness standards.

## 2. Architecture
The project follows a modular **Layered Architecture** ensuring separation of concerns between data access, business logic, and presentation.

### High-Level Structure
- **Presentation Layer (`ui`)**: Handles user interaction, displaying data, and capturing inputs using **Shiny for Python**. It is structured into `pages` (views) and `controllers` (logic for views).
- **Service Layer (`services`)**: Contains the core business logic, orchestrating data flow between the UI and the Data layer.
- **Data Layer (`data`)**: Manages database interactions using the Repository pattern and SQLAlchemy ORM.
- **Core Domain (`core`)**: Defines fundamental domain types, enums, and constants.

## 3. Technology Stack
- **Language**: Python 3.13.7
- **Package Manager**: uv
- **Web/Async Framework**: Tornado (underlying Shiny)
- **UI Framework**: Shiny for Python
- **Database**: SQLAlchemy (ORM), Alembic (Migrations), SQLite (default via `messages.db`, extensible)
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
- **Fitness Services**: `service_test.py`, `service_cross.py`, `service_mars.py`.
- **Reporting**: `report_generator_pdf.py`, `report_generator_csv.py`, `mail_service.py`.
- **Calculation**: Algorithms for calculating scores (e.g., PHEF, Functional tests).

### 4.5 User Interface (`ui`)
Organized into **Controllers** and **Pages** using **Shiny**.
- **Application Entry**: `app.py` defines the main `FitnessWarriorApp` class, handling authentication, navigation, and dynamic UI generation based on user roles.
- **Controllers**: Handle the logic for specific UI actions (e.g., `auditlog_events_controller.py`, `combat_controller.py`).
- **Pages**: Define the Shiny UI layout (inputs, outputs, cards) for specific application screens (e.g., `dashboard_own_unit.py`, `cross_planning.py`).

### 4.6 Integration (`military_api_rest`)
Handles external communication or exposes RESTful endpoints for military data integration.

## 5. Data Flow
1.  **User Action**: User interacts with a **Shiny Page** (e.g., clicks a button, enters text).
2.  **Reactive Event**: Shiny's reactive system triggers an event in the server logic.
3.  **Controller/Server**: The page's server function or associated controller processes the input.
4.  **Service**: The controller calls a **Service** method.
5.  **Repository**: The service delegates data retrieval/persistence to a **Repository**.
6.  **Database**: The repository executes queries against the **Database**.
7.  **Response**: Data flows back up.
8.  **Reactive Update**: Shiny updates the UI components (e.g., `render.text`, `render.data_frame`, `render.ui`) with the new data.

## 6. Diagrams

### 6.1 High-Level Architecture
![overview-WARRIORFIT_Architectuur.png](overview-WARRIORFIT_Architectuur.png)