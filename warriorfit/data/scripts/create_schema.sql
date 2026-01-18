-- WarriorFit Database Schema
-- PostgreSQL Complete Schema Generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS hr_messages CASCADE;
DROP TABLE IF EXISTS march CASCADE;
DROP TABLE IF EXISTS cross_runners CASCADE;
DROP TABLE IF EXISTS runners CASCADE;
DROP TABLE IF EXISTS "cross" CASCADE;
DROP TABLE IF EXISTS session_fitness_tests CASCADE;
DROP TABLE IF EXISTS test_sessions CASCADE;
DROP TABLE IF EXISTS combat_swimming_tests CASCADE;
DROP TABLE IF EXISTS combat_tests CASCADE;
DROP TABLE IF EXISTS functional_tests CASCADE;
DROP TABLE IF EXISTS phef_tests CASCADE;
DROP TABLE IF EXISTS fitness_tests CASCADE;
DROP TABLE IF EXISTS service_men CASCADE;
DROP TABLE IF EXISTS units CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop existing types
DROP TYPE IF EXISTS gender_enum CASCADE;
DROP TYPE IF EXISTS role_enum CASCADE;
DROP TYPE IF EXISTS typefitnesstest_enum CASCADE;

-- Create ENUM types
CREATE TYPE gender_enum AS ENUM ('M', 'F');

CREATE TYPE role_enum AS ENUM ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');

CREATE TYPE typefitnesstest_enum AS ENUM ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING');

-- ================================
-- Core Tables
-- ================================

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    role role_enum NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    serial_number VARCHAR(50) UNIQUE
);

-- Audit logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    details JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Units table
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_location VARCHAR(150) NOT NULL,
    CONSTRAINT uq_units_name UNIQUE (name)
);

-- Service men table
CREATE TABLE service_men (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    mail VARCHAR(120) NOT NULL,
    rank INTEGER NOT NULL,
    service_number VARCHAR(50) NOT NULL,
    birthdate DATE NOT NULL,
    gender gender_enum NOT NULL,
    unit_id INTEGER NOT NULL,
    para BOOLEAN NOT NULL DEFAULT FALSE,
    ops_test BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INTEGER UNIQUE,
    CONSTRAINT uq_service_men_service_number UNIQUE (service_number),
    CONSTRAINT fk_service_men_unit FOREIGN KEY (unit_id) REFERENCES units(id),
    CONSTRAINT fk_service_men_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ================================
-- Fitness Tests (Polymorphic)
-- ================================

-- Base fitness tests table
CREATE TABLE fitness_tests (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50),
    type VARCHAR(50),
    CONSTRAINT fk_fitness_tests_servicemen FOREIGN KEY (serial_number)
        REFERENCES service_men(service_number)
);

-- PHEF tests table
CREATE TABLE phef_tests (
    id INTEGER PRIMARY KEY,
    running_time FLOAT NOT NULL,
    sidebridge_r FLOAT NOT NULL,
    sidebridge_l FLOAT NOT NULL,
    CONSTRAINT fk_phef_tests_fitness FOREIGN KEY (id) REFERENCES fitness_tests(id) ON DELETE CASCADE
);

-- Functional tests table
CREATE TABLE functional_tests (
    id INTEGER PRIMARY KEY,
    push_ups INTEGER NOT NULL,
    sit_ups INTEGER NOT NULL,
    pull_ups INTEGER NOT NULL,
    CONSTRAINT fk_functional_tests_fitness FOREIGN KEY (id) REFERENCES fitness_tests(id) ON DELETE CASCADE
);

-- Combat tests table
CREATE TABLE combat_tests (
    id INTEGER PRIMARY KEY,
    running_time FLOAT NOT NULL,
    obstacle_passed BOOLEAN NOT NULL DEFAULT FALSE,
    rope_passed BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_combat_tests_fitness FOREIGN KEY (id) REFERENCES fitness_tests(id) ON DELETE CASCADE
);

-- Combat swimming tests table
CREATE TABLE combat_swimming_tests (
    id INTEGER PRIMARY KEY,
    swim_paased BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_combat_swimming_tests_fitness FOREIGN KEY (id) REFERENCES fitness_tests(id) ON DELETE CASCADE
);

