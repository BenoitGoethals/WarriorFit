# Data Protection Impact Assessment (DPIA) — WarriorFit

**Document version:** 1.1
**Date:** 2026-04-30
**Controller:** Belgian Defence (Land Component — 3 Para)
**System:** WarriorFit — Military Physical Fitness Test Digitization Platform
**Deployment:** Intranet only (no public Internet exposure)

## 1. Why a DPIA is required

WarriorFit processes **special-category personal data** under GDPR
Art. 9(1) — specifically, health-related fitness test results of
military personnel (physical capabilities, injuries derivable from
performance, medical deferrals). Art. 35(3)(b) mandates a DPIA when
processing special-category data on a large scale.

## 2. Systematic description of processing

| Item | Description |
|---|---|
| Purpose | Track, score and plan mandatory physical fitness tests (PHEF, Combat, Swim, Functional, March, Cross) for active military personnel |
| Nature | Collection, storage, scoring, reporting, scheduling |
| Scope | All servicemen of the unit (~hundreds per deployment) |
| Context | Deployed on the unit's internal network, restricted to authenticated users |
| Legal basis (Art. 6) | Art. 6(1)(c) — legal obligation (military training regulations) and Art. 6(1)(e) — public interest |
| Special-category basis (Art. 9) | Art. 9(2)(b) — necessary for obligations in employment and social security law |

## 3. Categories of personal data

- **Identity:** first name, last name, service number, email
- **Demographic:** birthdate (→ age), gender, rank, unit
- **Health (Art. 9):** fitness test scores, pass/fail outcomes, fitness-related medical aptitudes (`para`, `ops_test` flags)
- **Technical:** IP address (audit), login timestamps, session activity

## 4. Data flow

```
Serviceman → PTI (instructor) → WarriorFit UI → PostgreSQL
                                            ↘
                                             HR integration (async broker)
```

No data leaves the intranet. No third-party processors except the
internal HR system reachable via the `hr_url` allowlist.

## 5. Risks identified and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Unauthorized read of health data | Medium | High | RBAC (6 roles), Argon2id password hashing, 10-min inactivity timeout, rate-limited login |
| Insider abuse | Medium | High | Audit log of all CRUD actions + login/logout events (Art. 32) |
| Retention creep | High | Medium | Automated retention purge (`RetentionService`), configurable per category |
| Lack of lawful basis for health data | Medium | Critical | Explicit consent table (`user_consents`), Art. 9(2)(a) fallback |
| Data-subject rights not honored | High | High | Self-service Privacy page (export, erase, consent management) |
| DB breach (theft of backup) | Low | High | Platform admin scope: full-disk encryption, encrypted backups, restricted DB account |
| TLS absent on DB transport | Low (intranet) | Medium | TLS configurable per environment via `db.ssl` (`disable`/`prefer`/`require`/`verify-ca`/`verify-full`) and `db.ssl_root_cert`. Production set to `verify-full` against `/etc/WarriorFit/pg-ca.pem`. Dev/test default `prefer`. |
| TLS absent on outbound HTTP (HR) | Low (intranet) | Medium | Platform admin scope: unit firewall + VLAN isolation; HTTPS + URL allowlist on HR endpoint is open work (OWASP A10) |
| Orphan PII after user deletion | Previously high | — | FK `ON DELETE CASCADE` on `service_men.user_id`; application-level cascade in `GdprService.erase_user` |

## 6. Data subject rights implemented

| Right | Article | Implementation |
|---|---|---|
| Information | Art. 13 | `documentation/compliance/PRIVACY_POLICY.md` + in-app Privacy page |
| Access | Art. 15 | `GdprService.export_user_data` → JSON download |
| Rectification | Art. 16 | Admin-mediated via User Management; user-facing edit form is future work |
| Erasure | Art. 17 | `GdprService.erase_user` — cascades across User, ServiceMen, FitnessTest, March, Reservation, UserConsent |
| Portability | Art. 20 | Same JSON export (machine-readable) |
| Consent mgmt | Art. 7 | `user_consents` table + `ConsentService` grant/withdraw |

## 7. Retention schedule

| Category | Retention | Justification |
|---|---|---|
| Fitness tests | 5 years after execution (1825 days) | Aligned with military training record retention |
| Marches | 5 years | Same |
| Reservations | 5 years | Same |
| Audit logs | 1 year (365 days) | Security monitoring window |
| HR broker messages | 90 days | Transient integration data |
| Consent records | Lifetime of account + legal-proof window | GDPR Art. 7(1) requires demonstrability |

Configurable per environment via the `gdpr:` block in `config.yml`,
`config_dev.yml`, `config_test.yml`, and `config_prod.yml`. All
environments now declare retention windows explicitly (no implicit
defaults) so audit reviewers can verify the active values without
reading code.

## 8. Residual risks

- **TLS to HR system** still HTTP — open work (OWASP A10): add HTTPS + URL allowlist + request timeout.
- **No column-level encryption at rest** for birthdate/name/scores. Accepted risk given intranet-only deployment and DB full-disk encryption at OS level.
- **No automated DPIA review cadence** — recommend annual review or on schema change.

### Resolved since v1.0
- **TLS to PostgreSQL** — `verify-full` enforced in production via `db.ssl` config (2026-04-30).

## 9. Sign-off

| Role | Name | Date |
|---|---|---|
| DPO | _pending_ | _pending_ |
| Project Owner | _pending_ | _pending_ |
| Security Officer | _pending_ | _pending_ |

---

**Next review:** 2027-04-24 or on material change (new data category, new processor, scope extension).
