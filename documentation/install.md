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
1. Set `APP_ENV=production` environment variable
2. Mount the configuration file at `/etc/WarriorFit/config.yml`
3. Update database credentials and external service URLs
4. Use secure passwords and API keys


## 2. Docker Deployment

### Local Development Deployment

```bash
sudo docker build -t warriorfit-app .
docker run -p 8000:8000 -e APP_ENV=development warriorfit-app
```

### Production Server Deployment

```bash
# 1. List containers to find the one you want
docker ps -a

# 2. Stop it if running
docker stop warriorfit-app

# 3. Remove it
sudo docker rm warriorfit-app

# 4. Build the image
sudo docker build -t api-warriorfit-app .

# 5. Run with production configuration
sudo docker run -d --restart unless-stopped \
  --name warriorfit-app \
  -p 8500:8000 \
  -e APP_ENV=production \
  -v /path/to/your/config.yml:/etc/WarriorFit/config.yml:ro \
  -v /path/to/your/version.yaml:/app/version.yaml:ro \
  api-warriorfit-app
```

**Note**: Replace `/path/to/your/config.yml` and `/path/to/your/version.yaml` with the actual paths to your configuration files on the host system.


## 3. SQL

Run this script to create the database and the tables on a PostgreSQL database.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
create user produser
    createdb;
       
create database warriorfit  with owner produser;;


create type typefitnesstest as enum ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING');

alter type typefitnesstest owner to produser;

create type role as enum ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');

alter type role owner to produser;

create type gender as enum ('M', 'F');

alter type gender owner to produser;

create table alembic_version
(
    version_num varchar(32) not null
        constraint alembic_version_pkc
            primary key
);



create table fitness_tests
(
    id            serial
        primary key,
    serial_number varchar(50),
    type          varchar(50)
);

alter table fitness_tests
    owner to produser;

create table test_sessions
(
    id                serial
        primary key,
    serial_number_pti varchar(50),
    datetime_start    timestamp       not null,
    canceled          boolean         not null,
    description       varchar(255),
    type_test         typefitnesstest not null
);

alter table test_sessions
    owner to produser;

create table users
(
    id            serial
        primary key,
    username      varchar(50)  not null
        unique,
    email         varchar(100) not null
        unique,
    password_hash varchar(128) not null,
    created_at    timestamp    not null,
    role          role         not null,
    is_active     boolean      not null,
    serial_number varchar(50)
        unique
);

alter table users
    owner to produser;

create table audit_logs
(
    id         serial
        primary key,
    user_id    integer     not null
        references users,
    action     varchar(50) not null,
    details    json,
    ip_address varchar(45),
    created_at timestamp   not null
);

alter table audit_logs
    owner to produser;

create table combat_swimming_tests
(
    id          integer not null
        primary key
        references fitness_tests,
    swim_paased boolean not null
);

alter table combat_swimming_tests
    owner to produser;

create table combat_tests
(
    id              integer          not null
        primary key
        references fitness_tests,
    running_time    double precision not null,
    obstacle_passed boolean          not null,
    rope_passed     boolean          not null
);

alter table combat_tests
    owner to produser;


create table functional_tests
(
    id       integer not null
        primary key
        references fitness_tests,
    push_ups integer not null,
    sit_ups  integer not null,
    pull_ups integer not null
);

alter table functional_tests
    owner to produser;

create table phef_tests
(
    id             integer          not null
        primary key
        references fitness_tests,
    running_time   double precision not null,
    "sideBridge_r" double precision not null,
    "sideBridge_l" double precision not null
);

alter table phef_tests
    owner to produser;

create table session_fitness_tests
(
    session_id      integer not null
        references test_sessions,
    fitness_test_id integer not null
        references fitness_tests,
    primary key (session_id, fitness_test_id)
);

alter table session_fitness_tests
    owner to produser;

create table "cross"
(
    id             serial
        primary key,
    datetime_start timestamp        not null,
    distance       double precision not null,
    executed       boolean          not null,
    description    varchar(255)
);

alter table "cross"
    owner to produser;

create table runners
(
    id            serial
        primary key,
    serial_number varchar(50),
    running_time  double precision not null
);

alter table runners
    owner to produser;

create table cross_runners
(
    cross_id  integer not null
        references "cross",
    runner_id integer not null
        references runners,
    primary key (cross_id, runner_id)
);

alter table cross_runners
    owner to produser;

create table units
(
    id            serial
        primary key,
    name          varchar(100) not null
        constraint uq_units_name
            unique,
    base_location varchar(150) not null
);

alter table units
    owner to produser;

create table service_men
(
    id             serial
        primary key,
    first_name     varchar(80)  not null,
    last_name      varchar(80)  not null,
    mail           varchar(120) not null,
    rank           integer  not null,
    service_number varchar(50)  not null
        constraint uq_service_men_service_number
            unique,
    birthdate      date         not null,
    gender         gender       not null,
    unit_id        integer      not null
        references units,
    para           boolean      not null,
    ops_test       boolean      not null
);

alter table service_men
    owner to produser;

create index ix_service_men_unit_id
    on service_men (unit_id);

create table march
(
    id                serial
        primary key,
    distance          double precision,
    succeeded         boolean   not null,
    datetime_executed timestamp not null,
    service_number    varchar(50)
);

alter table march
    owner to produser;

create index ix_march_service_number
    on march (service_number);

create table hr_messages
(
    id               serial
        primary key,
    message          varchar(255) not null,
    datetime_created timestamp    not null
);

alter table hr_messages
    owner to produser;


INSERT INTO users (username, email, password_hash, created_at, role, is_active, serial_number) VALUES
('user1', 'user1@example.com', crypt('password', gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'SN001'),
('user2', 'user2@example.com', crypt('password2', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN002'),
('user3', 'user3@example.com', crypt('password3', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN003'),
('user4', 'user4@example.com', crypt('password4', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN004'),
('user5', 'user5@example.com', crypt('password5', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN005'),
('user6', 'user6@example.com', crypt('password6', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN006'),
('user7', 'user7@example.com', crypt('password7', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN007'),
('user8', 'user8@example.com', crypt('password8', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN008'),
('user9', 'user9@example.com', crypt('password9', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN009'),
('user10', 'user10@example.com', crypt('password10', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN010'),
('benoit', 'benoit@example.com', public.crypt('password', public.gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'benoit');

INSERT INTO users (username, email, password_hash, created_at, role, is_active, serial_number)
VALUES ('pti', 'pti@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI'),
       ('pti2', 'pti2@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI2'),
       ('pti3', 'pti3@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI3'),
       ('pti4', 'pti4@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI4'),
       ('pti5', 'pti5@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI5'),
       ('pti6', 'pti6@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI6'),
       ('pti7', 'pti7@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI7'),
       ('pti8', 'pti8@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI8'),
       ('pti9', 'pti9@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI9'),
       ('pti10', 'pti10@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI10');

-- Test Sessions data

```