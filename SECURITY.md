# Security Documentation — WarriorFit

## Table of Contents
1. [Authentication Flow](#authentication-flow)
2. [Authorization Model](#authorization-model)
3. [Cryptography](#cryptography)
4. [Password Storage](#password-storage)
5. [Session Management](#session-management)
6. [Rate Limiting](#rate-limiting)
7. [Audit Logging](#audit-logging)
8. [OWASP Top 10 Assessment](#owasp-top-10-assessment)

---

## Authentication Flow

```
User loads app
      │
      ▼
login_dialog() triggered (app.py:556)
      │
      ├── APP_ENV == "development" → inject synthetic admin user, skip auth
      │
      └── production / test
             │
             ▼
         Modal login form shown (username + password)
             │
             ▼ input.handle_login event
         Username lowercased (app.py:595)
             │
             ▼
         LoginRateLimiter.is_locked(username) (rate_limiter.py:21)
             │ locked → display lockout message, abort
             │
             ▼
         UserService.check_user(username, password)
           └── UserRepository.check_user()
                 └── SELECT User WHERE username = ? (parameterized)
                       └── Auth.verify_password(plain, stored_hash)
                             ├── Try Fernet decrypt → compare
                             └── Fallback: bcrypt.checkpw (legacy)
             │
             ├── FAIL → LoginRateLimiter.record_failure()
             │          display remaining attempts or lockout message
             │
             └── SUCCESS
                   │
                   ▼
               user.is_active check → inactive → abort with message
                   │
                   ▼
               LoginRateLimiter.reset(username)
               UserStore.set_user(user)        ← singleton process-wide store
               session.user = user             ← per-session object (Shiny)
               AuditLog: "User X logged in"
               Modal dismissed
               Navbar rebuilt for user's role
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
| `USER`    | (Defined but not currently assigned pages)      |

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

`FitnessWarriorApp._pages_for_role(role)` filters the list of `PageSpec` objects at
navbar build time. Only pages whose `allowed_roles` set contains the logged-in user's role
are rendered and registered. **There is no backend middleware guard** — the access control
relies entirely on Shiny server-side rendering not exposing UI elements to unauthorized users.

---

## Cryptography

### Key Material

| Secret          | Source                         | Derivation                                    |
|-----------------|--------------------------------|-----------------------------------------------|
| `WF_SECRET_KEY` | Environment variable (runtime) | Raw string, must be set before app start       |
| Fernet key      | Derived in `auth_service.py`   | `base64url(SHA-256(WF_SECRET_KEY.encode()))`  |

```python
# auth_service.py:19
_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
_fernet = Fernet(_FERNET_KEY)
```

`WF_SECRET_KEY` is intentionally **not baked into the Docker image**. It must be
injected at runtime via `-e WF_SECRET_KEY=...` or Docker secrets.

### Algorithms in Use

| Purpose              | Algorithm                          | Library            |
|----------------------|------------------------------------|--------------------|
| Password encryption  | Fernet (AES-128-CBC + HMAC-SHA256) | `cryptography`     |
| Legacy password hash | bcrypt (cost factor unspecified)   | `bcrypt`           |
| Key derivation       | SHA-256 (no salt, no iterations)   | `hashlib`          |
| Token scheme         | OAuth2 / HS256 (declared, unused)  | `fastapi.security` |

---

## Password Storage

### Current Scheme — Fernet Symmetric Encryption

New passwords are **encrypted**, not hashed. `Auth.hash_password()` calls
`_fernet.encrypt(password.encode())` and stores the ciphertext in `users.password_hash`.

```
stored = Fernet(SHA-256(WF_SECRET_KEY)).encrypt(plaintext_password)
```

This means:
- Passwords are **recoverable** if `WF_SECRET_KEY` is known.
- `Auth.decrypt_password()` explicitly provides this recovery capability.
- Compromise of `WF_SECRET_KEY` exposes **all** user passwords in plaintext.

### Legacy Scheme — bcrypt (fallback path)

Users created before the Fernet migration have bcrypt hashes. `Auth.verify_password()`
falls back to `bcrypt.checkpw()` when Fernet decryption raises `InvalidToken`.

```python
# auth_service.py:54 — verify_password()
try:
    decrypted = _fernet.decrypt(stored.encode()).decode()
    return decrypted == plain_password
except (InvalidToken, Exception):
    pass
# bcrypt fallback
return bcrypt.checkpw(plain_password.encode("utf-8"), stored_bytes)
```

### Database Column

```python
# db_model.py
password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
```

---

## Session Management

| Property            | Detail                                                                    |
|---------------------|---------------------------------------------------------------------------|
| Session store       | Shiny server-side session object (`session.user`)                         |
| Global user store   | `UserStore` singleton — process-wide, single value                        |
| Inactivity timeout  | 10 minutes (`app.py:767` — `time.time() - ts >= 600`)                    |
| Activity events     | JS: `click`, `keydown`, `mousemove`, `scroll`, `touchstart`, `touchmove`, `visibilitychange` |
| Poll interval       | 5 seconds (`reactive.invalidate_later(5)`)                                |
| Logout              | Clears `session.user`, triggers JS `location.reload()`                    |
| Dev bypass          | `APP_ENV=development` auto-injects `ADMIN` user, skips auth               |

### Logout Flow

```
User clicks "Logout"
      │
      ▼
_clear_session_user()   → delattr(session, "user")
ui.update_navs(...)     → redirect to Dashboard
notification_show(...)  → "You have been logged out."
location.reload()       → full page reload (JS, 100 ms delay)
```

---

## Rate Limiting

Implemented in `warriorfit/security/rate_limiter.py` as an **in-memory** store.

| Parameter    | Value              |
|--------------|--------------------|
| Max attempts | 5                  |
| Window       | 15 minutes (900 s) |
| Lock scope   | Per username       |
| Storage      | Process memory     |
| Reset        | On successful login|

```
Attempts 1–4 → "Invalid username or password. N attempt(s) remaining."
Attempt 5    → "Too many failed attempts. Account locked for N minute(s)."
After window → Automatic unlock (sliding window pruning)
```

**Limitation:** The rate limiter is not persisted. A process restart resets all counters.
In a multi-process or multi-instance deployment, each process maintains independent counters.

---

## Audit Logging

Login events and user CRUD operations are written to the `audit_logs` table.

```
audit_logs
  id          INTEGER PK
  user_id     FK → users.id
  action      VARCHAR(50)    e.g. "login", "add", "update", "delete"
  details     JSON           free-form context string
  ip_address  VARCHAR(45)    present in schema, not currently populated
  created_at  TIMESTAMP      server default
```

Logged events:

| Event         | Action value | Details                          |
|---------------|--------------|----------------------------------|
| Login         | `login`      | `"User X logged in"`             |
| User created  | `add`        | `"User X added"`                 |
| User updated  | `update`     | `"User X updated"`               |
| User deleted  | `delete`     | `"User X deleted"`               |

---

## OWASP Top 10 Assessment

### A01 — Broken Access Control

| Finding | Severity | Detail |
|---------|----------|--------|
| UI-only enforcement | Medium | Page access is controlled by filtering rendered UI elements. No server-side guard exists for individual reactive handlers. An adversary with WebSocket access to the Shiny server could potentially invoke handlers for pages they are not authorized to see. |
| `UserStore` singleton | Low | The singleton holds one user globally per process. In the standard single-user-per-session Shiny model this is acceptable, but it creates a risk if the server ever handles concurrent sessions in the same process without isolation. |

### A02 — Cryptographic Failures

| Finding | Severity | Detail |
|---------|----------|--------|
| **Passwords encrypted, not hashed** | **Critical** | `Auth.hash_password()` uses Fernet symmetric encryption. Passwords are fully recoverable from the database if `WF_SECRET_KEY` is known. This violates the principle that a credential store breach should not directly yield usable passwords. |
| `decrypt_password()` exists | Critical | An explicit method to recover plaintext passwords is exposed on the `Auth` class. Any code path that calls it can leak credentials. |
| Weak key derivation | High | The Fernet key is derived as `SHA-256(WF_SECRET_KEY)` with no salt and no iterations. A brute-force or dictionary attack against a captured key succeeds in a single SHA-256 pass. A proper KDF (PBKDF2, Argon2id, or scrypt) should be used instead. |
| HS256 / JWT declared but unused | Info | `ALGORITHM = "HS256"` and `ACCESS_TOKEN_EXPIRE_MINUTES = 30` are defined but no JWT is ever issued. Dead code, no current risk. |

**Recommended fix:** Replace Fernet encryption with Argon2id hashing (already a project dependency):
```python
from argon2 import PasswordHasher
ph = PasswordHasher()

# Store
stored = ph.hash(plain_password)

# Verify
ph.verify(stored, plain_password)
```
The existing bcrypt fallback path proves the verification logic already supports one-way hashing.

### A03 — Injection

| Finding | Severity | Detail |
|---------|----------|--------|
| SQLAlchemy ORM | Low | All queries use parameterized ORM expressions (`select(User).where(User.username == username)`). No raw SQL strings detected. SQL injection risk is minimal. |

### A04 — Insecure Design

| Finding | Severity | Detail |
|---------|----------|--------|
| Reversible credential design | Critical | The explicit `decrypt_password()` method implies password reversibility is an intended design feature (admin recovery). This should be removed entirely. Admins should use a password reset flow instead. |
| Dev auto-login guard | Medium | `APP_ENV=development` injects a full ADMIN session. If this variable is accidentally set on a production host, authentication is completely bypassed. |

### A05 — Security Misconfiguration

| Finding | Severity | Detail |
|---------|----------|--------|
| `WF_SECRET_KEY` at build time | Low | `ARG WF_SECRET_KEY` / `ENV WF_SECRET_KEY=${WF_SECRET_KEY}` bakes the key into the image layer if provided at `docker build` time. Pass it only via `docker run -e` or Docker secrets, never at build time. |
| Config file not mounted | Info | `/etc/WarriorFit/config.yml` must be volume-mounted at runtime. No default or fallback exists for production. |

### A06 — Vulnerable and Outdated Components

| Finding | Severity | Detail |
|---------|----------|--------|
| Dependency audit | Info | Not assessed here. Run `uv pip audit` or `pip-audit` against the locked dependencies to identify known CVEs in `cryptography`, `bcrypt`, `sqlalchemy`, `shiny`, `uvicorn`, etc. |

### A07 — Identification and Authentication Failures

| Finding | Severity | Detail |
|---------|----------|--------|
| In-memory rate limiter | Medium | Lost on restart; bypassable by restarting the container or running multiple instances. |
| No password complexity policy | Medium | No minimum length, complexity, or expiry is enforced when passwords are set via User Management. |
| No MFA | Low | Single-factor authentication only. |
| Username existence leak | Low | `"N attempt(s) remaining"` implicitly confirms the username exists. A generic `"Invalid credentials"` message is preferred. |

### A08 — Software and Data Integrity Failures

| Finding | Severity | Detail |
|---------|----------|--------|
| No image signing | Info | Docker image integrity is not verified at deployment. Consider signing images if deploying from a registry. |

### A09 — Security Logging and Monitoring Failures

| Finding | Severity | Detail |
|---------|----------|--------|
| IP address not captured | Medium | `audit_logs.ip_address` column exists but is never populated. Login origin cannot be traced after the fact. |
| Failed logins not persisted | Medium | Failed login attempts are tracked only in the in-memory rate limiter, not written to `audit_logs`. A forensic review of the database would show no evidence of brute-force attempts. |

### A10 — Server-Side Request Forgery (SSRF)

| Finding | Severity | Detail |
|---------|----------|--------|
| HR API URL from config | Low | `settings_data.hr_url` is read from `config.yml`. If an attacker can write to the config (e.g. via the Settings admin page), they could redirect internal HTTP requests. Validate the URL scheme and host against an allowlist before use. |

---

## Priority Remediation Summary

| Priority | Issue | Location |
|----------|-------|----------|
| P0 | Replace Fernet encryption with Argon2id one-way hashing | `security/auth_service.py` |
| P0 | Remove `decrypt_password()` entirely | `security/auth_service.py` |
| P1 | Persist rate-limiter state (Redis or DB) | `security/rate_limiter.py` |
| P1 | Populate `ip_address` in audit log on login | `app.py` — `handle_login()` |
| P1 | Log failed login attempts to `audit_logs` | `app.py` — `handle_login()` |
| P2 | Enforce password complexity on creation/update | `ui/controllers/usermanagement_controller.py` |
| P2 | Harden Fernet key derivation (PBKDF2 / Argon2) | `security/auth_service.py:19` |
| P3 | Use generic error message on failed login | `app.py:636` |
| P3 | Validate `hr_url` scheme and host on load | `config/appliccation_config.py` |
