# Changelog

All notable changes to the WarriorFit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
