# User Stories – Overview per Epic

User stories are used instead of Use Cases for more flexibility in agile development.
The points are just for planning and prioritization.

### Total Overview

* **Total epics:** 13
* **Total stories:** 48
* **Total story points:** 150

### Story Point Legend

* 1 point = 2–4 hours
* 2 points = 4–8 hours
* 3 points = 1–2 days
* 5 points = 2–3 days
* 8 points = 3–5 days


## Epic 1: User Management (20 points)

**Epic total:** 20 points
**Estimated:** 4–5 sprints (2-week sprints)

| #   | Story                                     | Points | Priority    |
| --- | ----------------------------------------- | ------ | ----------- |
| 1.1 | Create new user                           | 5      | Must Have   |
| 1.2 | Error handling for user creation          | 3      | Must Have   |
| 1.3 | Edit user                                 | 5      | Must Have   |
| 1.4 | Password reset by admin                   | 2      | Should Have |
| 1.6 | User list with search                     | 2      | Should Have |

### Story 1.1: Create new user [5 points]

**As** admin
**I want** to create a new user with username, email, password, role, and serial number
**So that** staff members can access the system

**Acceptance criteria:**

* Form fields: username, email, password, role (dropdown), serial_number
* Username must be unique (3–30 characters, a-z, 0–9, ., _, -)
* Email must be valid and unique
* Password minimum 12 characters with complexity check (TBD)
* Serial_number must be unique
* Audit log records creation (who, what, when)
* Success response: 201 Created with user_id


**Tasks:**

* Frontend form with validation
* Backend POST /api/users endpoint
* Implement password hashing
* Audit logging service
* Unit + integration tests

### Story 1.2: Error handling for user creation [3 points]

**As** admin
**I want** clear error messages when something fails
**So that** I know what to fix

**Acceptance criteria:**

* Username conflict: "USERNAME_TAKEN" with suggestions (username1, username_01)
* Email conflict: "EMAIL_TAKEN"
* Serial_number conflict: error + admin override option
* Weak password: specific feedback (min length, complexity)
* Inline validation while typing (debounced)
* Server errors: user-friendly message with error-id

**Tasks:**

* Error handling in frontend
* Backend error responses
* Validation messages EN
* Tests for all error scenarios

### Story 1.3: Edit user [5 points]

**As** admin
**I want** to select and update an existing user
**So that** data stays up-to-date

**Acceptance criteria:**

* Select user from list (with search/filter)
* Edit form shows current values
* Editable: email, role, serial_number, status, remarks
* Same validation as creation (unique constraints)
* Audit log records all changes
* Concurrency handling (version conflict message)
* Success: “Changes saved” toast

**Tasks:**

* User list component
* Pre-filled edit form
* PUT /api/users/:id endpoint
* Implement optimistic locking
* Tests

### Story 1.4: Password reset by admin [2 points]

**As** admin
**I want** to reset a user password
**So that** users can log in again when they forget it

**Acceptance criteria:**

* “Reset password” button in edit screen
* Audit logs reset action

**Tasks:**

* Reset token generation
* POST /api/users/:id/reset-password endpoint
* Email template
* Token validation endpoint
* Tests



### Story 1.6: User list with search [2 points]

**As** admin
**I want** an overview of all users and a search function
**So that** I can quickly find a specific user

**Acceptance criteria:**

* Table columns: username, email, role, serial_number, status
* Search on username, email, serial_number
* Filter on role and status
* Sortable columns
* Pagination (25 per page)
* “Edit” action per row
* Loads within 2 seconds

**Tasks:**

* GET /api/users with query params
* Data table component
* Implement search/filter
* Tests

---

## Epic 2: Test Session Planning (17 points)

**Epic total:** 17 points
**Estimated:** 3–4 sprints

| #   | Story                   | Points | Priority    |
| --- | ----------------------- | ------ | ----------- |
| 2.1 | Create new test session | 5      | Must Have   |
| 2.2 | Update session          | 3      | Should Have |
| 2.3 | Delete session          | 2      | Should Have |
| 2.4 | View calendar           | 5      | Should Have |
| 2.5 | View session list       | 2      | Must Have   |

### Story 2.1: Create new test session [5 points]

**As** planner or PTI
**I want** to create a new test session
**So that** tests can be scheduled

**Acceptance criteria:**

