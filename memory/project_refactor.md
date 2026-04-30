---
name: Code quality refactor branch
description: refactor/code-quality branch — naming fixes, app.py split, notify_mail move
type: project
---

Branch `refactor/code-quality` (off develop) contains a code quality refactor:
- Fixed 5 filename typos: appliccation_config→application_config, usermangement→usermanagement, mom_repositor→mom_repository, cross_plannig_controller→cross_planning_controller, StatusApplicationController→status_application_controller (plus all import references updated)
- Fixed "Psychical Tests" → "Physical Tests" in navbar group label
- Split monolithic 1023-line app.py into: warriorfit/ui/page_registry.py (PageSpec + page list), warriorfit/ui/app_server.py (build_app_ui + make_server factory), warriorfit/app.py (minimal entry point)
- Moved notify_mail.py from ui/pages/ to services/

**Why:** Align codebase with project_proposel.md design doc; improve maintainability
**How to apply:** When working on auth/session logic look in app_server.py; page RBAC config lives in page_registry.py; all 141 tests pass on this branch
