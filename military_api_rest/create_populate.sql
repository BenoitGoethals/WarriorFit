CREATE TABLE units
(
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    base_location TEXT NOT NULL
);


CREATE TABLE service_men
(
    id             INTEGER PRIMARY KEY,
    first_name     TEXT    NOT NULL,
    last_name      TEXT    NOT NULL,
    rank           TEXT    NOT NULL,
    service_number TEXT    NOT NULL UNIQUE,
    birthdate      TEXT    NOT NULL, -- store as ISO-8601 string (YYYY-MM-DD or with time)
    gender         TEXT    NOT NULL, -- store enum name/value as TEXT
    unit_id        INTEGER NOT NULL,
    FOREIGN KEY (unit_id) REFERENCES units (id)
);

INSERT INTO units (id, name, base_location) VALUES
(1, '1/3 Bn Lanciers', 'Leopoldsburg'),
(2, '1 Para', 'Brasschaat'),
(3, '2 Commando', 'Flawinne'),
(4, 'Special Operations Regiment', 'Heverlee'),
(5, 'Medium Brigade Artillerie', 'Brasschaat'),
(6, 'Genie 4 Compagnie', 'Amay'),
(7, 'Landcomponent HQ', 'Evere'),
(8, 'Defence Staff', 'Evere'),
(9, 'Opleidingscentrum', 'Leopoldsburg'),
(10, 'Medical Component', 'Neder-Over-Heembeek'),
(11, 'Luchtcomponent 15 Wing', 'Melsbroek'),
(12, 'Luchtcomponent 349 Sqn', 'Kleine-Brogel'),
(13, 'Luchtcomponent 18 Sqn', 'Beauvechain'),
(14, 'Luchtcomponent 21 Sqn', 'Florennes'),
(15, 'Luchtcomponent 80 UAV Sqn', 'Florennes'),
(16, 'Marinecomponent M917', 'Zeebrugge'),
(17, 'Marinecomponent M923', 'Zeebrugge'),
(18, 'Marinecomponent A960', 'Zeebrugge'),
(19, 'Training Command', 'Leopoldsburg'),
(20, 'Artillerie - Brasschaat', 'Brasschaat'),
(21 ,'3 Para','Tielen');


INSERT INTO service_men (id, first_name, last_name, rank, service_number, birthdate, gender, unit_id) VALUES
(1, 'Lucas', 'Peeters', 'Sld', 'BE-20250001', '1994-03-12', 'M', 1),
(2, 'Emma', 'Dubois', 'Kpl', 'BE-20250002', '1992-07-25', 'F', 1),
(3, 'Noah', 'Janssens', 'Sgt', 'BE-20250003', '1989-11-02', 'M', 1),
(4, 'Lina', 'Vermeulen', 'Adj', 'BE-20250004', '1985-05-16', 'F', 1),
(5, 'Louis', 'Lefebvre', 'SgtMaj', 'BE-20250005', '1987-09-08', 'M', 1),
(6, 'Mila', 'Maes', 'Lt', 'BE-20250006', '1996-01-30', 'F', 1),
(7, 'Arthur', 'Willems', 'Kpt', 'BE-20250007', '1991-04-11', 'M', 1),
(8, 'Zoé', 'Lambert', 'Maj', 'BE-20250008', '1984-02-22', 'F', 1),
(9, 'Adam', 'De Smet', 'LtKol', 'BE-20250009', '1979-08-14', 'M', 1),
(10, 'Olivia', 'Claes', 'Kol', 'BE-20250010', '1976-12-05', 'F', 1),

(11, 'Victor', 'Goossens', 'Sld', 'BE-20250011', '1998-06-19', 'M', 2),
(12, 'Juliette', 'Simon', 'Kpl', 'BE-20250012', '1995-03-03', 'F', 4),
(13, 'Gabriel', 'Declercq', 'Sgt', 'BE-20250013', '1990-10-21', 'M', 5),
(14, 'Nora', 'De Ridder', 'Adj', 'BE-20250014', '1986-07-02', 'F', 17),
(15, 'Hugo', 'Hermans', 'Lt', 'BE-20250015', '1997-01-09', 'M', 15),
(16, 'Camille', 'Dupont', 'Kpt', 'BE-20250016', '1992-09-27', 'F', 13),
(17, 'Mathis', 'De Graaf', 'Maj', 'BE-20250017', '1983-04-06', 'M', 1),
(18, 'Alice', 'Baudoin', 'LtKol', 'BE-20250018', '1978-11-13', 'F', 7),
(19, 'Jules', 'Pauwels', 'Kol', 'BE-20250019', '1975-02-18', 'M', 8),
(20, 'Louise', 'Vandenberghe', 'SgtMaj', 'BE-20250020', '1988-12-29', 'F', 9),