* Form: test_type, date, time, responsible_pti, remarks
* Test types: PHEF, Combat, Functional, Swimming
* Date cannot be in the past
* Responsible PTI dropdown loads active PTIs
* Unique constraint: test_type + date (conflict check)
* Status on creation: "PLANNED"
* Audit log records creation
* Email to responsible PTI with details
* Success: confirmation with session_id

**Tasks:**

* Session form component
* POST /api/sessions endpoint
* PTI dropdown API
* Duplicate check query
* Email notification service
* Tests

### Story 2.2: Update session [3 points]

**As** planner or PTI
**I want** to modify a test session
**So that** planning can be adjusted

**Acceptance criteria:**

* Select session from list
* Editable: test_type, date, time, responsible_pti, remarks
* Date cannot be in the past
* Conflict check (excluding current session)
* Audit log storing old/new values
* Optional: email new PTI if changed
* Success: “Session updated”

**Tasks:**

* Edit form
* PUT /api/sessions/:id endpoint
* Conflict detection
* Tests

### Story 2.3: Delete session [2 points]

**As** planner or admin
**I want** to cancel a test session
**So that** incorrect planning is removed

**Acceptance criteria:**

* “Delete” button with confirmation dialog
* Only sessions without results can be deleted
* Sessions with results → status “CANCELLED”
* Audit log records deletion/cancellation
* Email to responsible PTI
* Success message

**Tasks:**

* Delete/cancel logic
* DELETE /api/sessions/:id
* Results check query
* Tests

### Story 2.4: View calendar [5 points]

**As** PTI, APTI, or admin
**I want** to see all test sessions in a calendar
**So that** I have a clear overview

**Acceptance criteria:**

* Month/week/day views
* Session items displayed on date/time
* Colors by test type
* Click session → details popup
* PTI/APTI see only their unit
* Admin sees everything
* Filter by test type
* Loads < 2 seconds
* Responsive design

**Tasks:**

* Calendar component
* GET /api/sessions with filters
* Authorization scope filtering
* Responsive styling
* Tests

### Story 2.5: View session list [2 points]

**As** PTI or planner
**I want** to see a list of test sessions
**So that** I can review upcoming and recent tests

**Acceptance criteria:**

* Columns: test_type, date, time, PTI, status
* Filter on test type, status, date range
* Sorting by date
* Actions: Edit, Enter Results
* Pagination
* Default: next 30 days

**Tasks:**

* Session list component
* Query filters
* Action buttons
* Tests

---

## Epic 3: PHEF Test Input (18 points)

**Epic total:** 18 points
**Estimated:** 3–4 sprints

| #   | Story                   | Points | Priority    |
| --- | ----------------------- | ------ | ----------- |
| 3.1 | Select PHEF session     | 2      | Must Have   |
| 3.2 | Lookup soldier via HRM  | 3      | Must Have   |
| 3.3 | Enter PHEF measurements | 5      | Must Have   |
| 3.4 | Save PHEF result        | 5      | Must Have   |
| 3.5 | PHEF result list        | 3      | Should Have |

### Story 3.1: Select PHEF session [2 points]

**As** PTI
**I want** to select a PHEF session
**So that** results link to the correct session

**Acceptance criteria:**

* Dropdown with PHEF sessions (PLANNED or ACTIVE) (TBD: include inactive)
* Show: date, time, location
* Filter by date (today/week/month)
* Session stays selected for multiple entries
* “New session” button if none exists
* Selected session info visible at top

**Tasks:**

* Session selector component
* GET /api/sessions?type=PHEF
* Session state management
* Tests

### Story 3.2: Lookup soldier via HRM [3 points]

**As** PTI
**I want** to validate soldier via HRM
**So that** data is correct

**Acceptance criteria:**

* Input for serial number
* API call GET /hrm/soldier/{id}
* If found: show name, gender, birthdate, age, email (read-only)
* If not found: “Soldier not found”
* Retry option for network errors
* Timeout after 5s
* Loading indicator

**Tasks:**

* HRM API client
* Lookup component
* Error handling
* Retry logic
* Tests + mocks

### Story 3.3: Enter PHEF measurements [5 points]

**As** PTI
**I want** to enter PHEF values
**So that** test results are calculated

**Acceptance criteria:**

