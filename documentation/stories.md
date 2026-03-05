# User Stories – Overview per Epic

User stories are used instead of Use Cases for more flexibility in agile development.
WarriorFit is a Python Shiny for Python desktop web application for managing Belgian military fitness tests.
The point estimates below reflect implementation effort.

### Total Overview

* **Total epics:** 19
* **Total stories:** 71
* **Total story points:** 196

### Story Point Legend

* 1 point = 2–4 hours
* 2 points = 4–8 hours
* 3 points = 1–2 days
* 5 points = 2–3 days
* 8 points = 3–5 days

### Roles

* **admin** – Full system access including user management, settings, audit logs, and status monitoring
* **PTI** – Physical Training Instructor; manages test sessions, enters test results for own unit
* **APTI** – Assistant PTI; same permissions as PTI but for a sub-unit
* **PLANNER** – Limited role; can only access the Sessions planning page
* **GUEST** – Read-only access to unit status and individual test history

---

## Epic 1: User Management (18 points)

**Epic total:** 18 points
**Estimated:** 3–4 sprints

| #   | Story                            | Points | Priority    |
| --- | -------------------------------- | ------ | ----------- |
| 1.1 | Create new user                  | 5      | Must Have   |
| 1.2 | Error handling for user creation | 2      | Must Have   |
| 1.3 | Edit user                        | 5      | Must Have   |
| 1.4 | Password reset by admin          | 2      | Should Have |
| 1.5 | User list with search/filter     | 2      | Should Have |
| 1.6 | Delete user                      | 2      | Should Have |

### Story 1.1: Create new user [5 points]

**As** admin
**I want** to create a new user with username, email, password, role, and serial number
**So that** staff members can access the system

**Acceptance criteria:**

* Form fields: username, email, password (masked with toggle), role (dropdown), serial number
* Username must be unique (3–30 characters, a-z, 0–9, ., _, -)
* Email must be valid and unique
* Password minimum 12 characters with complexity requirements
* Serial number must be unique and must exist in BEMIL
* Role choices: admin, PTI, APTI, PLANNER, GUEST
* Audit log records creation (who, what, when)
* Success notification: "User created"

**Tasks:**

* User creation form
* Backend user creation with password hashing
* Audit logging on save

### Story 1.2: Error handling for user creation [2 points]

**As** admin
**I want** clear error messages when something fails
**So that** I know what to fix

**Acceptance criteria:**

* Username conflict: "Username already taken" message
* Email conflict: "Email already in use"
* Serial number conflict: error displayed in status field
* Weak password: specific validation feedback
* Error message shown inline in the form

**Tasks:**

* Input validation before save
* Server-side uniqueness checks

### Story 1.3: Edit user [5 points]

**As** admin
**I want** to select and update an existing user
**So that** data stays up-to-date

**Acceptance criteria:**

* Select user from grid (click row → form pre-fills)
* Editable fields: email, role, serial number, active status, remarks
* Password field: leave blank to keep unchanged
* Same validation as creation (unique constraints)
* Audit log records all changes
* Success: "User updated" notification

**Tasks:**

* Row selection fills form fields
* Update button triggers save
* Validation on changed fields

### Story 1.4: Password reset by admin [2 points]

**As** admin
**I want** to reset a user password
**So that** users can log in again when they forget it

**Acceptance criteria:**

* New password field in edit form
* Audit log records reset action
* Password hashed before save
* Status message confirms reset

**Tasks:**

* Password field with toggle in edit form
* Save new hashed password on submit

### Story 1.5: User list with search [2 points]

**As** admin
**I want** an overview of all users with filtering
**So that** I can quickly find a specific user

**Acceptance criteria:**

* Grid columns: username, email, role, serial number, active status
* Column filters on the grid
* Click row to load user in edit form
* Refresh button to reload data

**Tasks:**

* Filterable grid populated from user data
* Row selection triggers form fill

### Story 1.6: Delete user [2 points]

**As** admin
**I want** to delete a user account
**So that** inactive accounts can be removed

**Acceptance criteria:**

* Select user row, click "Delete Selected"
* Confirmation via status message
* Audit log records deletion
* Grid refreshes after delete

**Tasks:**

* Delete button with selected row check
* Backend deletion with audit log

---

## Epic 2: Test Session Planning (15 points)

**Epic total:** 15 points
**Estimated:** 3 sprints

| #   | Story                   | Points | Priority    |
| --- | ----------------------- | ------ | ----------- |
| 2.1 | Create new test session | 5      | Must Have   |
| 2.2 | Update session          | 3      | Should Have |
| 2.3 | Delete session          | 2      | Should Have |
| 2.4 | View session list       | 3      | Must Have   |
| 2.5 | Upcoming sessions       | 2      | Should Have |

### Story 2.1: Create new test session [5 points]

**As** PTI, APTI, admin, or PLANNER
**I want** to create a new test session
**So that** fitness tests can be scheduled

**Acceptance criteria:**

