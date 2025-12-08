# Complete Test Plan - WarriorFit System

## Epic 1: User Management

### Story 1.1: Create New User [5 points]

**Functional Tests:**
- [ ] Verify form displays all required fields (username, email, password, role, serial_number)
- [ ] Test username validation (3-30 characters, a-z, 0-9, ., _, -)
- [ ] Test username uniqueness check
- [ ] Test email format validation
- [ ] Test email uniqueness check
- [ ] Test password minimum 12 characters
- [ ] Test password complexity requirements
- [ ] Test serial_number uniqueness
- [ ] Verify role dropdown displays available roles
- [ ] Test successful user creation returns 201 Created with user_id
- [ ] Verify audit log records creation (who, what, when)
- [ ] Test form clears after successful submission

**Security Tests:**
- [ ] Verify password is hashed in database
- [ ] Test SQL injection attempts in all fields
- [ ] Verify only authorized users can create accounts

**Performance Tests:**
- [ ] Test form submission response time < 2 seconds

---

### Story 1.2: Error Handling for User Creation [3 points]

**Functional Tests:**
- [ ] Test USERNAME_TAKEN error with username suggestions
- [ ] Test EMAIL_TAKEN error message
- [ ] Test serial_number conflict with admin override option
- [ ] Test weak password feedback (min length, complexity)
- [ ] Verify inline validation while typing (debounced)
- [ ] Test server error displays user-friendly message with error-id
- [ ] Test network timeout error handling
- [ ] Verify all error messages are clear and actionable

**UI/UX Tests:**
- [ ] Verify error messages display near relevant fields
- [ ] Test error message styling is consistent
- [ ] Verify inline validation doesn't trigger too frequently

---

### Story 1.3: Edit User [5 points]

**Functional Tests:**
- [ ] Test user selection from list
- [ ] Verify edit form pre-fills with current values
- [ ] Test editing email (with uniqueness validation)
- [ ] Test editing role
- [ ] Test editing serial_number (with uniqueness validation)
- [ ] Test editing status
- [ ] Test editing remarks
- [ ] Verify username is NOT editable
- [ ] Test audit log records all changes (old/new values)
- [ ] Test concurrency handling (version conflict message)
- [ ] Verify success toast "Changes saved" displays
- [ ] Test search/filter functionality in user list

**Edge Cases:**
- [ ] Test editing user while another admin edits same user
- [ ] Test form validation when changing to existing email
- [ ] Test canceling edit returns to list without changes

---

### Story 1.4: Password Reset by Admin [2 points]

**Functional Tests:**
- [ ] Verify "Reset password" button appears in edit screen
- [ ] Test reset token generation
- [ ] Test email sent to user with reset link
- [ ] Test reset token validation
- [ ] Test reset token expiration
- [ ] Verify audit log records reset action
- [ ] Test user can successfully reset password via link

**Security Tests:**
- [ ] Verify reset token is cryptographically secure
- [ ] Test expired token cannot be used
- [ ] Test token can only be used once

---

### Story 1.6: User List with Search [2 points]

**Functional Tests:**
- [ ] Verify table displays columns: username, email, role, serial_number, status
- [ ] Test search on username
- [ ] Test search on email
- [ ] Test search on serial_number
- [ ] Test filter by role
- [ ] Test filter by status
- [ ] Test sortable columns (ascending/descending)
- [ ] Test pagination (25 per page)
- [ ] Verify "Edit" action per row opens edit form
- [ ] Test combined search and filter

**Performance Tests:**
- [ ] Verify list loads within 2 seconds
- [ ] Test performance with 1000+ users

---

## Epic 2: Test Session Planning

### Story 2.1: Create New Test Session [5 points]

**Functional Tests:**
- [ ] Verify form displays all fields (test_type, date, time, responsible_pti, remarks)
- [ ] Test test_type dropdown shows: PHEF, Combat, Functional, Swimming
- [ ] Test date validation (cannot be in past)
- [ ] Test responsible PTI dropdown loads active PTIs only
- [ ] Test unique constraint check (test_type + date)
- [ ] Verify status set to "PLANNED" on creation
- [ ] Verify audit log records creation
- [ ] Test email sent to responsible PTI with session details
- [ ] Verify success confirmation displays with session_id
- [ ] Test time format validation (HH:MM)