* Fields:
  * 2400m run: time mm:ss
  * Side-bridge left/right: mm:ss
* Format validation (00:00 to 99:59)
* Plausibility check (run < 30min, bridge < 10min) (TBD)
* Automatic scoring (age + gender corrected)
* Show score and GO/NO-GO
* Reference score table visible
* Optional remarks
* “Reset” + “Save” buttons

**Tasks:**

* Input form
* Time input component
* Scoring service (PHEF rules)
* Validation logic
* Tests

### Story 3.4: Save PHEF result [5 points]

**As** PTI
**I want** to save PHEF result
**So that** it is registered

**Acceptance criteria:**


* Transactional saving
* Audit log
* Success: 201 with result_id
* Async tasks:
  * Email soldier 
  * POST result to HRM
* UI: “Result saved” + “Next soldier”
* On error: clear message, data remains

**Tasks:**

* Endpoint
* DB transaction
* Background jobs
* Email service + PDF
* HRM POST
* Retry logic
* Tests

### Story 3.5: PHEF result list [3 points]

**As** PTI
**I want** to see PHEF results
**So that** I know who has been tested

**Acceptance criteria:**

* List: name, serial, run_time, bridges, score, status
* Filter on status
* Search on name/serial
* Edit option
* Export to Excel
* Show total GO/NO-GO

**Tasks:**

* Results component
* GET endpoint
* Edit function
* Export service
* Tests

---

## Epic 4: Combat Test Input (13 points)

**Epic total:** 13 points
**Estimated:** 2–3 sprints

| #   | Story                     | Points | Priority    |
| --- | ------------------------- | ------ | ----------- |
| 4.1 | Enter combat test results | 8      | Must Have   |
| 4.2 | Combat result list        | 3      | Should Have |
| 4.3 | Combat statistics         | 2      | Could Have  |

### Story 4.1: Enter combat test results [8 points]

**As** PTI
**I want** to enter combat test results (3 components)
**So that** performance is registered

**Acceptance criteria:**

* Session selection (same as PHEF)
* HRM lookup (same as PHEF)
* Inputs:
  * 16km speed march → GO/NO-GO + optional time hh:mm:ss
  * Obstacle course → GO/NO-GO + optional remarks
  * Rope course → GO/NO-GO + optional remarks
* Final result: GO only if all 3 components are GO
* Show result (green/red)
* General remarks
* Save to database
* Email to soldier
* POST to HRM
* Audit log

**Tasks:**

* Combat form
* GO/NO-GO toggle
* Optional time input
* Final result logic
* Endpoint
* Email + HRM integration
* Tests

### Story 4.2: Combat result list [3 points]

**As** PTI
**I want** to see combat results
**So that** I have an overview

**Acceptance criteria:**

* List: name, serial, each component result, final result
* Icons ✓/✗
* Filter on final result
* Search
* Export
* Edit

**Tasks:**

* List component
* GET endpoint
* Tests

### Story 4.3: Combat statistics [2 points]

**As** planner
**I want** combat statistics
**So that** I have performance overview

**Acceptance criteria:**

* Dashboard:

  * Total tested
  * % GO vs NO-GO
  * Component results
  * Average speed march time
* Filter on unit + date range
* Bar chart

**Tasks:**

* Stats query
* Dashboard component
* Chart (recharts)
* Tests

---

## Epic 5: Swimming Test Input (8 points)

**Epic total:** 8 points
**Estimated:** 1–2 sprints

| #   | Story                      | Points | Priority    |
| --- | -------------------------- | ------ | ----------- |
| 5.1 | Enter swimming test result | 5      | Should Have |
| 5.2 | Swimming result list       | 2      | Should Have |


### Story 5.1: Enter swimming test result [5 points]

**As** PTI
**I want** to enter swimming test results
**So that** the 100m combat-gear swim test is registered

**Acceptance criteria:**

* Swimming test session selection
* HRM lookup
* Result: GO / NO-GO
* GO = 100m completed per conditions
* NO-GO = not completed or disqualified
* Remarks (safety)
* Save to DB
* Email to soldier
* POST to HRM
* Audit log

**Tasks:**

* Swimming form
* POST endpoint
* Email + HRM integration
* Tests

### Story 5.2: Swimming result list [2 points]

**As** PTI
**I want** to view swimming results
**So that** I have oversight

**Acceptance criteria:**