* Form fields: PTI serial number (dropdown from BEMIL), date, time (HH:MM), test type, description, canceled checkbox
* Test types: PHEF, Combat, Functional, Swimming
* PTI dropdown populates from BEMIL (all known PTIs)
* Validation: date and type are required, time format HH:MM
* Session appears immediately in the list after add
* Status message confirms "Session added successfully"
* Form clears after successful add
* Email notification sent to PTI on session creation (if mail configured)
* Sessions page is accessible at root level for PLANNER; also under "Psychical Tests" menu for PTI/APTI/admin

**Tasks:**

* Session creation form
* Input validation
* Email notification on successful save

### Story 2.2: Update session [3 points]

**As** PTI, APTI, admin, or PLANNER
**I want** to modify a test session
**So that** planning can be adjusted

**Acceptance criteria:**

* Click row in grid → form pre-fills
* Editable: PTI, date, time, type, description, canceled
* "Update" button saves changes
* Grid refreshes on save
* Status message: "Session updated"

**Tasks:**

* Row selection triggers form fill
* Update button handler

### Story 2.3: Delete session [2 points]

**As** PTI, APTI, admin, or PLANNER
**I want** to cancel a test session
**So that** incorrect planning is removed

**Acceptance criteria:**

* "Delete Selected" button removes selected session
* Grid refreshes after delete
* Status message confirms deletion

**Tasks:**

* Delete button with selected row check
* Backend deletion

### Story 2.4: View session list [3 points]

**As** PTI, APTI, admin, or PLANNER
**I want** to see a list of test sessions
**So that** I can review upcoming and recent tests

**Acceptance criteria:**

* Grid columns: Start date, Type, PTI serial, Canceled, Description
* Filterable columns
* Sorted by start date ascending
* Refresh button to reload
* Row selection loads session in form

**Tasks:**

* Filterable and sortable session grid
* Row selection triggers form fill

### Story 2.5: Upcoming sessions on welcome page [2 points]

**As** PTI or APTI
**I want** to see upcoming test sessions on the welcome page
**So that** I know what's planned for my unit

**Acceptance criteria:**

* Grid on "Welcome" tab visible to PTI/APTI roles only
* Shows sessions where PTI serial matches logged-in user
* Filterable and refreshable

**Tasks:**

* Upcoming sessions query filtered by logged-in user serial
* Role check before showing the widget

---

## Epic 3: PHEF Test Input (18 points)

**Epic total:** 18 points
**Estimated:** 3–4 sprints

| #   | Story                       | Points | Priority    |
| --- | --------------------------- | ------ | ----------- |
| 3.1 | Select PHEF session         | 2      | Must Have   |
| 3.2 | Lookup serviceman via BEMIL | 2      | Must Have   |
| 3.3 | Enter PHEF measurements     | 5      | Must Have   |
| 3.4 | Add PHEF result             | 5      | Must Have   |
| 3.5 | Update/delete PHEF result   | 2      | Should Have |
| 3.6 | PHEF result grid            | 2      | Should Have |

### Story 3.1: Select PHEF session [2 points]

**As** PTI
**I want** to select a PHEF session
**So that** results link to the correct session

**Acceptance criteria:**

* Dropdown lists available sessions of type PHEF
* Session stays selected for multiple entries within same page load
* Changing session refreshes result grid

**Tasks:**

* Session dropdown populated from available PHEF sessions
* Session selection state retained during page use

### Story 3.2: Lookup serviceman via BEMIL [2 points]

**As** PTI
**I want** to validate a serviceman via BEMIL before entering results
**So that** data is correct

**Acceptance criteria:**

* Serial number text input
* "Confirm Serial" button triggers BEMIL lookup
* If found: show rank, name, gender, age (read-only)
* If not found: "Not found" message; form inputs stay disabled
* Search icon button opens modal to browse all servicemen
* After confirmation: measurement inputs become enabled

**Tasks:**

* Serial number lookup against BEMIL
* Browse modal with filterable servicemen grid

### Story 3.3: Enter PHEF measurements [5 points]

**As** PTI
**I want** to enter PHEF measurement values
**So that** test results are calculated in real time

**Acceptance criteria:**

* Fields: Side-bridge Right (mm:ss), Side-bridge Left (mm:ss), 2400m run (mm:ss)
* Live score displayed next to each field (green if ≥10, red if <10)
* Total score shown with PASSED/FAILED label (color-coded)
* PASSED = side-bridge total ≥20 AND run score ≥10
* Inputs disabled until serviceman is confirmed
* Format validation: mm:ss pattern

**Tasks:**

* Time parsing from mm:ss to seconds
* Real-time score calculation per component
* Reactive score display with color feedback

### Story 3.4: Add PHEF result [5 points]

**As** PTI
**I want** to save a PHEF result
**So that** it is registered

**Acceptance criteria:**

* "Add" button enabled only after serviceman confirmed and session selected
* Saves serial, session, times (in seconds), scores, pass/fail
* Audit log entry created
* Grid refreshes after save
* Status: "Added PHEF test for [serial] in session [id]"
* Form clears after save
* Email notification sent on successful save (if mail configured)

**Tasks:**

* Backend save with audit logging
* Email notification on successful save
* Form reset after save

### Story 3.5: Update/delete PHEF result [2 points]

