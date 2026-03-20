# 🛡️ WARRIORFIT

### Digitization of Physical Military Tests at SOR-Unit Level

**Author:** Benoit Goethals

**Academic Year:** 2025–2026

**Project Status:** In Progress

**Project Type:** Software Engineering

**Project Duration:** 6 months

**Project Language:** Python

**Project development methodology:** Agile

**Project Development server:** https://test.warriorfit.bensoft.be/
username: tester
password: Tester@1401!

**Test mailserver view : https://mailstub.bensoft.be/
**Test HR Simulator view : https://api.bensoft.be/

Final view of the Architecture -> [Architectural Structure](documentation/ARCHITECTURE.md)



## Updates
* 2025-09-1: Project started
* 2025-10-30: all user stories done 
* 2025-11-15: extra user stories for cross management done
* 2025-11-30 Room reservation done
* 2025-12-01: HRM SIMULATOR done
* 2025-12-12: Prof of concept WarriorFit cross app done
* 2025-12-13: video demo done 
* 2026-01-04: Project first release ready for testing
* 2026-01-11: Start testing, test cases 
* 2026-01-18: Testing completed, release to 1.0 RC
* 2026-01-19: added search in tests sessions
* 2026-01-27: update retrospective
* 2026-01-27: demo video uploaded https://youtu.be/bblCsxhbMEg
* 2026-01-28: make HRM simulator API secure with key:
* 2026-02-01: setup nginx reverse proxy
* 2026-02-02: Cross app and api SSL/HTTPS Support**: Encrypted communication with SSL certificates
* 2026-02-03: versioning by git hook pre-commit
* 2026-02-07 : update cross app and rest api with 2oauth and certificates
* 2026-02-13 : Big refactoring, use Dependency Injection [DI Usage Guide](documentation/DI_USAGE_GUIDE.md)
* 2026-02-14 : Add Architectural structure document [Architectural Structure](documentation/ARCHITECTURE.md)
* 2026-02-14 : Bug fix container.py (DI wiring)
* 2026-02-14 : Update cross app documentation [Cross App](documentation/crsossapp.md)
* 2026-02-15 : refactor security + audit security
* 2026-03-18 : security hardening — remove Fernet, migrate to bcrypt, fix audit log nullable user_id, add SECURITY.md
* 2026-03-19 : migrate password hashing from bcrypt to Argon2id, remove bcrypt/passlib dependencies
* 2026-03-19 : fix Docker read-only volume mount — settings can now be saved from the UI in production
* 2026-03-20 : modern UI/UX redesign — custom CSS design system (navy/amber theme, `www/custom.css`), 
  consistent button colours (Refresh, Confirm Serial, Search own Unit) across all pages, 
  login modal error feedback fixed, User Management sidebar restructured, 
  Plotly chart fix on Dashboard tab switch, 
  Reserve Room renamed to Sport Area, reservation overlay CSS fixed
* 2026-03-21 : update video demo



## Project Description
WarriorFit is a comprehensive fitness and military management application designed to track physical performance, manage personnel data, and generate analytical reports. The system integrates data collection, statistical analysis, and reporting capabilities tailored for military fitness standards.
Each unit within Defence has a **physical training cell** aimed at preparing soldiers physically for operational deployment.
Annually, every soldier must complete the **PHEF** (Physical Fitness Evaluation Defence). In addition, combat units carry out **functional** and **combat tests**, while paracommandos must endure additional **combat evaluations**.
Currently, much of this process is manual, leading to inefficiency, errors, and administrative delays.

The system includes user management, test input, calculations, PDF reporting, and email distribution. It is designed for local server deployment within Defense.

## Project Goals
The main goals of this project are:
* To develop a comprehensive fitness military management application
* To integrate data collection, statistical analysis, and reporting capabilities tailored for military fitness standards
* Cross (running event) management (out of scope)
* Reservation of rooms (out of scope)
* To integrate with existing Defence systems (HRM)
* To integrate with existing Defence systems (SIMULATOR)

## Project Development Methodology
The project is developed using Agile methodology and SOLID principles.
Using Epic and User Stories, the project is divided into different Epic implementations. With as goal to deliver a working product at the end of each epic implementation.
The project is developed using Github.
The project is managed using Github.


## 1. Project Structure (click links)
The project documentation is structured in different documents:
1. * [Design](documentation/Design.md) (Done)
2. * [Business Logic](documentation/business_logic.md) (Done)
3. * [Datamodel/ERD](documentation/datamodel.md) (Done)
4. * [Stories](documentation/stories.md) (Done)
5. * [Initial proposal](documentation/project_proposel.md) (Done)
6. * [Architectural Structure](documentation/ARCHITECTURE.md) (Done)
7. * [Module Structures](documentation/module_structure.md) (Done)
8. * [MOM (broker)](documentation/broker.md) (In testing) Message-Oriented Middleware
9. * [Install and Deploy](documentation/install.md) (Done)
10. * [Retrospective](documentation/retrospective.md)
11. * [Reservation Rooms](documentation/reservation_rooms.md) (out of scope, In Development)
12. * [HRM SIMULATOR](https://github.com/BenoitGoethals/HRM_API_REST) (Done)
13. * [Testing](documentation/testcases.md) (In Development)
14. * [Cross App](documentation/crsossapp.md) (out of scope, In Development)
15. * [Server architecture](documentation/server.md) (Done)
16. * [DI Usage Guide](documentation/DI_USAGE_GUIDE.md) (Done)
17. * [Changelog](CHANGELOG.md)
18. * [Security](SECURITY.md) (Done)

if you want to see the project in action, you can check  :
 uvicorn ui.app:app --reload --log-level debug --host 0.0.0.0

## 2. Project Roadmap (PLANNING)
![progress.png](documentation/progress.png)

### **Phase 1 — Initiation & Project Charter (Sept 2025)** (Done)

* Project scope and vision
* Initialize backlog and repository

### **Phase 2 — Architecture & Structure (Okt 2025)** (Done)

* Technical foundation, layer structure, and UML
* Working skeleton project
* Proof of concept, working demo

### **Phase 3 — Development/enhancements/testing & Iterations (Okt 2025–April 2026 (DONE))**

* Incremental deliveries via Agile sprints
* Enhancements and bug fixes
* Testing and validation

### **Phase 4 — Testing & Validation (April 2026)**

* Acceptance testing and bug fixing

### **Phase 5 — Delivery & Demo (Jun 2026)**

* Final demo and handover to end users


## 3. Project Management
This project is managed by a team of 1 person.
Using Github project with Agile methodology.
On the kanban board, you can see the different tasks and their status.
https://github.com/users/BenoitGoethals/projects/20


## 4. SOR structuur

![land-nl.png](documentation/land-nl.png)


 ## Licence

Copyright (c) 2026 Goethals Benoit

This source code is provided for viewing purposes only.

You may NOT:
- Use this code in any project
- Copy, modify, or distribute this code
- Use this code for commercial or non-commercial purposes

All rights reserved.


