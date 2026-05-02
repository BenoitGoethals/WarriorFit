# WarriorFit - User Manual

## Table of Contents

- [Introduction](#introduction)
- [Roles and Access](#roles-and-access)
- [Logging In](#logging-in)
- [Navigation](#navigation)
- [Guide by Role](#guide-by-role)
  - [All Users](#all-users)
  - [PTI / APTI (Physical Training Instructor)](#pti-apti-physical-training-instructor)
  - [PLANNER](#planner)
  - [GUEST](#guest)
  - [ADMIN](#admin)
- [Page Reference](#page-reference)
  - [Welcome](#welcome)
  - [Dashboard](#dashboard)
  - [Status Unit](#status-unit)
  - [Individual](#individual)
  - [Reports](#reports)
  - [Reserve Sport Area](#reserve-sport-area)
  - [Sessions](#sessions)
  - [PHEF Tests](#phef-tests)
  - [Combat Tests](#combat-tests)
  - [Functional Tests](#functional-tests)
  - [Swimming Tests](#swimming-tests)
  - [March](#march)
  - [PHEF Not Done](#phef-not-done)
  - [Cross Planning](#cross-planning)
  - [Cross](#cross)
  - [Cross Statistics](#cross-statistics)
  - [User Management](#user-management)
  - [Audit Logs](#audit-logs)
  - [Settings](#settings)
  - [Status Application](#status-application)
  - [About](#about)

---

## Introduction

WarriorFit is a military physical fitness test digitization platform. It allows units to record, manage, and report on all mandated fitness tests — PHEF, Combat, Functional, Swimming, and March — as well as plan cross-running events and reserve sport facilities.

---

## Roles and Access

| Role | Description | Access Level |
|------|-------------|--------------|
| **ADMIN** | System administrator | Full access to all pages, user management, settings, and audit logs |
| **PTI** | Physical Training Instructor | Record tests, manage sessions, view dashboards, generate reports, book sport areas |
| **APTI** | Assistant PTI | Same access as PTI |
| **PLANNER** | Training session planner | Create and manage test sessions |
| **GUEST** | Read-only viewer | View unit status and individual test records |
| **USER** | Basic user | Limited access |

---

## Logging In

1. Open WarriorFit in your browser.
2. Enter your **username** and **password**.
3. Click **Sign In**.
4. You will be redirected to the Welcome page.

Your role determines which pages and actions are available to you.

---

## Navigation

The top navigation bar contains:

- **Root pages**: Welcome, Dashboard, Status Unit, Individual, Reports, Reserve Sport Area
- **Psychical Tests** menu: PHEF, Combat, Functional, Swimming, March, PHEF Not Done, Sessions
- **Cross/Runs** menu: Cross Statistics, Cross Planning, Cross
- **Admin** menu (admin only): Audit Logs, User Management, Settings, Status Application
- **Right side**: Your username and role, My Calendar, Unit Calendar, and Sign Out

---

## Guide by Role

### All Users

All logged-in users can access the **About** page for application information.

---

### PTI / APTI (Physical Training Instructor)

As a PTI or APTI, your primary tasks are recording fitness tests and managing your unit's training status.

#### Daily workflow

1. **Check your upcoming sessions** on the Welcome page.
2. **Record test results** during a session:
   - Navigate to the appropriate test page (PHEF, Combat, Functional, Swimming, or March).
   - Select the test session from the dropdown.
   - Enter the serviceman's serial number (use **Search own Unit** to look up by name).
   - Click **Confirm Serial** to validate.
   - Enter the test results. Scores update in real time.
   - Click **Add** to save the record.
3. **Review unit status** on the Dashboard or Status Unit page.
4. **Generate reports** from the Reports page.
5. **Book sport areas** via Reserve Sport Area.

#### Recording a PHEF Test

1. Go to **Psychical Tests > PHEF Tests**.
2. Select a **Session** from the dropdown.
3. Enter the serviceman's **serial number** or click **Search own Unit** to find them.
4. Click **Confirm Serial**.
5. Enter:
   - **Side-bridge Right** time (mm:ss)
   - **Side-bridge Left** time (mm:ss)
   - **2400m Run** time (mm:ss)
6. Observe the real-time score (green = pass, red = fail).
7. Click **Add** to save.
8. The record appears in the data grid on the right.

#### Recording a Combat Test

1. Go to **Psychical Tests > Combat Tests**.
2. Select a session and confirm the serviceman's serial.
3. Check the boxes for completed components:
   - **Obstacle course**
   - **Robe course**
4. Enter **Speedmars** time (mm:ss).
5. Click **Add**.

#### Recording a Functional Test

1. Go to **Psychical Tests > Functional Tests**.
2. Select a session and confirm the serial.
3. Enter counts for:
   - **Push-ups**
   - **Sit-ups**
   - **Pull-ups**
4. Click **Add**.

#### Recording a Swimming Test

1. Go to **Psychical Tests > Swimming Tests**.
2. Select a session and confirm the serial.
3. Check **Swimming test passed** if applicable.
4. Click **Add**.

#### Recording a March

1. Go to **Psychical Tests > March**.
2. Enter the serviceman's serial number.
3. Enter **distance** (km), **date**, and check **Succeeded** if applicable.
4. Click **Add**.

#### Editing or Deleting a Test Record

1. On any test page, click a row in the data grid to select it.
2. The form populates with the selected record's data.
3. Modify the values and click **Update**, or click **Delete Selected** to remove it.
4. Click **Clear Form** to reset the form.

#### Generating Reports

1. Go to **Reports**.
2. Configure:
   - **Report title**
   - **Test type** (All, PHEF, Functional, Combat, Swimming)
   - **Scope** (Own unit only or all units)
   - **Time period** (This year or all)
   - **Format** (PDF, CSV, or Both)
3. Click **Generate Report**.
4. Click **Download** to get the ZIP file with your reports.

#### Booking a Sport Area

1. Go to **Reserve Sport Area**.
2. Browse the **Weekly**, **Monthly**, or **List** view.
3. Click **New Reservation**.
4. Fill in the PTI, room, date/time, and notes.
5. Submit the reservation.
6. To edit or cancel, select the reservation and modify it.

#### Managing Cross Events

1. Go to **Cross/Runs > Cross Planning** to create an event (date, time, distance).
2. Go to **Cross/Runs > Cross** to manage runners:
   - Select the cross event from the dropdown.
   - Add runners by serial number, or **upload a Chronos XML file** with runner times.
   - Generate a running report.
3. View **Cross/Runs > Cross Statistics** for best performers by distance and age group.

#### Checking Who Still Needs Testing

Go to **Psychical Tests > PHEF Not Done** to see servicemen who have not completed their PHEF test this year.

---

### PLANNER

As a Planner, you manage test session scheduling.

#### Creating a Test Session

1. Go to **Sessions** (your main page).
2. Fill in:
   - **Date** and **Time**
   - **Test type** (PHEF, Combat, Functional, Swimming)
   - **PTI serial number** (the instructor running the session)
   - **Description** (optional)
3. Click **Add**.

#### Editing or Cancelling a Session

1. Select a session row in the data grid.
2. Modify fields as needed, or check **Cancelled**.
3. Click **Update**.

#### Deleting a Session

1. Select a session row.
2. Click **Delete**.

---

### GUEST

As a Guest, you have read-only access.

#### What You Can Do

- **Status Unit**: View servicemen in the unit and their test completion status. Click a row to see individual test history in a modal.
- **Individual**: Look up any serviceman by serial number to view their full test history. Generate and download an individual PDF report.

---

### ADMIN

As an Admin, you have full access to all PTI/APTI features plus system administration.

#### Managing Users

1. Go to **Admin > User Management**.
2. The left panel shows all users. Click a row to select and edit.
3. **Create a user**:
   - Fill in: serial number, username, password, email, role, active status.
   - Use **Search** to look up the serial from the military personnel list.
   - Click **Create**.
4. **Edit a user**: Select the user, modify fields, click **Update**.
5. **Delete a user**: Select the user, click **Delete**.

#### Viewing Audit Logs

1. Go to **Admin > Audit Logs**.
2. Browse the data grid showing all system events (logins, failed attempts, data changes).
3. Use column filters to narrow results.

#### Configuring Settings

1. Go to **Admin > Settings**.
2. Edit the following sections:
   - **Unit Settings**: Your unit's name.
   - **Database**: Host, port, database, credentials.
   - **HR Configuration**: HR system URL and API key.
   - **Mail**: SMTP host, port, credentials, sender, SSL/TLS toggles.
   - **Paths**: PDF output path for reports.
3. Click **Save All Configuration**.

#### Monitoring System Health

1. Go to **Admin > Status Application**.
2. View service connectivity cards: Database, HR service, mail server, server status.
3. Review runtime metrics: memory usage, CPU, threads, uptime.
4. Check the live log viewer for recent application logs.

---

## Page Reference

### Welcome

Your landing page after login. Shows a welcome banner with version info and upcoming test sessions for PTI/APTI users.

### Dashboard

Unit-level statistics: personnel count, test counts by type, pass/fail charts, and PHEF score distribution. Click **Refresh** to reload.

### Status Unit

Lists all servicemen in your unit with their test completion status (PHEF, Combat, Swimming). Click a row to view individual history. Generate a full unit PDF report.

### Individual

Look up a serviceman by serial number. Displays all test history across all test types. Generate and download an individual PDF report.

### Reports

Configurable report generator. Filter by test type, scope, time period. Export as PDF, CSV, or both. Download as ZIP.

### Reserve Sport Area

Weekly/monthly/list calendar views for sport area bookings. Create, edit, and delete reservations.

### Sessions

Create and manage fitness test sessions. Each session has a date, time, test type, assigned PTI, and optional description. Sessions can be cancelled.

### PHEF Tests

Record Physical and Endurance Fitness test results: side-bridge (left/right) and 2400m run times. Real-time scoring. Pass criteria: side-bridge total score >= 20 AND running score >= 10.

### Combat Tests

Record combat fitness results: obstacle course, robe course (checkboxes), and speedmars time. All components must be completed to pass.

### Functional Tests

Record functional strength results: push-ups, sit-ups, and pull-ups counts. Scores calculated per exercise.

### Swimming Tests

Record swimming test as pass/fail.

### March

Record march/ruck march results: distance, date, and pass/fail.

### PHEF Not Done

View servicemen who have not yet completed a PHEF test in the current year.

### Cross Planning

Plan cross-running events: set date, time, distance, and description. Mark events as executed.

### Cross

Manage runners in a cross event. Add runners manually or upload Chronos XML data. Generate running reports.

### Cross Statistics

View top 10 runners for 5km and 10km distances, broken down by age group.

### User Management

Admin-only. Full CRUD for user accounts: create, edit, delete, assign roles, toggle active status.

### Audit Logs

Admin-only. Filterable log of all system events: logins, failed login attempts, data modifications.

### Settings

Admin-only. Configure unit name, database, HR integration, mail server, and file paths.

### Status Application

Admin-only. System health dashboard: service connectivity, runtime metrics (memory, CPU, threads, uptime), and live log viewer.

### About

Application information: project overview, development team, version, and release date.
