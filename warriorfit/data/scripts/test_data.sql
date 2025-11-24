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


INSERT INTO mars(distance, succeeded, datetime_executed, service_number) VALUES (100, true, '2025-08-06 09:00:00', 'BE-20250001');
INSERT INTO mars(distance, succeeded, datetime_executed, service_number)
VALUES (23, true, '2025-08-06 09:30:00', 'BE-20250002'),
       (25, true, '2025-08-06 10:00:00', 'BE-20250003'),
       (28, true, '2025-08-06 10:30:00', 'BE-20250004'),
       (21, true, '2025-08-06 11:00:00', 'BE-20250005'),
       (27, true, '2025-08-06 11:30:00', 'BE-20250006'),
       (24, true, '2025-08-06 12:00:00', 'BE-20250007'),
       (26, true, '2025-08-06 12:30:00', 'BE-20250008'),
       (29, true, '2025-08-06 13:00:00', 'BE-20250009'),
       (22, true, '2025-08-06 13:30:00', 'BE-20250010'),
       (30, true, '2025-08-06 14:00:00', 'BE-20250011'),
       (20, true, '2025-08-07 09:00:00', 'BE-20250012'),
       (25, true, '2025-08-07 09:30:00', 'BE-20250013'),
       (28, true, '2025-08-07 10:00:00', 'BE-20250014'),
       (23, true, '2025-08-07 10:30:00', 'BE-20250015'),
       (26, true, '2025-08-07 11:00:00', 'BE-20250016'),
       (29, true, '2025-08-07 11:30:00', 'BE-20250017'),
       (21, true, '2025-08-07 12:00:00', 'BE-20250018'),
       (24, true, '2025-08-07 12:30:00', 'BE-20250019'),
       (27, true, '2025-08-07 13:00:00', 'BE-20250020'),
       (30, true, '2025-08-07 13:30:00', 'BE-20250021'),
       (22, true, '2025-08-08 09:00:00', 'BE-20250022'),
       (25, true, '2025-08-08 09:30:00', 'BE-20250023'),
       (28, true, '2025-08-08 10:00:00', 'BE-20250024'),
       (21, true, '2025-08-08 10:30:00', 'BE-20250025'),
       (24, true, '2025-08-08 11:00:00', 'BE-20250026'),
       (27, true, '2025-08-08 11:30:00', 'BE-20250027'),
       (30, true, '2025-08-08 12:00:00', 'BE-20250028'),
       (23, true, '2025-08-08 12:30:00', 'BE-20250029'),
       (26, true, '2025-08-08 13:00:00', 'BE-20250030'),
       (29, true, '2025-08-08 13:30:00', 'BE-20250031'),
       (20, true, '2025-08-09 09:00:00', 'BE-20250032'),
       (25, true, '2025-08-09 09:30:00', 'BE-20250033'),
       (28, true, '2025-08-09 10:00:00', 'BE-20250034'),
       (22, true, '2025-08-09 10:30:00', 'BE-20250035'),
       (26, true, '2025-08-09 11:00:00', 'BE-20250036'),
       (29, true, '2025-08-09 11:30:00', 'BE-20250037'),
       (21, true, '2025-08-09 12:00:00', 'BE-20250038'),
       (24, true, '2025-08-09 12:30:00', 'BE-20250039'),
       (27, true, '2025-08-09 13:00:00', 'BE-20250040'),
       (30, true, '2025-08-09 13:30:00', 'BE-20250041'),
       (23, true, '2025-08-10 09:00:00', 'BE-20250042'),
       (26, true, '2025-08-10 09:30:00', 'BE-20250043'),
       (29, true, '2025-08-10 10:00:00', 'BE-20250044'),
       (22, true, '2025-08-10 10:30:00', 'BE-20250045'),
       (25, true, '2025-08-10 11:00:00', 'BE-20250046'),
       (28, true, '2025-08-10 11:30:00', 'BE-20250047'),
       (21, true, '2025-08-10 12:00:00', 'BE-20250048'),
       (24, true, '2025-08-10 12:30:00', 'BE-20250049'),
       (27, true, '2025-08-10 13:00:00', 'BE-20250050'),
       (30, true, '2025-08-10 13:30:00', 'BE-20250051');

