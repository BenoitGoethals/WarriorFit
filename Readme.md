# WARRIORFIT

> **Digitalisering van de fysische militaire testen op niveau SOR eenheid**

---

## 📌 Inhoudsopgave

- [Project Overzicht](#-project-overzicht)
- [Probleemstelling](#-probleemstelling)
- [Doelstellingen](#-doelstellingen)
- [Testtypes](#️-testtypes)
  - [PHEF](#1-phef-physical-fitness-evaluation-defence)
  - [Gevechtstesten](#2-gevechtstesten)
  - [Gevechtszwemmen](#3-gevechtszwemmen)
  - [Functionele Testen](#4-functionele-testen)
- [Scope & Use Cases](#-scope--use-cases)
- [Functionele Requirements](#-functionele-requirements)
- [Architectuur](#️-architectuur)
- [Project Fasering](#-project-fasering)
- [Definition of Done](#-definition-of-done)
- [Risico's](#️-risicos)

---

## 🎯 Project Overzicht

**Project Naam:** WARRIORFIT

WARRIORFIT is een digitaal systeem ontwikkeld voor de cel fysieke testen van eenheden van SOR (Special Operations Regiment). Het platform centraliseert het beheer van alle fysieke testen voor militair personeel en automatiseert de communicatie en rapportage rondom testresultaten.

---

## 🔍 Probleemstelling

Elke eenheid van Defensie heeft een cel fysische training die militairen fysiek traint voor operationele inzet. Momenteel worden de volgende testen afgenomen:

- **PHEF (statutair verplicht)**: Jaarlijkse fysieke basistest voor alle militairen
- **Functionele testen**: Voor gevechtseenheden
- **Gevechtstesten**: Voor paracommando's

Het huidige proces is handmatig, versnipperd en inefficiënt, wat leidt tot administratieve overhead en gebrek aan overzicht.

---

## 🎯 Doelstellingen

Het ontwikkelen van een digitaal systeem dat:

1. **Centraal beheer** biedt voor alle fysieke testen van eigen personeel
2. **Geautomatiseerde notificaties** verstuurt over toekomstige testmomenten via e-mail
3. **Automatische rapportage** verzorgt naar HRM en betrokken militairen
4. **Primaire focus** legt op PHEF-testen

---

## 🏋️ Testtypes

### 1. PHEF (Physical Fitness Evaluation Defence)

#### Wat is PHEF?

De PHEF-testen vormen het **gestandaardiseerde systeem** binnen Defensie om de fysieke paraatheid van militairen te meten en te bewaken. Ze dienen als objectieve evaluatie van:

- Lichamelijke conditie
- Kracht
- Uithoudingsvermogen
- Functionele geschiktheid voor operationele inzet

#### Verplichtingen

- **Wie:** Alle militairen binnen Defensie (ongeacht rang, functie of component)
- **Frequentie:** Jaarlijks verplicht
- **Normering:** Leeftijds- en geslachtsafhankelijke normtabellen
- **Leeftijd:** Leeftijd die de militair bereikt in het lopende kalenderjaar

#### Testsamenstelling

| Onderdeel | Beschrijving | Punten |
|-----------|--------------|--------|
| **Core-stabiliteit** | Left & Right Side Bridge (beide zijden) | 2x 20 punten |
| **Loopproef** | 2400 meter | 20 punten |

#### Puntensysteem & Berekening

**Scoring per onderdeel:**
- **Zijbrug links**: Maximum 20 punten (minimum 10/20 vereist)
- **Zijbrug rechts**: Maximum 20 punten (minimum 10/20 vereist)
- Som van beide zijbruggen wordt herleid naar **20 punten**
- **Loopproef**: 20 punten

**Totaalscore:**
- Maximum: **40 punten**
- Slaaggrens: Minimaal **50% per onderdeel** (10/20 per component)

#### Brevetten

| Brevet | Vereiste Score | Percentage |
|--------|---------------|------------|
| 🥇 **Gouden brevet** | 40/40 | 100% |
| 🥈 **Zilveren brevet** | 36-39/40 | ≥ 90% |
| 🥉 **Bronzen brevet** | 32-35/40 | ≥ 80% |

#### Praktische Zaken

- Test moet **jaarlijks** worden afgelegd
- Eenheden moeten **minimaal één testdatum per maand** voorzien
- **Medische certificering** vereist voorafgaand aan de test
- Bij medische vrijstelling kunnen **alternatieve proeven** gelden

---

### 2. Gevechtstesten

#### Overzicht

| Test | Specificaties | Beoordeling |
|------|--------------|-------------|
| **Speedmars** | 16 km in 120 min<br>• Gevechtskledij<br>• Wapen<br>• Webbing (3 kg) | GO / NGO |
| **Koordenpiste** | Met portiek | GO / NGO |
| **Hindernissenparcours** | Standaard parcours | GO / NGO |

**Slaagvereiste:** Alle onderdelen afzonderlijk moeten geslaagd worden (GO)

---

### 3. Gevechtszwemmen

#### Specificaties

- **Afstand:** 100 meter
- **Uitrusting:** 
  - Gevechtskledij
  - Wapen
  - Bottinen

**Beoordeling:** GO / NGO

---

### 4. Functionele Testen

#### Onderdelen

| Test | Beoordeling |
|------|-------------|
| **Optrekken** | GO / NGO |
| **Sit-ups** | GO / NGO |
| **Pompen** | GO / NGO |

**Slaagvereiste:** Alle onderdelen afzonderlijk moeten geslaagd worden (GO)

---

## 📋 Scope & Use Cases

### Use Cases

1. **Beheer van users** voor de applicatie
2. **Registreren en beheren** van testsessies en momenten
3. **Registreren en beheren** van PHEF testen
4. **Registreren en beheren** van Functionele testen
5. **Registreren en beheren** van Gevechtstesten
6. **Analyse van testen** - Wie is geslaagd/gefaald
7. **Status tracking** - Wie moet testen nog uitvoeren in lopend jaar
8. **Rapportage** - Export naar PDF en CSV voor uitgevoerde testen
9. **Beheer eenheid cross**
10. **Notificaties** - Versturen van testresultaten via e-mail
11. **HRM notificatie** van uitgevoerde testen
12. **Dashboard** - Overzicht toestand eigen eenheid

---

## 📊 Functionele Requirements

| ID | Requirement | Beschrijving |
|----|-------------|--------------|
| **FR1** | Gebruikersauthenticatie | Gebruikers (trainers, militairen, admins) kunnen inloggen via een beveiligd loginformulier |
| **FR2** | Gebruikersbeheer | Beheerders kunnen nieuwe gebruikers aanmaken, bewerken of verwijderen |
| **FR3** | Dashboardweergave | Gebruikers zien een gepersonaliseerd dashboard met testresultaten, geplande testen en statistieken |
| **FR4** | Registratie fysieke testen | Gebruiker kan testresultaten invoeren (lopen, push-ups, sit-ups, etc.) via de UI |
| **FR5** | Automatische berekening scores | Systeem berekent automatisch de totaalscore en het resultaat (geslaagd/niet geslaagd) |
| **FR6** | Rapportgeneratie (PDF) | Systeem kan individuele of groepsrapporten genereren in PDF-formaat met resultaten, gemiddelden en opmerkingen |
| **FR7** | Rapportverzending via mail | PDF-rapporten worden automatisch via e-mail naar gebruiker of leidinggevende gestuurd |
| **FR8** | Data opslag in database | Alle testdata, gebruikersinfo en rapporten worden opgeslagen in een centrale database |
| **FR9** | Zoek- en filterfuncties | Gebruikers kunnen filteren op naam, eenheid, datum of testtype |
| **FR10** | Audit logging | Systeem houdt bij wie welke data heeft ingevoerd of gewijzigd |
| **FR11** | Beheer van testtypes | Admins kunnen testtypes toevoegen, wijzigen of verwijderen |
| **FR12** | Export naar Excel/CSV | Gebruikers kunnen testresultaten exporteren naar Excel of CSV |
| **FR13** | Notificatiesysteem | Gebruikers krijgen meldingen bij aankomende testen of nieuwe resultaten |
| **FR14** | Meertalige ondersteuning | UI ondersteunt minimaal Nederlands en Engels |
| **FR15** | API-toegang | Externe systemen (Defensie HR of dataplatform) kunnen resultaten ophalen via een beveiligde API |

---

## 🏗️ Architectuur

### Gelaagde Architectuur

Het WARRIORFIT systeem volgt een moderne gelaagde architectuur:

```
┌─────────────────────────────────────┐
│         UI Layer                    │
│   (User Interface)                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│       Controllers                   │
│   (Request Handling)                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Services                     │
│   (Business Logic)                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Repositories                   │
│   (Data Access)                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│       Database                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       Utilities                     │
│   (Helper Functions)                │
└─────────────────────────────────────┘
```

### Technologische Componenten

Te bepalen in Fase 2:
- Framework keuze
- Database systeem
- Mail service
- PDF generator
- API framework

---

## 📅 Project Fasering

Het project volgt een **Agile-aanpak** met iteratieve en incrementele opleveringen.

### Fase 1: Projectinitiatie & Projectletter

**Timing:** November 2025

**Doel:** Afbakening van het project en vastleggen van visie, scope en verwachtingen

**Activiteiten:**
- Opstellen en goedkeuren van de projectletter
- Bepalen van projectdoelstellingen en succescriteria
- Eerste productvisie en roadmap opstellen
- Voorbereiding van Agile werkwijze (Scrum/Kanban, sprintduur, backlogstructuur)

**Deliverables:**
- ✅ Goedgekeurde projectletter
- ✅ Initiële productvisie en roadmap
- ✅ Opstart van backlog en repository

---

### Fase 2: Basisstructuur & Architectuurkeuze

**Timing:** Januari 2026 (na kerstvakantie)

**Doel:** Creëren van de technische en organisatorische basis voor het project

**Activiteiten:**
- Uitwerken van de architectuur en lagenstructuur
- Opzetten van ontwikkelomgeving en versiebeheer
- Definiëren van Use Cases en User Stories op hoog niveau
- Technologische keuzes maken

**Deliverables:**
- ✅ UML-architectuurdiagram
- ✅ Gelaagde codebasis (skeleton project)
- ✅ Backlog met eerste use cases
- ✅ Werkende build- en testomgeving

---

### Fase 3: Iteratieve Ontwikkeling & Uitbreiding

**Timing:** 1 januari 2026 - 1 juni 2026

**Doel:** In opeenvolgende sprints functionele componenten opleveren

**Deliverables:**
- ✅ Werkende software-incrementen na elke sprint
- ✅ Geüpdatete product backlog en documentatie

**Agile kenmerken:**
- Iteratieve sprints
- Continue feedback loops
- Aanpasbare scope op basis van prioriteiten
- Focus op werkende software

---

### Fase 4: Integratie, Test & Validatie

**Timing:** 1 juni 2026 - 10 juni 2026

**Doel:** Het systeem als geheel testen en klaarzetten voor operationeel gebruik

**Activiteiten:**
- Systeem- en acceptatietesten
- Foutcorrecties en optimalisaties
- Performance testing
- Security audits

---

### Fase 5: Oplevering & Afsluiting

**Timing:** Juni 2026

**Doel:** Definitieve oplevering van het werkende product en overdracht

**Activiteiten:**
- Einddemo en oplevering van het volledige WARRIORFIT-platform
- Documentatie en codeoverdracht
- Training van eindgebruikers
- Projectevaluatie

---

## ✅ Definition of Done

### Analyse Dossier

- [x] User stories (Use Cases)
- [x] Component structuur
- [x] Architecture diagram

### Werkende Webapplicatie

- [ ] Beheer users
- [ ] Authenticatie systeem
- [ ] Beheer PHEF tests
- [ ] Beheer Combat tests
- [ ] Beheer Functionele tests
- [ ] Beheer Swimming tests
- [ ] Dashboard functionaliteit
- [ ] Rapportage systeem
- [ ] Notificatie systeem
- [ ] API endpoints

### Kwaliteitseisen

- [ ] Unit tests coverage > 80%
- [ ] Integration tests
- [ ] Security audit passed
- [ ] Performance benchmarks behaald
- [ ] Documentatie compleet

---

## ⚠️ Risico's

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| **Gebrek aan data** | Medium | Tijdelijk gebruik van fictieve datasets voor ontwikkeling en testing |
| **Gebrek aan kennis specifieke packages** | Medium | Training, externe consultancy, prototype-first aanpak |
| **Scope creep** | Hoog | Strikte backlog prioritering, Agile sprint planning |
| **Integratie met externe systemen** | Medium | Vroeg contact met HRM, API-first design |

---

## 📞 Contact & Support

Voor meer informatie over het WARRIORFIT project:

- **Projectverantwoordelijke:** [Naam]
- **Email:** [Email]
- **Eenheid:** SOR

---

## 📄 Licentie

Dit project is eigendom van het Belgisch Defensie - SOR eenheid.

---

**Project Status:** 🟢 In ontwikkeling  
**Start Datum:** November 2025  
**Verwachte Oplevering:** Juni 2026  
**Laatste Update:** Oktober 2025