* List: name, serial, result, remarks
* Filter
* Search
* Export
* Edit

**Tasks:**

* List component
* GET endpoint
* Tests


## Epic 6: Functional Test Input (15 points)

**Epic total:** 15 points
**Estimated:** 2–3 sprints

| #   | Story                              | Points | Priority    |
| --- | ---------------------------------- | ------ | ----------- |
| 6.1 | Enter functional test measurements | 5      | Must Have   |
| 6.2 | Determine GO/NO-GO                 | 3      | Must Have   |
| 6.3 | Save functional test results       | 5      | Must Have   |
| 6.4 | Functional results list            | 2      | Should Have |

### Story 6.1: Enter functional test measurements [5 points]

**As** PTI
**I want** to enter functional test data
**So that** performance is recorded

**Acceptance criteria:**

* Functional session selection
* HRM lookup
* Inputs (integer):

  * Pull-ups: 0–100
  * Push-ups (2 min): 0–200
  * Sit-ups (2 min): 0–200
* Plausibility checks
* Real-time calculation:

  * Points per component (age/gender table)
  * Percentage of max
  * Total points
* Show score reference table
* Remarks field

**Tasks:**

* Functional form
* Integer validation
* Scoring service
* Percentage calculation
* Tests

### Story 6.2: Determine GO/NO-GO [3 points]

**As** PTI
**I want** the system to determine GO/NO-GO
**So that** evaluation is objective

**Acceptance criteria:**

* **Rule:** minimum 50% per component
* Component = GO if ≥50%
* Final GO only if all 3 = GO
* Visual feedback:

  * Green/red per component
  * Big final result badge
* Highlight failures

**Tasks:**

* GO/NO-GO logic
* Visual component
* Configurable business rules
* Tests

### Story 6.3: Save functional results [5 points]

**As** PTI
**I want** to save the functional test
**So that** results are stored and shared

**Acceptance criteria:**
* Save counts, points, percentages, component GO/NO-GO, final result
* Transactional
* Audit log
* Email to soldier (detailed)
* POST to HRM
* Success message

**Tasks:**

* Endpoint
* Transaction
* Email template
* HRM POST
* Tests

### Story 6.4: Functional result list [2 points]

**As** PTI
**I want** to view functional test results
**So that** I can compare performance and have a record of all attempts

**Acceptance criteria:**

* List: name, serial, pull-ups, push-ups, sit-ups, total points, final result
* Color-coded components
* Sort on points
* Filter GO/NO-GO
* Export
* Edit

**Tasks:**

* Results list
* Color coding
* GET endpoint
* Tests

---

## Epic 7: Reporting (12 points)

**Epic total:** 12 points
**Estimated:** 2 sprints

| #   | Story                      | Points | Priority    |
| --- | -------------------------- | ------ | ----------- |
| 7.1 | PHEF Failed overview       | 5      | Should Have |
| 7.2 | Combat Failed overview     | 3      | Could Have  |
| 7.3 | Functional Failed overview | 3      | Could Have  |
| 7.4 | Dashboard per test type    | 1      | Should Have |

### Story 7.1: PHEF Failed overview [5 points]

**As** PTI or APTI
**I want** to see soldiers who failed PHEF this year
**So that** I can follow up

**Acceptance criteria:**

* Tab “PHEF Failed”
* Grid columns:

  * serial_number, name, rank, gender, age, unit, test_date, score, run_time, bridges
* Filters:

  * Unit scope (own unit for PTI/APTI, all for admin)
  * Current calendar year only
  * Only NO-GO
* Column filters
* Sort by date (newest first)
* Excel export
* Refresh button
* Load < 2 seconds

**Tasks:**

* Query with filters
* Data grid component
* Unit scope filtering
* Export
* Tests

### Story 7.2: Combat Failed overview [3 points]

**As** PTI
**I want** combat fails overview
**So that** I see failure reasons

**Acceptance criteria:**

* Same structure as PHEF failed
* Extra columns: each component result
* Highlight failed component
* Filter per component
* Export

**Tasks:**

* Combat failed query
* Grid reuse
* Tests

### Story 7.3: Functional Failed overview [3 points]

**As** PTI
**I want** functional fails overview
**So that** I can train more effectively

**Acceptance criteria:**

