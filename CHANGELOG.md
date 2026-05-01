# Changelog

All notable changes to the WarriorFit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-05-01] - Code quality refactor: naming fixes, app.py split, full DI wiring

### Changed
- **`app.py` split** — 1 023-line monolith decomposed into three focused modules:
  - `warriorfit/ui/page_registry.py` — `PageSpec` dataclass + `get_pages()` + `pages_for_role()`
  - `warriorfit/ui/app_server.py` — `build_app_ui()` + `make_server()` server factory
  - `warriorfit/app.py` — minimal entry point (logger setup, broker start, `App()`)
- **`@inject` DI applied to `make_server()`** — `user_service`, `servicemen_repository` and `config`
  are now resolved via `Provide[Container.xxx]`; no explicit container reference at call site.
- **Full DI wiring across the service layer** — all method-level `ApplicationConfig()` and
  direct repository instantiations replaced with injected instance variables:
  - `Service` base class now stores `self._config = config` (all 10 subclasses inherit it)
  - `RetentionService` — removed the `_config()` factory method; uses `self._config.gdpr_retention`
  - `ServiceMarch` — `ApplicationConfig().own_unit` → `self._config.own_unit`
  - `DataCollector` — `config` injected via constructor; 3 method-level calls removed
  - `GeneratorReport` — `config` injected via constructor; 4 method-level calls removed
  - `Broker` — `_process_cycle` methods use `self._mom_repo` instead of new `MomRepository()`;
    `worker()` and `_send_message_to_hr()` use `self._config.hr_url`
  - `SessionsController` — `MailService()` and `ApplicationConfig()` replaced with
    `self._mail_service` / `self._config`; `mail_service` and `config` added to constructor
  - `StatusLoginUser` page — `config` injected via `Provide[Container.config]`; `version_header`
    uses `self._config.version`
- **`Auth.authenticate_user`** — removed circular-import-inducing `@inject`; `user_service` is
  now a required parameter so callers supply their already-injected instance.
- **Container providers updated** — `data_collector`, `sessions_controller`,
  `report_generator_pdf`, `report_generator_csv` now receive `config=config`.
- **Navbar label** corrected from "Psychical Tests" → "Physical Tests".

### Fixed
- **5 filename typos** corrected (all import references updated across 29 files):
  - `appliccation_config.py` → `application_config.py`
  - `usermangement.py` → `usermanagement.py`
  - `mom_repositor.py` → `mom_repository.py`
  - `cross_plannig_controller.py` → `cross_planning_controller.py`
  - `StatusApplicationController.py` → `status_application_controller.py`
- **`notify_mail.py`** moved from `warriorfit/ui/pages/` to `warriorfit/services/` — the class
  has no UI concern and was incorrectly placed in the pages layer.
- Broker unit tests updated to use `broker._mom_repo = mock_repo` instead of patching the now-removed
  `MomRepository()` call sites inside `_process_cycle` methods.

---

## [2026-04-27] - Broker outbox: exponential back-off, batch send, dead-letter

### Added
- **Exponential back-off** in the HR outbox. After a failed POST the row's
  `next_retry_at` is set to `now + min(base_backoff_s × 2^(attempt-1), max_backoff_s)`,
  so HR is no longer hammered every 5 s during outages.
- **Dead-letter state** for poison messages. After `max_attempts` failures (default 10)
  the row is flipped to `dead_letter = TRUE`; the broker stops retrying it but keeps the
  row for ops triage. Operators can list parked rows via `MomRepository.list_dead_letter()`.
- **Batched sending**. Each worker cycle now drains up to `batch_size` due rows
  (default 5) instead of exactly one — drastically faster recovery after an outage.
- **Failure bookkeeping** on `hr_messages`: `attempt_count`, `next_retry_at`,
  `dead_letter`, `last_error` (truncated to 500 chars).
- **Tunable broker config** under `broker:` in `config_dev.yml` (and production YAML):
  `poll_interval_s`, `batch_size`, `max_attempts`, `base_backoff_s`, `max_backoff_s`.
  Exposed via `ApplicationConfig.broker_*` properties.
- Alembic migration `e5f6a7b8c9d0` adds the four new columns + a composite index
  `ix_hr_messages_due` on `(dead_letter, next_retry_at)` for the new "due now" query.

