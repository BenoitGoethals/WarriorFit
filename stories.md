# WARRIORFIT - Software Technisch Design Document

## Inleiding

Dit Software Technische Design Document beschrijft de architectuur en ontwerpbeslissingen van het WARRIORFIT systeem.

WARRIORFIT digitaliseert de Fysieke Militaire Testen (PHEF), gevecht testen, zwemtest, functionele test op niveau SOR eenheid, en biedt een veilige, betrouwbare en efficiënte manier om resultaten vast te leggen, verwerken en te rapporteren.

### Doel
Dit document dient als leidraad voor ontwikkelaar bij de implementatie van WARRIORFIT.

### Scope
Het systeem omvat gebruikersbeheer, testinvoer, berekeningen, PDF-rapportages en mailverzending. Het is ontworpen voor lokale serverimplementatie binnen Defensie.

### Referenties
- SRS-document
- Interne Defensie standaarden
- Python Shiny documentatie
- PostgreSQL handleiding
- ReportLab documentatie

---

## Systeemoverzicht

WARRIORFIT is opgebouwd in een gelaagde architectuur met de volgende lagen:

- **UI-laag**: Python Shiny frontend voor invoer en weergave
- **Controller-laag**: Verwerkt gebruikersinteracties en stuurt requests naar services
- **Service-laag**: Bevat de business logic, berekeningen van PHEF resultaten en validatie
- **Repository-laag**: Data access layer voor interactie met PostgreSQL database
- **Externe services**: PDF-generator (ReportLab) en Mailservice (SMTP via Defensie-server)

### Architectuur Principe
De lagen moeten zodanig geïmplementeerd worden indien nodig is, de UI kan vervangen worden andere web/desktop framework en zelfde voor database.

---

## Rollen binnen de applicatie

De applicatie heeft verschillende rollen. Deze rollen bepalen welke menu-items zij te zien krijgen. PHEF testen zijn statutair en zijn gevoelige gegevens.

### 1. Planner

De Planner heeft toegang tot alle plannings- en beheermodules, maar geen testinvoer.

**Hoofdmenu:**
- **Dashboard** - Overzicht van geplande sessies en status per PTI
- **Sessies beheren**
  - Nieuwe sessie aanmaken
  - Sessies bewerken / annuleren
  - Sessiehistoriek bekijken
- **PTI-planning** - Overzicht van geplande opdrachten per PTI
- **Rapporten & Statistieken**
  - Resultaten per eenheid
  - Deelnamepercentages
  - Export naar PDF of Excel

### 2. PTI (Physical Training Instructor)

De PTI ziet alle sessies, en kan resultaten invoeren en valideren.

**Hoofdmenu:**
- **Dashboard** - Actieve sessies vandaag
- **Sessies**
  - Nieuwe testresultaten invoeren
  - Resultaten bewerken / valideren
  - Commentaren toevoegen
- **Rapporten**
  - Individueel rapport genereren
  - Sessierapport exporteren

### 3. APTI (Assistant PTI)

De APTI ondersteunt de PTI en heeft gelimiteerde invoerrechten.

**Hoofdmenu:**
- **Dashboard** - Overzicht van toegewezen sessies
- **Resultaten invoeren**
  - Testdata ingeven per deelnemer
  - Opmerkingen toevoegen
- **Deelnemerslijst** - Alleen-lezen toegang tot persoonlijke data
- **Rapporten** - Bekijken van niet-gevalideerde resultaten

### 4. Deelnemer (Militair)

Beperkte toegang tot eigen testresultaten.

### 5. Administrator

De administrator heeft toegang tot alle beheer- en systeemfuncties.

**Hoofdmenu:**
- **Dashboard** - Systeemstatus en logs
- **Gebruikersbeheer**
  - Gebruikers aanmaken / deactiveren
  - Rollen en rechten toewijzen
- **Systeeminstellingen**
  - Parameters en drempelwaarden
  - Mail- en PDF-services
- **Audit & Logboek** - Historiek van wijzigingen
- **Rapporten & Statistieken** - Overkoepelend overzicht

### 6. Guest (S3, S1, Coy Comd)

De Guest heeft enkel **leesrechten** binnen zijn eigen eenheid.

**Hoofdmenu:**
- **Dashboard** - Samenvatting fysieke paraatheid van de eenheid
- **Resultatenoverzicht**
  - Gemiddelde scores per test
  - Statistieken per sectie of peloton
- **Rapporten**
  - Eenheidsrapport genereren (alleen-lezen)
  - Export naar PDF
- **Zoeken / Filteren** - Op naam, graad of testdatum

### 7. Systeem (Automatische processen)

Geen UI-menu - deze rol werkt achter de schermen.

**Achtergrondprocessen:**
- Automatische validatie-controle
- PDF-generatie en e-maildistributie
- Synchronisatie met centrale databanken
- Logging en foutopvolging

---

## Design beslissingen op technologisch niveau

De keuze genomen in het initiële projectvoorstel aangaande technologieën.

### Web / API en UI
- **FastAPI**: REST API voor HRM integratie
- **Shiny for Python**: UI framework

### Database / ORM
- **SQLAlchemy**: ORM layer
- **PostgreSQL drivers**: asyncpg, psycopg (psycopg-binary), psycopg2-binary
- **Migraties**: alembic, mako

### Security / Authenticatie
- **Hashing**: bcrypt, passlib
- **JWT/JOSE**: python-jose, pyjwt
- **Crypto**: ecdsa, rsa, pyasn1

### Data / Analyse / Rapportering
- **Core**: pandas, numpy, pytz, tzdata
- **Export**: openpyxl (Excel), reportlab (PDF)
- **Visualisatie**: plotly

### Netwerk / HTTP
- **Clients**: httpx, requests
- **Utilities**: pythonping

### Build / Tools / Formatting (dev)
- **Formatter/linter**: black
- **Testen**: pytest, iniconfig, pluggy