**As** PTI
**I want** to correct or remove a PHEF entry
**So that** errors can be fixed

**Acceptance criteria:**

* Click row in grid → form pre-fills (Add disabled, Update enabled)
* "Update" button saves changes
* "Delete Selected" button removes entry
* Grid refreshes on both actions

**Tasks:**

* Row selection fills form and switches button state
* Backend update and delete

### Story 3.6: PHEF result grid [2 points]

**As** PTI
**I want** to see PHEF results for the selected session
**So that** I know who has been tested

**Acceptance criteria:**

* Columns: Serial, Sidebridge R, Sidebridge L, Run time, Scores, Pass/Fail
* Filtered by selected session
* Sortable by serial
* Refreshes when data changes

**Tasks:**

* Filterable result grid with color-coded pass/fail column

---

## Epic 4: Combat Test Input (10 points)

**Epic total:** 10 points
**Estimated:** 2 sprints

| #   | Story                      | Points | Priority    |
| --- | -------------------------- | ------ | ----------- |
| 4.1 | Enter combat test results  | 5      | Must Have   |
| 4.2 | Add/update/delete combat   | 3      | Must Have   |
| 4.3 | Combat result grid         | 2      | Should Have |

### Story 4.1: Enter combat test results [5 points]

**As** PTI
**I want** to enter combat test results (3 components)
**So that** performance is registered

**Acceptance criteria:**

* Session selection (Combat type)
* BEMIL serial lookup + "Confirm Serial"
* Inputs:
  * Speed march (16km) → GO/NO-GO checkbox
  * Obstacle course → GO/NO-GO checkbox
  * Rope course → GO/NO-GO checkbox
* Final result: GO only if all 3 components are GO
* Visual GO/FAIL indicator
* Optional remarks per component

**Tasks:**

* Combat form with 3 GO/NO-GO inputs
* Final result logic based on all components

### Story 4.2: Add/update/delete combat result [3 points]

**As** PTI
**I want** to save, edit, or remove a combat result
**So that** it is correctly registered

**Acceptance criteria:**

* "Add" saves new result; grid updates
* Row selection → form fill for update
* "Update" / "Delete Selected" available on selection
* Status message confirms each action

**Tasks:**

* Backend create, update, delete
* Grid refresh on each action

### Story 4.3: Combat result grid [2 points]

**As** PTI
**I want** to see combat results for the selected session

**Acceptance criteria:**

* Columns: serial, speed march, obstacle, rope, final result, remarks
* Filtered by selected session
* Refresh button works

**Tasks:**

* Filterable result grid filtered by session

---

## Epic 5: Swimming Test Input (7 points)

**Epic total:** 7 points
**Estimated:** 1–2 sprints

| #   | Story                        | Points | Priority    |
| --- | ---------------------------- | ------ | ----------- |
| 5.1 | Enter swimming test result   | 4      | Should Have |
| 5.2 | Add/update/delete swim       | 2      | Should Have |
| 5.3 | Swimming result grid         | 1      | Should Have |

### Story 5.1: Enter swimming test result [4 points]

**As** PTI
**I want** to enter swimming test results
**So that** the 100m combat-gear swim test is registered

**Acceptance criteria:**

* Swimming session selection
* BEMIL serial lookup
* Result: GO / NO-GO selection
* Optional remarks
* Form clears after save

**Tasks:**

* Swimming test form with session selection and serial lookup
* Backend save

### Story 5.2: Add/update/delete swim result [2 points]

**As** PTI
**I want** to save, edit, or remove a swimming result

**Acceptance criteria:**

* "Add" creates new result
* Row selection → form pre-fill for update
* "Delete Selected" removes result
* Grid refreshes after each action

**Tasks:**

* Backend create, update, delete

### Story 5.3: Swimming result grid [1 point]

**As** PTI
**I want** to see swimming results for the selected session

**Acceptance criteria:**

* Columns: serial, result, remarks
* Filtered by selected session

**Tasks:**

* Result grid filtered by selected session

---

## Epic 6: Functional Test Input (12 points)

**Epic total:** 12 points
**Estimated:** 2–3 sprints

| #   | Story                               | Points | Priority    |
| --- | ----------------------------------- | ------ | ----------- |
| 6.1 | Enter functional test measurements  | 5      | Must Have   |
| 6.2 | Determine GO/NO-GO                  | 2      | Must Have   |
| 6.3 | Add/update/delete functional result | 3      | Must Have   |
| 6.4 | Functional result grid              | 2      | Should Have |

### Story 6.1: Enter functional test measurements [5 points]

**As** PTI
**I want** to enter functional test data
**So that** performance is recorded

**Acceptance criteria:**

* Functional session selection
* BEMIL serial lookup + confirm
* Integer inputs: pull-ups (0–100), push-ups 2min (0–200), sit-ups 2min (0–200)
* Real-time calculation of points per component (age/gender corrected)
* Percentage of max shown per component
* Total score displayed

**Tasks:**

* Functional test form with session selection and serial lookup
* Real-time scoring per component

### Story 6.2: Determine GO/NO-GO [2 points]

