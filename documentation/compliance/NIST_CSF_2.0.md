# NIST Cybersecurity Framework 2.0 — WarriorFit Self-Assessment

> Last reviewed: 2026-04-30 (rev. 2 — TLS to PostgreSQL closed; GDPR retention now explicit in all envs)
> Framework: NIST CSF 2.0 (released 2024)
> Scope: WarriorFit application, build pipeline, and supporting governance artifacts in this repository

## Tier Summary

Self-assessed implementation tier per CSF 2.0 (Tier 1 Partial → Tier 4 Adaptive):

| Function     | Tier | Trend |
|--------------|------|-------|
| GOVERN (GV)  | 2 — Risk Informed | improving |
| IDENTIFY (ID)| 2 — Risk Informed | improving |
| PROTECT (PR) | 3 — Repeatable    | stable    |
| DETECT (DE)  | 2 — Risk Informed | gaps      |
| RESPOND (RS) | 1 — Partial       | gaps      |
| RECOVER (RC) | 1 — Partial       | gaps      |

## GOVERN (GV)

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| GV.OC — Organizational Context | Partial | `Readme.md`, `ARCHITECTURE.md`, `documentation/project_proposel.md` | Mission/stakeholder mapping informal |
| GV.RM — Risk Management Strategy | Partial | `SECURITY.md` "Open Issues" prioritized P1/P2/P3 | No documented risk appetite or acceptance criteria |
| GV.RR — Roles, Responsibilities, Authorities | Partial | `CODEOWNERS`, `documentation/authors.md` | Single-owner project; no separation of duties |
| GV.PO — Policy | Partial | `SECURITY.md`, `documentation/compliance/PRIVACY_POLICY.md`, `LICENSE` | No incident response policy, no acceptable use policy |
| GV.OV — Oversight | Weak | PR review via `CODEOWNERS` | No periodic security review cadence |
| GV.SC — Cybersecurity Supply Chain Risk | Partial | `pip-audit`, `bandit` in `python3-app.yml` | No SBOM produced, no image signing (A08), unused dep `python-jose` (A06) |

**Priority gaps:** documented risk acceptance, incident-response policy, SBOM generation.

## IDENTIFY (ID)

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| ID.AM — Asset Management | Good | `ASSETS.md`, `ARCHITECTURE.md`, `pyproject.toml`, `uv.lock` | Hardware/host inventory not tracked here |
| ID.RA — Risk Assessment | Good | `SECURITY.md` OWASP Top 10 + Open Issues table | No threat model document (STRIDE/LINDDUN) |
| ID.IM — Improvement | Partial | `SECURITY.md` is dated and tracked; `documentation/evolution.md` | No lessons-learned log or post-incident reviews (no incidents recorded) |

**Priority gaps:** threat model, host/runtime inventory, formal lessons-learned log.

## PROTECT (PR)

