# Complete Test Plan – WarriorFit System

WarriorFit is a Python Shiny for Python desktop web application.
Test cases validate UI behaviour, reactive state, business logic, and data persistence.
Test status: `[x]` = implemented/passing, `[ ]` = pending.

---

## Epic 1: User Management

### Story 1.1: Create New User [5 points]

**Functional Tests:**
- [x] Verify form displays all required fields (username, email, password with toggle, role dropdown, serial_number)
- [x] Test username validation (3–30 characters, allowed: a-z, 0–9, ., _, -)
- [x] Test username uniqueness check — duplicate shows error in status output
- [x] Test email format validation
- [x] Test email uniqueness check — duplicate shows error in status output
- [x] Test password complexity requirements (minimum 12 characters)
- [x] Test serial_number uniqueness
- [x] Verify role dropdown displays: admin, PTI, APTI
- [x] Verify serial_number must exist in BEMIL
- [x] Test successful user creation — "User created" notification shown
- [x] Verify audit log entry created after user creation
- [x] Test form clears after successful creation

**Security Tests:**
- [x] Verify password is hashed before storing in database
- [x] Verify password is not visible in plain text in the DataGrid
- [x] Verify only admin role can access User Management tab

**UI Tests:**
- [x] Password field shows masked characters by default
- [x] Password toggle button switches between masked and plain text

---

### Story 1.2: Error Handling for User Creation [2 points]

**Functional Tests:**
- [x] Test duplicate username — error message in status output field
- [x] Test duplicate email — error message in status output field
- [x] Test duplicate serial_number — error message in status output field
- [x] Test weak password — specific feedback about requirements
- [x] Verify error messages are clear and appear in the status text output

**UI Tests:**
- [x] Status output text is visible and styled after error

---

### Story 1.3: Edit User [5 points]

**Functional Tests:**
- [x] Test user row selection from DataGrid — form pre-fills with current values
- [x] Test editing email (with uniqueness validation)
- [x] Test editing role (dropdown updates)
- [x] Test editing serial_number (with uniqueness validation)
- [x] Test toggling active status checkbox
- [x] Test "Update" button saves changes
- [x] Verify audit log records changes
- [x] Verify success notification or status message shown

**Edge Cases:**
- [x] Test editing with no row selected — Update button should show error
- [x] Test changing email to one that is already used by another user

---

### Story 1.4: Password Reset by Admin [2 points]

**Functional Tests:**
- [x] Test entering new password in edit form resets user password
- [x] Verify audit log records password reset action
- [x] Test leaving password field blank on update does NOT change password
- [x] Verify new password is hashed before storing

---

### Story 1.5: User List with Search [2 points]

**Functional Tests:**
- [x] Verify DataGrid displays columns: username, email, role, serial_number, active
- [x] Test column filter on username
- [x] Test column filter on role
- [x] Test column filter on active status
- [x] Test Refresh button reloads data
- [x] Test clicking a row loads user into edit form

**Performance Tests:**
- [x] Verify grid loads within 3 seconds

---

### Story 1.6: Delete User [2 points]

**Functional Tests:**
- [x] Select user row and click "Delete Selected" — user is removed
- [x] Verify DataGrid updates after deletion
- [x] Verify audit log records deletion
- [x] Test delete with no row selected — shows appropriate error

---

## Epic 2: Test Session Planning

### Story 2.1: Create New Test Session [5 points]

**Functional Tests:**
- [x] Verify form displays all fields (PTI dropdown, date, time, type, description, canceled)
- [x] Test type dropdown shows: PHEF, Combat, Functional, Swimming
- [x] Test PTI dropdown loads from BEMIL service
- [x] Test validation: date required
- [x] Test validation: type required and must be valid
- [x] Test time format validation (HH:MM)
- [x] Test "Add" creates session and grid updates
- [x] Verify form clears after successful add
- [x] Verify status message: "Session added successfully"

**Edge Cases:**
- [x] Test add with no PTI selected
- [x] Test add with invalid time format

---

### Story 2.2: Update Session [3 points]

**Functional Tests:**
- [x] Click row in DataGrid — form pre-fills with session values
- [x] Modify type and date, click "Update" — grid updates
- [x] Test canceled checkbox toggle saves correctly
- [x] Verify status message after update

---

### Story 2.3: Delete Session [2 points]