### Changed
- `Broker.check_and_send_messages` rewritten to use `MomRepository.get_due_pending_messages`
  (oldest-first, dead-letter-aware) instead of `get_last_added_hr_message_by_send_date`
  (which was newest-first and could starve older rows behind a permanently-failing newer one).
- `Broker.worker` poll interval is now read from config (default still 5 s).
- New internal helper `Broker._try_send_to_hr` returns `(result, error_reason)` so the
  failure cause can be persisted in `last_error`.

### Removed
- `MomRepository.get_last_added_hr_message_by_send_date` (replaced by `get_due_pending_messages`).

### Docs
- `documentation/PHEF_DATA_FLOW.md` updated: the "Caveats — what the broker does NOT do"
  block is gone; replaced with a "What if HR can never accept the message?" section and a
  focused "Limitations still in place" list (one process, no admin UI for dead-letter, no
  metrics endpoint).
- Diagram `documentation/diagrams/test_flow_ui_db_broker.svg/png` updated to show the new
  back-off + DLQ flow and the new `hr_messages` columns.

---

## [2026-04-27] - Cross Statistics Redesign

### Added
- **Extended Cross statistics** (`ServiceCross.get_extended_stats`) bundling:
  - **Per-cross**: median, std-dev, pace (s/km), turnout, gap (worst − best)
  - **Per-runner**: personal best, race count, average pace, average improvement vs. previous race
  - **Demographics**: best & avg time per (age group × distance), gender split per distance
  - **Trends**: chronological average running time per cross / distance
  - **Podium**: gold/silver/bronze counts per serviceman across all crosses
  - **Data quality**: unmatched serials (in race data but not in registry), registered-but-never-raced servicemen, rows with missing time
  - **Per-distance overview**: best/avg/median/std/gap/finishers/unique runners broken down by distance — replaces the previous global aggregates which mixed 5K and 10K times
- **Redesigned Cross Statistics page** (`warriorfit/ui/pages/cross_statics.py`):
  - KPI strip with three `value_box` cards (Crosses, Finishers, Unique runners)
  - `navset_card_tab` with 8 tabs: **Overview**, **Per cross**, **Best 10**, **Demographics**, **Runners**, **Trends**, **Podium**, **Data quality**
  - Filterable DataGrids on the larger tabs (Per cross, Runners, Podium)

### Changed
- **Top-N runner lists** (`get_cross_stats`, `get_top_10_runners_based_on_running_time`) now deduplicate by `serial_number` per distance — each person appears at most once, with their best time kept
- **Age-group counts** (`get_cross_stats`) now count each unique person once instead of once per race
- `_runners_df` now carries `cross_datetime` and `cross_description` so chronological analyses are possible
- `Gender` enum values are converted to string before pandas groupby (the enum has no `__lt__`, which broke factorize)
- `CrossStaticsController` exposes new accessors (`overview_per_distance_df`, `per_cross_df`, `per_runner_df`, `age_distance_best_df`, `age_distance_avg_df`, `gender_distance_df`, `trends_df`, `podium_df`, `data_quality`, `distances`) and keeps legacy ones for backward compatibility

### Fixed
- mypy errors across the codebase (13 → 0): replaced `T = None  # type: ignore[assignment]` patterns with proper `T | None = None` typing in `service_gdpr.py`, `service_consent.py`, `servicemen_overview_controller.py`, `privacy_controller.py`, `my_progress_controller.py`
- `UserConsent.consent_given_at` / `withdrawn_at` corrected from `Mapped[TIMESTAMP]` (SQL column type) to `Mapped[datetime]` (the actual Python runtime type) — `.isoformat()` callers no longer fall over mypy
- `ApplicationConfig().version` is now `None`-checked before subscripting in `status_login_user.py`
- `_failed_styles` in `own_unit.py` returns properly-typed `list[StyleInfoBody]` for Shiny DataGrid

---

## [2026-04-25] - GDPR Compliance & Servicemen Overview