---

## User Stories - Overzicht per Epic

User stories zijn gekozen in plaats van Use Cases voor meer flexibiliteit bij agile ontwikkeling.

### Totaal Overzicht
- **Totaal aantal epics:** 9
- **Totaal aantal stories:** 48
- **Totaal story points:** 150

### Story Points Legenda
- 1 punt = 2-4 uur
- 2 punten = 4-8 uur
- 3 punten = 1-2 dagen
- 5 punten = 2-3 dagen
- 8 punten = 3-5 dagen

---

## Epic 1: Gebruikersbeheer (20 punten)

**Epic totaal:** 20 punten  
**Geschat:** 4-5 sprints (bij 2 weken sprints)

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 1.1 | Nieuwe gebruiker aanmaken | 5 | Must Have |
| 1.2 | Foutafhandeling gebruikersaanmaak | 3 | Must Have |
| 1.3 | Gebruiker bewerken | 5 | Must Have |
| 1.4 | Wachtwoord reset door admin | 2 | Should Have |
| 1.5 | Autorisatie controle gebruikersbeheer | 3 | Must Have |
| 1.6 | Gebruikerslijst met zoeken | 2 | Should Have |

### Story 1.1: Nieuwe gebruiker aanmaken [5 punten]

**Als** admin  
**Wil ik** een nieuwe gebruiker kunnen aanmaken met username, email, wachtwoord, rol en serienummer  
**Zodat** medewerkers toegang hebben tot het systeem

**Acceptatiecriteria:**
- Formulier met velden: username, email, password, role (dropdown), serial_number
- Username moet uniek zijn (3-30 karakters, a-z, 0-9, ., _, -)
- Email moet geldig en uniek zijn
- Wachtwoord minimaal 12 karakters met complexiteitscheck
- Wachtwoord wordt gehashed met Argon2id
- Serial_number moet uniek zijn
- Audit log registreert aanmaak (wie, wat, wanneer)
- Success response: 201 Created met user_id
- UI toont bevestiging

**Taken:**
- Frontend formulier met validatie
- Backend POST /api/users endpoint
- Password hashing implementeren
- Audit logging service
- Unit + integration tests

### Story 1.2: Foutafhandeling gebruikersaanmaak [3 punten]

**Als** admin  
**Wil ik** duidelijke foutmeldingen zien bij fouten  
**Zodat** ik weet wat ik moet aanpassen

**Acceptatiecriteria:**
- Username conflict: "USERNAME_TAKEN" met suggesties (username1, username_01)
- Email conflict: "EMAIL_TAKEN"
- Serial_number conflict: foutmelding + admin override optie
- Zwak wachtwoord: specifieke feedback (min lengte, complexiteit)
- Inline validatie bij typen (debounced)
- Server errors: gebruiksvriendelijke melding met error-id

**Taken:**
- Error handling in frontend
- Backend error responses
- Validation messages NL
- Tests voor alle error scenarios

### Story 1.3: Gebruiker bewerken [5 punten]

**Als** admin  
**Wil ik** een bestaande gebruiker kunnen selecteren en aanpassen  
**Zodat** gegevens actueel blijven

**Acceptatiecriteria:**
- Selecteer gebruiker uit lijst (met zoeken/filteren)
- Bewerkformulier toont huidige waarden
- Wijzigbaar: email, role, serial_number, status, opmerkingen
- Validatie zoals bij aanmaken (unieke constraints)
- Wachtwoord reset optie (genereert token)
- Audit log registreert alle wijzigingen
- Concurrency handling (versieconflict melding)
- Success: "Wijzigingen opgeslagen" toast

**Taken:**
- Gebruikerslijst component
- Edit formulier met pre-filled data
- PUT /api/users/:id endpoint
- Optimistic locking implementeren
- Tests

### Story 1.4: Wachtwoord reset door admin [2 punten]

**Als** admin  
**Wil ik** een wachtwoord kunnen resetten voor een gebruiker  
**Zodat** gebruikers weer kunnen inloggen bij vergeten wachtwoord

**Acceptatiecriteria:**
- "Reset wachtwoord" button in edit scherm
- Genereert veilige reset token (24u geldig)
- Stuurt email naar gebruiker met reset link
- Token is single-use
- Audit log registreert reset actie
- Oude token invalideren bij nieuwe aanvraag

**Taken:**
- Reset token generatie
- POST /api/users/:id/reset-password endpoint
- Email template
- Token validatie endpoint
- Tests

### Story 1.5: Autorisatie controle gebruikersbeheer [3 punten]

**Als** systeem  
**Wil ik** controleren dat alleen admins gebruikers mogen beheren  
**Zodat** security gewaarborgd is

**Acceptatiecriteria:**
- Alleen rol "admin" mag users aanmaken/bewerken
- HTTP 403 Forbidden bij onvoldoende rechten
- Frontend verbergt admin functies voor niet-admins
- Backend valideert altijd autorisatie
- JWT token bevat role claim
- Rate limiting op user endpoints

**Taken:**
- Authorization middleware
- Role-based access control (RBAC)
- Frontend route guards
- Tests met verschillende rollen

### Story 1.6: Gebruikerslijst met zoeken [2 punten]

**Als** admin  
**Wil ik** een overzicht van alle gebruikers kunnen zien en zoeken  
**Zodat** ik snel specifieke gebruikers kan vinden

**Acceptatiecriteria:**
- Tabel toont: username, email, role, serial_number, status
- Zoeken op username, email, serial_number
- Filteren op role en status
- Sorteren op kolommen
- Paginering (25 per pagina)
- "Bewerken" actie per rij
- Laadt binnen 2 seconden

**Taken:**
- GET /api/users endpoint met query params
- Data table component
- Search/filter implementatie
- Tests

---

## Epic 2: Testsessie Planning (17 punten)

