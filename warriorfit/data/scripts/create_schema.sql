-- PostgreSQL DDL generated from warriorfit/data/model/db_model.py
-- Notes:
-- - Uses native ENUM types for Role, Gender, TypeFitnessTest (as per SQLAlchemy Enum/SAEnum usage).
-- - Rank is stored as INTEGER (because the model uses a custom IntEnumType).
-- - Timestamps are "timestamp without time zone" (SQLAlchemy postgresql.TIMESTAMP).
-- - "cross" is a reserved-ish word in some contexts; the model uses __tablename__="cross".
--   Keeping it quoted is the safest.

-- =========================
-- 0) (Optional) DB + user
-- =========================
-- Use placeholders; adjust as needed.
-- CREATE USER <db_user> WITH PASSWORD '<db_password>' CREATEDB;
-- CREATE DATABASE <db_name> OWNER <db_user>;

-- Connect to the target database before running the rest:
-- \c <db_name>

-- =========================
-- 1) Types (Enums)
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role') THEN
        CREATE TYPE role AS ENUM ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender') THEN
        CREATE TYPE gender AS ENUM ('M', 'F');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'typefitnesstest') THEN
        CREATE TYPE typefitnesstest AS ENUM ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING');
    END IF;
END
$$;

-- =========================
-- 2) Tables
-- =========================

-- ---- users
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    role          role         NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    serial_number VARCHAR(50) UNIQUE
);

-- ---- audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id),
    action     VARCHAR(50) NOT NULL,
    details    JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ---- units
CREATE TABLE IF NOT EXISTS units (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    base_location VARCHAR(150) NOT NULL,
    CONSTRAINT uq_units_name UNIQUE (name)
);

-- ---- service_men
CREATE TABLE IF NOT EXISTS service_men (
    id             SERIAL PRIMARY KEY,
    first_name     VARCHAR(80)  NOT NULL,
    last_name      VARCHAR(80)  NOT NULL,
    mail           VARCHAR(120) NOT NULL,
    rank           INTEGER      NOT NULL,
    service_number VARCHAR(50)  NOT NULL,
    birthdate      DATE         NOT NULL,
    gender         gender       NOT NULL,
    unit_id        INTEGER      NOT NULL REFERENCES units(id),
    para           BOOLEAN      NOT NULL DEFAULT FALSE,
    ops_test       BOOLEAN      NOT NULL DEFAULT FALSE,
    user_id        INTEGER UNIQUE REFERENCES users(id),
    CONSTRAINT uq_service_men_service_number UNIQUE (service_number)
);

CREATE INDEX IF NOT EXISTS ix_service_men_unit_id ON service_men(unit_id);
CREATE INDEX IF NOT EXISTS ix_service_men_user_id ON service_men(user_id);

-- ---- fitness_tests (polymorphic base)
CREATE TABLE IF NOT EXISTS fitness_tests (
    id            SERIAL PRIMARY KEY,
    serial_number VARCHAR(50) REFERENCES service_men(service_number),
    type          VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_fitness_tests_serial_number ON fitness_tests(serial_number);

-- ---- phef_tests
CREATE TABLE IF NOT EXISTS phef_tests (
    id             INTEGER PRIMARY KEY REFERENCES fitness_tests(id),
    running_time   DOUBLE PRECISION NOT NULL,
    "sideBridge_r" DOUBLE PRECISION NOT NULL,
    "sideBridge_l" DOUBLE PRECISION NOT NULL
);

-- ---- functional_tests
CREATE TABLE IF NOT EXISTS functional_tests (
    id       INTEGER PRIMARY KEY REFERENCES fitness_tests(id),
    push_ups INTEGER NOT NULL,
    sit_ups  INTEGER NOT NULL,
    pull_ups INTEGER NOT NULL
);

-- ---- combat_tests
CREATE TABLE IF NOT EXISTS combat_tests (
    id              INTEGER PRIMARY KEY REFERENCES fitness_tests(id),
    running_time    DOUBLE PRECISION NOT NULL,
    obstacle_passed BOOLEAN NOT NULL DEFAULT FALSE,
    rope_passed     BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---- combat_swimming_tests
CREATE TABLE IF NOT EXISTS combat_swimming_tests (
    id          INTEGER PRIMARY KEY REFERENCES fitness_tests(id),
    swim_paased BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---- test_sessions
CREATE TABLE IF NOT EXISTS test_sessions (
    id                SERIAL PRIMARY KEY,
    serial_number_pti VARCHAR(50),
    datetime_start    TIMESTAMP        NOT NULL,
    canceled          BOOLEAN          NOT NULL DEFAULT FALSE,
    description       VARCHAR(255),
    type_test         typefitnesstest  NOT NULL DEFAULT 'PHEF'
);

-- ---- session_fitness_tests (many-to-many)
CREATE TABLE IF NOT EXISTS session_fitness_tests (
    session_id      INTEGER NOT NULL REFERENCES test_sessions(id),
    fitness_test_id INTEGER NOT NULL REFERENCES fitness_tests(id),
    PRIMARY KEY (session_id, fitness_test_id)
);

-- ---- cross
CREATE TABLE IF NOT EXISTS "cross" (
    id             SERIAL PRIMARY KEY,
    datetime_start TIMESTAMP        NOT NULL,
    distance       DOUBLE PRECISION NOT NULL,
    executed       BOOLEAN          NOT NULL DEFAULT FALSE,
    description    VARCHAR(255)
);

-- ---- runners
CREATE TABLE IF NOT EXISTS runners (
    id            SERIAL PRIMARY KEY,
    serial_number VARCHAR(50),
    running_time  DOUBLE PRECISION NOT NULL
);

-- ---- cross_runners (many-to-many)
CREATE TABLE IF NOT EXISTS cross_runners (
    cross_id  INTEGER NOT NULL REFERENCES "cross"(id),
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    PRIMARY KEY (cross_id, runner_id)
);

-- ---- march
CREATE TABLE IF NOT EXISTS march (
    id                SERIAL PRIMARY KEY,
    service_number    VARCHAR(50) REFERENCES service_men(service_number),
    distance          DOUBLE PRECISION DEFAULT 30,
    succeeded         BOOLEAN NOT NULL DEFAULT FALSE,
    datetime_executed TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_march_service_number ON march(service_number);

-- ---- hr_messages
CREATE TABLE IF NOT EXISTS hr_messages (
    id               SERIAL PRIMARY KEY,
    message          VARCHAR(255) NOT NULL,
    datetime_created TIMESTAMP    NOT NULL
);

-- ---- rooms
CREATE TABLE IF NOT EXISTS rooms (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    capacity INTEGER      NOT NULL,
    location VARCHAR(100) NOT NULL
);

-- ---- reservations
CREATE TABLE IF NOT EXISTS reservations (
    id         SERIAL PRIMARY KEY,
    room_id    INTEGER NOT NULL REFERENCES rooms(id),
    date       TIMESTAMP DEFAULT NOW(),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time   TIMESTAMP DEFAULT NOW(),
    serial_number VARCHAR(50)  NOT NULL,
    activity     VARCHAR(100) NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);