* Same structure as PHEF failed
* Columns: pull-ups, push-ups, sit-ups, percentages, total, component fails
* Filters
* Export

**Tasks:**

* Functional failed query
* Grid reuse
* Tests

### Story 7.4: Dashboard per test type [1 point]

**As** admin
**I want** summaries per test type
**So that** I have high-level insights

**Acceptance criteria:**

* Simple dashboard showing:

  * Total tested
  * GO/NO-GO ratio
  * Per test type
* Quick filters

**Tasks:**

* Summary queries
* Dashboard component
* Tests

# Epic 8: General Functionality (Total: 15 points)

## Story 8.1: HRM Integration - GET Military Personnel [5 points]

**As** a system  
**I want to** retrieve military data from HRM  
**So that** correct information is available

### Acceptance Criteria: (TBC)
- Implement GET /hrm/militair/{serial_number}
- Response: name, gender, date of birth, age, unit, email
- Authentication via API key or OAuth2
- Timeout: 5 seconds
- Retry: 2x on error
- Error handling: 404, 500, timeout
- Cache result (5 minutes)
- Logging of all calls

### Tasks:
- HRM API client class
- Authentication setup
- Retry logic (exponential backoff)
- Cache implementation (Redis or in-memory)
- Error handling
- Unit tests with mocks
- Integration tests with test HRM

---

## Story 8.2: HRM Integration - POST Test Result [5 points]

**As** a system  
**I want to** send test results to HRM  
**So that** central registration is up-to-date

### Acceptance Criteria:
- POST /hrm/test-result with JSON:
```json
{
  "serial_number": "...",
  "test_type": "PHEF|Combat|Functional|Swimming",
  "test_date": "ISO8601",
  "result": "GO|NO-GO",
  "score": 123,
  "details": {...}
}
```
- Idempotent (same result_id = no duplicate)
- Timeout: 10 seconds
- Retry: 3x with exponential backoff
- On persistent error: queue for later retry
- Success: 200/201 response
- Logging of all calls
- Background job (async)

### Tasks:
- HRM POST implementation
- Background job queue (BullMQ, RabbitMQ, or database queue)
- Retry worker
- Idempotency check
- Error queue for failed jobs
- Admin UI for failed jobs
- Tests

---

## Story 8.3: Email Service - Send Results [3 points]

**As** a system  
**I want to** email military personnel with test results  
**So that** they are informed

### Acceptance Criteria:
- Email templates per test type (HTML + plain text)
- Contains: name, test date, session, result (GO/NO-GO), scores/details
- Attachment: PDF with complete result (TBC)
- PDF generation with logo and styling
- From address: noreply@warriorfit.mil
- Retry: 3x on error
- Background job (async)
- Logging of sent emails
- Bounce handling

### Tasks:
- Email service (Nodemailer or SendGrid)
- HTML/text templates (Handlebars or EJS)
- PDF generation (PDFKit or Puppeteer)
- Background job queue
- Retry worker
- Tests with mock SMTP

---

## Story 8.4: Audit Logging Service [2 points]

**As** a system  
**I want to** log all actions  
**So that** compliance is guaranteed

### Acceptance Criteria:
- Log table: event_type, actor_id, target_id, timestamp, ip_address, request_id, changes (JSON)
- Events: user_create, user_update, session_create, session_update, result_create, result_update
- Middleware automatically logs all POST/PUT/DELETE requests
- Logs are immutable (no updates/deletes)
- Retention: 7 years
- Searchable interface for admins
- Export capability

### Tasks:
- Audit log database schema
- Logging middleware
- Helper functions for manual logs
- Admin search interface
- Tests

---

# Epic 9: Cross Session Management (18 points)

## Story 9.1: Create Cross Session [5 points]

**As** a planner or PTI  
**I want to** create a new cross session  
**So that** training sessions can be scheduled

### Acceptance Criteria:
- Form with fields: Date, Time, Distance, Executed (checkbox), Description
- Date cannot be in the past
- Time in format HH:MM (e.g., "09:30")
- Display: "Selected time: DD/MM/YYYY HH:MM"
- Distance required and numeric
- "Add" button creates new cross
- Cross appears immediately in table on the right
- Form clears after adding
- "Clear" button resets all fields

---

## Story 9.2: Edit Cross [5 points]

**As** a planner or PTI  
**I want to** modify an existing cross  
**So that** errors can be corrected

