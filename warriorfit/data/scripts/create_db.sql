
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================
-- WarriorFit Database Schema
-- PostgreSQL DDL
-- ============================================

-- Create ENUM types
CREATE TYPE role_enum AS ENUM ('ADMIN', 'USER', 'PTI', 'VIEWER');
CREATE TYPE gender_enum AS ENUM ('MALE', 'FEMALE', 'OTHER');
CREATE TYPE type_fitness_test_enum AS ENUM ('PHEF', 'FUNCTIONAL', 'COMBAT', 'COMBAT_SWIMMING');

-- Note: Rank enum values need to be defined based on warriorfit.core.rank_enum.Rank
-- Assuming common military ranks:
CREATE TYPE rank_enum AS ENUM (
    'PRIVATE', 'CORPORAL', 'SERGEANT', 'STAFF_SERGEANT',
    'MASTER_SERGEANT', 'SECOND_LIEUTENANT', 'FIRST_LIEUTENANT',
    'CAPTAIN', 'MAJOR', 'LIEUTENANT_COLONEL', 'COLONEL', 'GENERAL'
);

-- ============================================
-- Core Tables
-- ============================================

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    role role_enum NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    serial_number VARCHAR(50) UNIQUE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_serial_number ON users(serial_number);

-- Audit logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    details JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Units table
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_location VARCHAR(150) NOT NULL,
    CONSTRAINT uq_units_name UNIQUE (name)
);

CREATE INDEX idx_units_name ON units(name);

-- Service Men table
CREATE TABLE service_men (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    mail VARCHAR(120) NOT NULL,
    rank INTEGER NOT NULL,
    service_number VARCHAR(50) NOT NULL,
    birthdate DATE NOT NULL,
    gender gender_enum NOT NULL,
    unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE RESTRICT,
    para BOOLEAN NOT NULL DEFAULT FALSE,
    ops_test BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_service_men_service_number UNIQUE (service_number)
);

CREATE INDEX idx_service_men_service_number ON service_men(service_number);
CREATE INDEX idx_service_men_unit_id ON service_men(unit_id);
CREATE INDEX idx_service_men_user_id ON service_men(user_id);
CREATE INDEX idx_service_men_last_name ON service_men(last_name);

-- ============================================
-- Fitness Tests (Polymorphic Hierarchy)
-- ============================================

-- Base fitness tests table
CREATE TABLE fitness_tests (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50) REFERENCES service_men(service_number) ON DELETE CASCADE,
    type VARCHAR(50)
);

CREATE INDEX idx_fitness_tests_serial_number ON fitness_tests(serial_number);
CREATE INDEX idx_fitness_tests_type ON fitness_tests(type);

-- PHEF tests
CREATE TABLE phef_tests (
    id INTEGER PRIMARY KEY REFERENCES fitness_tests(id) ON DELETE CASCADE,
    running_time FLOAT NOT NULL,
    sidebridge_r FLOAT NOT NULL,
    sidebridge_l FLOAT NOT NULL
);

-- Functional tests
CREATE TABLE functional_tests (
    id INTEGER PRIMARY KEY REFERENCES fitness_tests(id) ON DELETE CASCADE,
    push_ups INTEGER NOT NULL,
    sit_ups INTEGER NOT NULL,
    pull_ups INTEGER NOT NULL
);

-- Combat tests (paratrooper)
CREATE TABLE combat_tests (
    id INTEGER PRIMARY KEY REFERENCES fitness_tests(id) ON DELETE CASCADE,
    running_time FLOAT NOT NULL,
    obstacle_passed BOOLEAN NOT NULL DEFAULT FALSE,
    rope_passed BOOLEAN NOT NULL DEFAULT FALSE
);

-- Combat swimming tests
CREATE TABLE combat_swimming_tests (
    id INTEGER PRIMARY KEY REFERENCES fitness_tests(id) ON DELETE CASCADE,
    swim_paased BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================
-- Test Sessions
-- ============================================

-- Test sessions table
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    serial_number_pti VARCHAR(50),
    datetime_start TIMESTAMP NOT NULL,
    canceled BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(255),
    type_test type_fitness_test_enum NOT NULL DEFAULT 'PHEF'
);

CREATE INDEX idx_test_sessions_datetime_start ON test_sessions(datetime_start);
CREATE INDEX idx_test_sessions_serial_number_pti ON test_sessions(serial_number_pti);

-- Many-to-many relationship: test sessions <-> fitness tests
CREATE TABLE session_fitness_tests (
    session_id INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    fitness_test_id INTEGER NOT NULL REFERENCES fitness_tests(id) ON DELETE CASCADE,
    PRIMARY KEY (session_id, fitness_test_id)
);

CREATE INDEX idx_session_fitness_tests_session_id ON session_fitness_tests(session_id);
CREATE INDEX idx_session_fitness_tests_fitness_test_id ON session_fitness_tests(fitness_test_id);

-- ============================================
-- Cross (Running Events)
-- ============================================

-- Cross events table
-- ... existing code ...
-- ============================================
-- Cross (Running Events)
-- ============================================

-- Cross events table
CREATE TABLE "cross"
(
    id             SERIAL PRIMARY KEY,
    datetime_start TIMESTAMP NOT NULL,
    distance       FLOAT     NOT NULL,
    executed       BOOLEAN   NOT NULL DEFAULT FALSE,
    description    VARCHAR(255)
);