**Epic totaal:** 17 punten  
**Geschat:** 3-4 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 2.1 | Nieuwe testsessie aanmaken | 5 | Must Have |
| 2.2 | Testsessie bijwerken | 3 | Should Have |
| 2.3 | Testsessie verwijderen | 2 | Should Have |
| 2.4 | Kalender bekijken | 5 | Should Have |
| 2.5 | Sessie lijst bekijken | 2 | Must Have |

### Story 2.1: Nieuwe testsessie aanmaken [5 punten]

**Als** planner of PTI  
**Wil ik** een nieuwe testsessie kunnen aanmaken  
**Zodat** tests gepland kunnen worden

**Acceptatiecriteria:**
- Formulier: test_type (dropdown), datum, tijd, verantwoordelijke_pti (dropdown), opmerkingen
- Test types: PHEF, Combat, Functioneel, Zwemtest
- Datum mag niet in verleden liggen
- Verantwoordelijke PTI dropdown laadt actieve PTI's
- Unieke constraint: testtype + datum (conflict check)
- Status bij aanmaak: "GEPLAND"
- Audit log registreert aanmaak
- Mail naar verantwoordelijke PTI met details
- Success: bevestiging met sessie_id

**Taken:**
- Sessie formulier component
- POST /api/sessions endpoint
- PTI dropdown met API call
- Duplicate check query
- Email notificatie service
- Tests

### Story 2.2: Testsessie bijwerken [3 punten]

**Als** planner of PTI  
**Wil ik** een testsessie kunnen wijzigen  
**Zodat** planning aangepast kan worden

**Acceptatiecriteria:**
- Selecteer sessie uit lijst
- Wijzig: test_type, datum, tijd, verantwoordelijke_pti, opmerkingen
- Datum mag niet in verleden
- Conflict check (excl. huidige sessie)
- Audit log met oude en nieuwe waarden
- Optioneel: mail naar nieuwe PTI indien gewijzigd
- Success: "Sessie bijgewerkt" bevestiging

**Taken:**
- Edit sessie formulier
- PUT /api/sessions/:id endpoint
- Conflict detection logica
- Tests

### Story 2.3: Testsessie verwijderen [2 punten]

**Als** planner of admin  
**Wil ik** een testsessie kunnen annuleren  
**Zodat** verkeerde planning verwijderd kan worden

**Acceptatiecriteria:**
- "Verwijderen" button met bevestigingsdialoog
- Alleen sessies zonder resultaten verwijderbaar
- Sessies met resultaten: status wijzigen naar "GEANNULEERD"
- Audit log registreert verwijdering/annulering
- Mail naar verantwoordelijke PTI
- Success: "Sessie verwijderd/geannuleerd"

**Taken:**
- Delete/cancel logica
- DELETE /api/sessions/:id endpoint
- Results check query
- Tests

### Story 2.4: Kalender bekijken [5 punten]

**Als** PTI, APTI of admin  
**Wil ik** alle testsessies in een kalender zien  
**Zodat** ik planning overzicht heb

**Acceptatiecriteria:**
- Kalender met maand/week/dag views
- Sessies tonen als items op datum/tijd
- Kleuren per testtype (PHEF=blauw, Combat=rood, etc.)
- Klik op sessie: popup met details
- PTI/APTI zien alleen eigen eenheid
- Admin ziet alles
- Filter op testtype
- Laadt binnen 2 seconden
- Responsief (mobiel/desktop)

**Taken:**
- Kalender component (react-big-calendar of fullcalendar)
- GET /api/sessions endpoint met filters
- Autorisatie scope filtering
- Responsive styling
- Tests

### Story 2.5: Sessie lijst bekijken [2 punten]

**Als** PTI of planner  
**Wil ik** een lijst van testsessies zien  
**Zodat** ik komende en recente tests kan bekijken

**Acceptatiecriteria:**
- Tabel: test_type, datum, tijd, verantwoordelijke_pti, status
- Filter op testtype, status, datum range
- Sorteren op datum
- "Bewerken" en "Resultaten invoeren" acties
- Pagination
- Default: komende 30 dagen

**Taken:**
- Sessies lijst component
- Query filters
- Action buttons
- Tests

---

## Epic 3: PHEF Test Invoer (18 punten)

**Epic totaal:** 18 punten  
**Geschat:** 3-4 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 3.1 | PHEF sessie selecteren | 2 | Must Have |
| 3.2 | Militair opzoeken via HRM | 3 | Must Have |
| 3.3 | PHEF metingen invoeren | 5 | Must Have |
| 3.4 | PHEF resultaat opslaan | 5 | Must Have |
| 3.5 | PHEF resultaat lijst | 3 | Should Have |

### Story 3.1: PHEF sessie selecteren [2 punten]

**Als** PTI  
**Wil ik** een PHEF sessie selecteren voor resultaat invoer  
**Zodat** resultaten gekoppeld worden aan de juiste sessie

**Acceptatiecriteria:**
- Dropdown met PHEF sessies (status GEPLAND of ACTIEF)
- Toon: datum, tijd, locatie
- Filter op datum (vandaag, deze week, deze maand)
- Sessie blijft geselecteerd tijdens meerdere invoeren
- "Nieuwe sessie" knop indien geen sessies
- Selected sessie info bovenaan scherm zichtbaar

**Taken:**
- Sessie selector component
- GET /api/sessions?type=PHEF endpoint
- Session state management
- Tests

### Story 3.2: Militair opzoeken via HRM [3 punten]

**Als** PTI  
**Wil ik** militair valideren via stamnummer in HRM  
**Zodat** ik zeker weet dat gegevens kloppen

**Acceptatiecriteria:**
- Input veld voor stamnummer
- API call naar GET /hrm/militair/{stamnummer}
- Bij gevonden: toon naam, geslacht, geboortedatum, leeftijd, email (read-only)
- Bij niet gevonden: "Militair niet gevonden in HRM" error
- Retry optie bij netwerk fout
- Timeout na 5 seconden
- Loading indicator tijdens lookup

