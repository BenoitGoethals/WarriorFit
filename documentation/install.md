```sql
create type typefitnesstest as enum ('PHEF', 'COMBAT', 'FUNCTIONAL', 'SWIMMING');

alter type typefitnesstest owner to benoi;

create type role as enum ('ADMIN', 'USER', 'GUEST', 'PTI', 'PLANNER', 'APTI');

alter type role owner to benoi;

create type gender as enum ('M', 'F');

alter type gender owner to benoi;

create table alembic_version
(
    version_num varchar(32) not null
        constraint alembic_version_pkc
            primary key
);

alter table alembic_version
    owner to benoi;

create table fitness_tests
(
    id            serial
        primary key,
    serial_number varchar(50),
    type          varchar(50)
);

alter table fitness_tests
    owner to benoi;

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
    owner to benoi;

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
    owner to benoi;

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
    owner to benoi;

create table combat_swimming_tests
(
    id          integer not null
        primary key
        references fitness_tests,
    swim_paased boolean not null
);

alter table combat_swimming_tests
    owner to benoi;

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
    owner to benoi;


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
    owner to benoi;

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
    owner to benoi;

create table session_fitness_tests
(
    session_id      integer not null
        references test_sessions,
    fitness_test_id integer not null
        references fitness_tests,
    primary key (session_id, fitness_test_id)
);

alter table session_fitness_tests
    owner to benoi;

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
    owner to benoi;

create table runners
(
    id            serial
        primary key,
    serial_number varchar(50),
    running_time  double precision not null
);

alter table runners
    owner to benoi;

create table cross_runners
(
    cross_id  integer not null
        references "cross",
    runner_id integer not null
        references runners,
    primary key (cross_id, runner_id)
);

alter table cross_runners
    owner to benoi;

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
    owner to benoi;

create table service_men
(
    id             serial
        primary key,
    first_name     varchar(80)  not null,
    last_name      varchar(80)  not null,
    mail           varchar(120) not null,
    rank           varchar(50)  not null,
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
    owner to benoi;

create index ix_service_men_unit_id
    on service_men (unit_id);

create table mars
(
    id                serial
        primary key,
    distance          double precision,
    succeeded         boolean   not null,
    datetime_executed timestamp not null,
    service_number    varchar(50)
);

alter table mars
    owner to benoi;

create index ix_mars_service_number
    on mars (service_number);

create table hr_messages
(
    id               serial
        primary key,
    message          varchar(255) not null,
    datetime_created timestamp    not null
);

alter table hr_messages
    owner to benoi;

```