**As** PTI
**I want** the system to determine GO/NO-GO automatically

**Acceptance criteria:**

* Rule: minimum 50% per component required
* Component GO if ≥ 50%
* Final GO only if all 3 components are GO
* Visual color-coded feedback per component (green/red)
* Final result badge shown prominently

**Tasks:**

* GO/NO-GO calculation logic
* Color-coded result display per component

### Story 6.3: Add/update/delete functional result [3 points]

**As** PTI
**I want** to save, edit, or remove functional test results

**Acceptance criteria:**

* "Add" saves counts, percentages, component GO/NO-GO, final result
* Row selection → form pre-fill for update
* "Delete Selected" removes result
* Grid refreshes after each action
* Status message confirms action

**Tasks:**

* Backend create, update, delete
* Grid refresh on each action

### Story 6.4: Functional result grid [2 points]

**As** PTI
**I want** to view functional test results for the selected session

**Acceptance criteria:**

* Columns: serial, pull-ups, push-ups, sit-ups, total score, final result
* Filtered by selected session

**Tasks:**

* Result grid filtered by selected session

---

## Epic 7: March Registration (13 points)

**Epic total:** 13 points
**Estimated:** 2–3 sprints

| #   | Story           | Points | Priority    |
| --- | --------------- | ------ | ----------- |
| 7.1 | Enter march     | 5      | Must Have   |
| 7.2 | Update march    | 3      | Should Have |
| 7.3 | Delete march    | 2      | Should Have |
| 7.4 | March list view | 3      | Should Have |

### Story 7.1: Enter march [5 points]

**As** PTI or APTI
**I want** to register a march for a serviceman
**So that** march performances are tracked

**Acceptance criteria:**

* Serial number input + "Confirm Serial" validates via BEMIL
* BEMIL search modal available ("Search own Unit" button)
* After confirmation: rank, name, gender, age shown read-only
* Date picker (date executed)
* Distance (km, numeric, default 30, min 0)
* Succeeded checkbox (default unchecked)
* "Add" button creates record
* Uniqueness check: same serial + distance + date = duplicate rejected
* Form clears after successful add
* Email notification sent on successful add (if mail configured)

**Tasks:**

* March registration form with serial lookup
* Uniqueness validation before save
* Email notification on successful save

### Story 7.2: Update march [3 points]

**As** PTI or APTI
**I want** to modify a march registration

**Acceptance criteria:**

* Click row → form pre-fills
* Editable: date, distance, succeeded
* "Update" button saves
* Grid updates immediately

**Tasks:**

* Row selection triggers form fill
* Backend update

### Story 7.3: Delete march [2 points]

**As** PTI or admin
**I want** to delete a march registration

**Acceptance criteria:**

* Select row and click "Delete"
* Grid updates after deletion

**Tasks:**

* Backend deletion with grid refresh

### Story 7.4: March list view [3 points]

**As** PTI or APTI
**I want** to see all march registrations

**Acceptance criteria:**

* Grid columns: serial number, distance, Succeeded (✓/✗), Date
* Sortable by serial number
* Refresh button
* Internal ID not shown in grid

**Tasks:**

* Sortable march grid excluding internal ID column

---

## Epic 8: Cross Session & Runner Management (18 points)

**Epic total:** 18 points
**Estimated:** 3 sprints

| #   | Story                      | Points | Priority    |
| --- | -------------------------- | ------ | ----------- |
| 8.1 | Create/edit/delete cross   | 5      | Must Have   |
| 8.2 | Enter cross runner results | 5      | Must Have   |
| 8.3 | Update/delete cross runner | 3      | Should Have |
| 8.4 | Cross planning list view   | 2      | Should Have |
| 8.5 | Cross statistics           | 3      | Could Have  |

### Story 8.1: Create/edit/delete cross session [5 points]

**As** PTI or admin
**I want** to manage cross sessions
**So that** cross training sessions can be scheduled

**Acceptance criteria:**

* Form: date, time (HH:MM), distance (km), executed (checkbox), description
* "Add" creates cross session; list updates immediately
* Click row → form pre-fills for edit
* "Update" saves changes
* "Delete" removes selected session
* "Clear" resets all form fields
* Grid columns: ID, Start, Executed, Distance, Description

**Tasks:**

* Cross session form with create, update, delete
* Grid refresh on each action

### Story 8.2: Enter cross runner results [5 points]

**As** PTI
**I want** to enter running times for servicemen in a cross
**So that** performances are recorded

**Acceptance criteria:**

* Select cross session from dropdown
* Serial number input + "Confirm Serial" via BEMIL
* BEMIL search modal available
* Enter running time (hh:mm:ss format)
* System calculates running time in seconds
* "Add" adds runner to grid
* Grid columns: Order, Serial, Running Time, Runner Name, Gender, Age, Seconds, Unit
* Order assigned automatically (sequence)
* No duplicate serial per cross
* Form ready for next runner after add

**Tasks:**

* Runner entry form with serial lookup and time parsing
* Duplicate check before save

### Story 8.3: Update/delete cross runner [3 points]

**As** PTI
**I want** to modify or delete a runner result

**Acceptance criteria:**