**Functional Tests:**
- [x] Select session row and click "Delete Selected" — session removed
- [x] Verify DataGrid updates after deletion
- [x] Test delete with no row selected — error shown

---

### Story 2.4: View Session List [3 points]

**Functional Tests:**
- [x] Verify DataGrid shows columns: Start, Type, Serial PTI, Canceled, Description
- [x] Test column filters work
- [x] Verify sessions sorted by Start date ascending
- [x] Test Refresh button reloads grid

---

### Story 2.5: Upcoming Sessions on Welcome Page [2 points]

**Functional Tests:**
- [x] Verify PTI/APTI role sees upcoming sessions DataGrid on Welcome tab
- [x] Verify admin does NOT see the sessions DataGrid section
- [x] Test DataGrid shows only sessions for logged-in user's serial
- [x] Verify Refresh button on welcome page reloads sessions

---

## Epic 3: PHEF Test Input

### Story 3.1: Select PHEF Session [2 points]

**Functional Tests:**
- [x] PHEF session dropdown shows only sessions of type PHEF
- [x] Selecting session updates the result grid for that session
- [x] Session stays selected across multiple serial lookups

---

### Story 3.2: Lookup Serviceman via BEMIL [2 points]

**Functional Tests:**
- [x] Enter valid serial number and click "Confirm Serial" — serviceman info displayed
- [x] Display format: "Rank Serial FirstName LastName Gender Age years old"
- [x] Enter invalid serial — "Not found" message; measurement inputs stay disabled
- [x] Click "Search own Unit" — modal opens with servicemen DataGrid
- [x] Modal DataGrid is filterable
- [x] Select row in modal — serial fills into main field; modal closes

---

### Story 3.3: Enter PHEF Measurements [5 points]

**Functional Tests:**
- [x] Side-bridge Right input (mm:ss) — live score updates next to field
- [x] Side-bridge Left input (mm:ss) — live score updates next to field
- [x] 2400m run input (mm:ss) — live score updates next to field
- [x] Score ≥ 10 shown in green; score < 10 shown in red
- [x] Total score shows PASSED when side total ≥ 20 AND run ≥ 10
- [x] Total score shows FAILED and is red when criteria not met
- [x] Measurement inputs are disabled before serial confirmation
- [x] After serial confirmation: inputs become enabled

**Edge Cases:**
- [x] Empty measurement fields → scores show blank
- [x] Invalid time format (e.g., "abc") → score shows blank, no crash

---

### Story 3.4: Add PHEF Result [5 points]

**Functional Tests:**
- [x] "Add" button disabled until session selected AND serial confirmed
- [x] Click "Add" — result saved to database
- [x] Grid updates to show new entry
- [x] Form clears after successful add
- [x] Status message: "Added PHEF test for [serial] in session [id]"
- [x] Verify audit log entry created

**Error Cases:**
- [x] Add with no session selected — error in status
- [x] Add with no serial confirmed — error in status

---

### Story 3.5: Update/Delete PHEF Result [2 points]

**Functional Tests:**
- [x] Click result row — form fills; Add disabled, Update enabled
- [x] Modify time values, click Update — record changes in grid
- [x] Click "Delete Selected" with row selected — record removed from grid
- [x] Verify status message after update/delete

---

### Story 3.6: PHEF Result Grid [2 points]

**Functional Tests:**
- [x] Grid shows records only for selected session
- [x] Columns include: Serial, Sidebridge R, Sidebridge L, Run time, Scores, Pass/Fail
- [x] Grid sorts by serial number
- [x] Refresh button reloads grid data

---

## Epic 4: Combat Test Input

### Story 4.1: Enter Combat Test Results [5 points]

**Functional Tests:**
- [x] Combat session dropdown shows only Combat-type sessions
- [x] BEMIL serial lookup works same as PHEF
- [x] Three GO/NO-GO inputs: Speed March, Obstacle Course, Rope Course
- [x] Final result = GO only when all 3 are GO
- [x] Final result = NO-GO if any component is NO-GO
- [x] Visual indicator shows GO (green) or FAIL (red)

---

### Story 4.2: Add/Update/Delete Combat Result [3 points]

**Functional Tests:**
- [x] "Add" saves new result — grid updates
- [x] Row selection fills form for update
- [x] "Update" saves changes — grid updates
- [x] "Delete Selected" removes entry — grid updates
- [x] Status messages confirm each action

---

### Story 4.3: Combat Result Grid [2 points]

