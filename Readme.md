# 🛡️ WARRIORFIT  
### Digitalisering van de Fysische Militaire Testen op niveau SOR-eenheid  
**Auteur:** Goethals Benoit  
**Academiejaar:** 2025–2026  

---

## 📘 Inhoudstafel
1. [Aanleiding / Probleemstelling](#-aanleiding--probleemstelling)
2. [Doelstelling](#-doelstelling)
3. [Overzicht PHEF](#-phef)
4. [Andere Testen](#-andere-testen)
5. [Scope & Use Cases](#-scope--use-cases)
6. [Functionele Requirements](#-functionele-requirements)
7. [Niet-Functionele Requirements](#-niet-functionele-requirements)
8. [Definition of Done (DoD)](#-definition-of-done-dod)
9. [Projectfasering](#-projectfasering)
10. [Risico’s](#-risicos)
11. [Frameworks & Packages](#-frameworks--packages)
12. [Prototype Idee UX](#-prototype-idee-ux)

---

## 🎯 Aanleiding / Probleemstelling
Elke eenheid binnen Defensie beschikt over een **cel fysieke training** met als doel militairen optimaal fysiek voor te bereiden op operationele inzet.  
Jaarlijks moet elke militair de **PHEF** (Physical Fitness Evaluation Defence) afleggen. Daarnaast voeren gevechtseenheden **functionele** en **gevechtsproeven** uit, terwijl paracommando’s extra **gevechtstesten** moeten doorstaan.

Momenteel verloopt dit grotendeels manueel — wat zorgt voor inefficiëntie, fouten en administratieve vertraging.

---

## 🧭 Doelstelling
Ontwikkel een **digitaal platform** voor de SOR-eenheid waarmee de cel fysieke training:
- PHEF-, gevecht-, zwem- en functionele testen kan **beheren en registreren**.  
- **Automatische notificaties** kan verzenden voor geplande testmomenten.  
- **PDF-rapporten en e-mails** kan genereren voor HRM en militairen.  
- De **status van fysieke paraatheid** van het personeel kan opvolgen via een dashboard.  

---

## 💪 PHEF
De **PHEF-test** vormt de officiële fysieke evaluatie binnen Defensie.  
Ze beoordeelt **kracht, uithouding en functionele geschiktheid** volgens leeftijd, geslacht en functiecategorie.

### 🧩 Samenstelling
1. **Core-stabiliteitstest:** Left & Right Side Bridge  
2. **Loopproef:** 2400 meter  

### 📊 Berekening
| Onderdeel | Max punten | Min. vereiste | Opmerkingen |
|------------|-------------|----------------|--------------|
| Zijbrug L/R | 20 (elk) | 10/20 per zijde | Beide herleid naar 20 |
| Loop 2400 m | 20 | 10/20 |  |
| **Totaal** | **40** | **Geslaagd vanaf 50% per deel** |  |

🏅 **Brevetten:**
- Goud: 40/40  
- Zilver: 36–39/40  
- Brons: 32–35/40  

---

## 🪖 Andere Testen

### ⚔️ Gevechtstesten
- Speedmars 16 km (120 min, gevechtsuitrusting + wapen + webbing 3kg)  
- Koordenpiste & hindernissenparcours  
> Vereist: **GO** op elk onderdeel

### 🌊 Gevechtszwemmen
- 100 m zwemmen in gevechtskledij met wapen & bottines  
> Vereist: **GO/NGO**

### 🏋️ Functionele Testen
- Optrekken  
- Sit-ups  
- Pompen  
> Vereist: **GO** op elk onderdeel  

---

## 🧩 Scope & Use Cases

### Hoofdfunctionaliteiten
1. Gebruikersbeheer (Admin, PTI, Planner, Militair)  
2. Beheer van testmomenten & sessies  
3. Registratie van PHEF-, Functionele-, Gevechts- en Zwemtesten  
4. Automatische berekening & rapportering  
5. Mailnotificaties en HRM-integratie  
6. Dashboards & rapportexport (PDF/CSV)  

---

## ⚙️ Functionele Requirements

| Nr | Requirement | Beschrijving |
|----|--------------|--------------|
| FR1 | Gebruikersauthenticatie | Login via beveiligd formulier (JWT + bcrypt) |
| FR2 | Gebruikersbeheer | CRUD-acties op gebruikers |
| FR3 | Dashboard | Persoonlijk overzicht van testen, resultaten en planning |
| FR4 | Testregistratie | Invoer van fysieke testresultaten via UI |
| FR5 | Scoreberekening | Automatische berekening en GO/NGO-status |
| FR6 | PDF-rapporten | Individuele/groepsrapporten met resultaten |
| FR7 | Mailverzending | Automatische e-mails met resultaten |
| FR8 | Databaseopslag | Alle data persistent in PostgreSQL |
| FR9 | Filtering & zoekfuncties | Op naam, eenheid, testtype, datum |
| FR10 | Audit logging | Historiek van acties per gebruiker |
| FR12 | Export | CSV/Excel-export van resultaten |
| FR13 | Notificatiesysteem | Herinneringen en updates via mail |
| FR14 | Identiteitscontrole | Verificatie via HRM REST API |
| FR15 | API-toegang | Beveiligde externe API voor data-uitwisseling |

---

## 🧱 Niet-Functionele Requirements

### 💻 Technologie
- **UI:** Shiny for Python  
- **API:** FastAPI  
- **Database:** PostgreSQL  
- **ORM:** SQLAlchemy + Alembic  
- **Beveiliging:** bcrypt, JWT, rolgebaseerde autorisatie  
- **Export:** ReportLab (PDF), OpenPyXL (Excel)  

### 🔐 Beveiliging
- HTTPS/TLS-versleuteling  
- Geen plaintext wachtwoorden  
- Logging van kritieke acties  

### 🧩 Onderhoud & Kwaliteit
- Gelaagde architectuur (UI → Controllers → Services → Repositories)  
- Linting (Black) + Testing (pytest)  
- Migratiebeheer met Alembic  

### 🧠 Usability
- Intuïtieve UI met duidelijke feedback  
- Rolgebaseerde menu’s  
- Toegankelijk voor moderne browsers  

---

## ✅ Definition of Done (DoD)
- Analyse- en architectuurdossier  
- Werkende webapplicatie  
- Authenticatie & autorisatie  
- Beheer van alle testtypes  
- Dashboard met status eenheid  
- Rapporten (PDF/CSV)  
- Notificatiesysteem & HRM-koppeling  

---

## 📅 Projectfasering

### **Fase 1 — Initiatie & Projectletter (Nov 2025)**
- Projectafbakening en visie  
- Opstart van backlog en repository  

### **Fase 2 — Architectuur & Structuur (Jan 2026)**
- Technische basis, lagenstructuur en UML  
- Werkende skeleton-project  

### **Fase 3 — Ontwikkeling & Iteraties (Jan–Juni 2026)**
- Incrementele opleveringen via Agile sprints  

### **Fase 4 — Test & Validatie (Juni 2026)**
- Acceptatietests en bugfixing  

### **Fase 5 — Oplevering & Demo (Juni 2026)**
- Einddemo en overdracht aan eindgebruikers  

---

## ⚠️ Risico’s
- Onvoldoende data → fictieve datasets  
- Onvoldoende kennis van specifieke packages  
- Tijdgebrek  
- HRM REST-koppeling onbeschikbaar  

---

## 🧰 Frameworks & Packages

| Categorie | Packages |
|------------|-----------|
| **Web & UI** | `FastAPI`, `shiny` |
| **Database** | `SQLAlchemy`, `PostgreSQL`, `Alembic` |
| **Beveiliging** | `bcrypt`, `passlib`, `python-jose`, `pyjwt` |
| **Data & Analyse** | `pandas`, `numpy`, `plotly` |
| **Export & Rapporten** | `reportlab`, `openpyxl` |
| **Testing & Tools** | `pytest`, `black` |

---

## 🧠 Prototype Idee UX
Het **WARRIORFIT-dashboard** biedt:
- Overzicht van geplande testen  
- Grafieken met prestaties over tijd  
- Lijst van militairen per status (geslaagd/niet geslaagd)  
- Snelkoppelingen voor rapporten en exports  

---

## 🏁 Conclusie
> **WARRIORFIT** vormt een moderne, veilige en efficiënte oplossing voor het digitaliseren van fysieke testen binnen Defensie.  
Het project integreert **Shiny for Python**, **FastAPI**, **PostgreSQL** en **secure automation** om operationele paraatheid en databetrouwbaarheid te versterken.

---