* Click row → form pre-fills
* Modify running time and update
* "Delete" removes selected runner
* Grid refreshes after change

**Tasks:**

* Row selection triggers form fill
* Backend update and delete

### Story 8.4: Cross planning list view [2 points]

**As** PTI or admin
**I want** a list of all cross sessions

**Acceptance criteria:**

* Grid with all sessions
* Filterable and refreshable

**Tasks:**

* Filterable cross session grid

### Story 8.5: Cross statistics [3 points]

**As** PTI or APTI
**I want** to see performance statistics for crosses
**So that** I have an overview of unit performance

**Acceptance criteria:**

* Two grids: Top 10 all-time (5km), Top 10 all-time (10km)
* Rankings based on fastest times
* Refresh button to reload

**Tasks:**

* Top 10 rankings query per distance

---

## Epic 9: BEMIL Personnel Lookup (5 points)

**Epic total:** 5 points
**Estimated:** 1 sprint

| #   | Story                              | Points | Priority    |
| --- | ---------------------------------- | ------ | ----------- |
| 9.1 | Lookup serviceman by serial number | 3      | Must Have   |
| 9.2 | Browse all servicemen via modal    | 2      | Should Have |

### Story 9.1: Lookup serviceman by serial number [3 points]

**As** the system (used by PTI on all test input pages)
**I want** to retrieve serviceman data from BEMIL
**So that** test results are linked to the correct person

**Acceptance criteria:**

* Input: serial number
* Returns: rank, first name, last name, gender, birthdate, age, unit
* If not found: "Not found" message; dependent inputs remain disabled
* Display format: "Rank SerialNr FirstName LastName Gender Age years old"
* Used on: PHEF, Combat, Swimming, Functional, March, Cross pages

**Tasks:**

* BEMIL lookup by serial number
* Consistent display format across all test pages

### Story 9.2: Browse all servicemen via modal [2 points]

**As** PTI
**I want** to browse all servicemen in a modal and select one
**So that** I can find a serial number without typing it manually

**Acceptance criteria:**

* "Search own Unit" icon button opens modal
* Modal contains filterable grid with columns: serial number, first name, last name, gender
* Clicking a row fills the serial number field and closes modal
* Available on: PHEF, Combat, Swimming, Functional, March, Cross, Individual Test History pages

**Tasks:**

* Browse modal with filterable servicemen grid
* Row selection fills serial number field

---

## Epic 10: Individual Test History (15 points)

**Epic total:** 15 points
**Estimated:** 2–3 sprints

| #   | Story                              | Points | Priority    |
| --- | ---------------------------------- | ------ | ----------- |
| 10.1 | Search individual by serial number | 3      | Must Have   |
| 10.2 | Display complete test history      | 5      | Must Have   |
| 10.3 | Generate individual PDF report     | 5      | Should Have |
| 10.4 | Download PDF report                | 2      | Should Have |

### Story 10.1: Search individual by serial number [3 points]

**As** PTI, APTI, admin, or GUEST
**I want** to search for an individual by serial number
**So that** I can access their complete test history

**Acceptance criteria:**

* Serial number text input
* "Confirm Servicemen" button triggers BEMIL lookup
* "Search own Unit" modal available for browsing
* If found: serviceman info displayed (rank, name, serial number, unit)
* If not found: "Not found" message; test grid stays empty
* "Refresh" button reloads test data for current serial

**Tasks:**

* Serial number lookup against BEMIL
* Browse modal for serviceman selection

### Story 10.2: Display complete test history [5 points]

**As** PTI, APTI, admin, or GUEST
**I want** to view all tests for an individual
**So that** I can assess their performance history

**Acceptance criteria:**

* Grid shows all test results across all types (PHEF, Combat, Swimming, Functional, March)
* Columns: Date, Type, Details, Scores, Total, Result
* Tests sorted by date (newest first)
* Record count shown in status ("Loaded N records")
* Empty grid if no results found

**Tasks:**

* Aggregation of all test types into a single grid
* Sort by date descending

### Story 10.3: Generate individual PDF report [5 points]

**As** PTI, APTI, or admin
**I want** to generate a PDF report of test history
**So that** I can save, share, or print the assessment record

**Acceptance criteria:**

* "Generate Full Report" button triggers PDF generation
* Notification: "Report generated" on success
* Error message if generation fails or no serial entered
* PDF includes all test history data for the serviceman
* Download button appears after generation

**Tasks:**

* Async PDF generation for individual serviceman
* Download button shown conditionally after generation

### Story 10.4: Download PDF report [2 points]

**As** PTI, APTI, or admin
**I want** to download the generated PDF
**So that** I can store or share it

**Acceptance criteria:**

* "Download PDF" button appears only after successful generation
* Filename: "Report_{serial_number}.pdf"
* Button disappears / report resets after use

**Tasks:**

* File download handler
* Conditional display of download button

---

## Epic 11: Unit Status & Dashboard (12 points)

**Epic total:** 12 points
**Estimated:** 2 sprints