-- Test sessions table
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    serial_number_pti VARCHAR(50),
    datetime_start TIMESTAMP NOT NULL,
    canceled BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(255),
    type_test typefitnesstest_enum NOT NULL DEFAULT 'PHEF'
);

-- Session fitness tests association table (Many-to-Many)
CREATE TABLE session_fitness_tests (
    session_id INTEGER NOT NULL,
    fitness_test_id INTEGER NOT NULL,
    PRIMARY KEY (session_id, fitness_test_id),
    CONSTRAINT fk_session_fitness_tests_session FOREIGN KEY (session_id)
        REFERENCES test_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_fitness_tests_fitness FOREIGN KEY (fitness_test_id)
        REFERENCES fitness_tests(id) ON DELETE CASCADE
);

-- ================================
-- Cross/Running Events
-- ================================

-- Cross table
CREATE TABLE "cross" (
    id SERIAL PRIMARY KEY,
    datetime_start TIMESTAMP NOT NULL,
    distance FLOAT NOT NULL,
    executed BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(255)
);

-- Runners table
CREATE TABLE runners (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50),
    running_time FLOAT NOT NULL
);

-- Cross runners association table (Many-to-Many)
CREATE TABLE cross_runners (
    cross_id INTEGER NOT NULL,
    runner_id INTEGER NOT NULL,
    PRIMARY KEY (cross_id, runner_id),
    CONSTRAINT fk_cross_runners_cross FOREIGN KEY (cross_id)
        REFERENCES "cross"(id) ON DELETE CASCADE,
    CONSTRAINT fk_cross_runners_runner FOREIGN KEY (runner_id)
        REFERENCES runners(id) ON DELETE CASCADE
);

-- ================================
-- March Events
-- ================================

-- March table
CREATE TABLE march (
    id SERIAL PRIMARY KEY,
    service_number VARCHAR(50),
    distance FLOAT DEFAULT 30,
    succeeded BOOLEAN NOT NULL DEFAULT FALSE,
    datetime_executed TIMESTAMP NOT NULL,
    CONSTRAINT fk_march_servicemen FOREIGN KEY (service_number)
        REFERENCES service_men(service_number)
);

-- ================================
-- HR Messages
-- ================================

-- HR messages table
CREATE TABLE hr_messages (
    id SERIAL PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    datetime_created TIMESTAMP NOT NULL
);

-- ================================
-- Room Reservations
-- ================================

-- Rooms table
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL,
    location VARCHAR(100) NOT NULL
);

-- Reservations table
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL,
    date TIMESTAMP DEFAULT NOW(),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP DEFAULT NOW(),
    serial_number VARCHAR(50) NOT NULL,
    activity VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_reservations_room FOREIGN KEY (room_id)
        REFERENCES rooms(id) ON DELETE CASCADE
);

-- ================================
-- Indexes for Performance
-- ================================

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_serial_number ON users(serial_number);
CREATE INDEX idx_users_role ON users(role);

-- Audit logs indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Service men indexes
CREATE INDEX idx_service_men_unit_id ON service_men(unit_id);
CREATE INDEX idx_service_men_user_id ON service_men(user_id);
CREATE INDEX idx_service_men_service_number ON service_men(service_number);
CREATE INDEX idx_service_men_rank ON service_men(rank);
CREATE INDEX idx_service_men_gender ON service_men(gender);

-- Fitness tests indexes
CREATE INDEX idx_fitness_tests_serial_number ON fitness_tests(serial_number);
CREATE INDEX idx_fitness_tests_type ON fitness_tests(type);

-- Test sessions indexes
CREATE INDEX idx_test_sessions_datetime_start ON test_sessions(datetime_start);
CREATE INDEX idx_test_sessions_type_test ON test_sessions(type_test);
CREATE INDEX idx_test_sessions_canceled ON test_sessions(canceled);

-- Session fitness tests indexes
CREATE INDEX idx_session_fitness_tests_session ON session_fitness_tests(session_id);
CREATE INDEX idx_session_fitness_tests_fitness ON session_fitness_tests(fitness_test_id);

-- March indexes
CREATE INDEX idx_march_service_number ON march(service_number);
CREATE INDEX idx_march_datetime_executed ON march(datetime_executed);

