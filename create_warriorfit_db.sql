-- ============================================================================
-- WarriorFit — full database creation script
--   1. Enum types + all tables (schema, generated from the ORM models)
--   2. Two seed ADMIN users
--
-- Login credentials (CHANGE THESE after first login):
--   admin / ChangeMe!Admin1
--   admin2 / ChangeMe!Admin2
--
-- Run against an EMPTY database:
--   createdb warriorfit
--   psql "$PROD_DATABASE_URL" -f create_warriorfit_db.sql
-- ============================================================================

-- ---------- 1. SCHEMA ----------

CREATE TYPE role AS ENUM ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');

CREATE TYPE typefitnesstest AS ENUM ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING', 'MFFT_EVAL');

CREATE TYPE gender AS ENUM ('M', 'F');

CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	role role NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	serial_number VARCHAR(50), 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email), 
	UNIQUE (serial_number)
);

CREATE TABLE user_consents (
	id SERIAL NOT NULL, 
	service_number VARCHAR(50) NOT NULL, 
	consent_type VARCHAR(64) NOT NULL, 
	version VARCHAR(16) NOT NULL, 
	consent_given_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	withdrawn_at TIMESTAMP WITHOUT TIME ZONE, 
	ip_address VARCHAR(45), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_consent_type_version UNIQUE (service_number, consent_type, version)
);

CREATE INDEX ix_user_consents_service_number ON user_consents (service_number);

CREATE TABLE test_sessions (
	id SERIAL NOT NULL, 
	serial_number_pti VARCHAR(50), 
	datetime_start TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	canceled BOOLEAN NOT NULL, 
	description VARCHAR(255), 
	type_test typefitnesstest NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE "cross" (
	id SERIAL NOT NULL, 
	datetime_start TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	distance FLOAT NOT NULL, 
	executed BOOLEAN NOT NULL, 
	description VARCHAR(255), 
	PRIMARY KEY (id)
);

CREATE TABLE runners (
	id SERIAL NOT NULL, 
	serial_number VARCHAR(50), 
	running_time FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE units (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	base_location VARCHAR(150) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_units_name UNIQUE (name)
);

CREATE TABLE hr_messages (
	id SERIAL NOT NULL, 
	message VARCHAR(255) NOT NULL, 
	datetime_created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	attempt_count INTEGER NOT NULL, 
	next_retry_at TIMESTAMP WITHOUT TIME ZONE, 
	dead_letter BOOLEAN NOT NULL, 
	last_error VARCHAR(500), 
	PRIMARY KEY (id)
);

CREATE TABLE rooms (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	capacity INTEGER NOT NULL, 
	location VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(50) NOT NULL, 
	details JSON, 
	ip_address VARCHAR(45), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE cross_runners (
	cross_id INTEGER NOT NULL, 
	runner_id INTEGER NOT NULL, 
	PRIMARY KEY (cross_id, runner_id), 
	FOREIGN KEY(cross_id) REFERENCES "cross" (id), 
	FOREIGN KEY(runner_id) REFERENCES runners (id)
);

CREATE TABLE service_men (
	id SERIAL NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	mail VARCHAR(120) NOT NULL, 
	rank INTEGER NOT NULL, 
	service_number VARCHAR(50) NOT NULL, 
	birthdate DATE NOT NULL, 
	gender gender NOT NULL, 
	unit_id INTEGER NOT NULL, 
	para BOOLEAN NOT NULL, 
	ops_test BOOLEAN NOT NULL, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_service_men_service_number UNIQUE (service_number), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_service_men_unit_id ON service_men (unit_id);

CREATE UNIQUE INDEX ix_service_men_user_id ON service_men (user_id);

CREATE TABLE reservations (
	id SERIAL NOT NULL, 
	room_id INTEGER NOT NULL, 
	date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	start_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	end_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	serial_number VARCHAR(50) NOT NULL, 
	activity VARCHAR(100) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(room_id) REFERENCES rooms (id)
);

CREATE TABLE fitness_tests (
	id SERIAL NOT NULL, 
	serial_number VARCHAR(50), 
	type VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(serial_number) REFERENCES service_men (service_number)
);

CREATE INDEX ix_fitness_tests_serial_number ON fitness_tests (serial_number);

CREATE TABLE march (
	id SERIAL NOT NULL, 
	service_number VARCHAR(50), 
	distance FLOAT, 
	succeeded BOOLEAN NOT NULL, 
	datetime_executed TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(service_number) REFERENCES service_men (service_number)
);

CREATE INDEX ix_march_service_number ON march (service_number);

CREATE TABLE phef_tests (
	id INTEGER NOT NULL, 
	running_time FLOAT NOT NULL, 
	"sideBridge_r" FLOAT NOT NULL, 
	"sideBridge_l" FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES fitness_tests (id)
);

CREATE TABLE functional_tests (
	id INTEGER NOT NULL, 
	push_ups INTEGER NOT NULL, 
	sit_ups INTEGER NOT NULL, 
	pull_ups INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES fitness_tests (id)
);

CREATE TABLE combat_tests (
	id INTEGER NOT NULL, 
	running_time FLOAT NOT NULL, 
	obstacle_passed BOOLEAN NOT NULL, 
	rope_passed BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES fitness_tests (id)
);

CREATE TABLE combat_swimming_tests (
	id INTEGER NOT NULL, 
	swim_paased BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES fitness_tests (id)
);

CREATE TABLE mfft_eval_tests (
	id INTEGER NOT NULL, 
	pull_ups INTEGER NOT NULL, 
	burpees_step_over INTEGER NOT NULL, 
	farmer_walk_m INTEGER NOT NULL, 
	push_ups_release INTEGER NOT NULL, 
	casualty_drag_m INTEGER NOT NULL, 
	sandbag_carry_m INTEGER NOT NULL, 
	combat_run_seconds INTEGER NOT NULL, 
	combat_swim_seconds INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES fitness_tests (id)
);

CREATE TABLE session_fitness_tests (
	session_id INTEGER NOT NULL, 
	fitness_test_id INTEGER NOT NULL, 
	PRIMARY KEY (session_id, fitness_test_id), 
	FOREIGN KEY(session_id) REFERENCES test_sessions (id), 
	FOREIGN KEY(fitness_test_id) REFERENCES fitness_tests (id)
);

-- ---------- 2. SEED ADMIN USERS ----------

BEGIN;

INSERT INTO users (username, email, password_hash, role, is_active, serial_number)
VALUES ('admin', 'admin@warriorfit.local', '$argon2id$v=19$m=65536,t=3,p=4$PZ6y9TqIFmETyTmnaUISrQ$rcW1UG9pbR0DiuemOQrFCc8BSA0LsB9f4v6UohEleEM', 'ADMIN', TRUE, 'ADM-0001')
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    serial_number = EXCLUDED.serial_number;

INSERT INTO users (username, email, password_hash, role, is_active, serial_number)
VALUES ('admin2', 'admin2@warriorfit.local', '$argon2id$v=19$m=65536,t=3,p=4$1WYl5tMPTf1hLBbAdtsbXg$AA5R5uOn04YEWZ3QEuibu0XkDmUOHfo3rqNRRnPTBlU', 'ADMIN', TRUE, 'ADM-0002')
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    serial_number = EXCLUDED.serial_number;

COMMIT;