**Edge Cases:**
- [ ] Test creating session for same type on same date (should fail)
- [ ] Test creating session with inactive PTI (should fail)
- [ ] Test creating multiple sessions on same date (different types)

---

### Story 2.2: Update Session [3 points]

**Functional Tests:**
- [ ] Test session selection from list
- [ ] Verify form pre-fills with current values
- [ ] Test editing test_type
- [ ] Test editing date (cannot be in past)
- [ ] Test editing time
- [ ] Test changing responsible_pti
- [ ] Test editing remarks
- [ ] Test conflict check excludes current session
- [ ] Verify audit log stores old/new values
- [ ] Test email sent to new PTI if changed
- [ ] Verify success message "Session updated"

**Edge Cases:**
- [ ] Test changing date to conflict with another session
- [ ] Test updating already started session

---

### Story 2.3: Delete Session [2 points]

**Functional Tests:**
- [ ] Verify "Delete" button displays
- [ ] Test confirmation dialog appears
- [ ] Test deleting session without results (hard delete)
- [ ] Test attempting to delete session with results (status → CANCELLED)
- [ ] Verify audit log records deletion/cancellation
- [ ] Test email sent to responsible PTI
- [ ] Verify success message displays
- [ ] Test deletion of multiple sessions

**Edge Cases:**
- [ ] Test canceling deletion in confirmation dialog
- [ ] Test deleting session with partial results

---

### Story 2.4: View Calendar [5 points]

**Functional Tests:**
- [ ] Test month view displays correctly
- [ ] Test week view displays correctly
- [ ] Test day view displays correctly
- [ ] Verify sessions display on correct date/time
- [ ] Test color coding by test type
- [ ] Test click session opens details popup
- [ ] Verify PTI sees only their unit sessions
- [ ] Verify APTI sees only their unit sessions
- [ ] Verify admin sees all sessions
- [ ] Test filter by test type
- [ ] Test navigation between months/weeks/days
- [ ] Test responsive design on mobile/tablet

**Performance Tests:**
- [ ] Verify calendar loads < 2 seconds
- [ ] Test performance with 100+ sessions in month

**UI/UX Tests:**
- [ ] Test calendar is visually clear and readable
- [ ] Verify color scheme is accessible

---

### Story 2.5: View Session List [2 points]

**Functional Tests:**
- [ ] Verify columns display: test_type, date, time, PTI, status
- [ ] Test filter by test type
- [ ] Test filter by status
- [ ] Test filter by date range
- [ ] Test sorting by date
- [ ] Verify "Edit" action opens edit form
- [ ] Verify "Enter Results" action navigates correctly
- [ ] Test pagination
- [ ] Verify default shows next 30 days

**Edge Cases:**
- [ ] Test empty list state
- [ ] Test list with past and future sessions

---

## Epic 3: PHEF Test Input

### Story 3.1: Select PHEF Session [2 points]

**Functional Tests:**
- [ ] Verify dropdown shows PHEF sessions (PLANNED or ACTIVE status)
- [ ] Test session info displays: date, time, location
- [ ] Test filter by date (today/week/month)
- [ ] Verify session stays selected for multiple entries
- [ ] Test "New session" button creates session
- [ ] Verify selected session info visible at top of form

**Edge Cases:**
- [ ] Test behavior when no sessions available
- [ ] Test changing session mid-entry (with warning)

---

### Story 3.2: Lookup Soldier via HRM [3 points]

**Functional Tests:**
- [ ] Test serial number input field
- [ ] Test API call to GET /hrm/soldier/{id}
- [ ] Verify successful lookup displays: name, gender, birthdate, age, email (read-only)
- [ ] Test "Soldier not found" error message
- [ ] Test retry option for network errors
- [ ] Test timeout after 5 seconds
- [ ] Verify loading indicator displays during lookup
- [ ] Test HRM API unavailable scenario

**Performance Tests:**
- [ ] Test lookup response time
- [ ] Test multiple rapid lookups

**Edge Cases:**
- [ ] Test invalid serial number format
- [ ] Test empty serial number field

---

### Story 3.3: Enter PHEF Measurements [5 points]

**Functional Tests:**
- [ ] Test 2400m run time input (mm:ss format)
- [ ] Test side-bridge left time input (mm:ss format)
- [ ] Test side-bridge right time input (mm:ss format)
- [ ] Test format validation (00:00 to 99:59)
- [ ] Test plausibility check (run < 30min, bridge < 10min)
- [ ] Verify automatic scoring calculation
- [ ] Test age-based scoring adjustments
- [ ] Test gender-based scoring adjustments
- [ ] Verify GO/NO-GO display
- [ ] Test reference score table visibility
- [ ] Test optional remarks field
- [ ] Test "Reset" button clears form
- [ ] Test "Save" button validation

