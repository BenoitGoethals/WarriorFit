# Changelog

All notable changes to the WarriorFit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