### Added
- **GDPR / Privacy self-service** page (`warriorfit/ui/pages/privacy.py`) — Art. 7 grant/withdraw of consents, Art. 15/20 personal-data JSON export, Art. 13 link to the privacy notice
- **Serviceman-scoped consent storage**: new `user_consents` table keyed by `service_number` (instead of `users.id`) so consent records survive application-user lifecycle and follow the data subject (the serviceman)
- **Consent types** (with current versions): `terms_of_service`, `privacy_policy`, `health_data_processing`
- **Serviceman login mode** on the login modal — choose between "Application user" and "Serviceman"; serviceman view is restricted to *My Progress* + *About* + *Logout* and hides Calendar nav
- **My Progress** page (`warriorfit/ui/pages/my_progress.py`, USER role) — current-year tests grid, full history grid, PHEF progress chart (Plotly)
- **GDPR JSON export** (`GdprService.export_serviceman_data`) — serviceman fields, fitness tests with date (`TestSession.datetime_start` joined via `SessionFitnessTests`), marches, reservations, full consent history
- **Data-retention service** (`RetentionService`) — config-driven purge of fitness tests, marches, reservations, audit logs, HR messages
- **Admin → Servicemen Overview** page (`warriorfit/ui/pages/servicemen_overview.py`, ADMIN-only) — DataGrid of all servicemen with personal fields and one column per consent type showing grant timestamp or `—`
- **Compliance docs**: `documentation/compliance/PRIVACY_POLICY.md`, `documentation/compliance/DPIA.md`
- New repository helpers: `ServicemenRepository.list_all_with_unit`, `ConsentRepository.list_all_active`, `list_for_serviceman`
- Alembic migrations: `b2c3d4e5f6a7` (add `user_consents`), `c3d4e5f6a7b8` (cascade `service_men.user_id`), `d4e5f6a7b8c9` (rekey `user_consents` by `service_number`)
- README links to compliance docs in the Project Structure section

### Changed
- "Erase your account (Art. 17)" replaced by an alert: erasure is unavailable because organisational/regulatory rules require fitness records and the service file to be retained — restriction or rectification requests must go via the unit admin or Defence DPO
- Privacy page UI moved into the **About** menu group (with About)
- `PrivacyController` is serviceman-scoped: `serviceman_serial(session_user)`, `consents/grant/withdraw/export_json` all take `service_number`
- `ConsentService` / `ConsentRepository` API now use `service_number` everywhere
- `GdprService.erase_user` cleans `user_consents` by `service_number`

### Removed
- `User.consents` ORM relationship (no longer applicable now that consents are serviceman-scoped)
- "Erase your account" action button from the Privacy page (and its dead reactive handler)

---

## [2026-03-29] - User Manual & Documentation

### Added
- **User Manual** (`documentation/USER_MANUAL.md`) — comprehensive step-by-step guide covering all 6 user roles (Admin, PTI, APTI, Planner, Guest, User) with GUI workflows for every page
- User Manual reference added to `README.md` (Updates section and Project Structure)

---

## [2026-03-22] - Chronos XML Import for Cross Results

### Added
- **Chronos XML import** on Cross page: upload a Chronos race result file (`.xml`) to bulk-import runner times
- `chronorace.xsd` XSD schema — uploaded files are validated before processing; invalid files are rejected with an error notification
- `lxml` dependency added for XSD validation (`pyproject.toml`, `uv.lock`)
- Upload button shown only when a cross is selected **and** runners are already registered (hidden otherwise)
- Download/Generate Report buttons also shown conditionally (cross selected + runners exist)
- `Cross.executed` flag set to `True` automatically after a successful Chronos import
- Deduplication guard in `_handle_file_upload`: same filename cannot be processed twice in one session
- Dedicated `_upload_tick` reactive value so runners grid refreshes after import without re-triggering the upload effect

### Changed
- `read_xml_chronos_and_save` (service): parses `<athlete>/<bib>` as military serial number; maps `<net>` (hh:mm:ss) to `running_time` in seconds
- `add_runners_to_cross` (repository): returns `bool`; marks `cross.executed = True` with `flush()` inside the same transaction
- File processing moved from `render.text` to `@reactive.effect` (`_handle_file_upload`) — side-effects (notifications, DB writes) no longer mixed with UI rendering
- `upload_btn_ui` and `download_generated_report_btn_ui` now use `@render.ui` with async `runners_df()` as sole visibility guard
- Test data `tests/chronorace_data.xml`: all 20 `<bib>` values replaced with real `service_number` values from `test_data.sql`

### Fixed
- `upload_btn_ui` condition was inverted (`not df.empty`) — corrected to `df.empty`
- `download_generated_report_btn_ui` buttons were floating expressions (never returned) — wrapped in `ui.div()` and returned
- Infinite upload loop caused by `refresh_tick` invalidating `upload_btn_ui` — resolved by separating concerns into `_upload_tick`

---