**Taken:**
- HRM API client
- Militair lookup component
- Error handling
- Retry logica
- Tests + mocks

### Story 3.3: PHEF metingen invoeren [5 punten]

**Als** PTI  
**Wil ik** PHEF meetgegevens invoeren  
**Zodat** testresultaten worden berekend

**Acceptatiecriteria:**
- Invoer velden:
  - 2400m run: tijd in mm:ss format (keyboard + picker)
  - Side-bridge links: tijd in mm:ss format
  - Side-bridge rechts: tijd in mm:ss format
- Format validatie (00:00 tot 99:59)
- Plausibiliteitscheck (run < 30:00, bridge < 10:00)
- Score berekening automatisch (leeftijd + geslacht correctie)
- Toon berekende score en GO/NO-GO
- Score tabel referentie zichtbaar
- Opmerkingen veld (optioneel)
- "Reset" en "Opslaan" buttons

**Taken:**
- PHEF invoer formulier
- Time input component (mm:ss)
- Score calculatie service (PHEF regels)
- Validatie logica
- Tests met verschillende scenarios

### Story 3.4: PHEF resultaat opslaan [5 punten]

**Als** PTI  
**Wil ik** PHEF resultaat opslaan  
**Zodat** het geregistreerd is in het systeem

**Acceptatiecriteria:**
- POST /api/test-results/phef met: session_id, serial_number, run_time, bridge_left, bridge_right, score, status (GO/NO-GO), opmerkingen
- Transactioneel opslaan (alles slaagt of niets)
- Audit log met volledige data
- Success: HTTP 201 met result_id
- Asynchrone taken starten:
  - Email naar militair (met PDF)
  - POST naar HRM met resultaat
- UI: "Resultaat opgeslagen" + optie "Volgende militair"
- Bij fout: duidelijke melding, data blijft in formulier

**Taken:**
- POST /api/test-results/phef endpoint
- Database transactie
- Background job queue
- Email service met PDF generatie
- HRM POST implementatie
- Retry mechanisme
- Tests

### Story 3.5: PHEF resultaat lijst [3 punten]

**Als** PTI  
**Wil ik** ingevoerde PHEF resultaten van een sessie zien  
**Zodat** ik kan controleren wie al getest is

**Acceptatiecriteria:**
- Lijst per sessie: naam, serial_number, run_time, bridge_left, bridge_right, score, status
- Filter op status (GO/NO-GO)
- Zoeken op naam of serial_number
- "Bewerken" optie (overschrijven met nieuwe waarde)
- Export naar Excel optie
- Toon totaal aantal GO en NO-GO

**Taken:**
- Results lijst component
- GET /api/test-results?session_id=X endpoint
- Edit functionaliteit
- Export service
- Tests

---

## Epic 4: Combat Test Invoer (13 punten)

**Epic totaal:** 13 punten  
**Geschat:** 2-3 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 4.1 | Combat test resultaat invoeren | 8 | Must Have |
| 4.2 | Combat resultaat lijst | 3 | Should Have |
| 4.3 | Combat statistieken | 2 | Could Have |

### Story 4.1: Combat test resultaat invoeren [8 punten]

**Als** PTI  
**Wil ik** Combat test resultaten invoeren met 3 onderdelen  
**Zodat** alle prestaties worden geregistreerd

**Acceptatiecriteria:**
- Sessie selectie (zoals PHEF)
- Militair lookup via HRM (zoals PHEF)
- Invoer per onderdeel:
  - **16km speedmars**: GO/NO-GO (required) + tijd (optioneel, hh:mm:ss)
  - **Hindernispiste**: GO/NO-GO (required) + opmerkingen (optioneel)
  - **Koordenpiste**: GO/NO-GO (required) + opmerkingen (optioneel)
- Eindresultaat berekening: GO als alle 3 onderdelen GO, anders NO-GO
- Toon eindresultaat duidelijk (groen/rood)
- Algemene opmerkingen veld
- Opslaan naar database
- Email naar militair
- POST naar HRM
- Audit logging

**Taken:**
- Combat invoer formulier (3 onderdelen)
- GO/NO-GO toggle component
- Time input (optioneel)
- Eindresultaat logica
- POST /api/test-results/combat endpoint
- Email + HRM integratie
- Tests

### Story 4.2: Combat resultaat lijst [3 punten]

**Als** PTI  
**Wil ik** Combat resultaten per sessie zien  
**Zodat** ik overzicht heb van prestaties

**Acceptatiecriteria:**
- Lijst: naam, serial, speedmars, hindernis, koorden, eindresultaat
- GO/NO-GO met iconen (✓/✗)
- Filter op eindresultaat
- Zoeken op naam/serial
- Export naar Excel
- Bewerken optie

**Taken:**
- Combat results lijst component
- GET /api/test-results?session_id=X&type=combat endpoint
- Tests

### Story 4.3: Combat statistieken [2 punten]

**Als** planner  
**Wil ik** Combat statistieken zien  
**Zodat** ik prestatie-overzicht heb

**Acceptatiecriteria:**
- Dashboard met:
  - Totaal getest
  - % GO vs NO-GO
  - Per onderdeel: hoeveel GO/NO-GO
  - Gemiddelde speedmars tijd
- Filter op eenheid en datum range
- Grafiek (bar chart)

**Taken:**
- Stats berekening query
- Dashboard component
- Chart library (recharts)
- Tests

---

## Epic 5: Zwemtest Invoer (8 punten)

**Epic totaal:** 8 punten  
**Geschat:** 1-2 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 5.1 | Zwemtest resultaat invoeren | 5 | Should Have |
| 5.2 | Zwemtest resultaat lijst | 2 | Should Have |
| 5.3 | Veiligheidsincident markeren | 1 | Should Have |