| #   | Story                             | Points | Priority    |
| --- | --------------------------------- | ------ | ----------- |
| 11.1 | View unit status grid             | 5      | Must Have   |
| 11.2 | View individual history via modal | 2      | Should Have |
| 11.3 | Unit dashboard with statistics    | 3      | Should Have |
| 11.4 | PHEF not-done list                | 2      | Should Have |

### Story 11.1: View unit status grid [5 points]

**As** PTI, APTI, admin, or GUEST
**I want** to see the fitness test status of all servicemen in my unit
**So that** I can assess overall unit readiness

**Acceptance criteria:**

* Grid with all servicemen in own unit
* Columns: Serial number, Rank, Name, Gender, Birthdate, PHEF status, Combat status, Swimming status
* Status color-coded (passed/failed/not done)
* Filterable columns
* "Refresh" button reloads data
* "Pdf Status Unit" button generates a unit status PDF
* Download button appears after PDF generation

**Tasks:**

* Unit servicemen grid with color-coded status columns
* PDF generation for unit status report

### Story 11.2: View individual test history via modal [2 points]

**As** PTI, APTI, admin, or GUEST
**I want** to click on a serviceman row to see their test details
**So that** I can drill into individual performance

**Acceptance criteria:**

* Click row in unit status grid → modal opens
* Modal shows grid of all tests for that serviceman
* Columns: Test Type, Session, Status
* "Close" button or click outside to dismiss

**Tasks:**

* Row selection opens detail modal
* Test history grid inside modal

### Story 11.3: Unit dashboard with statistics [3 points]

**As** PTI or APTI
**I want** a dashboard summary of unit fitness statistics
**So that** I have high-level insights per test type

**Acceptance criteria:**

* Summary cards per test type (total tested, GO/NO-GO count, pass rate)
* Charts for pass rates
* Current calendar year scope
* Refresh button reloads all statistics

**Tasks:**

* Summary cards per test type
* Chart generation for pass rates

### Story 11.4: PHEF not-done list [2 points]

**As** PTI or APTI
**I want** to see which servicemen have NOT completed PHEF this year
**So that** I can follow up with them

**Acceptance criteria:**

* Tab "PHEF Not done" under Psychical Tests menu
* Header shows current year and unit name
* Grid with all servicemen missing a PHEF result for current year
* Filterable columns
* Refresh button

**Tasks:**

* Query servicemen without a PHEF result in the current year
* Filterable grid display

---

## Epic 12: Calendar Events (5 points)

**Epic total:** 5 points
**Estimated:** 1 sprint

| #   | Story                            | Points | Priority    |
| --- | -------------------------------- | ------ | ----------- |
| 12.1 | View personal test calendar     | 3      | Should Have |
| 12.2 | View all test sessions calendar | 2      | Could Have  |

### Story 12.1: View personal test calendar [3 points]

**As** PTI or APTI
**I want** to see my scheduled test sessions in a calendar
**So that** I have a clear temporal overview

**Acceptance criteria:**

* Calendar opens as a full-page panel via "Personal Calendar" button in the top navigation bar
* Weekly time-grid view
* Shows sessions where PTI serial matches logged-in user
* Events color-coded by test type
* Click event → event turns red (highlight)
* Calendar is read-only (no create from calendar)
* "Close" button returns to the main navigation

**Tasks:**

* Personal calendar view filtered by logged-in user serial
* Global "Personal Calendar" button in navbar

### Story 12.2: View all test sessions calendar [2 points]

**As** admin
**I want** to see all test sessions across all units in the calendar
**So that** I have a complete scheduling overview

**Acceptance criteria:**

* "Open Calendar" button in top navigation bar opens a full-page calendar panel
* All sessions visible regardless of PTI
* Same calendar layout as personal view
* "Close" button returns to main navigation
* Personal and all-sessions calendars are mutually exclusive (opening one closes the other)

**Tasks:**

* All-sessions calendar view without PTI filter
* Mutual exclusion with personal calendar panel

---

## Epic 13: Fitness Room Reservation (8 points)

**Epic total:** 8 points
**Estimated:** 1–2 sprints

| #   | Story                                   | Points | Priority    |
| --- | --------------------------------------- | ------ | ----------- |
| 13.1 | Create room reservation                | 5      | Should Have |
| 13.2 | View reservations (weekly/monthly/list) | 2      | Should Have |
| 13.3 | Delete reservation                     | 1      | Should Have |

### Story 13.1: Create room reservation [5 points]

**As** PTI or admin
**I want** to reserve a fitness room for a training session
**So that** resources are properly managed

**Acceptance criteria:**

* Form: room (dropdown by name/color/capacity/location), PTI serial, activity description, date, start time, end time
* Room overlap validation: no double booking for same room/time
* "Reserve" button creates reservation
* Reservation appears immediately in list/calendar view
* Error message on overlap conflict
* Email notification sent to PTI on successful reservation (if mail configured)

**Tasks:**

* Room reservation form with overlap detection
* Email notification on successful save

### Story 13.2: View reservations (weekly/monthly/list) [2 points]

**As** PTI or admin
**I want** to see all reservations in different views
**So that** I can see room availability at a glance

**Acceptance criteria:**

