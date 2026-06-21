# WarriorFit Install

This guide covers configuration, database setup, and Docker deployment. All paths
are relative to the project root.

## 1. Configuration

### Environment-specific configuration files

The active config is selected by the `APP_ENV` environment variable:

| `APP_ENV`     | Config file used                              |
|---------------|-----------------------------------------------|
| `development` | `warriorfit/config/config_dev.yml` (default)  |
| `test`        | `warriorfit/config/config_test.yml`           |
| `production`  | `/etc/WarriorFit/config.yml` (inside container) |

In `development` mode the app auto-injects an admin user and skips authentication.

### Runtime secrets (never stored in the config file)

These are supplied as environment variables at run time and are **never** baked into
the Docker image:

| Variable         | Required | Purpose                                                                                  |
|------------------|----------|------------------------------------------------------------------------------------------|
| `WF_SECRET_KEY`  | yes      | Session / crypto secret. The deploy scripts abort if it is unset.                        |
| `WF_MOM_API_KEY` | no\*     | API key that unlocks the MOM `/api/v1/phef/test` HR endpoint. If unset the endpoint stays locked (401). |
| `APP_ENV`        | yes      | `development` \| `test` \| `production`.                                                  |
| `APP_PORT`       | no       | Port Shiny binds to (default `8000`; `8500` prod, `8501` test via the deploy scripts).   |

\* Optional, but the HR integration is disabled without it.

### Configuration file structure

Example `config.yml` (production mounts this at `/etc/WarriorFit/config.yml`):

```yaml
db:
  host: "localhost"
  port: 5432
  database: "warriorfit"
  username: "produser"
  password: "your_secure_password"
  ssl: prefer                 # disable | allow | prefer | require | verify-ca | verify-full
  ssl_root_cert: ""           # path to CA cert, required for verify-ca / verify-full
path:
  pdf_path: "/app/pdf_output"
unit:
  name: "1-3 Bn Lanciers"     # the "own unit" the instance is scoped to
mail:
  host: "smtp.example.com"
  port: 25
  username: "your_email@example.com"
  password: "your_email_password"
  sender: "WarriorFit"
  sender_email: "noreply@example.com"
  use_tls: prefer
  use_ssl: false
hr:
  url: "http://hr-api.example.com/api/v1/phef/test"
  api_key: "your_hr_api_key"
version:
  number: "0.1.0"
  status: "production"
gdpr:
  fitness_retention_days: 1825    # fitness/march/reservation records (5 years)
  audit_retention_days: 365       # audit logs (1 year)
  hr_message_retention_days: 90   # HR broker messages
broker:
  poll_interval_s: 30             # how often the worker drains the queue
  batch_size: 50                  # due messages attempted per cycle
  max_attempts: 5                 # attempts before a message is dead-lettered
  base_backoff_s: 10              # exponential back-off lower bound
  max_backoff_s: 3600             # exponential back-off upper bound
  alert_email: ""                 # notified on dead-letter; empty disables alerts
```

### Version file

The application also reads a `version.yaml` file at the project root (kept up to date
automatically by the pre-commit hook):

```yaml
version: "0.1.0"
date: "2026-01-01"
```

## 2. Database setup

WarriorFit targets **PostgreSQL**. There are ready-made SQL scripts under `scripts/`
and `warriorfit/data/scripts/` — you do not need to write the schema by hand.

### Option A — one-shot full setup (recommended)

`scripts/create_warriorfit_db.sql` creates every enum type and table (schema generated
from the ORM models, including `mfft_eval_tests`, `user_consents`, and the
`hr_messages` retry / dead-letter columns) and seeds two ADMIN users.

```bash
createdb warriorfit
psql "postgresql://produser@localhost/warriorfit" -f scripts/create_warriorfit_db.sql
```

Seeded logins (**change these after first login**):

| Username | Password         | Role  |
|----------|------------------|-------|
| `admin`  | `ChangeMe!Admin1` | ADMIN |
| `admin2` | `ChangeMe!Admin2` | ADMIN |

### Option B — schema only, then migrate with Alembic

`warriorfit/data/scripts/create_schema.sql` is a schema-only script (idempotent
`CREATE TABLE IF NOT EXISTS`). After applying it — or instead of it on an empty DB —
bring the schema to the latest revision with Alembic:

```bash
.venv/bin/alembic upgrade head
```

To generate a new migration after changing the ORM models:

```bash
.venv/bin/alembic revision --autogenerate -m "description"
.venv/bin/alembic upgrade head
```

### Seed / reference data (optional)

| Script | Contents |
|--------|----------|
| `scripts/units_*.sql`        | `units` reference rows |
| `scripts/service_men_*.sql`  | `service_men` personnel rows |
| `scripts/rooms_*.sql`        | `rooms` (sport areas) reference rows |
| `warriorfit/data/scripts/test_data.sql` | Demo users + test data (all passwords: `R@nger&1401!`) |
| `warriorfit/data/scripts/update_passwords.sql` | Resets every user's password to `R@nger&1401!` (recovery helper) |

Load order matters because of foreign keys — units before service_men:

```bash
psql "$DATABASE_URL" -f scripts/units_202606151523.sql
psql "$DATABASE_URL" -f scripts/service_men_202606151518.sql
psql "$DATABASE_URL" -f scripts/rooms_202606151539.sql
```

## 3. Local development

```bash
uv sync                                                   # install dependencies
shiny run --host 0.0.0.0 --port 8501 --reload warriorfit/app.py
```

## 4. Docker deployment

The image is built from the root `Dockerfile` (Python 3.13 slim, `uv`-based). The
secret key is passed at run time and never baked in. Two deploy scripts wrap the
build + run; each stops and removes any existing container, rebuilds the image, and
starts a fresh container with `--network host`.

### Production (`deploy-prod.sh`)

```bash
WF_SECRET_KEY=<secret> WF_MOM_API_KEY=<key> ./deploy-prod.sh
```

- Container: `warriorfit-app`
- Image: `warriorfit-app:prod`
- `APP_ENV=production`, `APP_PORT=8500`, networking: `--network host`
- Restart policy: `unless-stopped`
- Config mount: host `/etc/WarriorFit/config_prod.yml` → container `/etc/WarriorFit/config.yml`

### Test (`deploy-test.sh`)

Runs a separate test instance alongside production.

```bash
WF_SECRET_KEY=<secret> WF_MOM_API_KEY=<key> ./deploy-test.sh
```

- Container: `warriorfit-app-test`
- Image: `warriorfit-app:test`
- `APP_ENV=test`, `APP_PORT=8501`, networking: `--network host`
- Restart policy: `on-failure`
- Config mount: host `/etc/WarriorFit/config_test.yml` → container `/etc/WarriorFit/config.yml`

> With `--network host` there is no `-p` port mapping; the app listens directly on
> `APP_PORT` (8500 prod / 8501 test) on the host.

### Continuous deployment (`auto-deploy.sh`)

A cron-friendly poller that runs `gh repo sync` and redeploys only when the upstream
commit changed. Run it from a scheduler (e.g. crontab) on the host. Provide the GitHub
token via the environment or a secrets file — do not hard-code it in the script.

### Viewing logs

```bash
docker logs warriorfit-app          # production
docker logs -f warriorfit-app       # follow production logs
docker logs warriorfit-app-test     # test instance
```