### Story 5.1: Zwemtest resultaat invoeren [5 punten]

**Als** PTI  
**Wil ik** zwemtest resultaten invoeren  
**Zodat** 100m zwemtest in gevechtskledij wordt geregistreerd

**Acceptatiecriteria:**
- Sessie selectie (swimming test)
- Militair lookup via HRM
- Resultaat: GO of NO-GO (radio buttons)
- GO = 100m volledig gezwommen in voorwaarden
- NO-GO = niet volledig of diskwalificatie
- Opmerkingen veld (veiligheid incidents)
- GO/NO-GO direct = geslaagd/niet geslaagd
- Opslaan naar database
- Email naar militair
- POST naar HRM
- Audit logging

**Taken:**
- Zwemtest formulier (simpel GO/NO-GO)
- POST /api/test-results/swimming endpoint
- Email + HRM integratie
- Tests

### Story 5.2: Zwemtest resultaat lijst [2 punten]

**Als** PTI  
**Wil ik** zwemtest resultaten zien per sessie  
**Zodat** ik overzicht heb

**Acceptatiecriteria:**
- Lijst: naam, serial, resultaat (GO/NO-GO), opmerkingen
- Filter op resultaat
- Zoeken
- Export
- Bewerken

**Taken:**
- Swimming results lijst
- GET endpoint
- Tests

### Story 5.3: Veiligheidsincident markeren [1 punt]

**Als** PTI  
**Wil ik** veiligheidsincident kunnen markeren  
**Zodat** dit geregistreerd en opgevolgd wordt

**Acceptatiecriteria:**
- Checkbox "Veiligheidsincident"
- Bij aanvinken: verplicht opmerkingen veld
- Resultaat status: "ON HOLD"
- Notificatie naar medische dienst en eenheidscommandant
- Kan niet gepubliceerd worden tot validatie

**Taken:**
- Safety checkbox
- Notification service
- Status workflow
- Tests

---

## Epic 6: Functionele Test Invoer (15 punten)

**Epic totaal:** 15 punten  
**Geschat:** 2-3 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 6.1 | Functionele test metingen invoeren | 5 | Must Have |
| 6.2 | Functionele test GO/NO-GO bepalen | 3 | Must Have |
| 6.3 | Functionele test opslaan | 5 | Must Have |
| 6.4 | Functionele test resultaat lijst | 2 | Should Have |

### Story 6.1: Functionele test metingen invoeren [5 punten]

**Als** PTI  
**Wil ik** functionele test metingen invoeren  
**Zodat** prestaties per onderdeel worden vastgelegd

**Acceptatiecriteria:**
- Sessie selectie (functionele test)
- Militair lookup via HRM
- Invoer aantal herhalingen (integer):
  - Optrekken (pull-ups): 0-100
  - Pompen (push-ups 2min): 0-200
  - Sit-ups (2min): 0-200
- Plausibiliteitscheck (max waarden)
- Real-time berekening:
  - Punten per onderdeel (obv leeftijd + geslacht tabel)
  - Percentage van max punten per onderdeel
  - Totaal punten
- Toon score tabel referentie
- Opmerkingen veld

**Taken:**
- Functionele test formulier (3 onderdelen)
- Integer input validatie
- Score calculator service (leeftijd/geslacht tabellen)
- Percentage berekening
- Tests met verschillende leeftijd/geslacht combinaties

### Story 6.2: Functionele test GO/NO-GO bepalen [3 punten]

**Als** PTI  
**Wil ik** dat systeem GO/NO-GO automatisch bepaalt  
**Zodat** beoordeling objectief is

**Acceptatiecriteria:**
- **Business rule**: minimaal 50% per onderdeel vereist
- Per onderdeel: GO als ≥50%, anders NO-GO
- Eindresultaat: GO als alle 3 onderdelen GO, anders NO-GO
- Visueel feedback:
  - Groen/rood indicator per onderdeel
  - Grote eindresultaat badge
- Highlight onderdelen onder 50% in rood
- Toon behaalde vs vereiste punten

**Taken:**
- GO/NO-GO berekening logica
- Visual feedback component
- Business rules configureerbaar maken
- Tests

### Story 6.3: Functionele test opslaan [5 punten]

**Als** PTI  
**Wil ik** functionele test resultaat opslaan  
**Zodat** het geregistreerd en gedeeld wordt

**Acceptatiecriteria:**
- POST /api/test-results/functional met alle data
- Opslaan: aantallen, punten, percentages, GO/NO-GO per onderdeel, eindresultaat
- Transactioneel
- Audit log
- Email naar militair met gedetailleerde breakdown
- POST naar HRM
- Success: bevestiging + "Volgende militair" optie

**Taken:**
- POST endpoint
- Database transactie
- Email template (gedetailleerd)
- HRM POST
- Tests

### Story 6.4: Functionele test resultaat lijst [2 punten]

**Als** PTI  
**Wil ik** functionele test resultaten zien  
**Zodat** ik prestaties kan vergelijken

**Acceptatiecriteria:**
- Lijst: naam, serial, optrekken, pompen, sit-ups, totaal punten, eindresultaat
- Kleurcode per onderdeel (GO=groen, NO-GO=rood)
- Sorteren op punten
- Filter op GO/NO-GO
- Export
- Bewerken

**Taken:**
- Results lijst component
- Color coding
- GET endpoint
- Tests

---

## Epic 7: Rapportage (12 punten)

**Epic totaal:** 12 punten  
**Geschat:** 2 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 7.1 | PHEF Failed overzicht | 5 | Should Have |
| 7.2 | Combat Failed overzicht | 3 | Could Have |
| 7.3 | Functionele Test Failed overzicht | 3 | Could Have |
| 7.4 | Dashboard overzicht per testtype | 1 | Should Have |

### Story 7.1: PHEF Failed overzicht [5 punten]