**Functional Tests:**
- [x] Grid shows results for selected session only
- [x] Columns: serial, speed march result, obstacle result, rope result, final result
- [x] Refresh button reloads data

---

## Epic 5: Swimming Test Input

### Story 5.1: Enter Swimming Test Result [4 points]

**Functional Tests:**
- [x] Swimming session dropdown shows only Swimming sessions
- [x] BEMIL serial lookup works
- [x] GO/NO-GO selection available
- [x] Optional remarks field
- [x] Form clears after save

---

### Story 5.2: Add/Update/Delete Swim Result [2 points]

**Functional Tests:**
- [x] "Add" creates result; grid updates
- [x] Row selection fills form for update
- [x] "Update" and "Delete" work correctly
- [x] Status messages after each action

---

### Story 5.3: Swimming Result Grid [1 point]

**Functional Tests:**
- [x] Grid filtered by selected session
- [x] Columns: serial, result, remarks

---

## Epic 6: Functional Test Input

### Story 6.1: Enter Functional Test Measurements [5 points]

**Functional Tests:**
- [x] Functional session dropdown shows only Functional sessions
- [x] BEMIL serial lookup works
- [x] Pull-ups input: integer, 0–100
- [x] Push-ups (2min) input: integer, 0–200
- [x] Sit-ups (2min) input: integer, 0–200
- [x] Points per component calculated in real time (age/gender corrected)
- [x] Percentage of maximum shown per component

---

### Story 6.2: Determine GO/NO-GO [2 points]

**Functional Tests:**
- [x] Component ≥ 50% → GO (shown in green)
- [x] Component < 50% → NO-GO (shown in red)
- [x] Final GO only when all 3 components are GO
- [x] Final result badge updates reactively as values change

**Edge Cases:**
- [x] Exactly 50% on one component → GO (boundary check)
- [x] 49% on one component → NO-GO

---

### Story 6.3: Add/Update/Delete Functional Result [3 points]

**Functional Tests:**
- [x] "Add" saves counts, percentages, component and final GO/NO-GO
- [x] Row selection fills form for update
- [x] "Update" and "Delete" work correctly
- [x] Status messages after each action

---

### Story 6.4: Functional Result Grid [2 points]

**Functional Tests:**
- [x] Grid filtered by selected session
- [x] Columns: serial, pull-ups, push-ups, sit-ups, total score, final result

---

## Epic 7: March Registration

### Story 7.1: Enter March [5 points]

**Functional Tests:**
- [x] Serial number input + "Confirm Serial" validates via BEMIL
- [x] "Search own Unit" modal opens; row selection fills serial and closes modal
- [x] After confirmation: rank, name, gender, age shown read-only
- [x] Date picker shows today by default
- [x] Distance numeric field (default 30, min 0)
- [x] Succeeded checkbox (default unchecked)
- [x] "Add" creates record — grid updates
- [x] Uniqueness check: same serial + distance + date → error, no save
- [x] Form clears after successful add

**Error Cases:**
- [x] Add with unconfirmed serial — error shown
- [x] Add duplicate march — error in status

---

### Story 7.2: Update March [3 points]

**Functional Tests:**
- [x] Click row — form pre-fills with date, distance, succeeded
- [x] Modify values and click "Update" — grid updates
- [x] Status confirms update

---

### Story 7.3: Delete March [2 points]

**Functional Tests:**
- [x] Select row and click "Delete" — record removed
- [x] Grid refreshes after deletion

---

### Story 7.4: March List View [3 points]

**Functional Tests:**
- [x] DataGrid shows columns: service_number, distance, Succeeded (✓/✗), Date
- [x] Sorted by service_number
- [x] Refresh button reloads data
- [x] ID column is hidden from display

---

## Epic 8: Cross Session & Runner Management

### Story 8.1: Create/Edit/Delete Cross Session [5 points]

**Functional Tests:**
- [x] Form fields: date, time (HH:MM), distance (km), executed checkbox, description
- [x] "Add" creates cross session; grid updates
- [x] Click row → form pre-fills for edit
- [x] "Update" saves changes; grid updates
- [x] "Delete" removes selected session; grid updates
- [x] "Clear" resets all form fields
- [x] Grid columns: ID, Start, Executed, Distance, Description

---

### Story 8.2: Enter Cross Runner Results [5 points]