## [2026-03-21] - Runtime Metrics Dashboard & Reactive Refresh

### Added
- Live **Runtime Metrics** row on Status Application page (auto-refreshes every 5 s via `reactive.invalidate_later`):
  - 🧠 Physical Memory RSS (MB)
  - 💾 Virtual Memory VMS (MB)
  - ⚙️ CPU usage % with total core count
  - 🔀 Active thread count
  - ⏱️ Process uptime (hh:mm:ss)
- `psutil` used for process metrics (`memory-profiler` already a dependency, pulls `psutil` transitively)

### Changed
- Clarified reactive refresh strategy across the codebase:
  - `refresh_tick` (event-driven) for DataGrids — only re-queries DB after explicit user action (CRUD / button click)
  - `reactive.invalidate_later` reserved for live-polling outputs (metrics, logs, status checks)

---

## [2026-03-20] - Modern UI/UX Redesign

### Added
- Custom CSS design system (`warriorfit/www/custom.css`) — navy/amber theme with CSS design tokens, consistent across all pages
- Reservation overlay panel (`wf-overlay-*` classes) replacing conflicting Bootstrap modal class names
- Sidebar form structure for User Management: labeled sections (Lookup / User Details / Actions), status bar, selected-user hint
- Serial Number input highlighted with blue-tinted background (`wf-serial-input`) on User Management and Individual pages

### Changed
- All Refresh buttons changed from `btn-outline-secondary` (transparent) to `btn-secondary` (solid background) across all 13 pages
- All "Confirm Serial" buttons on test pages (`phef`, `combat`, `swim`, `functional`, `cross`, `march`) given `btn-primary` colour and fixed `width="200px"`
- "Search own Unit" button changed from invalid `btn-lm` class to `btn-info` on User Management and Individual pages
- Login modal redesigned: branded logo, field labels, inline error output via `ui.output_ui` (replaces fragile JS observer)
- Calendar overlay panels styled with `wf-calendar-panel-*` classes replacing raw inline styles
- Navbar controls (calendar buttons, sign-out) use cohesive ghost-button style
- Navbar height locked at 52px with `flex-wrap: nowrap` to prevent height jumps between tabs
- Reserve Room page renamed to "Reserve Sport Area" throughout all visible UI text
- `PageSpec` tab name updated to `"Reserve Sport Area"` to match `nav_panel` title (fixes blank page on navigation)

### Fixed
- Plotly/chart diagrams blank on first Dashboard visit — fixed by firing `window.resize` event on `shown.bs.tab`
- Dropdown menus (Psychical Tests, Cross/Runs, Admin) hidden after navbar height fix — resolved by setting `overflow: visible` on navbar collapse
- Reservation form overlay broken after inline `<style>` block removal — CSS classes renamed to non-conflicting `wf-overlay-*` names
- Login error message (wrong password / rate limit) not visible in modal — replaced CSS `:empty` trick with server-side `ui.output_ui`

### Removed
- 220-line inline `<style>` block from `reserve_fitness_room.py` — all styles consolidated into `custom.css`

---

## [2026-03-19] - Argon2id Migration & Docker Volume Fix

### Security
- Migrate password hashing from bcrypt to Argon2id (memory-hard, resistant to GPU/ASIC attacks); cost parameters tuned for production
- Remove `bcrypt` and `passlib` dependencies; replace with `argon2-cffi`
- Update authentication logic to verify Argon2id hashes

### Changed
- Update `test_data.sql` and SQL migration scripts to use Argon2id hashed passwords

### Fixed
- Remove read-only (`ro`) restriction from Docker volume mounts in deploy scripts; config file at `/etc/WarriorFit/config.yml` is now writable, resolving `[Errno 30] Read-only file system` error when saving settings from the UI

---

## [2026-03-18] - Security Hardening & Test Data Cleanup

### Security
- Remove Fernet symmetric encryption entirely from codebase and dependencies (`cryptography` package dropped)
- Migrate all password storage to bcrypt one-way hashing (cost factor 12); no plaintext-recovery path remains
- Fix `AuditLog.user_id` nullable: failed login attempts (unauthenticated) now persist to `audit_logs` without crash
- Capture real client IP (X-Forwarded-For aware) in audit log for login and login_failed events
- Remove `decrypt_password()` exposure from user management list view
- Password field no longer pre-filled from database row when editing a user