(21, 'Lars', 'Martens', 'Sld', 'BE-20250021', '1999-04-23', 'M', 3),
(22, 'Sara', 'De Vos', 'Kpl', 'BE-20250022', '1993-12-02', 'F', 12),
(23, 'Thomas', 'De Clercq', 'Sgt', 'BE-20250023', '1991-02-07', 'M', 20),
(24, 'Amélie', 'Dumont', 'Adj', 'BE-20250024', '1987-08-15', 'F', 16),
(25, 'Elias', 'Wauters', 'Lt', 'BE-20250025', '1996-05-05', 'M', 6),
(26, 'Chloé', 'Renard', 'Kpt', 'BE-20250026', '1990-09-12', 'F', 11),
(27, 'Rayan', 'Aerts', 'Maj', 'BE-20250027', '1982-01-26', 'M', 7),
(28, 'Elise', 'Declerck', 'LtKol', 'BE-20250028', '1979-03-31', 'F', 10),
(29, 'Baptiste', 'Verschueren', 'Kol', 'BE-20250029', '1974-07-19', 'M', 8),
(30, 'Eva', 'Meunier', 'SgtMaj', 'BE-20250030', '1988-10-28', 'F', 19),

(31, 'Mohamed', 'El Hadi', 'Sld', 'BE-20250031', '1997-06-14', 'M', 2),
(32, 'Charlotte', 'Devos', 'Kpl', 'BE-20250032', '1994-01-18', 'F', 4),
(33, 'Nathan', 'Van Damme', 'Sgt', 'BE-20250033', '1990-04-03', 'M', 1),
(34, 'Clara', 'Vandamme', 'Adj', 'BE-20250034', '1986-11-22', 'F', 18),
(35, 'Simon', 'Vandenbossche', 'Lt', 'BE-20250035', '1995-07-07', 'M', 13),
(36, 'Anaïs', 'Moreau', 'Kpt', 'BE-20250036', '1992-02-27', 'F', 14),
(37, 'Yanis', 'Verhoeven', 'Maj', 'BE-20250037', '1983-09-09', 'M', 5),
(38, 'Manon', 'Peters', 'LtKol', 'BE-20250038', '1978-06-01', 'F', 7),
(39, 'Quentin', 'De Wilde', 'Kol', 'BE-20250039', '1975-01-29', 'M', 8),
(40, 'Paula', 'Coenen', 'SgtMaj', 'BE-20250040', '1988-05-17', 'F', 6),

(41, 'Arne', 'Jacobs', 'Sld', 'BE-20250041', '1999-03-08', 'M', 3),
(42, 'Inès', 'Masson', 'Kpl', 'BE-20250042', '1993-09-23', 'F', 10),
(43, 'Bram', 'Bauwens', 'Sgt', 'BE-20250043', '1989-12-11', 'M', 20),
(44, 'Maëlle', 'Lemaire', 'Adj', 'BE-20250044', '1985-04-02', 'F', 17),
(45, 'Stijn', 'Leclercq', 'Lt', 'BE-20250045', '1996-08-08', 'M', 12),
(46, 'Aline', 'Vervloet', 'Kpt', 'BE-20250046', '1991-01-05', 'F', 9),
(47, 'Pieter', 'Rutten', 'Maj', 'BE-20250047', '1984-03-15', 'M', 1),
(48, 'Maud', 'De Backer', 'LtKol', 'BE-20250048', '1979-10-06', 'F', 7),
(49, 'Olivier', 'Van den Bossche', 'Kol', 'BE-20250049', '1976-02-12', 'M', 8),
(50, 'Hélène', 'Gérard', 'SgtMaj', 'BE-20250050', '1987-12-20', 'F', 16);


-- Select all servicemen with their unit information
SELECT s.*,
       u.name as unit_name,
       u.base_location
FROM service_men s
         JOIN units u ON s.unit_id = u.id
ORDER BY s.id;


-- Select servicemen by service number
SELECT s.*,
       u.name as unit_name,
       u.base_location
FROM service_men s
         JOIN units u ON s.unit_id = u.id
WHERE s.service_number = 'BE-20250001'
ORDER BY s.id;