**Edge Cases:**
- [ ] Test entering invalid time formats
- [ ] Test extremely fast/slow times
- [ ] Test partial data entry

---

### Story 3.4: Save PHEF Result [5 points]

**Functional Tests:**
- [ ] Test transactional save (all or nothing)
- [ ] Verify audit log creation
- [ ] Test success response (201 with result_id)
- [ ] Verify email sent to soldier asynchronously
- [ ] Verify PDF generated in email
- [ ] Test POST result to HRM
- [ ] Test HRM POST retry logic
- [ ] Verify UI message "Result saved"
- [ ] Test "Next soldier" flow
- [ ] Test error handling with clear messages
- [ ] Verify form data retained on save error

**Integration Tests:**
- [ ] Test complete flow: session selection → lookup → measurements → save
- [ ] Test concurrent saves from multiple PTIs

**Edge Cases:**
- [ ] Test save with HRM offline
- [ ] Test save with email service offline
- [ ] Test duplicate save prevention

---

### Story 3.5: PHEF Result List [3 points]

**Functional Tests:**
- [ ] Verify columns: name, serial, run_time, bridges, score, status
- [ ] Test filter by status (GO/NO-GO)
- [ ] Test search by name
- [ ] Test search by serial number
- [ ] Test edit option opens result for editing
- [ ] Test export to Excel
- [ ] Verify total GO/NO-GO count displays
- [ ] Test sorting by each column

**Edge Cases:**
- [ ] Test empty results list
- [ ] Test export with large dataset (1000+ results)

---

## Epic 4: Combat Test Input

### Story 4.1: Enter Combat Test Results [8 points]

**Functional Tests:**
- [ ] Test session selection (same as PHEF)
- [ ] Test HRM lookup (same as PHEF)
- [ ] Test 16km speed march GO/NO-GO toggle
- [ ] Test optional time input for speed march (hh:mm:ss)
- [ ] Test obstacle course GO/NO-GO toggle
- [ ] Test optional remarks for obstacle course
- [ ] Test rope course GO/NO-GO toggle
- [ ] Test optional remarks for rope course
- [ ] Verify final result logic (GO only if all 3 components GO)
- [ ] Test visual result display (green/red)
- [ ] Test general remarks field
- [ ] Test save to database
- [ ] Verify email sent to soldier
- [ ] Verify POST to HRM
- [ ] Verify audit log creation

**Edge Cases:**
- [ ] Test with 2/3 components passed
- [ ] Test with all components failed
- [ ] Test partial data entry validation

---

### Story 4.2: Combat Result List [3 points]

**Functional Tests:**
- [ ] Verify columns: name, serial, each component result, final result
- [ ] Test icons display correctly (✓/✗)
- [ ] Test filter by final result
- [ ] Test search functionality
- [ ] Test export to Excel
- [ ] Test edit functionality
- [ ] Test component result highlighting

**UI/UX Tests:**
- [ ] Verify color coding is clear
- [ ] Test icon accessibility

---

### Story 4.3: Combat Statistics [2 points]

**Functional Tests:**
- [ ] Verify dashboard displays total tested
- [ ] Test % GO vs NO-GO calculation
- [ ] Test component results display
- [ ] Test average speed march time calculation
- [ ] Test filter by unit
- [ ] Test filter by date range
- [ ] Verify bar chart displays correctly
- [ ] Test chart interactivity

**Performance Tests:**
- [ ] Test statistics calculation with large datasets

---

## Epic 5: Swimming Test Input

### Story 5.1: Enter Swimming Test Result [5 points]

**Functional Tests:**
- [ ] Test swimming session selection
- [ ] Test HRM lookup
- [ ] Test GO/NO-GO toggle
- [ ] Verify GO definition (100m completed per conditions)
- [ ] Verify NO-GO definition (not completed or disqualified)
- [ ] Test remarks field (safety notes)
- [ ] Test save to database
- [ ] Verify email sent to soldier
- [ ] Verify POST to HRM
- [ ] Verify audit log creation

**Edge Cases:**
- [ ] Test multiple entries for same session
- [ ] Test disqualification scenarios