-- Cross indexes
CREATE INDEX idx_cross_datetime_start ON "cross"(datetime_start);
CREATE INDEX idx_cross_executed ON "cross"(executed);

-- Cross runners indexes
CREATE INDEX idx_cross_runners_cross ON cross_runners(cross_id);
CREATE INDEX idx_cross_runners_runner ON cross_runners(runner_id);

-- Reservations indexes
CREATE INDEX idx_reservations_room_id ON reservations(room_id);
CREATE INDEX idx_reservations_date ON reservations(date);
CREATE INDEX idx_reservations_start_time ON reservations(start_time);
CREATE INDEX idx_reservations_serial_number ON reservations(serial_number);

-- ================================
-- Comments for Documentation
-- ================================

COMMENT ON TABLE users IS 'System users with authentication and role information';
COMMENT ON TABLE audit_logs IS 'Audit trail for tracking user actions on entities';
COMMENT ON TABLE units IS 'Military units with base location information';
COMMENT ON TABLE service_men IS 'Service personnel with personal and military information';
COMMENT ON TABLE fitness_tests IS 'Base table for polymorphic fitness test records';
COMMENT ON TABLE phef_tests IS 'Physical Efficiency (PHEF) test results';
COMMENT ON TABLE functional_tests IS 'Functional fitness test results (push-ups, sit-ups, pull-ups)';
COMMENT ON TABLE combat_tests IS 'Combat test results for paratroopers';
COMMENT ON TABLE combat_swimming_tests IS 'Combat swimming test results';
COMMENT ON TABLE test_sessions IS 'Organized fitness testing sessions';
COMMENT ON TABLE session_fitness_tests IS 'Association between test sessions and fitness tests';
COMMENT ON TABLE "cross" IS 'Cross-country running events';
COMMENT ON TABLE runners IS 'Individual runner records for cross events';
COMMENT ON TABLE cross_runners IS 'Association between cross events and runners';
COMMENT ON TABLE march IS 'March event records for service personnel';
COMMENT ON TABLE hr_messages IS 'HR notification messages';
COMMENT ON TABLE rooms IS 'Facility rooms available for reservation';
COMMENT ON TABLE reservations IS 'Room reservation records';

COMMENT ON COLUMN service_men.rank IS 'Integer representation of military rank (1-23)';
COMMENT ON COLUMN service_men.para IS 'Indicates if serviceman is a paratrooper';
COMMENT ON COLUMN service_men.ops_test IS 'Indicates if serviceman takes operational tests';
COMMENT ON COLUMN fitness_tests.type IS 'Discriminator for polymorphic inheritance (phef_test, functional_test, combat_test, combat_swimming_test)';
COMMENT ON COLUMN test_sessions.serial_number_pti IS 'Serial number of Physical Training Instructor organizing the session';

-- ================================
-- Constraints Summary
-- ================================

-- UNIQUE constraints:
-- - users.username
-- - users.email
-- - users.serial_number
-- - service_men.service_number
-- - service_men.user_id
-- - units.name

-- FOREIGN KEY constraints:
-- - audit_logs.user_id -> users.id
-- - service_men.unit_id -> units.id
-- - service_men.user_id -> users.id
-- - fitness_tests.serial_number -> service_men.service_number
-- - phef_tests.id -> fitness_tests.id
-- - functional_tests.id -> fitness_tests.id
-- - combat_tests.id -> fitness_tests.id
-- - combat_swimming_tests.id -> fitness_tests.id
-- - session_fitness_tests.session_id -> test_sessions.id
-- - session_fitness_tests.fitness_test_id -> fitness_tests.id
-- - cross_runners.cross_id -> cross.id
-- - cross_runners.runner_id -> runners.id
-- - march.service_number -> service_men.service_number
-- - reservations.room_id -> rooms.id

-- ================================
-- Sample Data for Testing (Optional)
-- ================================

-- Insert a sample unit
-- INSERT INTO units (name, base_location) VALUES ('1st Battalion', 'Brussels');

-- Insert a sample user
-- INSERT INTO users (username, email, password_hash, role)
-- VALUES ('admin', 'admin@example.com', 'hashed_password_here', 'ADMIN');
