# Privacy Notice — WarriorFit

**Version:** 1.0 · **Effective:** 2026-04-24

## Who we are

WarriorFit is operated by the Belgian Defence (Land Component). The
Data Controller is your unit's command, assisted by the Defence Data
Protection Officer.

## What we collect

- **Identity data:** username, email, service number, rank, unit
- **Demographic data:** first name, last name, birthdate, gender
- **Health data (GDPR Art. 9):** physical fitness test results, pass/fail outcomes, qualifications (para, ops_test)
- **Technical data:** IP address, login timestamps, audit trail of actions performed in the application

## Why we process it

| Purpose | Legal basis |
|---|---|
| Fitness test scoring & planning | Art. 6(1)(c) + Art. 9(2)(b) — legal obligation under military training regulations |
| Account management & access control | Art. 6(1)(c) |
| Security audit & incident response | Art. 6(1)(f) — legitimate interest |
| Health-data processing | Art. 9(2)(b) and, where granted, Art. 9(2)(a) explicit consent |

## How long we keep it

| Category | Retention |
|---|---|
| Fitness tests, marches, reservations | 5 years |
| Audit logs | 1 year |
| HR integration messages | 90 days |
| Consent records | Life of account + legal-proof window |

## Who receives it

Data never leaves the Defence intranet. The internal HR system is the
only downstream recipient, via a rate-limited async broker.

## Your rights

You can exercise the following rights directly from the **Privacy**
page once logged in:

- **Access / Portability (Art. 15, 20):** download a JSON copy of all your data.
- **Erasure (Art. 17):** permanently delete your account and all associated records.
- **Consent (Art. 7):** grant or withdraw consent for each processing purpose.

For **rectification (Art. 16)** and **restriction (Art. 18)** requests
that cannot be handled via self-service, contact your unit admin.

## Security

- Passwords: Argon2id (time=3, memory=64 MB, parallelism=4)
- Access control: role-based (ADMIN, PTI, APTI, PLANNER, USER, GUEST)
- Session: 10-minute inactivity timeout, rate-limited login (5 attempts / 15 min lockout)
- Audit: every create/update/delete, login, logout, consent change is logged

## Contact

- Your unit admin (first line)
- Defence DPO — see intranet directory entry *DPO*

## Changes to this notice

Material changes will bump the version and re-trigger consent prompts
on next login.