---

### Story 5.2: Swimming Result List [2 points]

**Functional Tests:**
- [ ] Verify columns: name, serial, result, remarks
- [ ] Test filter by result
- [ ] Test search functionality
- [ ] Test export to Excel
- [ ] Test edit functionality

---

## Epic 6: Functional Test Input

### Story 6.1: Enter Functional Test Measurements [5 points]

**Functional Tests:**
- [ ] Test functional session selection
- [ ] Test HRM lookup
- [ ] Test pull-ups input (0-100 integer)
- [ ] Test push-ups input (0-200 integer)
- [ ] Test sit-ups input (0-200 integer)
- [ ] Test plausibility checks
- [ ] Verify real-time points calculation per component
- [ ] Test age-based scoring table
- [ ] Test gender-based scoring table
- [ ] Verify percentage of max calculation
- [ ] Verify total points calculation
- [ ] Test score reference table visibility
- [ ] Test remarks field

**Edge Cases:**
- [ ] Test entering 0 for any component
- [ ] Test entering maximum values
- [ ] Test decimal inputs (should reject)

---

### Story 6.2: Determine GO/NO-GO [3 points]

**Functional Tests:**
- [ ] Verify minimum 50% rule per component
- [ ] Test component GO when ≥50%
- [ ] Test component NO-GO when <50%
- [ ] Verify final GO only if all 3 components GO
- [ ] Test visual feedback (green/red per component)
- [ ] Test big final result badge display
- [ ] Verify failure highlighting

**Edge Cases:**
- [ ] Test exactly 50% scenarios
- [ ] Test 49.9% scenarios
- [ ] Test all three at exactly 50%

---

### Story 6.3: Save Functional Results [5 points]

**Functional Tests:**
- [ ] Verify all data saved (counts, points, percentages, GO/NO-GO)
- [ ] Test transactional save
- [ ] Verify audit log creation
- [ ] Test detailed email sent to soldier
- [ ] Verify POST to HRM
- [ ] Test success message display
- [ ] Verify "Next soldier" workflow
- [ ] Test error handling with data retention

**Integration Tests:**
- [ ] Test complete functional test workflow
- [ ] Test concurrent functional test entries

---

### Story 6.4: Functional Result List [2 points]

**Functional Tests:**
- [ ] Verify columns: name, serial, pull-ups, push-ups, sit-ups, total points, final result
- [ ] Test color-coded components
- [ ] Test sort by points
- [ ] Test filter by GO/NO-GO
- [ ] Test export to Excel
- [ ] Test edit functionality

**UI/UX Tests:**
- [ ] Verify color coding enhances readability
- [ ] Test accessibility of color indicators

---

## Epic 7: Reporting

### Story 7.1: PHEF Failed Overview [5 points]

**Functional Tests:**
- [ ] Verify "PHEF Failed" tab displays
- [ ] Test grid columns: serial_number, name, rank, gender, age, unit, test_date, score, run_time, bridges
- [ ] Test unit scope filter (own unit for PTI/APTI)
- [ ] Verify admin sees all units
- [ ] Test current calendar year filter only
- [ ] Test NO-GO results only filter
- [ ] Test column filters
- [ ] Test sort by date (newest first default)
- [ ] Test Excel export
- [ ] Test refresh button
- [ ] Verify load time < 2 seconds

**Performance Tests:**
- [ ] Test with 500+ failed results
- [ ] Test export with large datasets

---

### Story 7.2: Combat Failed Overview [3 points]

**Functional Tests:**
- [ ] Test same structure as PHEF failed
- [ ] Verify extra columns for each component result
- [ ] Test failed component highlighting
- [ ] Test filter per component
- [ ] Test export functionality

---

### Story 7.3: Functional Failed Overview [3 points]

**Functional Tests:**
- [ ] Test same structure as PHEF failed
- [ ] Verify columns: pull-ups, push-ups, sit-ups, percentages, total, component fails
- [ ] Test filters
- [ ] Test export functionality

---

### Story 7.4: Dashboard per Test Type [1 point]

**Functional Tests:**
- [ ] Verify dashboard shows total tested
- [ ] Test GO/NO-GO ratio per test type
- [ ] Test quick filters
- [ ] Verify data accuracy across all test types

---

## Epic 8: General Functionality

### Story 8.1: HRM Integration - GET Military Personnel [5 points]