* Three views: Weekly calendar, Monthly calendar, List view
* Weekly: time-grid per day showing room reservations with color
* Monthly: day-level overview
* List: filterable grid with all reservations
* Each view shows: room, PTI, activity, date/time

**Tasks:**

* Weekly and monthly calendar views
* Filterable list view

### Story 13.3: Delete reservation [1 point]

**As** PTI or admin
**I want** to cancel a room reservation
**So that** the room becomes available again

**Acceptance criteria:**

* Delete button available per reservation in list view
* Reservation removed from all views immediately

**Tasks:**

* Backend deletion with immediate grid/calendar refresh

---

## Epic 14: Audit Logs (5 points)

**Epic total:** 5 points
**Estimated:** 1 sprint

| #   | Story             | Points | Priority    |
| --- | ----------------- | ------ | ----------- |
| 14.1 | View audit log   | 3      | Must Have   |
| 14.2 | Filter audit log | 2      | Should Have |

### Story 14.1: View audit log [3 points]

**As** admin
**I want** to view all system audit log events
**So that** compliance is guaranteed

**Acceptance criteria:**

* Tab "Audit Logs" visible to admin only
* Grid with all logged events
* Columns: timestamp, event type, actor, target, details
* Logs are read-only (no edit/delete from UI)
* Refresh button reloads data

**Tasks:**

* Read-only audit log grid

### Story 14.2: Filter audit log [2 points]

**As** admin
**I want** to filter and search audit log entries
**So that** I can investigate specific events

**Acceptance criteria:**

* Column filters on the grid
* Filter by event type, actor, date range
* Results update on filter change

**Tasks:**

* Filterable columns on audit log grid

---

## Epic 15: Welcome Dashboard (5 points)

**Epic total:** 5 points
**Estimated:** 1 sprint

| #   | Story                                | Points | Priority    |
| --- | ------------------------------------ | ------ | ----------- |
| 15.1 | Welcome page with role-specific info | 3     | Must Have   |
| 15.2 | Upcoming sessions for PTI/APTI       | 2     | Should Have |

### Story 15.1: Welcome page with role-specific info [3 points]

**As** any authenticated user
**I want** to see a welcome page with my user and role information
**So that** I know I'm logged in correctly

**Acceptance criteria:**

* Welcome message: "Welcome back, {username}!"
* Logged-in role and email displayed
* Application version shown
* WarriorFit logo image displayed
* Refresh button to reload

**Tasks:**

* Welcome page with dynamic user info from session

### Story 15.2: Upcoming sessions for PTI/APTI [2 points]

**As** PTI or APTI
**I want** to see my upcoming test sessions on the welcome page
**So that** I always know what's planned

**Acceptance criteria:**

* Section visible only when role is PTI or APTI
* Grid: "Upcoming Test Sessions"
* Filtered by logged-in user's serial number
* Refreshable

**Tasks:**

* Upcoming sessions query filtered by user serial
* Role-based conditional display

---

## Epic 16: Application Settings (8 points)

**Epic total:** 8 points
**Estimated:** 1–2 sprints

| #   | Story                           | Points | Priority    |
| --- | ------------------------------- | ------ | ----------- |
| 16.1 | Configure application settings | 3      | Must Have   |
| 16.2 | Configure mail server           | 3      | Should Have |
| 16.3 | Configure HR integration        | 2      | Should Have |

### Story 16.1: Configure application settings [3 points]

**As** admin
**I want** to configure database connection and application paths
**So that** the application connects to the correct infrastructure

**Acceptance criteria:**

* Settings page accessible via Admin menu (admin only)
* Fields: DB host, DB port, DB name, DB username, DB password (masked)
* Field: PDF export path
* Field: Own unit name
* "Save All Configuration" button persists all settings
* Success notification: "Settings saved."
* Error notification on failure
* Form pre-loads current values on page load

**Tasks:**

* Settings form with pre-load of current configuration
* Save and persist all settings

### Story 16.2: Configure mail server [3 points]

**As** admin
**I want** to configure SMTP email settings
**So that** email notifications are sent correctly

**Acceptance criteria:**

* Fields: SMTP host, SMTP port, username, password (masked), sender email
* Checkboxes: Use SSL, Use TLS
* Saved together with other settings via "Save All Configuration"
* Mail settings used for session, march, and reservation notifications

**Tasks:**

* Mail configuration section in settings form

### Story 16.3: Configure HR integration [2 points]

**As** admin
**I want** to configure the HR (BEMIL) API connection
**So that** serviceman lookups work correctly

**Acceptance criteria:**

* Fields: HR URL, HR API key
* Saved together with other settings
* Used for all personnel lookups

**Tasks:**

* HR URL and API key fields in settings form

---

## Epic 17: Application Status Monitoring (5 points)

**Epic total:** 5 points
**Estimated:** 1 sprint

| #   | Story                         | Points | Priority    |
| --- | ----------------------------- | ------ | ----------- |
| 17.1 | View system health dashboard | 3      | Should Have |
| 17.2 | View live application log    | 2      | Should Have |

### Story 17.1: View system health dashboard [3 points]

