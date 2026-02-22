# WarriorFit — Security Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication & Login](#authentication--login)
3. [Password Encryption](#password-encryption)
4. [Brute Force Protection](#brute-force-protection)
5. [Secret Key Management](#secret-key-management)
6. [OWASP Top 10 Audit](#owasp-top-10-audit)
7. [Deployment Security](#deployment-security)

---

## Overview

WarriorFit uses a layered security model:

| Layer | Technology | Location |
|---|---|---|
| Password encryption | Fernet (AES-128-CBC) | `warriorfit/security/auth_service.py` |
| Login rate limiting | In-memory limiter | `warriorfit/security/rate_limiter.py` |
| Secret key | Environment variable | `.env` / Docker `-e` |
| Role-based access | `Role` enum + page visibility | `warriorfit/app.py` |
| Audit logging | `AuditLog` DB table | `warriorfit/data/model/db_model.py` |

---

## Authentication & Login

### Login Flow

```
User submits username + password
        │
        ▼
Is username locked out? ──YES──► Show lockout message + remaining time
        │
        NO
        ▼
user_service.check_user(username, password)
        │
        ├── NOT FOUND ──► record_failure() ──► "Invalid username or password"
        │
        ├── WRONG PASSWORD ──► record_failure() ──► "X attempt(s) remaining"
        │
        └── OK ──► is_active check ──► set session ──► audit log ──► open app
```

### Dev Auto-Login Bypass

When `APP_ENV=development`, the login modal is skipped and a stub admin user is
injected automatically. This is **disabled in all other environments**.

| `APP_ENV` | Behaviour |
|---|---|
| `development` | Auto-login as admin (no credentials required) |
| `test` | Normal login modal |
| `production` | Normal login modal + `RuntimeError` guard if bypass is somehow reached |
| *(not set)* | Normal login modal |

The guard in `app.py`:

```python
app_env = os.getenv("APP_ENV", "")
if app_env == "production":
    raise RuntimeError(
        "Dev auto-login bypass must never run in production."
    )
if app_env == "development":
    # inject stub user ...
```

---

## Password Encryption

### Algorithm — Fernet (symmetric)

Passwords are stored using **Fernet symmetric encryption** (from the `cryptography`
library). Fernet uses AES-128 in CBC mode with a PKCS7-padded message, a HMAC-SHA256
authentication tag, and a random IV per token.

```
Plain text password
        │
        ▼
Fernet.encrypt(password.encode())
        │
        ▼
gAAAAAB...==   ← stored in users.password_hash (VARCHAR 255)
```

### Why Fernet and not bcrypt?

bcrypt is **one-way** — it cannot be reversed. WarriorFit administrators need to
be able to read and manage user passwords through the User Management screen.
Fernet allows decryption back to plain text while still keeping passwords
unreadable in the database without the secret key.

| Property | bcrypt | Fernet |
|---|---|---|
| Reversible | No | Yes |
| Stored value readable without key | No | No |
| Admin can view plain text | No | Yes |
| Authentication | Hash comparison | Decrypt + compare |

### Key Derivation

The Fernet key is derived from `WF_SECRET_KEY` using SHA-256:

```python
import base64, hashlib
from cryptography.fernet import Fernet

_FERNET_KEY = base64.urlsafe_b64encode(
    hashlib.sha256(SECRET_KEY.encode()).digest()
)
_fernet = Fernet(_FERNET_KEY)
```

This produces a stable, deterministic 32-byte URL-safe base64 key from any
arbitrary secret string.

### Auth API

```python
from warriorfit.security.auth_service import Auth

# Encrypt (called on create/update user)
token = Auth.hash_password("MyPassword@1")
# → "gAAAAABp..."

# Decrypt (called when listing users)
plain = Auth.decrypt_password(token)
# → "MyPassword@1"

# Verify (called on login)
ok = Auth.verify_password("MyPassword@1", token)
# → True
```

### Legacy bcrypt Fallback

Users created before the switch to Fernet have bcrypt hashes (`$2b$...`) stored
in the database. `verify_password` handles these transparently:

```python
@staticmethod
def verify_password(plain_password: str, stored: str) -> bool:
    # 1. Try Fernet decrypt + compare
    try:
        return _fernet.decrypt(stored.encode()).decode() == plain_password
    except InvalidToken:
        pass
    # 2. Fall back to bcrypt for legacy hashes
    try:
        return bcrypt.checkpw(plain_password.encode(), stored.encode())
    except Exception:
        return False
```

Legacy users can still log in. Their password will show blank in the admin UI
until they are re-saved, at which point a Fernet token is generated.

### Password Policy

Enforced on every create/update in `UserManagementController.validate_password()`:

- Minimum **8 characters**
- At least one **uppercase** letter
- At least one **lowercase** letter
- At least one **digit**
- At least one **special character**

---

## Brute Force Protection

### Rate Limiter — `LoginRateLimiter`

Located in `warriorfit/security/rate_limiter.py`.

| Setting | Value |
|---|---|
| Max failed attempts | 5 |
| Window | 15 minutes |
| Lockout duration | 15 minutes (same window) |
| Scope | Per username |

### How It Works

```python
from warriorfit.security.rate_limiter import login_rate_limiter

# Check before attempting login
locked, seconds_left = login_rate_limiter.is_locked("ben")

# Record a failure
login_rate_limiter.record_failure("ben")

# How many attempts remain before lockout
left = login_rate_limiter.attempts_remaining("ben")

# Clear on successful login
login_rate_limiter.reset("ben")
```

### User-Facing Messages

| Situation | Message |
|---|---|
| 1–4 failures | "Invalid username or password. X attempt(s) remaining." |
| 5th failure | "Too many failed attempts. Account locked for 15 minute(s)." |
| Already locked | "Too many failed attempts. Try again in X minute(s)." |
| Disabled account | "Your account is disabled. Please contact your administrator." |

### Limitations

The rate limiter is **in-memory** and scoped to a single process. It resets if
the application restarts. It is keyed by **username**, not by IP address, because
the Shiny framework does not expose client IP by default. For a multi-instance
deployment, replace with a Redis-backed implementation.

---

## Secret Key Management

### Environment Variable

The Fernet encryption key is derived from `WF_SECRET_KEY`, which must be set
as an environment variable. The app **will not start** if it is missing:

```python
SECRET_KEY = os.environ["WF_SECRET_KEY"]   # KeyError = crash at startup
```

### Local Development

Copy `.env.example` to `.env` and fill in a value:

```bash
cp .env.example .env
```

`.env.example`:
```
WF_SECRET_KEY=replace-with-a-long-random-hex-string
```

Generate a strong key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` is listed in `.gitignore` — **never commit it**.

### Docker / Production

Pass the key at container runtime:

```bash
docker run -e WF_SECRET_KEY=<your-secret> warriorfit-app
```

Or via `deploy.sh` (line 52):

```bash
sudo docker run -d \
    --name warriorfit-app \
    -e WF_SECRET_KEY=<your-secret> \
    ...
```

> **Warning:** Do not use `--build-arg` for secrets — build args are stored in
> image layer metadata and can be inspected with `docker history`.

### Key Rotation

If the key changes, **all stored Fernet tokens become unreadable**. Users will
not be able to log in until their passwords are reset. Procedure:

1. Update `WF_SECRET_KEY` in `.env` / Docker config
2. Re-insert test data with newly generated tokens (re-run `test_data.sql`)
3. Have all production users reset their passwords via an admin

---

## OWASP Top 10 Audit

Scan performed against OWASP Top 10 (2021). Status reflects current codebase.

### A02 — Cryptographic Failures

| Finding | Status | Detail |
|---|---|---|
| Hardcoded `SECRET_KEY` | ✅ Fixed | Moved to `os.environ["WF_SECRET_KEY"]` |
| Reversible password storage | ✅ Accepted | Fernet used intentionally for admin visibility |
| DB connection string in logs | ⚠️ Open | Mask password in SQLAlchemy engine URL |

### A05 — Security Misconfiguration

| Finding | Status | Detail |
|---|---|---|
| Dev auto-login in production | ✅ Fixed | `RuntimeError` guard + removed default `"development"` fallback |
| `APP_ENV` defaults to dev | ✅ Fixed | `os.getenv("APP_ENV", "")` — no default |
| Docker image `APP_ENV` | ✅ Fixed | Dockerfile sets `APP_ENV=production` |
| CORS wildcard in HR dummy API | ⚠️ Open | `allow_origins="*"` — restrict to frontend origin |

### A07 — Identification & Authentication Failures

| Finding | Status | Detail |
|---|---|---|
| No brute force protection | ✅ Fixed | `LoginRateLimiter` — 5 attempts / 15 min |
| Weak password policy | ⚠️ Partial | Min 8 chars + complexity enforced; no dictionary check |
| Username case normalisation | ⚠️ Open | Lowercased on login but not on create |

### A01 — Broken Access Control

| Finding | Status | Detail |
|---|---|---|
| Role checked in UI only | ⚠️ Open | No server-side per-request role enforcement |
| Password exposed in admin UI | ✅ Accepted | Admin panel intentionally shows decrypted password |

### A10 — Server-Side Request Forgery

| Finding | Status | Detail |
|---|---|---|
| HR API URL user-controlled | ⚠️ Open | Validate against domain whitelist |
| No HTTP timeout on external calls | ⚠️ Open | Add `timeout=10` to `httpx.AsyncClient()` |

### A06 — Vulnerable & Outdated Components

| Finding | Status | Detail |
|---|---|---|
| Loose version pinning (`>=`) | ⚠️ Open | Pin exact versions in production; run `pip-audit` monthly |

### A09 — Security Logging & Monitoring

| Finding | Status | Detail |
|---|---|---|
| HR URL printed to stdout | ⚠️ Open | Replace `print` with logger |
| Full message content logged | ⚠️ Open | Log only message ID; redact sensitive fields |

### A04 — Insecure Design

| Finding | Status | Detail |
|---|---|---|
| Undefined variable in error log | ⚠️ Open | `user_repository.py:299` — `id` not in scope |
| No audit log retention policy | ⚠️ Open | Add index on `created_at`; prune logs > 90 days |

---

## Deployment Security

### Checklist Before Going to Production

- [ ] `WF_SECRET_KEY` set as environment variable (not in source or image)
- [ ] `APP_ENV=production` set in Docker / deployment config
- [ ] `.env` not committed to version control
- [ ] `test_data.sql` **not** run against the production database
- [ ] Database credentials not logged or exposed in error messages
- [ ] HTTPS termination configured on reverse proxy (nginx / Traefik)
- [ ] Docker image built with `--no-cache` after dependency updates
- [ ] `pip-audit` run against current `uv.lock` before release

### Files Summary

| File | Purpose |
|---|---|
| `warriorfit/security/auth_service.py` | Fernet encrypt/decrypt/verify |
| `warriorfit/security/rate_limiter.py` | Login brute force protection |
| `.env` | Local secret key (gitignored) |
| `.env.example` | Template for required env vars |
| `Dockerfile` | Sets `APP_ENV=production`, accepts `WF_SECRET_KEY` via `-e` |
| `deploy.sh` | Stops, rebuilds, and restarts the container |