**Functional Tests:**
- [x] Cross session dropdown populates available sessions
- [x] Serial input + "Confirm Serial" validates via BEMIL
- [x] "Search own Unit" modal available
- [x] Running time input (hh:mm:ss)
- [x] Running seconds calculated and shown in grid
- [x] "Add" creates runner entry; grid updates
- [x] Order assigned sequentially
- [x] Duplicate serial per cross is rejected with error
- [x] Form stays ready for next runner after add

---

### Story 8.3: Update/Delete Cross Runner [3 points]

**Functional Tests:**
- [x] Click row in runners grid — form pre-fills
- [x] Modify running time and click "Update" — grid updates
- [x] "Delete" removes runner entry — grid updates

---

### Story 8.4: Cross Planning List View [2 points]

**Functional Tests:**
- [x] DataGrid shows all cross sessions
- [x] Filterable columns
- [x] Refresh button works

---

### Story 8.5: Cross Statistics [3 points]

**Functional Tests:**
- [x] Two DataGrids displayed: Top 10 (5km) and Top 10 (10km)
- [x] Rankings show fastest times
- [x] Refresh button reloads both grids
- [x] Same serviceman never appears twice in a Top-10 grid (best time kept across multiple crosses of same distance)
- [x] Age-group counts each person once even if they ran multiple crosses

---

### Story 8.6: Import Chronos XML Race Result [5 points]

**Functional Tests:**
- [ ] Upload button hidden when no cross session selected
- [ ] Upload button hidden when cross selected but no runners registered
- [ ] Upload button visible when cross selected and runners exist
- [ ] Upload valid XML file — runners grid refreshes, success notification shown
- [ ] Upload invalid XML (does not match XSD) — error notification shown, no data saved
- [ ] Upload XML with bib matching service_number — runner time updated in DB
- [ ] Upload XML with bib not in service_men — skipped silently, other runners still saved
- [ ] `Cross.executed` flag set to `True` after successful import
- [ ] Upload same file a second time in same session — not processed again (dedup guard)
- [ ] `<net>` time "00:35:12" correctly parsed to 2112.0 seconds

**UI Tests:**
- [ ] Download/Generate Report buttons hidden when no cross selected or no runners
- [ ] Download/Generate Report buttons visible after runners registered
- [ ] Runners grid auto-refreshes after import without page reload
- [ ] Upload input accepts only `.xml` files

---

### Story 8.7: Extended Cross Statistics & Redesigned UX [5 points]

**Functional Tests — KPI strip & Overview:**
- [ ] KPI strip shows three value boxes: Crosses, Finishers, Unique runners
- [ ] No global Best/Avg/Median value box (those are per-distance only)
- [ ] Overview "Best / Avg / Median per distance" grid: one row per distance with Finishers, Runners, Best, Avg, Median, Std (s), Gap
- [ ] Gender averages card shows female-avg + male-avg formatted as `HH:MM:SS`
- [ ] Age groups card lists each age bucket with unique-person count

**Functional Tests — Per cross / Best 10 / Demographics / Runners / Trends / Podium / Data quality tabs:**
- [ ] Per cross: one row per cross event with avg/median/std/best/worst/gap/pace; sorted most-recent first; filterable
- [ ] Best 10: separate 5 km and 10 km grids; rank column; each serviceman appears at most once per distance
- [ ] Demographics: best & avg per (age-group × distance), gender × distance grid (avg + finisher count); gender column displayed as readable string
- [ ] Runners: per-serviceman aggregates (Races, PB, Avg, Pace, Δ avg); filterable
- [ ] Trends: chronological rows of (date, distance, avg)
- [ ] Podium: per-serviceman gold/silver/bronze counts; sorted by gold/silver/bronze desc
- [ ] Data quality: counts + lists for unmatched serials, never-raced, rows missing time; ✅ shown when empty

**Edge Cases & Robustness:**
- [ ] Empty database (no crosses) → all KPIs show `0`, all grids empty, no exception
- [ ] Crosses without runners → handled gracefully
- [ ] Runner with `running_time = NULL` → counted in "Rows missing time", excluded from averages
- [ ] Cross with `datetime_start = NULL` → excluded from Trends only
- [ ] Refresh button reloads all metrics in one pass

---

## Epic 9: BEMIL Personnel Lookup

### Story 9.1: Lookup Serviceman by Serial Number [3 points]