CREATE INDEX idx_cross_datetime_start ON "cross" (datetime_start);
-- ... existing code ...
CREATE TABLE cross_runners
(
    cross_id  INTEGER NOT NULL REFERENCES "cross" (id) ON DELETE CASCADE,
    runner_id INTEGER NOT NULL REFERENCES runners (id) ON DELETE CASCADE,
    PRIMARY KEY (cross_id, runner_id)
);
-- ... existing code ...
COMMENT ON TABLE service_men IS 'Military service personnel records';
COMMENT ON TABLE fitness_tests IS 'Base table for polymorphic fitness test hierarchy';
COMMENT ON TABLE test_sessions IS 'Scheduled fitness test sessions';
COMMENT ON TABLE "cross" IS 'Cross-country running events';
COMMENT ON TABLE march IS 'Military march/ruck events';
COMMENT ON TABLE rooms IS 'Facility rooms available for reservation';
-- ... existing code ...;

CREATE INDEX idx_cross_datetime_start ON cross(datetime_start);

-- Runners table
CREATE TABLE runners (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50),
    running_time FLOAT NOT NULL
);

CREATE INDEX idx_runners_serial_number ON runners(serial_number);

-- Many-to-many relationship: cross <-> runners
CREATE TABLE cross_runners (
    cross_id INTEGER NOT NULL REFERENCES cross(id) ON DELETE CASCADE,
    runner_id INTEGER NOT NULL REFERENCES runners(id) ON DELETE CASCADE,
    PRIMARY KEY (cross_id, runner_id)
);

CREATE INDEX idx_cross_runners_cross_id ON cross_runners(cross_id);
CREATE INDEX idx_cross_runners_runner_id ON cross_runners(runner_id);

-- ============================================
-- March Events
-- ============================================

-- March table
CREATE TABLE march (
    id SERIAL PRIMARY KEY,
    service_number VARCHAR(50) REFERENCES service_men(service_number) ON DELETE CASCADE,
    distance FLOAT DEFAULT 30,
    succeeded BOOLEAN NOT NULL DEFAULT FALSE,
    datetime_executed TIMESTAMP NOT NULL
);

CREATE INDEX idx_march_service_number ON march(service_number);
CREATE INDEX idx_march_datetime_executed ON march(datetime_executed);

-- ============================================
-- HR Messages
-- ============================================

CREATE TABLE hr_messages (
    id SERIAL PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    datetime_created TIMESTAMP NOT NULL
);

CREATE INDEX idx_hr_messages_datetime_created ON hr_messages(datetime_created);

-- ============================================
-- Rooms and Reservations
-- ============================================

-- Rooms table
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL,
    location VARCHAR(100) NOT NULL
);

CREATE INDEX idx_rooms_name ON rooms(name);
CREATE INDEX idx_rooms_location ON rooms(location);

-- Reservations table
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    date TIMESTAMP NOT NULL DEFAULT NOW(),
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP NOT NULL DEFAULT NOW(),
    serial_number VARCHAR(50) NOT NULL,
    activity VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reservations_room_id ON reservations(room_id);
CREATE INDEX idx_reservations_date ON reservations(date);
CREATE INDEX idx_reservations_serial_number ON reservations(serial_number);
CREATE INDEX idx_reservations_start_time ON reservations(start_time);

-- ============================================
-- Comments and Additional Notes
-- ============================================

COMMENT ON TABLE users IS 'Application users with authentication and role-based access';
COMMENT ON TABLE audit_logs IS 'Audit trail for tracking user actions';
COMMENT ON TABLE service_men IS 'Military service personnel records';
COMMENT ON TABLE fitness_tests IS 'Base table for polymorphic fitness test hierarchy';
COMMENT ON TABLE test_sessions IS 'Scheduled fitness test sessions';
COMMENT ON TABLE cross IS 'Cross-country running events';
COMMENT ON TABLE march IS 'Military march/ruck events';
COMMENT ON TABLE rooms IS 'Facility rooms available for reservation';
COMMENT ON TABLE reservations IS 'Room booking reservations';

-- ============================================
-- Optional: Create Views for Common Queries
-- ============================================

-- View for active service men with unit details
CREATE VIEW v_active_service_men AS
SELECT
    sm.id,
    sm.first_name,
    sm.last_name,
    sm.mail,
    sm.rank,
    sm.service_number,
    sm.birthdate,
    sm.gender,
    sm.para,
    sm.ops_test,
    u.name AS unit_name,
    u.base_location,
    us.username,
    us.is_active AS user_is_active
FROM service_men sm
JOIN units u ON sm.unit_id = u.id
LEFT JOIN users us ON sm.user_id = us.id
WHERE us.is_active IS NULL OR us.is_active = TRUE;

-- View for upcoming test sessions
CREATE VIEW v_upcoming_test_sessions AS
SELECT
    ts.id,
    ts.serial_number_pti,
    ts.datetime_start,
    ts.type_test,
    ts.description,
    COUNT(sft.fitness_test_id) AS test_count
FROM test_sessions ts
LEFT JOIN session_fitness_tests sft ON ts.id = sft.session_id
WHERE ts.canceled = FALSE
  AND ts.datetime_start > NOW()
GROUP BY ts.id, ts.serial_number_pti, ts.datetime_start, ts.type_test, ts.description
ORDER BY ts.datetime_start;

-- ============================================
-- Grants (adjust based on your security needs)
-- ============================================

-- Example: Create application user and grant permissions
-- CREATE USER warriorfit_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE warriorfit_db TO warriorfit_app;
-- GRANT USAGE ON SCHEMA public TO warriorfit_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO warriorfit_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO warriorfit_app;