**Functional Tests:**
- [ ] Test GET /hrm/militair/{serial_number} endpoint
- [ ] Verify response includes: name, gender, date of birth, age, unit, email
- [ ] Test authentication (API key or OAuth2)
- [ ] Test 5 second timeout
- [ ] Test 2x retry on error
- [ ] Test error handling: 404, 500, timeout
- [ ] Verify caching (5 minutes)
- [ ] Test cache expiration
- [ ] Verify logging of all calls

**Integration Tests:**
- [ ] Test with real HRM test environment
- [ ] Test with mock HRM responses

**Security Tests:**
- [ ] Test unauthorized access attempts
- [ ] Verify secure credential storage

---

### Story 8.2: HRM Integration - POST Test Result [5 points]

**Functional Tests:**
- [ ] Test POST /hrm/test-result with complete JSON
- [ ] Verify JSON includes all required fields
- [ ] Test idempotency (same result_id no duplicate)
- [ ] Test 10 second timeout
- [ ] Test 3x retry with exponential backoff
- [ ] Test queue for persistent errors
- [ ] Verify 200/201 success response
- [ ] Test logging of all calls
- [ ] Verify background job execution
- [ ] Test failed job queue
- [ ] Test admin UI for failed jobs

**Edge Cases:**
- [ ] Test network interruption during POST
- [ ] Test HRM maintenance mode
- [ ] Test duplicate prevention

---

### Story 8.3: Email Service - Send Results [3 points]

**Functional Tests:**
- [ ] Test email template for each test type
- [ ] Verify HTML and plain text versions
- [ ] Test email content: name, test date, session, result, scores
- [ ] Test PDF attachment generation
- [ ] Verify PDF includes logo and styling
- [ ] Test from address: noreply@warriorfit.mil
- [ ] Test 3x retry on error
- [ ] Verify background job execution
- [ ] Test logging of sent emails
- [ ] Test bounce handling

**Integration Tests:**
- [ ] Test with mock SMTP server
- [ ] Test email delivery to various email providers

---

### Story 8.4: Audit Logging Service [2 points]

**Functional Tests:**
- [ ] Verify audit log table structure
- [ ] Test logging of all event types
- [ ] Test middleware logs POST/PUT/DELETE requests
- [ ] Verify logs are immutable
- [ ] Test 7-year retention
- [ ] Test admin search interface
- [ ] Test export capability
- [ ] Verify changes stored as JSON

**Security Tests:**
- [ ] Test log tampering prevention
- [ ] Verify access controls on audit logs

---

## Epic 9: Cross Session Management

### Story 9.1: Create Cross Session [5 points]

**Functional Tests:**
- [ ] Test form fields: Date, Time, Distance, Executed, Description
- [ ] Test date validation (cannot be in past)
- [ ] Test time format (HH:MM)
- [ ] Verify display format "DD/MM/YYYY HH:MM"
- [ ] Test distance required and numeric validation
- [ ] Test "Add" button creates new cross
- [ ] Verify cross appears in table immediately
- [ ] Test form clears after adding
- [ ] Test "Clear" button resets all fields

**Edge Cases:**
- [ ] Test adding cross with future date
- [ ] Test adding cross with missing fields

---

### Story 9.2: Edit Cross [5 points]

**Functional Tests:**
- [ ] Test row selection in table
- [ ] Verify selected row highlights
- [ ] Test form population with selected values
- [ ] Test modifying all fields
- [ ] Test "Update" button updates table
- [ ] Verify immediate table update
- [ ] Test "Update" button only active when row selected
- [ ] Test executed checkbox toggle

**Edge Cases:**
- [ ] Test deselecting row
- [ ] Test switching between rows during edit

---

### Story 9.3: Delete Cross [3 points]

**Functional Tests:**
- [ ] Test single row selection (checkbox)
- [ ] Test multiple row selection
- [ ] Test "Delete Selected" button
- [ ] Verify confirmation dialog text
- [ ] Test deletion removes rows from table
- [ ] Test button only active with selection
- [ ] Verify form resets after delete

**Edge Cases:**
- [ ] Test canceling deletion
- [ ] Test deleting all visible crosses

---

### Story 9.4: Cross List Filters & Sorting [3 points]

