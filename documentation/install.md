# WarriorFit Install


## 1. Configuration

### Environment-specific Configuration Files

The application uses different configuration files based on the `APP_ENV` environment variable:
- **Development**: `warriorfit/config/config_dev.yml` (default)
- **Test**: `warriorfit/config/config_test.yml`
- **Production**: `/etc/WarriorFit/config.yml` (when running in Docker container)

### Configuration File Structure

Example `config.yml`:

```yaml
db:
  host: "localhost"
  port: 5432
  database: "warriorfit"
  username: "produser"
  password: "your_secure_password"
path:
  pdf_path: "/app/pdf_output"
unit:
  name: "1-3 Bn Lanciers"
mail:
  host: "smtp.example.com"
  port: 587
  username: "your_email@example.com"
  password: "your_email_password"
  sender: "your_email@example.com"
  sender_email: "your_email@example.com"
  use_tls: true
  use_ssl: false
hr:
  url: "http://hr-api.example.com/api/v1/phef/test"
  api_key: "your_hr_api_key"
version:
  status: "production"
```

### Version File

The application also requires a `version.yaml` file at the project root:

```yaml
version: "0.1.0"
date: "2024-01-01"
```

### Production Deployment Configuration

For production deployment with Docker, ensure:
1. Set `APP_ENV=production` via the deploy script
2. Set `WF_SECRET_KEY` to a secure secret before running the script
3. Update database credentials and external service URLs in the config


## 2. Docker Deployment

Three deploy scripts are available at the project root. Each script automatically stops and removes any existing container, builds the image, and starts a new container.

### Basic Deployment (`deploy.sh`)

For quick local or ad-hoc deployments. The secret key is embedded in the script (development only).

```bash
./deploy.sh
```

- Container: `warriorfit-app`
- Image: `warriorfit-app`
- Port: `8500 → 8000`

### Production Deployment (`deploy-prod.sh`)

Requires `WF_SECRET_KEY` to be provided in the environment.

```bash
WF_SECRET_KEY=<your_secret> ./deploy-prod.sh
```

- Container: `warriorfit-app`
- Image: `warriorfit-app:prod`
- Port: `8500 → 8000`
- `APP_ENV=production`, `APP_PORT=8000`
- Restart policy: `unless-stopped`

### Test Deployment (`deploy-test.sh`)

Deploys a separate test instance alongside production.

```bash
WF_SECRET_KEY=<your_secret> ./deploy-test.sh
```

- Container: `warriorfit-app-test`
- Image: `warriorfit-app:test`
- Port: `8501 → 8501`
- `APP_ENV=test`, `APP_PORT=8501`
- Restart policy: `on-failure`

### Viewing Logs

```bash
docker logs warriorfit-app          # production
docker logs -f warriorfit-app       # follow production logs
docker logs warriorfit-app-test     # test instance
```


## 3. SQL

Run this script to create the database and the tables on a PostgreSQL database.

```sql

create user produser createdb;
create database warriorfit with owner produser;

-- Types
create type typefitnesstest as enum ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING');
create type role as enum ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');
create type gender as enum ('M', 'F');

-- Alembic
create table alembic_version
(
    version_num varchar(32) not null
        constraint alembic_version_pkc primary key
);

-- Users
create table users
(
    id            serial primary key,
    username      varchar(50)  not null unique,
    email         varchar(100) not null unique,
    password_hash varchar(128) not null,
    created_at    timestamp    not null,
    role          role         not null,
    is_active     boolean      not null,
    serial_number varchar(50)  unique
);

create table audit_logs
(
    id         serial primary key,
    user_id    integer     not null references users(id),
    action     varchar(50) not null,
    details    json,
    ip_address varchar(45),
    created_at timestamp   not null
);

-- Units & Service men
create table units
(
    id            serial primary key,
    name          varchar(100) not null constraint uq_units_name unique,
    base_location varchar(150) not null
);

create table service_men
(
    id             serial primary key,
    first_name     varchar(80)  not null,
    last_name      varchar(80)  not null,
    mail           varchar(120) not null,
    service_number varchar(50)  not null constraint uq_service_men_service_number unique,
    birthdate      date         not null,
    gender         gender       not null,
    unit_id        integer      not null references units(id),
    para           boolean      not null,
    ops_test       boolean      not null,
    rank           integer      not null,
    user_id        integer      references users(id)
);

create index ix_service_men_unit_id on service_men (unit_id);
create unique index ix_service_men_user_id on service_men (user_id);

-- Fitness tests
create table fitness_tests
(
    id            serial primary key,
    serial_number varchar(50) references service_men(service_number),
    type          varchar(50)
);

create index ix_fitness_tests_serial_number on fitness_tests (serial_number);

create table test_sessions
(
    id                serial primary key,
    serial_number_pti varchar(50),
    datetime_start    timestamp       not null,
    canceled          boolean         not null,
    description       varchar(255),
    type_test         typefitnesstest not null
);

create table session_fitness_tests
(
    session_id      integer not null references test_sessions(id),
    fitness_test_id integer not null references fitness_tests(id),
    primary key (session_id, fitness_test_id)
);

create table combat_swimming_tests
(
    id          integer not null primary key references fitness_tests(id),
    swim_paased boolean not null
);

create table combat_tests
(
    id              integer          not null primary key references fitness_tests(id),
    running_time    double precision not null,
    obstacle_passed boolean          not null,
    rope_passed     boolean          not null
);

create table functional_tests
(
    id       integer not null primary key references fitness_tests(id),
    push_ups integer not null,
    sit_ups  integer not null,
    pull_ups integer not null
);

create table phef_tests
(
    id             integer          not null primary key references fitness_tests(id),
    running_time   double precision not null,
    "sideBridge_r" double precision not null,
    "sideBridge_l" double precision not null
);

-- Cross country
create table "cross"
(
    id             serial primary key,
    datetime_start timestamp        not null,
    distance       double precision not null,
    executed       boolean          not null,
    description    varchar(255)
);

create table runners
(
    id            serial primary key,
    serial_number varchar(50),
    running_time  double precision not null
);

create table cross_runners
(
    cross_id  integer not null references "cross"(id),
    runner_id integer not null references runners(id),
    primary key (cross_id, runner_id)
);

-- March
create table march
(
    id                serial primary key,
    service_number    varchar(50) references service_men(service_number),
    distance          double precision,
    succeeded         boolean   not null,
    datetime_executed timestamp not null
);

create index ix_march_service_number on march (service_number);

-- HR
create table hr_messages
(
    id               serial primary key,
    message          varchar(255) not null,
    datetime_created timestamp    not null
);

-- Rooms & Reservations
create table rooms
(
    id       serial primary key,
    name     varchar(100) not null,
    capacity integer      not null,
    location varchar(100) not null
);

create table reservations
(
    id            serial primary key,
    room_id       integer      not null references rooms(id),
    date          timestamp    not null,
    start_time    timestamp    not null default now(),
    end_time      timestamp    not null default now(),
    serial_number varchar(50)  not null,
    activity      varchar(100) not null,
    created_at    timestamp    not null default now()
);




```