**Functional Tests:**
- [x] Valid serial → returns rank, name, gender, age, unit
- [x] Invalid serial → "Not found" / "Not found" message shown
- [x] Display format consistent: "Rank Serial FirstName LastName Gender Age years old"
- [x] Confirmed on all test entry pages: PHEF, Combat, Swimming, Functional, March, Cross

---

### Story 9.2: Browse All Servicemen via Modal [2 points]

**Functional Tests:**
- [x] "Search own Unit" button (🔍) opens modal on each test page
- [x] Modal DataGrid shows columns: service_number, first_name, last_name, gender
- [x] Column filters in modal DataGrid work
- [x] Click row → serial fills into main serial field
- [x] Modal closes automatically after selection
- [x] Available on: PHEF, Combat, Swimming, Functional, March, Cross, Individual Test History

---

## Epic 10: Individual Test History

### Story 10.1: Search Individual by Serial Number [3 points]

**Functional Tests:**
- [x] Serial input + "Confirm Servicemen" button triggers BEMIL lookup
- [x] "Search own Unit" modal available
- [x] Found: serviceman info displayed (rank, name, service_number, unit)
- [x] Not found: "Not found" message; test grid remains empty
- [x] Status shows "Loaded N records" after successful search
- [x] "Refresh" button reloads test data for current serial

---

### Story 10.2: Display Complete Test History [5 points]

**Functional Tests:**
- [x] DataGrid shows all test types: PHEF, Combat, Swimming, Functional, March
- [x] Columns present: Date, Type, Details, Scores, Total, Result
- [x] Tests sorted by date (newest first)
- [x] Record count shown: "Loaded N records" or "No tests found"
- [x] Empty DataFrame shown when no results

**Edge Cases:**
- [x] Serviceman with only one test type — other columns show appropriate empty/null values
- [x] Serviceman with no tests at all — grid shows empty state

---

### Story 10.3: Generate Individual PDF Report [5 points]

**Functional Tests:**
- [x] "Generate Full Report" button triggers async PDF generation
- [x] Notification shown: "Report generated" on success
- [x] Status message: "Full report for [serial] generated"
- [x] Error case: no serial entered — status: "No serviceman selected"
- [x] Error case: PDF generation fails — status: "Failed to generate report"
- [x] Download button appears after successful generation

---

### Story 10.4: Download PDF Report [2 points]

**Functional Tests:**
- [x] "Download PDF" button appears only when report_path is set
- [x] Download button triggers file download
- [x] Filename format: "Report_{serial_number}.pdf"
- [x] Button is hidden when no report has been generated

---

## Epic 11: Unit Status & Dashboard

### Story 11.1: View Unit Status Grid [5 points]

**Functional Tests:**
- [x] "Status Unit" tab shows all servicemen in own unit
- [x] DataGrid columns include: Service #, Rank, Name, Gender, Birthdate, test statuses
- [x] PHEF, Combat, Swimming status shown per serviceman
- [x] Filterable columns
- [x] Refresh button reloads data
- [x] "Pdf Status Unit" button generates unit PDF
- [x] Download button appears after PDF generation
- [x] Filename: "Report_{unit_name}.pdf"

---

### Story 11.2: View Individual History via Modal [2 points]

**Functional Tests:**
- [x] Click row in unit status grid → modal opens
- [x] Modal shows DataGrid of tests for selected serviceman
- [x] Columns: Test Type, Session, Status
- [x] "Close" button dismisses modal
- [x] Click outside modal (easy_close=True) also dismisses it

---

### Story 11.3: Unit Dashboard with Statistics [3 points]

**Functional Tests:**
- [x] Dashboard tab shows summary cards per test type
- [x] Each card: total tested count, GO count, NO-GO count, pass rate %
- [x] Plotly charts shown for pass rates (bar or pie)
- [x] Refresh button reloads all dashboard data
- [x] Data scoped to current calendar year

---

### Story 11.4: PHEF Not-Done List [2 points]

**Functional Tests:**
- [x] "PHEF Not done" tab shows servicemen who lack PHEF result for current year
- [x] Header shows current year and unit name
- [x] DataGrid is filterable
- [x] Refresh button reloads data

---

## Epic 12: Calendar Events

### Story 12.1: View Personal Test Calendar [3 points]

**Functional Tests:**
- [x] Calendar tab shows FullCalendar weekly time-grid view
- [x] Events shown for sessions where PTI serial = logged-in user's serial
- [x] Events are color-coded by test type
- [x] Click on event → event color turns red (highlight)
- [x] Calendar is read-only (no drag-and-drop creation)