**Functional Tests:**
- [ ] Test sortable columns: ID, Start, Distance, Executed
- [ ] Test date range filter (from/to)
- [ ] Test Executed status filter (All/True/False)
- [ ] Test Distance filter (min/max)
- [ ] Test Description search bar
- [ ] Test "Reset filters" button
- [ ] Test pagination (20 per page)
- [ ] Verify default sorting (Start date descending)

**Edge Cases:**
- [ ] Test invalid date ranges
- [ ] Test filters with no results

---

### Story 9.5: Export Cross List [2 points]

**Functional Tests:**
- [ ] Test "Export to Excel" button
- [ ] Verify export includes filtered/sorted results
- [ ] Test Excel columns: ID, Start, Executed, Distance, Description
- [ ] Verify filename format "Crosses_YYYYMMDD.xlsx"
- [ ] Test export with all data
- [ ] Test export with filtered data

---

## Epic 10: Cross Runners Management

### Story 10.1: Enter Cross Results [5 points]

**Functional Tests:**
- [ ] Test cross selection dropdown
- [ ] Test "Select" button loads cross
- [ ] Test serial number entry
- [ ] Test "Confirm Serial" HRM validation
- [ ] Verify read-only fields: Runner Name, Gender, Age, Unit
- [ ] Test running time input (hh:mm:ss format)
- [ ] Verify automatic running seconds calculation
- [ ] Test "Add" button adds runner to table
- [ ] Verify table columns: Order, ID, Serial, Running Time, Runner Name, Gender, Age, Running seconds, Unit
- [ ] Test automatic order assignment
- [ ] Verify form stays ready for next runner
- [ ] Test "Clear Form" button (keeps cross selection)

**Validations:**
- [ ] Test cross must be selected
- [ ] Test serial number must exist in HRM
- [ ] Test running time required
- [ ] Test no duplicate serial numbers per cross

---

### Story 10.2: Update Cross Results [2 points]

**Functional Tests:**
- [ ] Test row selection populates form
- [ ] Verify serial and runner info read-only
- [ ] Test modifying running time
- [ ] Test "Update" button adjusts time
- [ ] Verify running seconds recalculates
- [ ] Test "Delete Selected" button
- [ ] Test multi-select with checkboxes
- [ ] Verify deletion confirmation dialog
- [ ] Test order recalculation after delete

**Edge Cases:**
- [ ] Test deleting first runner
- [ ] Test deleting last runner

---

### Story 10.3: Report Cross List [1 point]

**Functional Tests:**
- [ ] Test "Generate Report" button
- [ ] Verify report content (cross name, date, runner table)
- [ ] Test report columns match requirements
- [ ] Test "Download" button (blue, prominent)
- [ ] Verify filename format
- [ ] Test report only available with cross selected and runners present

**Edge Cases:**
- [ ] Test report with 1 runner
- [ ] Test report with 100+ runners

---

## Epic 11: March Registration

### Story 11.1: Enter March [5 points]

**Functional Tests:**
- [ ] Test serial number input
- [ ] Test "Confirm Serial" HRM validation
- [ ] Verify read-only fields: Name, gender, age, unit
- [ ] Test date picker (required)
- [ ] Test distance dropdown (20, 30, 40, 50, 100, 120)
- [ ] Test passed checkbox (default unchecked)
- [ ] Test comments field (optional)
- [ ] Test "Add" button adds march
- [ ] Verify march appears in table: ID, Serial Number, Name, Date, KM, Passed, Unit
- [ ] Test form clears after adding
- [ ] Test "Clear Form" button

**Validations:**
- [ ] Test serial must exist in HRM
- [ ] Test date cannot be in future
- [ ] Test distance > 0
- [ ] Test no duplicate (serial + date + km)

---

### Story 11.2: Update March [3 points]

**Functional Tests:**
- [ ] Test row selection populates form
- [ ] Verify serial and military info read-only
- [ ] Test editing: date, distance, passed status, comments
- [ ] Test "Update" button modifies march
- [ ] Verify immediate table update
- [ ] Test "Update" button only active with selection

---

### Story 11.3: Delete March [2 points]

**Functional Tests:**
- [ ] Test single/multiple row selection
- [ ] Test "Delete Selected" button
- [ ] Verify confirmation dialog
- [ ] Test rows disappear after deletion
- [ ] Test button only active with selection

---

### Story 11.4: Unit March Overview (Current Year) [3 points]

