# 🛡️ WARRIORFIT

### Digitization of Physical Military Tests at SOR-Unit Level

**Author:** Benoit Goethals

**Academic Year:** 2025–2026

**Project Status:** In Progress

**Project Type:** Software Engineering

**Project Duration:** 6 months

**Project Language:** Python

**Project development methodology:** Agile

**Project Development server:** http://78.21.255.210:8500/  
username: tester
password: tester007!


## Updates
* 2025-09-1: Project started
* 2025-10-30: all user stories done 
* 2025-11-15: extra user stories for cross management done
* 2025-11-30 Room reservation done
* 2025-12-01: HRM SIMULATOR done
* 2025-12-12: Prof of concept WarriorFit cross app done
* 2025-12-13: video demo done https://youtu.be/SdIgCeE7cGY
* 2026-01-04: Project first release ready for testing


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
* Cross (running event) management
* Reservation of rooms
* To integrate with existing Defence systems (HRM)
* To integrate with existing Defence systems (SIMULATOR)

## Project Development Methodology
The project is developed using Agile methodology and SOLID principles.
Using Epic and User Stories, the project is divided into different Epic implementations. With as goal to deliver a working product at the end of each epic implementation.
The project is developed using Github.
The project is managed using Github.


## 1. Project Structure (click links)
The project documentation is structured in different documents:
1. * [Design](documentation/Design.md) (In Review)
2. * [Business Logic](documentation/business_logic.md) (In Review)
3. * [Datamodel/ERD](documentation/datamodel.md) (In Review)
4. * [Stories](documentation/stories.md) (In Review)
5. * [Initiale proposalInitiale proposal](documentation/project_proposel.md) (Done)
6. * [Module Structures](documentation/module_structure.md) (In Review)
7. * [MOM (broker)](documentation/broker.md) (In Development) Message-Oriented Middleware
8. * [Install and deply](documentation/install.md) (In Development)
9. * [Retrospective](documentation/retrospective.md) 
10. * [Reservation Rooms](documentation/reservation_rooms.md) (out of scope,In Development)
11. * [HRM SIMULATOR](https://github.com/BenoitGoethals/HRM_API_REST) (In Development)
12. * [Testing](documentation/testcases.md) (In Development)
13. * [Cross App](documentation/crsossapp.md) (In Development)

if you want to see the project in action, you can check  :
 uvicorn ui.app:app --reload --log-level debug --host 0.0.0.0

## 2. Project Roadmap (PLANNING)
![progress.png](documentation/progress.png)

### **Phase 1 — Initiation & Project Charter (Sept 2025)** (Done)

* Project scope and vision
* Initialize backlog and repository

### **Phase 2 — Architecture & Structure (Okt 2026)** (Done)

* Technical foundation, layer structure, and UML
* Working skeleton project
* Proof of concept, working demo

### **Phase 3 — Development/enhancements/testing & Iterations (Okt–april 2026 (DONE))**

* Incremental deliveries via Agile sprints
* Enhancements and bug fixes
* Testing and validation

### **Phase 4 — Testing & Validation (april 2026)**

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

Copyright (c) 2025 Goethals Benoit

This source code is provided for viewing purposes only.

You may NOT:
- Use this code in any project
- Copy, modify, or distribute this code
- Use this code for commercial or non-commercial purposes

All rights reserved.