### Added
- `SECURITY.md`: full authentication flow, RBAC matrix, cryptography table, OWASP Top 10 assessment, and open issues tracker
- Alembic migration `a1b2c3d4e5f6`: make `audit_logs.user_id` nullable
- `warriorfit/data/scripts/update_passwords.sql`: migrate legacy non-bcrypt password hashes to bcrypt

### Changed
- `test_data.sql`: all seeded users now use a real bcrypt hash; Fernet and Argon2 placeholders removed
- Editing a user without supplying a new password now preserves the existing hash

### Removed
- `cryptography` dependency removed from `pyproject.toml`

---

## [2026-02-24] - Documentation Refactoring & Refresh Buttons

### Added
- Add refresh button (🔄) to all pages with DataGrids (15+ pages): PHEF, Combat, Swimming, Functional, March, Cross, Cross Planning, Cross Statistics, Sessions, User Management, Individual Test History, Status Unit, Audit Logs, Status Login, Dashboard
- Add vertical spacing (`my-2`) to all refresh buttons for consistent UI

### Changed
- Rewrite `stories.md`: 15 epics aligned with actual Python Shiny application; remove REST API / HRM POST / Excel export / Redis references; fix roles (PTI, APTI, admin only — remove Planner/Guest roles); rename HRM integration to BEMIL Personnel Lookup; add Calendar Events, Fitness Room Reservation, Audit Logs, Welcome Dashboard epics
- Rewrite `testcases.md`: replace API tests with Shiny UI interaction tests; add test sections for Calendar, Fitness Room, Audit Logs, Welcome Dashboard; add cross-cutting tests for security, reactive state, and refresh button consistency
- Refactor `Design.md` to conform with `stories.md`: fix roles section (3 roles: PTI, APTI, admin with correct tab lists), update Section 4.6 to describe BEMIL integration instead of REST API, replace FastAPI reference with Shiny for Python + shiny_calendar, update all story tables (15 epics with correct numbering and point totals)

---

## [2026-02-22] - Security Audit & Password Improvements