---

### Story 12.2: View All Test Sessions Calendar [2 points]

**Functional Tests:**
- [x] Toggle between personal and all-sessions view
- [x] All-sessions view shows test sessions across all PTIs
- [x] Same FullCalendar UI is used for both views

---

## Epic 13: Fitness Room Reservation

### Story 13.1: Create Room Reservation [5 points]

**Functional Tests:**
- [x] Room dropdown shows available rooms with name, color indicator, capacity, location
- [x] PTI serial field (identifies who is booking)
- [x] Activity description text field
- [x] Date picker
- [x] Start time and end time pickers
- [x] "Reserve" button creates reservation; appears in list/calendar view
- [x] Overlap validation: booking same room at overlapping time → error shown
- [x] No overlap: reservation created successfully

**Error Cases:**
- [x] Reserve with missing required fields → error in status
- [x] Reserve overlapping slot → conflict error message shown

---

### Story 13.2: View Reservations (Weekly/Monthly/List) [2 points]

**Functional Tests:**
- [x] Three view tabs: Weekly, Monthly, List
- [x] Weekly view shows time-grid with reservations per room (color-coded)
- [x] Monthly view shows day-level reservation events
- [x] List view shows DataGrid with all reservations; filterable
- [x] All views display: room, PTI, activity, date/time

---

### Story 13.3: Delete Reservation [1 point]

**Functional Tests:**
- [x] Delete button available per reservation in list view
- [x] After deletion, reservation disappears from all views
- [x] No confirmation dialog required (immediate delete)

---

## Epic 14: Audit Logs

### Story 14.1: View Audit Log [3 points]

**Functional Tests:**
- [x] "Audit Logs" tab visible to admin role only
- [x] DataGrid shows all audit events
- [x] Columns: timestamp, event_type, actor, target, details
- [x] DataGrid is read-only (no edit buttons)
- [x] Refresh button reloads data

**Security Tests:**
- [x] Non-admin users cannot access "Audit Logs" tab
- [x] Log entries cannot be deleted or modified from UI

---

### Story 14.2: Filter Audit Log [2 points]

**Functional Tests:**
- [x] Built-in DataGrid column filters work (filters=True)
- [x] Can filter by event type column
- [x] Can filter by actor column
- [x] Can filter by date/timestamp column

---

## Epic 15: Welcome Dashboard

### Story 15.1: Welcome Page with Role-Specific Info [3 points]

**Functional Tests:**
- [x] Welcome tab shows: "Welcome back, {username}!"
- [x] Role and email displayed: "Logged in as {role} | {email}"
- [x] Application version shown
- [x] WarriorFit logo image displayed
- [x] Refresh button (🔄) reloads page content
- [x] Unauthenticated view shows generic welcome text

---

### Story 15.2: Upcoming Sessions for PTI/APTI [2 points]

**Functional Tests:**
- [x] PTI/APTI sees "Upcoming Test Sessions" DataGrid section on Welcome tab
- [x] admin does NOT see this section
- [x] DataGrid shows only sessions for logged-in user's serial number
- [x] Refresh button updates the sessions DataGrid
- [x] Empty grid shown if no upcoming sessions

---

## Cross-Cutting Test Cases

### Security

- [x] Role-based tab visibility: admin-only tabs hidden from PTI/APTI
- [x] PTI/APTI see only their own unit data where applicable
- [x] Passwords are hashed and not exposed in DataGrids
- [x] Password field uses toggle (masked by default)
- [x] All user inputs are validated before database writes

### Performance

- [x] DataGrids load within 3 seconds for typical unit sizes (< 500 records)
- [x] PDF generation completes within 10 seconds
- [x] BEMIL lookup responds within 3 seconds

### UI/UX

- [x] Refresh buttons (🔄) present on all pages with grids
- [x] Refresh buttons use consistent style: btn-outline-secondary btn-sm my-2
- [x] Status text outputs show meaningful messages after every action
- [x] DataGrids use consistent column filtering where appropriate
- [x] Modals close automatically after row selection (easy_close=True or explicit close)

### Reactive State

- [x] DataGrids re-render when refresh_tick is incremented
- [x] Form pre-fill on row selection does not trigger Add/Update automatically
- [x] Serial confirmation resets form state on each new serial lookup
- [x] Report download button only appears when report_path is set