**Als** PTI of APTI  
**Wil ik** militairen zien die PHEF niet haalden dit jaar  
**Zodat** ik opvolging kan doen

**Acceptatiecriteria:**
- Tab "PHEF Failed" in dashboard
- Data grid met:
  - Serial_number, naam, rang, geslacht, leeftijd, eenheid, testdatum, score, run_time, bridge_left, bridge_right
- Filter: alleen eigen eenheid (PTI/APTI), alle eenheden (admin)
- Filter: alleen lopend kalenderjaar
- Filter: alleen status NO-GO
- Kolom filters (zoeken per kolom)
- Sorteren op datum (meest recent eerst)
- Export naar Excel
- Refresh button
- Laadt binnen 2 seconden

**Taken:**
- PHEF failed query met filters
- Data grid component (ag-grid of MUI DataGrid)
- Eenheid scope filtering
- Export functionaliteit
- Tests

### Story 7.2: Combat Failed overzicht [3 punten]

**Als** PTI  
**Wil ik** Combat fails zien met details per onderdeel  
**Zodat** ik weet waar problemen zitten

**Acceptatiecriteria:**
- Vergelijkbaar met PHEF failed overzicht
- Extra kolommen: speedmars, hindernis, koorden (GO/NO-GO iconen)
- Highlight welk onderdeel failed
- Filter op specifiek onderdeel
- Export

**Taken:**
- Combat failed query
- Grid component hergebruik
- Tests

### Story 7.3: Functionele Test Failed overzicht [3 punten]

**Als** PTI  
**Wil ik** functionele test fails zien met scores per onderdeel  
**Zodat** ik gericht kan trainen

**Acceptatiecriteria:**
- Vergelijkbaar met PHEF failed
- Kolommen: optrekken, pompen, sit-ups (punten + percentage)
- Kleurcode per onderdeel (<50% rood)
- Filter op specifiek onderdeel <50%
- Export

**Taken:**
- Functional failed query
- Grid component
- Tests

### Story 7.4: Dashboard overzicht per testtype [1 punt]

**Als** planner  
**Wil ik** een dashboard zien met key metrics  
**Zodat** ik snel overzicht heb

**Acceptatiecriteria:**
- Cards per testtype met:
  - Totaal getest dit jaar
  - % GO vs NO-GO
  - Laatste test datum
- Filter op eenheid en jaar
- Click-through naar details

**Taken:**
- Dashboard component
- Stats queries
- Card components
- Tests

---

## Epic 8: Algemene Functionaliteit (15 punten)

**Epic totaal:** 15 punten  
**Geschat:** 2-3 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 8.1 | HRM integratie - GET militair | 5 | Must Have |
| 8.2 | HRM integratie - POST testresultaat | 5 | Must Have |
| 8.3 | Email service - resultaat versturen | 3 | Must Have |
| 8.4 | Audit logging service | 2 | Must Have |

### Story 8.1: HRM integratie - GET militair [5 punten]

**Als** systeem  
**Wil ik** militaire gegevens ophalen van HRM  
**Zodat** juiste info beschikbaar is

**Acceptatiecriteria:**
- GET /hrm/militair/{serial_number} implementeren
- Response: naam, geslacht, geboortedatum, leeftijd, eenheid, email
- Authenticatie via API key of OAuth2
- Timeout: 5 seconden
- Retry: 2x bij fout
- Error handling: 404, 500, timeout
- Cache resultaat (5 minuten)
- Logging van alle calls

**Taken:**
- HRM API client class
- Authentication setup
- Retry logica (exponential backoff)
- Cache implementatie (Redis of in-memory)
- Error handling
- Unit tests met mocks
- Integration tests met test HRM

### Story 8.2: HRM integratie - POST testresultaat [5 punten]

**Als** systeem  
**Wil ik** testresultaten sturen naar HRM  
**Zodat** centrale registratie up-to-date is

**Acceptatiecriteria:**
- POST /hrm/test-result met JSON:
```json
{
  "serial_number": "...",
  "test_type": "PHEF|Combat|Functional|Swimming",
  "test_date": "ISO8601",
  "result": "GO|NO-GO",
  "score": 123,
  "details": {...}
}
```
- Idempotent (zelfde result_id = geen duplicaat)
- Timeout: 10 seconden
- Retry: 3x met exponential backoff
- Bij blijvende fout: queue voor later retry
- Success: 200/201 response
- Logging van alle calls
- Background job (async)

**Taken:**
- HRM POST implementatie
- Background job queue (BullMQ, RabbitMQ, of database queue)
- Retry worker
- Idempotency check
- Error queue voor mislukte jobs
- Admin UI voor failed jobs
- Tests

### Story 8.3: Email service - resultaat versturen [3 punten]

**Als** systeem  
**Wil ik** militairen emailen met testresultaat  
**Zodat** ze geïnformeerd zijn

**Acceptatiecriteria:**
- Email templates per testtype (HTML + plain text)
- Bevat: naam, testdatum, sessie, resultaat (GO/NO-GO), scores/details
- Attachment: PDF met volledige resultaat
- PDF generatie met logo en styling
- Van adres: noreply@warriorfit.mil
- Retry: 3x bij fout
- Background job (async)
- Logging van verzonden emails
- Bounce handling

**Taken:**
- Email service (Nodemailer of SendGrid)
- HTML/text templates (Handlebars of EJS)
- PDF generatie (PDFKit of Puppeteer)
- Background job queue
- Retry worker
- Tests met mock SMTP

### Story 8.4: Audit logging service [2 punten]

**Als** systeem  
**Wil ik** alle acties loggen  
**Zodat** compliance gewaarborgd is