### Added
- Add password strength validation on user creation and edit (PR #191)
- Add password reveal/hide toggle button on all password fields

### Fixed
- Fix bug where password field was displaying the bcrypt hash in plain text (PR #193, #194)

### Security
- Security audit: review and harden secret handling, input validation, and role-based access controls
- Update README: remove sensitive credentials from documentation

### Changed
- Update deploy configuration

---

## [2026-02-15] - Deploy & Development Updates

### Added
- Add development auto-login feature for local development workflow

### Changed
- Update `deploy.sh`: improvements to container startup and configuration

---

## [2026-02-14] - Documentation & Cross App Updates

### Added
- Add architectural structure document (`ARCHITECTURE.md`)
- Add DI usage guide (`DI_USAGE_GUIDE.md`)
- Add changelog (`CHANGELOG.md`)
- Update cross app documentation with screenshots and expanded content

### Fixed
- Bug fix in `container.py` (DI wiring)

## [PR #188] - 2026-02-13 - Dependency Injection Refactoring

### Changed
- Refactor to integrate Dependency Injection via `Container` using `dependency-injector` library
- Replace hard-coded service instantiation with `Provide` annotations
- Simplify constructors across controllers and services for enhanced testability and maintainability
- Inject `NotifyMail` and `ReportGeneratorPdf` dependencies across services and controllers
- Replace direct instantiations with DI-managed singletons
- Update all 21 pages to use `@inject` with `Provide[Container.xxx_controller]`
- Fix `Gender` literal type issue

## [Unreleased] - 2026-02-11

### Changed
- Refine exception handling across the codebase, replace broad `Exception` blocks with specific error types
- Enhance logging precision and update SQL server default functions for consistency
- Introduce `ServiceMenSchema` for data validation
- Refactor `_build_serviceman` for robustness
- Enhance logging precision, improve error handling in `worker` loop
- Optimize message processing in `broker.py` for better maintainability and robustness

### Removed
- Remove unused dependencies (`rsconnect-python` and `shiny`) from `requirements.txt`

## [PR #186] - 2026-02-09 - Config File in Production

### Changed
- Refactor `Functional_calculator.py` by removing redundant constructor
- Reformat docstrings for clarity and align data structures with PEP 8 standards
- Update installation guide for environment-specific configurations
- Refine Docker deployment steps
- Enhance YAML handling in `ApplicationConfig`

### Fixed
- Bug fixes in `Functional_calculator.py`

## [2026-02-07] - Authentication & Documentation Updates

### Changed
- Expand `password_hash` column size to 255 characters
- Improve bcrypt hashing logic and update test data for consistency
- Revise deployment steps in Readme for OAuth2 and SSL certificate integration
- Add detailed docstrings to `app.py` effects for improved documentation and code maintainability

### Removed
- Remove outdated `server_archicteture.html`
- Correct formatting in `SECURITY.md`

## [2026-02-06] - Documentation & Configuration Improvements

### Added
- Add detailed docstrings for `MarchService` methods
- Add detailed docstrings to `ApplicationConfig` class
- Add detailed docstrings for `Os.is_alive` and `IntEnumType` methods
- Add detailed docstring to `ABCRepository`
- Document deployment process in Readme: add cron and GitHub actions

### Changed
- Update `config_test.yml`: set default email sender to `noreplay.benoit@albatros.be`
- Improve YAML file handling with UTF-8 encoding
- Docstring improvements across controllers and models
- Format method parameters for readability and align with PEP 8 standards
- Update dependencies in `uv.lock` and `pyproject.toml`
- Document `FunctionalCalculator` class in detail

### Removed
- Remove `FileService`
- Update parameter type for `details` in `ABCRepository`

### Fixed
- Improve logging precision and handle `SQLAlchemyError` exceptions

## [2026-02-05] - Error Handling & Documentation

### Added
- Add detailed docstrings for logging setup, page specifications, role-based page filtering, and navigation server logic

### Changed
- Handle specific exceptions for input and logging operations
- Add fallback logging for config errors

## [2026-02-04] - Deployment Automation & Documentation

### Added
- Add pre-commit hook to auto-update `version.yaml`
- Document pre-commit hook for versioning in Readme.md
- Add detailed docstrings for exercise scoring methods in `Functional_calculator.py`

### Changed
- Fix `auto-deploy.sh`: externalize log file path, add missing bracket for valid syntax
- Improve logging structure
- Update `auto-deploy.sh`: adjust log file path to `/home/benoit/log/deploy.log`

### Security
- Redact sensitive credentials in Readme.md

## [2026-02-03] - Auto-Deployment & Versioning

### Added
- Add `GH_TOKEN` environment variable to `auto-deploy.sh`
- Load version details from `version.yaml` and integrate into configuration initialization

### Changed
- Improve `auto-deploy.sh`: enable strict error handling, externalize token storage, and enhance logging
- Update `GH_TOKEN` value in `auto-deploy.sh`

### Removed
- Remove `post-commit` hook script
- Remove extraneous blank lines in `status_login_user.py`

### Fixed
- Fix punctuation in status messages on login page

## [PR #180] - Add Search Button for Serial on User Management

### Added
- Add search functionality for serial numbers in user management interface

### Changed
- UI enhancements for search functionality

## [PR #178] - Redesign Cross Statistics

### Changed
- Redesign cross statistics interface and functionality

## [PR #175] - Add Search Button on Individual History

### Added
- Add search button functionality on individual history page

## [PR #173] - UI Enhance Search Button

### Changed
- UI enhancements for search button across application

## [PR #166] - Add Mail Server Check on Status Page

### Added
- Add mail server connectivity check on status page

## [PR #162] - Search Button

### Added
- Add search button functionality to application

## [PR #156] - Testing Alpha1

### Changed
- Alpha testing improvements and bug fixes

## [PR #155] - Bug: Not Refresh After CRUD

### Fixed
- Fix refresh issue after CRUD operations

## [PR #147] - Bug: March

### Fixed
- Fix bugs in march functionality

## [PR #146] - Bug: View Sessions

### Fixed
- Fix bugs in session view functionality

## [PR #142] - ServiceMen FK

### Changed
- Update foreign key relationships for ServiceMen

## [PR #139] - Bug: Cross No Attribute Name

### Fixed
- Fix attribute name issue in cross functionality

## [PR #135] - Status Application Page

### Added
- Add status application page

## [PR #131] - Epic: Room Reservation

### Added
- Add room reservation functionality

## [PR #129] - Docstring

### Added
- Add comprehensive docstrings across the codebase

---

## Categories

### Added
New features and capabilities added to the project.

### Changed
Changes to existing functionality.

### Deprecated
Features that will be removed in upcoming releases.

### Removed
Features removed in this release.

### Fixed
Bug fixes.

### Security
Security-related changes.