Strongest function. RBAC, modern hashing, parameterized ORM, TLS planned.

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| PR.AA — Identity Mgmt, Auth, Access Control | Good | RBAC across 6 roles, Argon2id (`security/auth_service.py`), rate limiter (`security/rate_limiter.py`), session inactivity 10 min | UI-only enforcement (A01); dev auto-login bypass (A01); no MFA (A07); rate limiter in-memory (A07) |
| PR.AT — Awareness & Training | None | — | No documented developer security training |
| PR.DS — Data Security | Good | Argon2id at rest for credentials; `audit_logs` table; TLS to PostgreSQL (`verify-full` in prod via `db.ssl`); GDPR retention windows declared explicitly per environment in YAML | No field-level encryption for PII at rest |
| PR.PS — Platform Security | Good | Dockerized deploy, secrets via env (`WF_SECRET_KEY`), pre-commit hooks, ruff/mypy/black in CI | Image not signed (A08); base image patch cadence not documented |
| PR.IR — Technology Infrastructure Resilience | Partial | Async broker with outbox + retry + dead-letter (`warriorfit/mom/broker.py`); `UserStore` now per Shiny session (PR #217) | No documented HA/DR posture |

**Priority gaps:** persistent rate limiter, dev-mode guard, MFA for ADMIN, image signing.

**Resolved 2026-04-30:** TLS to PostgreSQL (`db.ssl=verify-full` in prod).
**Resolved 2026-05-10:** MOM API authenticated (`X-API-Key` / `WF_MOM_API_KEY`, fail-closed); IDOR guard on test deletes (`services/service_test.py`); `UserStore` scoped per Shiny session; GUEST role no longer reaches "Status Unit" / "Individual" pages.

## DETECT (DE)

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| DE.CM — Continuous Monitoring | Partial | `audit_logs` records `login`, `login_failed`, CRUD; client IP captured for login | Logout events not audited (A09); CRUD missing client IP (A09); no centralized log shipping; no alerting |
| DE.AE — Adverse Event Analysis | Weak | Audit trail queryable in DB | No SIEM, no anomaly detection, no on-call rotation |

**Priority gaps:** ship logs off-host, alert on `login_failed` spikes / lockout events, audit logout.

## RESPOND (RS)

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| RS.MA — Incident Management | None | — | No IR runbook, no severity matrix, no on-call |
| RS.AN — Incident Analysis | Partial | `audit_logs` provides forensic trail for login events | No documented analysis procedure |
| RS.CO — Incident Communication | None | — | No notification/escalation list (CODEOWNERS exists but is review routing, not IR) |
| RS.MI — Incident Mitigation | None | — | No documented containment / kill-switch procedure |

**Priority gaps:** IR runbook, severity classification, contact tree, kill-switch (block-user / disable-login).

## RECOVER (RC)

| Category | Coverage | Evidence | Gap |
|----------|----------|----------|-----|
| RC.RP — Incident Recovery Plan Execution | None | — | No documented recovery plan; no RTO/RPO targets |
| RC.CO — Recovery Communication | None | — | No stakeholder template / status page |

**Priority gaps:** documented backup/restore procedure for PostgreSQL, RTO/RPO statement, restore drill cadence.

## Top 10 Gaps (cross-function, prioritized)

These are the highest-leverage items to lift the overall posture. They map to existing OWASP P1/P2 issues where applicable.

| # | Function     | Action                                                            | Maps to            |
|---|--------------|-------------------------------------------------------------------|--------------------|
| 1 | PR.AA        | Persistent rate limiter (Redis or DB-backed)                      | OWASP A07 (P1)     |
| 2 | PR.AA        | Guard dev auto-login (hostname / required env-secret check)       | OWASP A01 (P1)     |
| 3 | PR.IR        | `aiohttp.ClientTimeout` + URL allowlist on HR status check        | OWASP A10 (P1)     |
| 4 | RS.MA        | Write `documentation/compliance/INCIDENT_RESPONSE.md` (severity, contacts, runbook) | new |
| 5 | RC.RP        | Document PostgreSQL backup & restore procedure with RTO/RPO       | new                |
| 6 | DE.CM        | Audit logout events; thread client IP through CRUD audit calls    | OWASP A09 (P2)     |
| 7 | GV.SC        | Generate SBOM in CI (`cyclonedx-py` or `syft`); sign Docker image | OWASP A08 (Info)   |
| 8 | ID.RA        | Add a threat model document (STRIDE per page)                     | new                |
| 9 | PR.AA        | TOTP MFA for ADMIN role                                           | OWASP A07 (P3)     |
|10 | PR.DS        | Field-level encryption for PII at rest (birthdate, name, scores)  | DPIA residual      |

### Closed since rev. 1
- TLS on PostgreSQL connection (was Top-10 #1) — `db.ssl=verify-full` in prod via `_build_db_ssl()` in `application_config.py`.

## Mapping Notes

- "OWASP …" references are the existing findings tracked in `SECURITY.md` "Open Issues" — fixing those advances PROTECT/DETECT tiers without new analysis.
- This assessment intentionally separates GOVERN gaps (policy/process) from PROTECT gaps (controls). GOVERN gaps are addressable with documents already partially scaffolded in `documentation/compliance/` (DPIA, Privacy Policy).
- Tiers are self-assessed for a single-maintainer codebase; an organization with formal SOC/IR functions would re-baseline DETECT/RESPOND/RECOVER higher.