**Functional Tests:**
- [ ] Test "Unit March Overview" tab
- [ ] Verify unit filter (own unit for PTI/APTI, all for admin)
- [ ] Test current year filter only
- [ ] Test grid columns: serial, name, rank, unit, march count, last march date, last distance, last status
- [ ] Test sortable columns
- [ ] Test search by name/serial
- [ ] Test filter "Has march" / "No march"
- [ ] Test filter passed/failed
- [ ] Test Excel export
- [ ] Test row click shows all marches (Story 11.5)

---

### Story 11.5: Personal March Overview [2 points]

**Functional Tests:**
- [ ] Test serial number input
- [ ] Test "Search" button retrieves all marches
- [ ] Verify military info display at top
- [ ] Test table columns: Date, Distance, Passed, Comments, Registered by
- [ ] Test sort by date (newest first default)
- [ ] Test filter by year dropdown
- [ ] Test filter passed/failed
- [ ] Test export to PDF
- [ ] Verify chart displays marches per year (bar chart)

---

## Epic 14: Individual Test History Management

### Story 14.1: Search Individual by Serial Number [3 points]

**Functional Tests:**
- [ ] Test serial number input field
- [ ] Verify format validation (e.g., BE-20250001)
- [ ] Test search button triggers lookup
- [ ] Test case-insensitive search
- [ ] Verify results display within 2 seconds
- [ ] Test error message for not found
- [ ] Test network error handling

**Edge Cases:**
- [ ] Test invalid serial number format
- [ ] Test empty serial number
- [ ] Test special characters in input

---

### Story 14.2: Display Complete Test History [5 points]

**Functional Tests:**
- [ ] Verify table columns: Date, Type, Details, Scores, Total, Result
- [ ] Test sort by date (newest first)
- [ ] Verify pass/fail color coding (green/red)
- [ ] Test all test types display: PHEF, Mars, Combat, Swimming
- [ ] Test pagination displays "Viewing rows X through Y of Z"
- [ ] Test table scrollability with large datasets

**Performance Tests:**
- [ ] Test with 50+ test records
- [ ] Test loading time

---

### Story 14.3: View Test Details and Scores [3 points]

**Functional Tests:**
- [ ] Test Details column shows test components (Run, SBR, SBL)
- [ ] Test Scores column displays component scores
- [ ] Verify total score format (X/100)
- [ ] Test missing scores show "-"
- [ ] Verify format consistency across test types
- [ ] Test data readability

---

### Story 14.4: Generate Full Report [5 points]

**Functional Tests:**
- [ ] Test "Generate Full Report" button
- [ ] Verify confirmation message displays
- [ ] Test report includes all visible test history
- [ ] Verify PDF professional formatting
- [ ] Test report includes serviceman identification
- [ ] Verify generation completes within 5 seconds

**Edge Cases:**
- [ ] Test report with no test history
- [ ] Test report with 50+ tests

---

### Story 14.5: Download PDF Report [2 points]

**Functional Tests:**
- [ ] Verify "Download PDF" button available after generation
- [ ] Test download initiates immediately on click
- [ ] Verify filename includes serial number and date
- [ ] Test file downloads to default location
- [ ] Verify download confirmation

---

### Story 14.6: View Serviceman Information [2 points]

**Functional Tests:**
- [ ] Verify display shows: Name, Serial Number, Battalion, Unit Location
- [ ] Test information displays in "Serviceman" section
- [ ] Verify data formatting and readability
- [ ] Test information remains visible while scrolling
- [ ] Verify all fields populated from database

---

## Epic 15: Unit Status Overview & Quick Test Access

### Story 15.1: View Unit Status Overview [5 points]

**Functional Tests:**
- [ ] Test table displays all servicemen in unit
- [ ] Verify columns: Service #, Rank, Name, Gender, Birthdate, Para, Ops Test status
- [ ] Test status indicators for: PHEF, Combat, Swimming, March
- [ ] Verify color coding (green=passed, red=failed/not done)
- [ ] Test pagination "Viewing rows X through Y of Z"
- [ ] Verify data loads within 3 seconds

**Performance Tests:**
- [ ] Test with 200+ servicemen
- [ ] Test loading time optimization

---

### Story 15.3: Search for Specific Servicemen [3 points]

**Functional Tests:**
- [ ] Test search fields: Service #, Rank, Last name, First name
- [ ] Verify case-insensitive search
- [ ] Test results filter as user types
- [ ] Test multiple search fields together
- [ ] Test "Clear" button resets search
- [ ] Verify partial