**Acceptatiecriteria:**
- Log tabel: event_type, actor_id, target_id, timestamp, ip_address, request_id, changes (JSON)
- Events: user_create, user_update, session_create, session_update, result_create, result_update
- Middleware logt automatisch alle POST/PUT/DELETE requests
- Logs zijn immutable (no updates/deletes)
- Retention: 7 jaar
- Searchable interface voor admins
- Export mogelijkheid

**Taken:**
- Audit log database schema
- Logging middleware
- Helper functies voor handmatige logs
- Admin search interface
- Tests

---

## Epic 9: Technische Infrastructure (32 punten)

**Epic totaal:** 32 punten  
**Geschat:** 5-6 sprints

| # | Story | Punten | Prioriteit |
|---|-------|--------|------------|
| 9.1 | Database schema en migraties | 5 | Must Have |
| 9.2 | Authentication & JWT setup | 5 | Must Have |
| 9.3 | Authorization middleware | 3 | Must Have |
| 9.4 | API error handling | 2 | Must Have |
| 9.5 | Frontend routing en layout | 5 | Must Have |
| 9.6 | Background job queue | 5 | Must Have |
| 9.7 | Logging en monitoring | 3 | Should Have |
| 9.8 | Deployment pipeline (CI/CD) | 4 | Should Have |

### Story 9.1: Database schema en migraties [5 punten]

**Als** developer  
**Wil ik** volledige database schema opzetten  
**Zodat** alle data opgeslagen kan worden

**Acceptatiecriteria:**
- Tabellen: users, sessions, test_results_phef, test_results_combat, test_results_functional, test_results_swimming, audit_log
- Indexes op: serial_number, username, email, session_id, test_date
- Foreign keys met cascade rules
- Migration framework (Flyway, Liquibase, of Prisma)
- Seed data voor development
- Backup strategie

**Taken:**
- ERD ontwerp
- SQL migrations
- Seed scripts
- Documentation
- Tests

### Story 9.2: Authentication & JWT setup [5 punten]

**Als** systeem  
**Wil ik** veilige authenticatie  
**Zodat** alleen geautoriseerde users toegang hebben

**Acceptatiecriteria:**
- Login endpoint: POST /auth/login (username/email + password)
- JWT token met claims: user_id, role, eenheid
- Access token: 1 uur geldig
- Refresh token: 7 dagen geldig
- Password hashing: Argon2id
- Rate limiting op login endpoint
- Brute force protection
- Token blacklist bij logout

**Taken:**
- Authentication endpoints
- JWT service
- Password hashing
- Token validation middleware
- Rate limiter
- Tests

### Story 9.3: Authorization middleware [3 punten]

**Als** systeem  
**Wil ik** autorisatie controleren per endpoint  
**Zodat** users alleen toegestane acties kunnen doen

**Acceptatiecriteria:**
- Middleware controleert JWT token
- Role-based access control (RBAC)
- Eenheid-scope filtering voor PTI/APTI
- HTTP 401 bij ontbrekende/invalide token
- HTTP 403 bij onvoldoende rechten
- Logging van authorization failures

**Taken:**
- Authorization middleware
- RBAC decorator/guards
- Scope filtering logic
- Tests met verschillende rollen

### Story 9.4: API error handling [2 punten]

**Als** systeem  
**Wil ik** consistente error responses  
**Zodat** frontend errors goed kan tonen