### Acceptance Criteria:
- Click on row in table to select
- Selected row is highlighted
- Form fields populate with selected values
- Modify values and click "Update"
- Table updates immediately with new values
- "Update" button only active when row is selected
- Executed checkbox can be toggled on/off

---

## Story 9.3: Delete Cross [3 points]

**As** a planner or PTI  
**I want to** delete a cross session  
**So that** incorrect planning can be removed

### Acceptance Criteria:
- Select one or multiple rows (checkboxes)
- "Delete Selected" button below table
- Confirmation dialog: "Are you sure you want to delete X cross(es)?"
- Selected row(s) disappear from table
- Button only active when at least 1 row is selected
- Form resets after delete

---

## Story 9.4: Cross List Filters & Sorting [3 points]

**As** a user  
**I want to** filter and sort the cross list  
**So that** I can quickly find specific crosses

### Acceptance Criteria:
- Sortable columns (click on header): ID, Start, Distance, Executed
- Filter on date range (from/to)
- Filter on Executed status (dropdown: All/True/False)
- Filter on Distance (min/max)
- Search bar: search in Description
- "Reset filters" button
- Pagination: 20 crosses per page
- Default sorting: Start date descending

---

## Story 9.5: Export Cross List [2 points]

**As** a planner  
**I want to** export the cross list to Excel  
**So that** I can create reports

### Acceptance Criteria:
- "Export to Excel" button above table
- Exports current filtered/sorted results
- Excel columns: ID, Start, Executed, Distance, Description
- Filename: "Crosses_YYYYMMDD.xlsx"

---

# Epic 10: Cross Runners Management (8 points)

## Story 10.1: Enter Cross Results [5 points]

**As** a PTI  
**I want to** enter running times of military personnel for a cross  
**So that** performances are recorded

### Acceptance Criteria:
- Select cross from dropdown (shows list of available crosses)
- "Select" button loads selected cross
- Enter Serial Number
- "Confirm Serial" button validates military personnel via HRM
- System retrieves: Runner Name, Gender, Age, Unit (read-only)
- Enter Running Time (format hh:mm:ss, e.g., "01:10:45")
- System automatically calculates Running seconds (e.g., 600 seconds for 10:00)
- "Add" button adds runner to table on the right
- Table shows: Order, ID, Serial, Running Time, Runner Name, Gender, Age, Running seconds, Unit
- Order is automatically assigned (sequence of addition)
- Form remains ready for next runner
- "Clear Form" button resets all fields except cross selection

### Validations:
- Cross must be selected
- Serial number must exist in HRM
- Running time required and correct format
- No duplicate serial numbers per cross

---

## Story 10.2: Update Cross Results [2 points]

**As** a PTI  
**I want to** modify or delete a runner result  
**So that** errors can be corrected

### Acceptance Criteria:
- Select row in runners table (click on row)
- Form populates with selected runner data
- Serial Number and runner info remain read-only (not editable)
- Modify Running Time
- "Update" button adjusts time in table
- Running seconds is recalculated
- "Delete Selected" button removes selected runner(s)
- Multi-select possible with checkboxes (Order column)
- Confirmation on delete: "Are you sure you want to delete X runner(s)?"
- Order numbers are recalculated after delete

---

## Story 10.3: Report Cross List [1 point]

**As** a PTI  
**I want to** generate a report of cross results  
**So that** I can share and archive results

### Acceptance Criteria:
- "Generate Report" button generates PDF or Excel report
- Report contains:
  - Cross name and date
  - Table with all runners (sorted by Order)
  - Columns: Order, Serial, Runner Name, Gender, Age, Running Time, Unit
- "Download" button (blue, prominent) downloads report
- Filename: "Cross_[CrossName]_[Date].pdf" or ".xlsx"
- Report only possible if cross is selected and has at least 1 runner

---


# Epic 11: March Registration (15 points)

## Story 11.1: Enter March [5 points]

**As** a PTI or APTI  
**I want to** register a march for military personnel  
**So that** march performances are tracked

### Acceptance Criteria:
- Form with fields:
  - Serial number (input, required)
  - "Confirm Serial" button validates via HRM
  - Name, gender, age, unit (read-only after validation)
  - Date (date picker, required)
  - Distance in km (dropdown or input: 20, 30, 40, 50, 100, 120)
  - Passed (checkbox, default unchecked)
  - Comments (optional)
