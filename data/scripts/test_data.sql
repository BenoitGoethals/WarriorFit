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
-- Column name changed from executed -> canceled to match SQLAlchemy model
INSERT INTO test_sessions (serial_number_pti, datetime_start, canceled, description, type_test)
VALUES ('SNPTI', '2025-08-06 09:00:00', false, 'Regular fitness evaluation session', 'PHEF'),
       ('SNPTI2', '2025-08-07 09:00:00', false, 'Combat readiness assessment', 'COMBAT'),
       ('SNPTI3', '2025-08-08 09:00:00', false, 'Standard physical evaluation', 'PHEF'),
       ('SNPTI4', '2025-08-09 09:00:00', false, 'Quarterly fitness check', 'PHEF'),
       ('SNPTI5', '2025-08-10 09:00:00', false, 'Annual physical assessment', 'PHEF'),
       ('SNPTI6', '2025-08-11 09:00:00', false, 'Regular training evaluation', 'PHEF'),
       ('SNPTI7', '2025-08-12 09:00:00', false, 'Physical readiness test', 'PHEF'),
       ('SNPTI8', '2025-08-13 09:00:00', false, 'Standard fitness evaluation', 'PHEF'),
       ('SNPTI9', '2025-08-14 09:00:00', false, 'Combat fitness assessment', 'COMBAT')

