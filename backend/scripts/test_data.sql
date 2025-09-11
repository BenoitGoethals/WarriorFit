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
('user10', 'user10@example.com', crypt('password10', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN010');



-- Test Sessions data
INSERT INTO test_sessions (serial_number_pti, datetime_start, executed, description, type_test) VALUES
('PTI-2025-001', '2025-08-06 09:00:00', false, 'Regular fitness evaluation session', 'PHEF'),
('PTI-2025-002', '2025-08-07 09:00:00', false, 'Combat readiness assessment', 'COMBAT'),
('PTI-2025-003', '2025-08-08 09:00:00', false, 'Standard physical evaluation', 'PHEF'),
('PTI-2025-004', '2025-08-09 09:00:00', false, 'Quarterly fitness check', 'PHEF'),
('PTI-2025-005', '2025-08-10 09:00:00', false, 'Annual physical assessment', 'PHEF'),
('PTI-2025-006', '2025-08-11 09:00:00', false, 'Regular training evaluation', 'PHEF'),
('PTI-2025-007', '2025-08-12 09:00:00', false, 'Physical readiness test', 'PHEF'),
('PTI-2025-008', '2025-08-13 09:00:00', false, 'Standard fitness evaluation', 'PHEF'),
('PTI-2025-009', '2025-08-14 09:00:00', false, 'Combat fitness assessment', 'COMBAT'),
('PTI-2025-010', '2025-08-15 09:00:00', false, 'Regular physical test session', 'PHEF'),
('PTI-2025-011', '2025-08-16 09:00:00', false, 'Monthly fitness evaluation', 'PHEF'),
('PTI-2025-012', '2025-08-17 09:00:00', false, 'Standard physical test', 'PHEF'),
('PTI-2025-013', '2025-08-18 09:00:00', false, 'Regular assessment session', 'PHEF'),
('PTI-2025-014', '2025-08-19 09:00:00', false, 'Fitness qualification test', 'PHEF'),
('PTI-2025-015', '2025-08-20 09:00:00', false, 'Physical conditioning check', 'PHEF'),
('PTI-2025-016', '2025-08-21 09:00:00', false, 'Regular evaluation session', 'PHEF'),
('PTI-2025-017', '2025-08-22 09:00:00', false, 'Standard fitness test', 'PHEF'),
('PTI-2025-018', '2025-08-23 09:00:00', false, 'Physical performance assessment', 'PHEF'),
('PTI-2025-019', '2025-08-24 09:00:00', false, 'Combat readiness evaluation', 'COMBAT'),
('PTI-2025-020', '2025-08-25 09:00:00', false, 'Final fitness session', 'PHEF');