**As** admin
**I want** to see the health status of all application dependencies
**So that** I can quickly diagnose connectivity or service issues

**Acceptance criteria:**

* "Status Application" page accessible via Admin menu (admin only)
* Status cards for: Database, HR Service, Mail Server, Server
* Each card shows connection status (up/down + details)
* Page refreshes status on navigation activation

**Tasks:**

* Health check per dependency displayed as status cards

### Story 17.2: View live application log [2 points]

**As** admin
**I want** to see the live application log in the browser
**So that** I can monitor errors and events without server access

**Acceptance criteria:**

* Scrollable log output panel on the Status Application page
* Log content updates automatically every 2 seconds when the file changes
* Maximum visible height with vertical scroll
* Shows recent lines of the application log file

**Tasks:**

* Polled log file reader with automatic refresh

---

## Epic 18: Reports & Export (8 points)

**Epic total:** 8 points
**Estimated:** 1–2 sprints

| #   | Story                         | Points | Priority    |
| --- | ----------------------------- | ------ | ----------- |
| 18.1 | Generate bulk fitness report | 5      | Should Have |
| 18.2 | Select export format         | 1      | Should Have |
| 18.3 | Download generated reports   | 2      | Should Have |

### Story 18.1: Generate bulk fitness report [5 points]

**As** PTI, APTI, or admin
**I want** to generate a fitness report for a group of servicemen
**So that** I can review results in bulk

**Acceptance criteria:**

* Reports page accessible from root navigation
* Filter options: Own Unit (checkbox), This Year (checkbox), Test Type (all / PHEF / Functional / Combat / Swimming)
* Custom report title field
* "Generate Report" button triggers async generation
* Status feedback shown (info / success / warning / error)
* Generated file names listed after generation

**Tasks:**

* Report generation with filter options
* Async generation with status feedback

### Story 18.2: Select export format [1 point]

**As** PTI, APTI, or admin
**I want** to choose the export format before generating a report
**So that** I get the output in the format I need

**Acceptance criteria:**

* Format dropdown: PDF, CSV, Both (PDF & CSV)
* Selection applied at generation time
* Both formats included in download if "Both" is selected

**Tasks:**

* Format selector applied to report generation

### Story 18.3: Download generated reports [2 points]

**As** PTI, APTI, or admin
**I want** to download the generated report files
**So that** I can store or share them

**Acceptance criteria:**

* "Download" button downloads all generated files as a ZIP archive
* ZIP filename: "reports.zip"
* Files in ZIP use their original filenames
* Button available as soon as a report is generated

**Tasks:**

* ZIP archive packaging all generated files
* File download handler

---

## Epic 19: Security & Authentication (7 points)

**Epic total:** 7 points
**Estimated:** 1–2 sprints

| #   | Story                        | Points | Priority    |
| --- | ---------------------------- | ------ | ----------- |
| 19.1 | Login with username/password | 2     | Must Have   |
| 19.2 | Rate limiting on login       | 2     | Must Have   |
| 19.3 | Auto-logout on inactivity    | 2     | Should Have |
| 19.4 | Role-based page access       | 1     | Must Have   |

### Story 19.1: Login with username/password [2 points]

**As** any user
**I want** to authenticate with my credentials
**So that** only authorized staff can access the system

**Acceptance criteria:**

* Login modal shown on application start (production mode)
* Fields: username, password
* "Login" button triggers authentication
* Successful login: modal closes, role-appropriate navigation renders
* Failed login: error message shown inline (red)
* Audit log records login event
* Disabled accounts receive "Account disabled" message

**Tasks:**

* Login modal with credential validation
* Role-appropriate navigation after successful login
* Audit log on login

### Story 19.2: Rate limiting on login [2 points]

**As** the system
**I want** to lock accounts after repeated failed login attempts
**So that** brute-force attacks are prevented

**Acceptance criteria:**

* Account locked after N consecutive failed attempts
* Locked account shows remaining lock time in minutes
* Successful login resets failure counter
* Remaining attempts shown after each failure

**Tasks:**

* Per-username attempt tracking
* Lock and unlock logic based on failure threshold

### Story 19.3: Auto-logout on inactivity [2 points]

**As** the system
**I want** to automatically log out users after 10 minutes of inactivity
**So that** unattended sessions are secured

**Acceptance criteria:**

* Activity tracked via browser events: click, keydown, mousemove, scroll, touch
* Heartbeat ping every 30 seconds
* Session cleared and page reloaded after 10 minutes of inactivity
* Notification: "You were logged out due to 10 minutes of inactivity."

**Tasks:**

* Client-side activity tracking sent to server
* Inactivity timer checked periodically server-side

### Story 19.4: Role-based page access [1 point]

**As** the system
**I want** to show only pages appropriate for the logged-in role
**So that** users cannot access unauthorized functionality

**Acceptance criteria:**

* Navigation dynamically built based on logged-in role
* admin: all pages
* PTI/APTI: all except Admin menu pages
* GUEST: Status Unit and Individual pages only
* PLANNER: Sessions page only
* Pages not allowed for the current role are not rendered

**Tasks:**

* Per-page role whitelist
* Navigation built from role-filtered page list