**Acceptatiecriteria:**
- Standaard error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Readable message",
    "details": {...},
    "request_id": "uuid"
  }
}
```
- HTTP status codes correct gebruikt
- Validation errors met field-level details
- Internal errors: generic message + logging
- Request ID voor tracing
- Error logging met stack traces

**Taken:**
- Error handler middleware
- Error response formatter
- Error codes enum
- Logging integration
- Tests

### Story 9.5: Frontend routing en layout [5 punten]

**Als** developer  
**Wil ik** routing en layout structuur  
**Zodat** navigatie werkt

**Acceptatiecriteria:**
- Route guards per rol
- Main layout met header, sidebar, content
- Sidebar menu gebaseerd op rol
- Breadcrumbs
- Loading states
- Error boundaries
- 404 page
- Responsive design

**Taken:**
- Router setup (React Router of Next.js)
- Layout components
- Route guards
- Menu configuration
- Tests

### Story 9.6: Background job queue [5 punten]

**Als** systeem  
**Wil ik** asynchrone taken verwerken  
**Zodat** API snel blijft

**Acceptatiecriteria:**
- Job queue implementatie (BullMQ, Celery, of database queue)
- Job types: email, pdf_generation, hrm_sync
- Retry mechanisme met exponential backoff
- Dead letter queue voor failed jobs
- Admin UI voor job monitoring
- Job priority levels
- Scheduled jobs voor cleanup

**Taken:**
- Queue setup
- Worker processes
- Job definitions
- Admin dashboard
- Monitoring
- Tests

### Story 9.7: Logging en monitoring [3 punten]

**Als** developer  
**Wil ik** comprehensive logging  
**Zodat** debugging en monitoring mogelijk is

**Acceptatiecriteria:**
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARN, ERROR
- Request/response logging
- Performance metrics
- Error tracking (Sentry of vergelijkbaar)
- Health check endpoint
- Metrics endpoint (Prometheus format)

**Taken:**
- Logger setup
- Middleware voor request logging
- Error tracking integration
- Health check endpoint
- Metrics collection
- Tests

### Story 9.8: Deployment pipeline (CI/CD) [4 punten]

**Als** developer  
**Wil ik** geautomatiseerde deployment  
**Zodat** releases snel en veilig gaan

**Acceptatiecriteria:**
- CI pipeline: linting, tests, build
- CD pipeline: deploy naar test/prod
- Docker images
- Database migrations in deployment
- Rollback mechanisme
- Environment variables configuratie
- Smoke tests na deployment

**Taken:**
- CI/CD config (GitHub Actions, GitLab CI, of Jenkins)
- Dockerfile
- Docker Compose voor local dev
- Deployment scripts
- Environment setup
- Documentation

---

## Database Schema

Het database schema bevat de volgende hoofdtabellen:

### Users
- `user_id` (PK)
- `username` (unique)
- `email` (unique)
- `password_hash`
- `role` (enum: admin, planner, pti, apti, deelnemer, guest)
- `serial_number` (unique)
- `status` (enum: active, inactive)
- `created_at`
- `updated_at`

### Sessions
- `session_id` (PK)
- `test_type` (enum: PHEF, Combat, Functional, Swimming)
- `test_date`
- `test_time`
- `verantwoordelijke_pti_id` (FK → users)
- `eenheid`
- `status` (enum: GEPLAND, ACTIEF, AFGEROND, GEANNULEERD)
- `opmerkingen`
- `created_at`
- `updated_at`

### Test_Results_PHEF
- `result_id` (PK)
- `session_id` (FK → sessions)
- `serial_number`
- `run_time` (interval)
- `bridge_left` (interval)
- `bridge_right` (interval)
- `score` (integer)
- `status` (enum: GO, NO-GO)
- `opmerkingen`
- `created_by` (FK → users)
- `created_at`
- `updated_at`

### Test_Results_Combat
- `result_id` (PK)
- `session_id` (FK → sessions)
- `serial_number`
- `speedmars_status` (enum: GO, NO-GO)
- `speedmars_time` (interval, nullable)
- `hindernis_status` (enum: GO, NO-GO)
- `hindernis_opmerkingen`
- `koorden_status` (enum: GO, NO-GO)
- `koorden_opmerkingen`
- `eindresultaat` (enum: GO, NO-GO)
- `opmerkingen`
- `created_by` (FK → users)
- `created_at`
- `updated_at`

### Test_Results_Functional
- `result_id` (PK)
- `session_id` (FK → sessions)
- `serial_number`
- `optrekken_aantal` (integer)
- `optrekken_punten` (integer)
- `optrekken_percentage` (decimal)
- `optrekken_status` (enum: GO, NO-GO)
- `pompen_aantal` (integer)
- `pompen_punten` (integer)
- `pompen_percentage` (decimal)
- `pompen_status` (enum: GO, NO-GO)
- `situps_aantal` (integer)
- `situps_punten` (integer)
- `situps_percentage` (decimal)
- `situps_status` (enum: GO, NO-GO)
- `totaal_punten` (integer)
- `eindresultaat` (enum: GO, NO-GO)
- `opmerkingen`
- `created_by` (FK → users)
- `created_at`
- `updated_at`

### Test_Results_Swimming
- `result_id` (PK)
- `session_id` (FK → sessions)
- `serial_number`
- `status` (enum: GO, NO-GO)
- `veiligheidsincident` (boolean)
- `opmerkingen`
- `created_by` (FK → users)
- `created_at`
- `updated_at`

### Audit_Log
- `log_id` (PK)
- `event_type` (varchar)
- `actor_id` (FK → users)
- `target_id` (varchar)
- `target_type` (varchar)
- `timestamp`
- `ip_address`
- `request_id` (uuid)
- `changes` (jsonb)

---

## Implementatie Roadmap

### Sprint 1-2: Foundation (Epic 9.1, 9.2, 9.3, 9.4)
- Database setup
- Authentication & authorization
- Basic API structure
- Error handling

### Sprint 3-4: User Management (Epic 1)
- Gebruikersbeheer volledige implementatie
- Admin functies

### Sprint 5-6: Session Planning (Epic 2)
- Testsessie planning
- Kalender functionaliteit

### Sprint 7-9: PHEF Testing (Epic 3)
- PHEF invoer volledige flow
- HRM integratie basis (Epic 8.1)

### Sprint 10-11: Combat Testing (Epic 4)
- Combat test invoer
- Multi-onderdeel logica

### Sprint 12: Swimming & Functional (Epic 5, 6)
- Zwemtest invoer
- Functionele test basis

### Sprint 13-14: Background Services (Epic 8, 9.6)
- Email service
- PDF generatie
- HRM POST integratie
- Background jobs

### Sprint 15-16: Reporting & Polish (Epic 7, 9.7, 9.8)
- Rapportage functionaliteit
- Monitoring & logging
- CI/CD pipeline
- Testing & bug fixes

---

## Technische Richtlijnen

### Code Organisatie
```
warriorfit/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── schemas/
│   ├── services/
│   │   ├── auth/
│   │   ├── test_results/
│   │   ├── hrm/
│   │   └── email/
│   ├── repositories/
│   ├── models/
│   ├── utils/
│   └── config/
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   └── utils/
├── database/
│   ├── migrations/
│   └── seeds/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### Coding Standards
- Python: PEP 8, Black formatter
- Type hints verplicht
- Docstrings voor alle publieke functies
- Unit test coverage minimaal 80%
- Code review verplicht voor alle PRs

### Security Requirements
- Alle passwords Argon2id hashed
- JWT tokens met korte expiry
- HTTPS only in productie
- SQL injection preventie via ORM
- XSS preventie via input sanitization
- CSRF protection enabled
- Rate limiting op alle endpoints
- Audit logging voor alle wijzigingen

### Performance Targets
- API response tijd < 200ms (p95)
- Database queries < 100ms (p95)
- UI interactie < 100ms
- Page load < 2 seconden
- Concurrent users: 100+

---

## Appendix

### Afkortingen
- **PHEF**: Fysieke Militaire Test
- **PTI**: Physical Training Instructor
- **APTI**: Assistant Physical Training Instructor
- **HRM**: Human Resource Management systeem
- **SOR**: Special Operations Regiment
- **RBAC**: Role-Based Access Control
- **JWT**: JSON Web Token

### Contacten
- Product Owner: [Naam]
- Tech Lead: [Naam]
- Security Officer: [Naam]

---

**Document Versie:** 1.0  
**Laatste Update:** [Datum]  
**Status:** Draft