- "Add" button adds march
- March appears in table on the right with: ID, Serial Number, Name, Date, KM, Passed, Unit
- Form clears after adding
- "Clear Form" button resets all fields

### Validations:
- Serial number must exist in HRM
- Date cannot be in the future
- Distance in km must be > 0
- No duplicate registration (same serial number + date + km)

---

## Story 11.2: Update March [3 points]

**As** a PTI or APTI  
**I want to** modify a march registration  
**So that** errors can be corrected

### Acceptance Criteria:
- Select row in table (click on row)
- Form populates with selected march data
- Serial number and military info remain read-only
- Editable: date, distance in km, passed status, comments
- "Update" button modifies march
- Table updates immediately with new values
- "Update" button only active when row is selected

---

## Story 11.3: Delete March [2 points]

**As** a PTI or admin  
**I want to** delete a march registration  
**So that** incorrect registrations can be removed

### Acceptance Criteria:
- Select one or multiple rows (checkboxes)
- "Delete Selected" button
- Confirmation dialog: "Are you sure you want to delete X march(es)?"
- Selected rows disappear
- Button only active when at least 1 row is selected

---

## Story 11.4: Unit March Overview (Current Year) [3 points]

**As** a PTI or APTI  
**I want to** see which military personnel from my unit have completed a march this year  
**So that** I have an overview of who still needs to march

### Acceptance Criteria:
- "Unit March Overview" tab in dashboard
- Filter: only own unit (PTI/APTI), all units (admin)
- Filter: only current calendar year
- Data grid with:
  - Serial number
  - Name
  - Rank
  - Unit  
  - Last march distance (km)
  - Last march status (Passed/Failed)
- Sortable on all columns
- Search by name or serial number
- Filter on "Has march" / "No march"
- Filter on passed/failed
- Export to Excel
- Click on row → show all marches for that person (Story 11.5)

---

## Story 11.5: Personal March Overview [2 points]

**As** a PTI or military personnel  
**I want to** view all marches for one person  
**So that** I can review history

### Acceptance Criteria:
- Input: serial number
- "Search" button retrieves all marches for that military personnel
- Military info at top: name, unit, total number of marches
- Table with all marches:
  - Date
  - Distance in km
  - Passed (✓/✗)
  - Comments
  - Registered by (PTI name)
- Sortable by date (newest first by default)
- Filter by year (dropdown: all years, 2025, 2024, ...)
- Filter on passed/failed
- Export to PDF "March_History_[Name].pdf"
- Chart: number of marches per year (bar chart)

## Epic 14: Individual Test History Management


| ID | User Story | Priority | Story Points |
|----|------------|----------|--------------|
|  14.1 | Search Individual by Serial Number | High | 3 | 
|  14.2 | Display Complete Test History | High | 5 |
|  14.3 | View Test Details and Scores | High | 3 |
|  14.4 | Generate Full Report | Medium | 5 |
|  14.5 | Download PDF Report | Medium | 2 |




## Epic Description
As a serviceman or administrator, I need to be able to view, search, and manage individual test history records so that I can track performance, identify patterns, and generate reports for military personnel assessments.

## Business Value
- Enables quick lookup of individual test performance across multiple assessment types
- Provides historical data for performance tracking and improvement analysis
- Supports compliance and reporting requirements for military training programs
- Facilitates data-driven decision making for personnel development

## Acceptance Criteria
- Users can search for individuals by serial number
- Complete test history is displayed with all relevant details
- Users can generate and download comprehensive PDF reports
- System accurately displays pass/fail status and scores
- Interface supports multiple test types (PHEF, Mars, Combat, Swimming)

---

## User Stories

### Story 14.1: Search Individual by Serial Number
**As a** serviceman/administrator  
**I want to** search for an individual using their serial number  
**So that** I can quickly access their complete test history

**Acceptance Criteria:**
- Input field accepts serial number format (e.g., BE-20250001)
- Search button triggers the lookup
- System validates serial number format
- Results display within 2 seconds
- Clear error message if serial number not found
- Search is case-insensitive

**Story Points:** 3

---

### Story 14.2: Display Complete Test History
**As a** serviceman/administrator  
**I want to** view a comprehensive list of all tests taken by an individual  
**So that** I can assess their overall performance and progress

