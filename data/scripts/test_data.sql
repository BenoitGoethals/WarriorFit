CREATE EXTENSION IF NOT EXISTS pgcrypto;


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
('Benoit', 'benoit@example.com', public.crypt('password', public.gen_salt('bf')), NOW(), 'USER', TRUE, 'benoit');

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
INSERT INTO test_sessions (serial_number_pti, datetime_start, executed, description, type_test) VALUES
('pti', '2025-08-06 09:00:00', false, 'Regular fitness evaluation session', 'PHEF'),
('pti2', '2025-08-07 09:00:00', false, 'Combat readiness assessment', 'COMBAT'),
('pti3', '2025-08-08 09:00:00', false, 'Standard physical evaluation', 'PHEF'),
('pti4', '2025-08-09 09:00:00', false, 'Quarterly fitness check', 'PHEF'),
('pti5', '2025-08-10 09:00:00', false, 'Annual physical assessment', 'PHEF'),
('pti6', '2025-08-11 09:00:00', false, 'Regular training evaluation', 'PHEF'),
('pti7', '2025-08-12 09:00:00', false, 'Physical readiness test', 'PHEF'),
('pti8', '2025-08-13 09:00:00', false, 'Standard fitness evaluation', 'PHEF'),
('pti9', '2025-08-14 09:00:00', false, 'Combat fitness assessment', 'COMBAT'),
('pti11', '2025-08-15 09:00:00', false, 'Regular physical test session', 'PHEF'),
('pti12', '2025-08-16 09:00:00', false, 'Monthly fitness evaluation', 'PHEF'),
('pti13', '2025-08-17 09:00:00', false, 'Standard physical test', 'PHEF'),
('ptidas', '2025-08-18 09:00:00', false, 'Regular assessment session', 'PHEF'),
('pti44', '2025-08-19 09:00:00', false, 'Fitness qualification test', 'PHEF'),
('pti77', '2025-08-20 09:00:00', false, 'Physical conditioning check', 'PHEF'),
('pti99', '2025-08-21 09:00:00', false, 'Regular evaluation session', 'PHEF'),
('pti00', '2025-08-22 09:00:00', false, 'Standard fitness test', 'PHEF'),
('pti454', '2025-08-23 09:00:00', false, 'Physical performance assessment', 'PHEF'),
('pti33', '2025-08-24 09:00:00', false, 'Combat readiness evaluation', 'COMBAT'),
('pti88', '2025-08-25 09:00:00', false, 'Final fitness session', 'PHEF');

