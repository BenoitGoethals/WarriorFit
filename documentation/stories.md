# User Stories – Overview per Epic

User stories are used instead of Use Cases for more flexibility in agile development.

### Total Overview

* **Total epics:** 9
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
| 1.5 | Authorization control for user management | 3      | Must Have   |
| 1.6 | User list with search                     | 2      | Should Have |

### Story 1.1: Create new user [5 points]

**As** admin
**I want** to create a new user with username, email, password, role, and serial number
**So that** staff members can access the system

**Acceptance criteria:**

* Form fields: username, email, password, role (dropdown), serial_number
* Username must be unique (3–30 characters, a-z, 0–9, ., _, -)
* Email must be valid and unique
* Password minimum 12 characters with complexity check
* Password hashed using Argon2id
* Serial_number must be unique
* Audit log records creation (who, what, when)
* Success response: 201 Created with user_id
* UI shows confirmation

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
* Password reset option (generates token)
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
* Generates secure reset token (valid 24h)
* Sends email to user with reset link
* Token single-use only
* Audit logs reset action
* Invalidate old token on new request

**Tasks:**

* Reset token generation
* POST /api/users/:id/reset-password endpoint
* Email template
* Token validation endpoint
* Tests

### Story 1.5: Authorization control for user management [3 points]

**As** system
**I want** only admins to manage users
**So that** security is ensured

**Acceptance criteria:**

* Only role “admin” may create/edit users
* HTTP 403 Forbidden when lacking permissions
* Frontend hides admin features for non-admins
* Backend always validates authorization
* JWT contains role claim
* Rate limiting on user endpoints

**Tasks:**

* Authorization middleware
* Role-based access control (RBAC)
* Frontend route guards
* Tests for different roles

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

* Dropdown with PHEF sessions (PLANNED or ACTIVE)
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
* Plausibility check (run < 30min, bridge < 10min)
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

* POST /api/test-results/phef with all fields
* Transactional saving
* Audit log
* Success: 201 with result_id
* Async tasks:

  * Email soldier (with PDF)
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
| 5.3 | Mark safety incident       | 1      | Should Have |

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

### Story 5.3: Mark safety incident [1 point]

**As** PTI
**I want** to mark a safety incident
**So that** it is tracked and followed up

**Acceptance criteria:**

* Checkbox “Safety incident”
* When checked → remarks required
* Result status becomes “ON HOLD”
* Notification to medical and unit commander
* Cannot be published until validated

**Tasks:**

* Safety checkbox
* Notification service
* Status workflow
* Tests

---

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

* POST /api/test-results/functional
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
**So that** I can compare performance

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

---

📌 **Indien je dit ook in PDF, Word, Excel of via canvas wilt, zeg het gerust!**
