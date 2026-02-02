CREATE EXTENSION IF NOT EXISTS pgcrypto;


INSERT INTO users (username, email, password_hash, created_at, role, is_active, serial_number) VALUES
('super', 'adminsuper@example.com', crypt('admin', gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'super');


INSERT INTO users (username, email, password_hash, created_at, role, is_active, serial_number) VALUES
('user1', 'user1@example.com', crypt('password', gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'SN001'),
('user2', 'user2@example.com', crypt('password2', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN002'),
('planner', 'user3@example.com', crypt('password', gen_salt('bf')), NOW(), 'PLANNER', TRUE, 'SN003'),
('user9', 'user9@example.com', crypt('password9', gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'SN009'),
('user10', 'user10@example.com', crypt('password10', gen_salt('bf')), NOW(), 'USER', TRUE, 'SN010'),
('pti', 'ptitest@example.com', crypt('pti', gen_salt('bf')), NOW(), 'USER', TRUE, 'pti'),
('tester', 'tester@example.com', public.crypt('tester007', public.gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'benoit'),
('benoit', 'benoit@example.com', public.crypt('ranger14!', public.gen_salt('bf')), NOW(), 'ADMIN', TRUE, 'tester');

INSERT INTO users (username, email, password_hash, created_at, role, is_active, serial_number)
VALUES ('pti2', 'ptitest2@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'snpt12'),
       ('pti20', 'pti2@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI2'),
       ('pti3', 'pti3@example.com', crypt('password', gen_salt('bf')), NOW(), 'APTI', TRUE, 'SNPTI3'),
       ('pti10', 'pti10@example.com', crypt('password', gen_salt('bf')), NOW(), 'PTI', TRUE, 'SNPTI10');

-- Test Sessions data
-- Column name changed from executed -> canceled to match SQLAlchemy model
INSERT INTO test_sessions (serial_number_pti, datetime_start, canceled, description, type_test)
VALUES ('SNPTI', '2025-12-06 09:00:00', false, 'Regular fitness evaluation session', 'PHEF'),
       ('SNPTI2', '2025-12-07 09:00:00', false, 'Combat readiness assessment', 'COMBAT'),
       ('SNPTI3', '2025-12-08 09:00:00', false, 'Standard physical evaluation', 'PHEF'),
       ('SNPTI4', '2025-12-09 09:00:00', false, 'Quarterly fitness check', 'PHEF'),
       ('SNPTI5', '2025-12-10 09:00:00', false, 'Annual physical assessment', 'PHEF'),
       ('SNPTI6', '2025-12-11 09:00:00', false, 'Regular training evaluation', 'PHEF'),
       ('SNPTI7', '2025-12-12 09:00:00', false, 'Physical readiness test', 'PHEF'),
       ('SNPTI8', '2025-12-13 09:00:00', false, 'Standard fitness evaluation', 'PHEF'),
       ('SNPTI9', '2025-12-14 09:00:00', false, 'Combat fitness assessment', 'COMBAT');


INSERT INTO march(distance, succeeded, datetime_executed, service_number) VALUES (100, true, '2025-08-06 09:00:00', 'BE-20250001');
INSERT INTO march(distance, succeeded, datetime_executed, service_number)
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

INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Mathis','De Graaf','benoit@albatros.be','BE-20250017','1983-04-06','M'::public.gender,1,false,false,3),
	 ('Lars','Martens','benoit@albatros.be','BE-20250021','1999-04-23','M'::public.gender,1,false,false,3),
	 ('Victor','Goossens','benoit@albatros.be','BE-20250011','1998-06-19','M'::public.gender,1,true,true,3),
	 ('Elias','Wauters','benoit@albatros.be','BE-20250025','1996-05-05','M'::public.gender,1,false,false,3),
	 ('Chloé','Renard','benoit@albatros.be','BE-20250026','1990-09-12','F'::public.gender,1,false,false,3),
	 ('Rayan','Aerts','benoit@albatros.be','BE-20250027','1982-01-26','M'::public.gender,1,false,false,3),
	 ('Elise','Declerck','benoit@albatros.be','BE-20250028','1979-03-31','F'::public.gender,1,false,false,3),
	 ('Baptiste','Verschueren','benoit@albatros.be','BE-20250029','1974-07-19','M'::public.gender,1,false,false,3),
	 ('Eva','Meunier','benoit@albatros.be','BE-20250030','1988-10-28','F'::public.gender,1,false,false,3),
	 ('Mohamed','El Hadi','benoit@albatros.be','BE-20250031','1997-06-14','M'::public.gender,1,false,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Charlotte','Devos','benoit@albatros.be','BE-20250032','1994-01-18','F'::public.gender,1,false,false,3),
	 ('Nathan','Van Damme','benoit@albatros.be','BE-20250033','1990-04-03','M'::public.gender,1,false,false,3),
	 ('Clara','Vandamme','benoit@albatros.be','BE-20250034','1986-11-22','F'::public.gender,1,false,false,3),
	 ('Simon','Vandenbossche','benoit@albatros.be','BE-20250035','1995-07-07','M'::public.gender,1,false,false,3),
	 ('Anaïs','Moreau','benoit@albatros.be','BE-20250036','1992-02-27','F'::public.gender,1,false,false,3),
	 ('Yanis','Verhoeven','benoit@albatros.be','BE-20250037','1983-09-09','M'::public.gender,1,false,false,3),
	 ('Manon','Peters','benoit@albatros.be','BE-20250038','1978-06-01','F'::public.gender,1,false,false,3),
	 ('Quentin','De Wilde','benoit@albatros.be','BE-20250039','1975-01-29','M'::public.gender,1,false,false,3),
	 ('Paula','Coenen','benoit@albatros.be','BE-20250040','1988-05-17','F'::public.gender,1,false,false,3),
	 ('Arne','Jacobs','benoit@albatros.be','BE-20250041','1999-03-08','M'::public.gender,1,false,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Inès','Masson','benoit@albatros.be','BE-20250042','1993-09-23','F'::public.gender,1,false,false,3),
	 ('Bram','Bauwens','benoit@albatros.be','BE-20250043','1989-12-11','M'::public.gender,1,false,false,3),
	 ('Maëlle','Lemaire','benoit@albatros.be','BE-20250044','1985-04-02','F'::public.gender,1,false,false,3),
	 ('Camille','Dupont','benoit@albatros.be','BE-20250016','1992-09-27','F'::public.gender,1,false,true,3),
	 ('Olivia','Claes','benoit@albatros.be','BE-20250010','1976-12-05','F'::public.gender,1,false,false,3),
	 ('Thomas','De Clercq','benoit@albatros.be','BE-20250023','1991-02-07','M'::public.gender,1,false,false,3),
	 ('Hugo','Hermans','benoit@albatros.be','BE-20250015','1997-01-09','M'::public.gender,1,false,true,3),
	 ('Zoé','Lambert','benoit@albatros.be','BE-20250008','1984-02-22','F'::public.gender,1,true,true,3),
	 ('Mila','Maes','benoit@albatros.be','BE-20250006','1996-01-30','F'::public.gender,1,true,true,3),
	 ('Lina','Vermeulen','benoit@albatros.be','BE-20250004','1985-05-16','F'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Louis','Lefebvre','benoit@albatros.be','BE-20250005','1987-09-08','M'::public.gender,1,true,true,3),
	 ('Amélie','Dumont','benoit@albatros.be','BE-20250024','1987-08-15','F'::public.gender,1,false,false,3),
	 ('Jules','Pauwels','benoit@albatros.be','BE-20250019','1975-02-18','M'::public.gender,1,false,false,3),
	 ('Arthur','Willems','benoit@albatros.be','BE-20250007','1991-04-11','M'::public.gender,1,false,false,3),
	 ('Noah','Janssens','benoit@albatros.be','BE-20250003','1989-11-02','M'::public.gender,1,true,false,3),
	 ('Stijn','Leclercq','benoit@albatros.be','BE-20250045','1996-08-08','M'::public.gender,1,false,false,3),
	 ('Aline','Vervloet','benoit@albatros.be','BE-20250046','1991-01-05','F'::public.gender,1,false,false,3),
	 ('Pieter','Rutten','benoit@albatros.be','BE-20250047','1984-03-15','M'::public.gender,1,false,false,3),
	 ('Maud','De Backer','benoit@albatros.be','BE-20250048','1979-10-06','F'::public.gender,1,false,false,3),
	 ('Olivier','Van den Bossche','benoit@albatros.be','BE-20250049','1976-02-12','M'::public.gender,1,false,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Hélène','Gérard','benoit@albatros.be','BE-20250050','1987-12-20','F'::public.gender,1,false,false,3),
	 ('Adam','Peeters','benoit@albatros.be','BE-20250051','1995-01-15','M'::public.gender,1,true,false,3),
	 ('Ben','Janssens','benoit@albatros.be','BE-20250052','1995-03-20','M'::public.gender,1,true,false,3),
	 ('Carl','Vermeulen','benoit@albatros.be','BE-20250053','1995-05-05','M'::public.gender,1,true,false,3),
	 ('Dirk','Willems','benoit@albatros.be','BE-20250054','1995-07-10','M'::public.gender,1,true,false,3),
	 ('Erik','Maes','benoit@albatros.be','BE-20250055','1995-09-25','M'::public.gender,1,true,false,3),
	 ('Frank','Goossens','benoit@albatros.be','BE-20250056','1995-11-30','M'::public.gender,1,true,false,3),
	 ('Gert','Lefebvre','benoit@albatros.be','BE-20250057','1996-01-12','M'::public.gender,1,true,false,3),
	 ('Hugo','De Smet','benoit@albatros.be','BE-20250058','1996-03-18','M'::public.gender,1,true,false,3),
	 ('Ian','Lambert','benoit@albatros.be','BE-20250059','1996-05-22','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Jan','Pauwels','benoit@albatros.be','BE-20250060','1996-07-09','M'::public.gender,1,true,false,3),
	 ('Lucas','Peeters','benoit@albatros.be','BE-20250001','1994-03-12','M'::public.gender,1,true,true,5),
	 ('Emma','Dubois','benoit@albatros.be','BE-20250002','1992-07-25','F'::public.gender,1,false,true,4),
	 ('Adam','De Smet','benoit@albatros.be','BE-20250009','1979-08-14','M'::public.gender,1,false,false,3),
	 ('Nora','De Ridder','benoit@albatros.be','BE-20250014','1986-07-02','F'::public.gender,1,false,true,3),
	 ('Juliette','Simon','benoit@albatros.be','BE-20250012','1995-03-03','F'::public.gender,1,false,true,3),
	 ('Gabriel','Declercq','benoit@albatros.be','BE-20250013','1990-10-21','M'::public.gender,1,false,true,3),
	 ('Alice','Baudoin','benoit@albatros.be','BE-20250018','1978-11-13','F'::public.gender,1,false,false,3),
	 ('Louise','Vandenberghe','benoit@albatros.be','BE-20250020','1988-12-29','F'::public.gender,1,false,false,3),
	 ('Sara','De Vos','benoit@albatros.be','BE-20250022','1993-12-02','F'::public.gender,1,false,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Koen','Hermans','benoit@albatros.be','BE-20250061','1996-09-14','M'::public.gender,1,true,false,3),
	 ('Lars','De Ridder','benoit@albatros.be','BE-20250062','1996-11-27','M'::public.gender,1,true,false,3),
	 ('Marc','Declercq','benoit@albatros.be','BE-20250063','1997-02-03','M'::public.gender,1,true,false,3),
	 ('Noah','De Graaf','benoit@albatros.be','BE-20250064','1997-04-06','M'::public.gender,1,true,false,3),
	 ('Olivier','Vandenberghe','benoit@albatros.be','BE-20250065','1997-06-11','M'::public.gender,1,true,false,3),
	 ('Pieter','Renard','benoit@albatros.be','BE-20250066','1997-08-19','M'::public.gender,1,true,false,3),
	 ('Quentin','Moreau','benoit@albatros.be','BE-20250067','1997-10-23','M'::public.gender,1,true,false,3),
	 ('Raf','Verhoeven','benoit@albatros.be','BE-20250068','1997-12-29','M'::public.gender,1,true,false,3),
	 ('Sam','Declerck','benoit@albatros.be','BE-20250069','1998-02-08','M'::public.gender,1,true,false,3),
	 ('Tom','De Wilde','benoit@albatros.be','BE-20250070','1998-04-14','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Ugo','Verschueren','benoit@albatros.be','BE-20250071','1998-06-20','M'::public.gender,1,true,false,3),
	 ('Victor','Coenen','benoit@albatros.be','BE-20250072','1998-08-26','M'::public.gender,1,true,false,3),
	 ('Wout','Rutten','benoit@albatros.be','BE-20250073','1998-10-30','M'::public.gender,1,true,false,3),
	 ('Xander','Vervloet','benoit@albatros.be','BE-20250074','1998-12-12','M'::public.gender,1,true,false,3),
	 ('Yannick','Jacobs','benoit@albatros.be','BE-20250075','1999-02-16','M'::public.gender,1,true,false,3),
	 ('Zeno','Bauwens','benoit@albatros.be','BE-20250076','1999-04-22','M'::public.gender,1,true,false,3),
	 ('Arne','Leclercq','benoit@albatros.be','BE-20250077','1999-06-28','M'::public.gender,1,true,false,3),
	 ('Bram','Van Damme','benoit@albatros.be','BE-20250078','1999-08-03','M'::public.gender,1,true,false,3),
	 ('Cedric','Devos','benoit@albatros.be','BE-20250079','1999-10-09','M'::public.gender,1,true,false,3),
	 ('Daan','Van den Bossche','benoit@albatros.be','BE-20250080','1999-12-15','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Eli','Peters','benoit@albatros.be','BE-20250081','2000-01-05','M'::public.gender,1,true,false,3),
	 ('Finn','Meunier','benoit@albatros.be','BE-20250082','2000-02-10','M'::public.gender,1,true,false,3),
	 ('Gilles','Simon','benoit@albatros.be','BE-20250083','2000-03-15','M'::public.gender,1,true,false,3),
	 ('Hendrik','Masson','benoit@albatros.be','BE-20250084','2000-04-20','M'::public.gender,1,true,false,3),
	 ('Ilan','Lemaire','benoit@albatros.be','BE-20250085','2000-05-25','M'::public.gender,1,true,false,3),
	 ('Jasper','Dupont','benoit@albatros.be','BE-20250086','2000-06-30','M'::public.gender,1,true,false,3),
	 ('Kenneth','Baudoin','benoit@albatros.be','BE-20250087','2000-07-07','M'::public.gender,1,true,false,3),
	 ('Lennart','Vandenbossche','benoit@albatros.be','BE-20250088','2000-08-12','M'::public.gender,1,true,false,3),
	 ('Milan','De Backer','benoit@albatros.be','BE-20250089','2000-09-17','M'::public.gender,1,true,false,3),
	 ('Niels','El Hadi','benoit@albatros.be','BE-20250090','2000-10-22','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Oscar','Vandamme','benoit@albatros.be','BE-20250091','1995-02-02','M'::public.gender,1,true,false,3),
	 ('Pablo','De Vos','benoit@albatros.be','BE-20250092','1995-04-07','M'::public.gender,1,true,false,3),
	 ('Quincy','De Clercq','benoit@albatros.be','BE-20250093','1995-06-13','M'::public.gender,1,true,false,3),
	 ('Ruben','Dumont','benoit@albatros.be','BE-20250094','1995-08-19','M'::public.gender,1,true,false,3),
	 ('Stijn','Wauters','benoit@albatros.be','BE-20250095','1995-10-24','M'::public.gender,1,true,false,3),
	 ('Tibo','Aerts','benoit@albatros.be','BE-20250096','1995-12-29','M'::public.gender,1,true,false,3),
	 ('Ulrik','Vandenberghe','benoit@albatros.be','BE-20250097','1996-02-04','M'::public.gender,1,true,false,3),
	 ('Victor','Renard','benoit@albatros.be','BE-20250098','1996-04-09','M'::public.gender,1,true,false,3),
	 ('Willem','Moreau','benoit@albatros.be','BE-20250099','1996-06-15','M'::public.gender,1,true,false,3),
	 ('Xavier','Verhoeven','benoit@albatros.be','BE-20250100','1996-08-21','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Adam','Peeters','benoit@albatros.be','BE-20250101','1995-01-05','M'::public.gender,1,true,false,3),
	 ('Ben','Janssens','benoit@albatros.be','BE-20250102','1995-02-10','M'::public.gender,1,true,false,3),
	 ('Carl','Vermeulen','benoit@albatros.be','BE-20250103','1995-03-15','M'::public.gender,1,true,false,3),
	 ('Dirk','Willems','benoit@albatros.be','BE-20250104','1995-04-20','M'::public.gender,1,true,false,3),
	 ('Erik','Maes','benoit@albatros.be','BE-20250105','1995-05-25','M'::public.gender,1,true,false,3),
	 ('Frank','Goossens','benoit@albatros.be','BE-20250106','1995-06-30','M'::public.gender,1,true,false,3),
	 ('Gert','Lefebvre','benoit@albatros.be','BE-20250107','1995-07-05','M'::public.gender,1,true,false,3),
	 ('Niels','El Hadi','benoit@albatros.be','BE-20250140','1998-04-21','M'::public.gender,1,true,false,3),
	 ('Oscar','Vandamme','benoit@albatros.be','BE-20250141','1998-05-26','M'::public.gender,1,true,false,3),
	 ('Pablo','De Vos','benoit@albatros.be','BE-20250142','1998-06-30','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Quincy','De Clercq','benoit@albatros.be','BE-20250143','1998-07-05','M'::public.gender,1,true,false,3),
	 ('Ruben','Dumont','benoit@albatros.be','BE-20250144','1998-08-10','M'::public.gender,1,true,false,3),
	 ('Stijn','Wauters','benoit@albatros.be','BE-20250145','1998-09-15','M'::public.gender,1,true,false,3),
	 ('Tibo','Aerts','benoit@albatros.be','BE-20250146','1998-10-20','M'::public.gender,1,true,false,3),
	 ('Ulrik','Vandenberghe','benoit@albatros.be','BE-20250147','1998-11-25','M'::public.gender,1,true,false,3),
	 ('Hugo','De Smet','benoit@albatros.be','BE-20250108','1995-08-10','M'::public.gender,1,true,false,3),
	 ('Ian','Lambert','benoit@albatros.be','BE-20250109','1995-09-15','M'::public.gender,1,true,false,3),
	 ('Jan','Pauwels','benoit@albatros.be','BE-20250110','1995-10-20','M'::public.gender,1,true,false,3),
	 ('Koen','Hermans','benoit@albatros.be','BE-20250111','1995-11-25','M'::public.gender,1,true,false,3),
	 ('Lars','De Ridder','benoit@albatros.be','BE-20250112','1995-12-30','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Marc','Declercq','benoit@albatros.be','BE-20250113','1996-01-06','M'::public.gender,1,true,false,3),
	 ('Noah','De Graaf','benoit@albatros.be','BE-20250114','1996-02-11','M'::public.gender,1,true,false,3),
	 ('Olivier','Vandenberghe','benoit@albatros.be','BE-20250115','1996-03-16','M'::public.gender,1,true,false,3),
	 ('Pieter','Renard','benoit@albatros.be','BE-20250116','1996-04-21','M'::public.gender,1,true,false,3),
	 ('Quentin','Moreau','benoit@albatros.be','BE-20250117','1996-05-26','M'::public.gender,1,true,false,3),
	 ('Raf','Verhoeven','benoit@albatros.be','BE-20250118','1996-06-30','M'::public.gender,1,true,false,3),
	 ('Sam','Declerck','benoit@albatros.be','BE-20250119','1996-07-05','M'::public.gender,1,true,false,3),
	 ('Tom','De Wilde','benoit@albatros.be','BE-20250120','1996-08-10','M'::public.gender,1,true,false,3),
	 ('Ugo','Verschueren','benoit@albatros.be','BE-20250121','1996-09-15','M'::public.gender,1,true,false,3),
	 ('Victor','Coenen','benoit@albatros.be','BE-20250122','1996-10-20','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Wout','Rutten','benoit@albatros.be','BE-20250123','1996-11-25','M'::public.gender,1,true,false,3),
	 ('Xander','Vervloet','benoit@albatros.be','BE-20250124','1996-12-30','M'::public.gender,1,true,false,3),
	 ('Yannick','Jacobs','benoit@albatros.be','BE-20250125','1997-01-07','M'::public.gender,1,true,false,3),
	 ('Zeno','Bauwens','benoit@albatros.be','BE-20250126','1997-02-12','M'::public.gender,1,true,false,3),
	 ('Arne','Leclercq','benoit@albatros.be','BE-20250127','1997-03-17','M'::public.gender,1,true,false,3),
	 ('Bram','Van Damme','benoit@albatros.be','BE-20250128','1997-04-22','M'::public.gender,1,true,false,3),
	 ('Cedric','Devos','benoit@albatros.be','BE-20250129','1997-05-27','M'::public.gender,1,true,false,3),
	 ('Daan','Van den Bossche','benoit@albatros.be','BE-20250130','1997-06-30','M'::public.gender,1,true,false,3),
	 ('Eli','Peters','benoit@albatros.be','BE-20250131','1997-07-05','M'::public.gender,1,true,false,3),
	 ('Finn','Meunier','benoit@albatros.be','BE-20250132','1997-08-10','M'::public.gender,1,true,false,3);
INSERT INTO public.service_men (first_name,last_name,mail,service_number,birthdate,gender,unit_id,para,ops_test,"rank") VALUES
	 ('Gilles','Simon','benoit@albatros.be','BE-20250133','1997-09-15','M'::public.gender,1,true,false,3),
	 ('Hendrik','Masson','benoit@albatros.be','BE-20250134','1997-10-20','M'::public.gender,1,true,false,3),
	 ('Ilan','Lemaire','benoit@albatros.be','BE-20250135','1997-11-25','M'::public.gender,1,true,false,3),
	 ('Jasper','Dupont','benoit@albatros.be','BE-20250136','1997-12-30','M'::public.gender,1,true,false,3),
	 ('Kenneth','Baudoin','benoit@albatros.be','BE-20250137','1998-01-06','M'::public.gender,1,true,false,3),
	 ('Lennart','Vandenbossche','benoit@albatros.be','BE-20250138','1998-02-11','M'::public.gender,1,true,false,3),
	 ('Milan','De Backer','benoit@albatros.be','BE-20250139','1998-03-16','M'::public.gender,1,true,false,3),
	 ('Victor','Renard','benoit@albatros.be','BE-20250148','1998-12-30','M'::public.gender,1,true,false,3),
	 ('Willem','Moreau','benoit@albatros.be','BE-20250149','1999-01-06','M'::public.gender,1,true,false,3),
	 ('Xavier','Verhoeven','benoit@albatros.be','BE-20250150','1999-02-11','M'::public.gender,1,true,false,3);




INSERT INTO units (name, base_location)
VALUES ('3para', 'Tielen'),
       ('3para-17cie', 'Gavere'),
       ('2cdo', 'Flawinne'),
       ('trgcdo', 'MLD'),
       ('SFG', 'Leuven'),
       ('trgpara', 'Schaffen');

INSERT INTO rooms (id, name, capacity, location) VALUES (1, 'Sports Hall A', 20, 'Floor 1');
INSERT INTO rooms (id, name, capacity, location) VALUES (2, 'Sports Hall B', 15, 'Floor 1');
INSERT INTO rooms (id, name, capacity, location) VALUES (3, 'Fitness Studio', 10, 'Floor 2');
INSERT INTO rooms (id, name, capacity, location) VALUES (4, 'Yoga Room', 12, 'Floor 2');
INSERT INTO rooms (id, name, capacity, location) VALUES (5, 'Fitness Room', 25, 'Ground Floor');