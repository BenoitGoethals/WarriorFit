# Security Documentation — WarriorFit

> Last reviewed: 2026-03-19

## Table of Contents
1. [Authentication Flow](#authentication-flow)
2. [Authorization Model](#authorization-model)
3. [Cryptography](#cryptography)
4. [Password Storage](#password-storage)
5. [Session Management](#session-management)
6. [Rate Limiting](#rate-limiting)
7. [Audit Logging](#audit-logging)
8. [OWASP Top 10 Assessment](#owasp-top-10-assessment)
9. [Open Issues](#open-issues)

---

## Authentication Flow

```
User loads app
      │
      ▼
login_dialog() triggered (app.py)
      │
      ├── APP_ENV == "development" → inject synthetic ADMIN user, skip auth entirely
      │
      └── production / test
             │
             ▼
         Modal login form (username + password)
             │
             ▼ input.handle_login event
         Username lowercased
             │
             ▼
         LoginRateLimiter.is_locked(username)
             │ locked → display lockout message, abort
             │
             ▼
         Read client IP (X-Forwarded-For → client.host fallback)
             │
             ▼
         UserService.check_user(username, password)
           └── UserRepository.check_user()
                 └── SELECT User WHERE username = ? (parameterized ORM)
                       └── await Auth.verify_password(plain, stored_hash)
                             └── argon2.PasswordHasher.verify() via asyncio.to_thread()
             │
             ├── FAIL ──► LoginRateLimiter.record_failure()
             │            audit_log: action="login_failed", ip=client_ip, user_id=NULL
             │            display remaining attempts or lockout message
             │
             └── SUCCESS
                   │
                   ├── user.is_active == False → abort with message
                   │
                   ▼
               LoginRateLimiter.reset(username)
               UserStore.set_user(user)         ← singleton process-wide store
               session.user = user              ← per-session Shiny object
               audit_log: action="login", ip=client_ip, user_id=user.id
               Modal dismissed — navbar rebuilt for user's role
```

---

## Authorization Model

Authorization is **role-based (RBAC)** enforced at the UI layer in `app.py`.

### Roles

| Role      | Description                                     |
|-----------|-------------------------------------------------|
| `ADMIN`   | Full access: user management, settings, audit   |
| `PTI`     | Physical training instructor                    |
| `APTI`    | Assistant PTI                                   |
| `PLANNER` | Session planning only                           |
| `GUEST`   | Read-only access to unit status and individuals |
| `USER`    | Defined, not currently assigned to any page     |

### Page Access Matrix

| Page / Feature                                      | ADMIN | PTI | APTI | PLANNER | GUEST |
|-----------------------------------------------------|:-----:|:---:|:----:|:-------:|:-----:|
| Welcome                                             | ✓     | ✓   | ✓    |         |       |
| Dashboard                                           | ✓     | ✓   | ✓    |         |       |
| Status Unit                                         | ✓     | ✓   | ✓    |         | ✓     |
| Individual                                          | ✓     | ✓   | ✓    |         | ✓     |
| Reports                                             | ✓     | ✓   | ✓    |         |       |
| Reserve Room                                        | ✓     | ✓   | ✓    |         |       |
| Sessions                                            | ✓     | ✓   | ✓    | ✓       |       |
| PHEF / Combat / Functional / Swimming / March Tests | ✓     | ✓   | ✓    |         |       |
| Cross / Cross Planning / Cross Statics              | ✓     | ✓   | ✓    |         |       |
| Audit Logs                                          | ✓     |     |      |         |       |
| User Management                                     | ✓     |     |      |         |       |
| Settings                                            | ✓     |     |      |         |       |
| Status Application                                  | ✓     |     |      |         |       |

### Enforcement Mechanism

`FitnessWarriorApp._pages_for_role(role)` filters the `PageSpec` list at navbar build
time. Only pages whose `allowed_roles` set contains the user's role are rendered and
server-registered. **There is no backend middleware guard** — access control relies
entirely on Shiny server-side rendering not exposing UI elements to unauthorized users.

---

## Cryptography

### Key Material

| Secret          | Source                         | Usage                                         |
|-----------------|--------------------------------|-----------------------------------------------|
| `WF_SECRET_KEY` | Environment variable (runtime) | Required at startup; injected via `docker run -e` |

`WF_SECRET_KEY` is intentionally not baked into the Docker image. The `ARG` / `ENV`
directive exists in the Dockerfile but the comment explicitly warns against supplying
it at build time.

### Algorithms in Use

| Purpose          | Algorithm                              | Library               | Status   |
|------------------|----------------------------------------|-----------------------|----------|
| Password hashing | Argon2id (time=3, mem=64 MB, p=4)      | `argon2-cffi >= 23.1` | Active   |

---

## Password Storage

### Scheme — Argon2id

All passwords are stored as Argon2id hashes via `Auth.hash_password()`:

```python
_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
await asyncio.to_thread(_ph.hash, password)
```

- One-way hash — plaintext is not recoverable.
- Salt generated per-password by `argon2-cffi` internally.
- Parameters: time_cost=3 iterations, memory_cost=64 MB, parallelism=4 lanes.
- Hash prefix: `$argon2id$v=19$...`
- Stored in `users.password_hash VARCHAR(255)`.
- CPU work offloaded to thread pool via `asyncio.to_thread()` — event loop is never blocked.

Verification via `Auth.verify_password()`:

```python
await asyncio.to_thread(_ph.verify, stored_hash, plain_password)
```

> **Migration note:** Any accounts created before the Argon2id migration still have
> bcrypt or Fernet values in `password_hash`. Run `update_passwords.sql` to migrate
> all non-Argon2id hashes to the test-reset hash, then have users set a new password.
> Find legacy accounts with: `SELECT * FROM users WHERE password_hash NOT LIKE '$argon2id$%'`

### Password Complexity Policy

Enforced at creation and password-change via `UserManagementController.validate_password()`:

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

---

## Session Management

| Property           | Detail                                                                          |
|--------------------|---------------------------------------------------------------------------------|
| Session store      | Shiny server-side session object (`session.user`)                               |
| Global user store  | `UserStore` singleton — one value per process                                   |
| Inactivity timeout | 10 minutes (`time.time() - ts >= 600`, polled every 5 s)                        |
| Activity tracking  | JS events: `click`, `keydown`, `mousemove`, `scroll`, `touchstart`, `touchmove`, `visibilitychange` |
| Logout             | Clears `session.user`, JS `location.reload()` after 100 ms                     |
| Dev bypass         | `APP_ENV=development` auto-injects ADMIN user — authentication skipped entirely |

### Auto-logout Flow

```
reactive.invalidate_later(5)  ← every 5 seconds
      │
      ▼
time.time() - last_activity >= 600 ?
      │ yes
      ▼
_clear_session_user()
ui.notification_show("logged out due to inactivity")
location.reload()
```

---

## Rate Limiting

Implemented in `warriorfit/security/rate_limiter.py` as an **in-memory** store.

| Parameter    | Value               |
|--------------|---------------------|
| Max attempts | 5                   |
| Window       | 15 minutes (900 s)  |
| Lock scope   | Per username        |
| Storage      | Process memory only |
| Reset        | On successful login |

```
Attempts 1–4 → "Invalid username or password. N attempt(s) remaining."
Attempt 5    → "Too many failed attempts. Account locked for N minute(s)."
After window → Automatic unlock (sliding window pruning)
```

**Known limitation:** State is not persisted. A process restart resets all counters.
In a multi-instance deployment, each instance maintains independent counters.

---

## Audit Logging

All security events and user CRUD operations are written to the `audit_logs` table.

```
audit_logs
  id          INTEGER PK
  user_id     INTEGER FK → users.id   NULLABLE (NULL for unauthenticated events)
  action      VARCHAR(50)
  details     JSON
  ip_address  VARCHAR(45)             real client IP (X-Forwarded-For aware)
  created_at  TIMESTAMP               server default
```

### Logged Events

| Event                | action         | user_id          | ip_address    |
|----------------------|----------------|------------------|---------------|
| Successful login     | `login`        | authenticated id | client IP     |
| Failed login attempt | `login_failed` | NULL             | client IP     |
| User created         | `add`          | acting admin id  | NULL (CRUD)   |
| User updated         | `update`       | acting admin id  | NULL (CRUD)   |
| User deleted         | `delete`       | acting admin id  | NULL (CRUD)   |

> **Note:** Logout events (manual and inactivity) are not currently audited.
> CRUD operations record user_id via `UserStore` but do not capture client IP.

---

## OWASP Top 10 Assessment

### A01 — Broken Access Control

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | UI-only enforcement | Medium | `app.py:296` | `_pages_for_role()` filters which panels are rendered; no server-side guard on reactive handlers. A WebSocket-level adversary could invoke handlers for pages they are not authorized to see. |
| 2 | `UserStore` singleton | Low | `ui/user_store.py` | One value per process. In standard single-worker Shiny deployment this is acceptable; concurrent sessions in the same process would share the same singleton. |
| 3 | Dev auto-login bypass | Medium | `app.py:559` | `APP_ENV=development` auto-injects a synthetic ADMIN session with no credentials and no hostname/key guard. If set accidentally on a production host, authentication is completely bypassed. |

### A02 — Cryptographic Failures

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | Argon2id hashing active | Resolved | `security/auth_service.py` | `argon2-cffi` `PasswordHasher` (time=3, mem=64MB, p=4). Passwords not recoverable. CPU work offloaded via `asyncio.to_thread()`. |
| 2 | `decrypt_password()` removed | Resolved | — | No plaintext-recovery path exists. |
| 3 | Fernet and bcrypt removed | Resolved | — | `cryptography` and `bcrypt` dependencies dropped. No reversible encryption in auth stack. |
| 4 | Legacy bcrypt/Fernet values in DB | Residual / Low | DB: `users.password_hash` | Accounts created before migration cannot log in (Argon2id rejects foreign hash formats). Run `update_passwords.sql` to force-reset, then have users change their password. |
| 5 | Dead auth constants removed | Resolved | `security/auth_service.py` | `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `oauth2_scheme` have been removed. |

### A03 — Injection

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | SQL injection | Low | `data/repositories/` | All queries use SQLAlchemy ORM parameterized expressions. No raw SQL strings found. |

### A04 — Insecure Design

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | Reversible passwords eliminated | Resolved | — | `hash_password()` is one-way Argon2id. No admin recovery mechanism. |
| 2 | Dev auto-login (see A01-3) | Medium | `app.py:559` | Covered above. |

### A05 — Security Misconfiguration

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | No TLS on PostgreSQL connection | Medium | `config/appliccation_config.py:202` | `create_async_engine()` builds the connection URL without `ssl=True` or `sslmode=require`. Database traffic is unencrypted in transit. |
| 2 | `WF_SECRET_KEY` at build time | Low | `Dockerfile:17` | `ARG WF_SECRET_KEY` could bake the secret into an image layer if provided at `docker build` time. Must only be passed via `docker run -e`. |
| 3 | Config not bundled in image | Info | `Dockerfile` | `/etc/WarriorFit/config.yml` must be volume-mounted. Intentional design; must be in the deployment runbook. |

### A06 — Vulnerable and Outdated Components

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | `passlib` and `bcrypt` removed | Resolved | `pyproject.toml` | Both unused dependencies removed. |
| 2 | Unused dependency `python-jose` | Low | `pyproject.toml` | `python-jose>=3.5.0` is declared but never imported. Unnecessary attack surface. |
| 3 | Dependency audit | Info | `pyproject.toml` | Run `uv pip audit` or `pip-audit` regularly. Key packages to watch: `argon2-cffi`, `sqlalchemy`, `shiny`, `uvicorn`. |

### A07 — Identification and Authentication Failures

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | Argon2id hashing active | Resolved | `security/auth_service.py` | All new/updated passwords use Argon2id with per-password salts. bcrypt and Fernet removed. |
| 2 | In-memory rate limiter | Medium | `security/rate_limiter.py:14` | Not persisted across restarts. Bypassable by restarting the container. In multi-instance deployment each process has independent counters — an attacker spreads 5 attempts per instance. |
| 3 | No MFA | Low | — | Single-factor authentication only. No TOTP or hardware key support. |
| 4 | No password expiry | Low | — | Passwords have no expiry or rotation policy enforced. |
| 5 | Username timing oracle | Info | `data/repositories/user_repository.py:149` | "User not found" returns immediately (~0 ms); "wrong password" runs Argon2id (~400 ms via thread pool). A timing oracle can confirm username existence. A constant minimum response delay would eliminate this. |

### A08 — Software and Data Integrity Failures

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | No image signing | Info | — | Docker image integrity not verified at deployment. |

### A09 — Security Logging and Monitoring Failures

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | Failed logins persisted | Resolved | `app.py:634` | `login_failed` events written to `audit_logs` with client IP. |
| 2 | Real client IP captured | Resolved | `app.py:606` | `X-Forwarded-For` header read first, falls back to `session.http_conn.client.host`. |
| 3 | `audit_logs.user_id` nullable | Resolved | `data/model/db_model.py:41` | Migration `a1b2c3d4e5f6` drops NOT NULL — unauthenticated events can be logged. |
| 4 | Logout not audited | Low | `app.py:670,749` | Manual logout and inactivity auto-logout do not write to `audit_logs`. Session end events cannot be reconstructed forensically. |
| 5 | CRUD operations missing client IP | Low | `services/service.py:46` | `add_audit_log()` does not receive a client IP for CRUD calls (user create/update/delete). Only login events carry the real IP. |

### A10 — Server-Side Request Forgery (SSRF)

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| 1 | HR URL used without validation | Medium | `ui/controllers/StatusApplicationController.py:27` | `self._config.hr_url` is passed directly to `aiohttp.ClientSession.get()`. A tampered `config.yml` (via Settings page) could redirect requests to internal network targets. URL scheme and host should be validated against an allowlist. |
| 2 | No request timeout | Medium | `ui/controllers/StatusApplicationController.py:38` | `session.get(url)` has no `timeout` parameter. A slow or unresponsive server will block the coroutine indefinitely, potentially stalling the UI. Add `aiohttp.ClientTimeout(total=5)`. |

---

## Open Issues

| Priority | Severity | OWASP | Issue | Recommended Fix |
|----------|----------|-------|-------|-----------------|
| P1 | Medium | A05 | No TLS on PostgreSQL connection | Add `ssl=True` (or `connect_args={"ssl": ssl_ctx}`) to `create_async_engine()` |
| P1 | Medium | A07 | Rate limiter is in-memory only | Replace with Redis-backed or DB counter |
| P1 | Medium | A01 | Dev auto-login has no guard | Add a hostname or secret-presence check before activating dev bypass |
| P1 | Medium | A10 | HTTP request to HR URL has no timeout | Add `aiohttp.ClientTimeout(total=5)` to `_check_http_status()` |
| P1 | Medium | A10 | HR URL not validated against allowlist | Validate scheme (`https`) and host before making the request |
| P1 | Low | A02 | Legacy bcrypt/Fernet values still in DB | Run `update_passwords.sql`; find accounts with `password_hash NOT LIKE '$argon2id$%'` and force password reset |
| P2 | Low | A09 | Logout events not audited | Add `audit_log` call in `_on_logout_button_click()` and `_auto_logout_timer()` |
| P2 | Low | A09 | CRUD operations missing client IP | Thread client IP through `add_audit_log()` calls for user management actions |
| P2 | Low | A06 | Unused dependency `python-jose` | Remove from `pyproject.toml` |
| P3 | Low | A07 | No MFA | Integrate TOTP (e.g. `pyotp`) for ADMIN accounts at minimum |
| P3 | Low | A07 | No password expiry | Add `password_changed_at` column; enforce rotation in `validate()` |
| P3 | Info | A07 | Username timing oracle | Introduce a constant minimum delay in `check_user()` regardless of hit/miss |