**Acceptance Criteria:**
- Table displays: Date, Type, Details, Scores, Total, Result
- Tests are sorted by date (newest first)
- Pass/Fail status is clearly indicated with color coding (green/red)
- All test types are displayed (PHEF, Mars, Combat, Swimming)
- Pagination shows "Viewing rows X through Y of Z"
- Table is scrollable for large datasets

**Story Points:** 5

---

### Story 14.3: View Test Details and Scores
**As a** serviceman/administrator  
**I want to** see detailed breakdown of each test  
**So that** I can understand specific performance metrics

**Acceptance Criteria:**
- Details column shows specific test components (Run, SBR, SBL times)
- Scores column displays individual component scores
- Total score is calculated and displayed as X/100
- Missing scores are indicated with "-"
- Format is consistent across all test types
- Data is clearly readable and properly formatted

**Story Points:** 3

---

### Story 14.4: Generate Full Report
**As a** serviceman/administrator  
**I want to** generate a comprehensive PDF report of test history  
**So that** I can save, share, or print the complete assessment record

**Acceptance Criteria:**
- "Generate Full Report" button creates PDF
- Confirmation message displays when report is generated
- Report includes all visible test history data
- PDF is professionally formatted
- Report includes serviceman identification details
- Generation completes within 5 seconds

**Story Points:** 5

---

### Story 14.5: Download PDF Report
**As a** serviceman/administrator  
**I want to** download the generated PDF report  
**So that** I can store it locally or share it with others

**Acceptance Criteria:**
- "Download PDF" button is available after report generation
- Download initiates immediately upon click
- PDF filename includes serial number and date
- File downloads to default browser location
- User receives confirmation of successful download

**Story Points:** 2

---

### Story 14.6: View Serviceman Information
**As a** serviceman/administrator  
**I want to** see basic information about the individual  
**So that** I can confirm I'm viewing the correct person's records

**Acceptance Criteria:**
- Display shows: Name, Serial Number, Battalion, Unit Location
- Information is displayed in dedicated "Serviceman" section
- Data is clearly formatted and readable
- Information remains visible while scrolling test history
- All fields are populated from database

**Story Points:** 2

# Epic #15: Unit Status Overview & Quick Test Access

| ID | User Story | Priority | Story Points |
|----|------------|----------|--------------|
| Story 15.1 | View Unit Status Overview | High | 5 | 
| Story 15.3 | Search for Specific Servicemen | High | 3 | 


## Epic Description
As a unit commander or PTI, I need to view the current fitness test status of all servicemen in my unit and quickly access individual test histories so that I can monitor unit readiness, identify personnel needing attention, and ensure compliance with fitness requirements.

## Business Value
- Provides at-a-glance view of entire unit fitness status
- Enables rapid identification of personnel failing tests
- Supports unit readiness assessment and reporting
- Facilitates targeted intervention for struggling personnel
- Streamlines access to detailed individual test histories

## Acceptance Criteria
- Display all servicemen with their current test statuses
- Show status for all test types (PHEF, Combat, Swimming, March)
- Enable quick access to detailed test history via modal
- Support filtering and searching of personnel
- Visual indicators clearly distinguish passed/failed tests
- System refreshes data on demand

---

## User Stories

### Story 15.1: View Unit Status Overview
**As a** unit commander  
**I want to** see a complete list of all servicemen with their test statuses  
**So that** I can assess overall unit fitness readiness at a glance

**Acceptance Criteria:**
- Table displays all servicemen in the unit 
- Each row shows: Service #, Rank, Name, Gender, Birthdate, Para, Ops Test status
- Test statuses shown for: PHEF, Combat, Swimming, March
- Status indicators use color coding (green = passed, red = failed, red=Not done)
- Pagination shows "Viewing rows X through Y of Z"
- Data loads within 3 seconds

**Story Points:** 5

### Story 15.3: Search for Specific Servicemen
**As a** PTI
**I want to** search for servicemen by name, rank, or service number  
**So that** I can quickly locate specific individuals

**Acceptance Criteria:**
- Search fields available for: Service #, Rank, Last name, First name
- Search is case-insensitive
- Results filter as user types
- Multiple search fields can be used together
- Clear button resets search fields
- Search works with partial matches

**Story Points:** 3





