# WarriorFit — Code Evolution

**946 commits** over ~7 maanden (sep 2025 – apr 2026) — nu ~21.800 regels Python.

---

## Tijdlijn

```mermaid
gantt
    title WarriorFit — Ontwikkeltijdlijn (sep 2025 → apr 2026)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Fases
    Fase 1 · Prototype (~50 commits)              :p1, 2025-09-01, 2025-10-31
    Fase 2 · Functionele groei (~250 commits)     :p2, 2025-10-15, 2025-12-15
    Fase 3 · Architecturele refactor (~300 c.)    :p3, 2025-12-01, 2026-02-15
    Fase 4 · Hardening & DevOps (~346 c.)         :p4, 2026-02-01, 2026-04-30

    section Mijlpalen
    Business-logic extractie    :milestone, 2025-10-31, 0d
    DI container & layering     :milestone, 2025-12-15, 0d
    CI/CD & Docker prod         :milestone, 2026-02-28, 0d
```

## Complexiteitsgroei

```mermaid
xychart-beta
    title "Architecturele complexiteit doorheen de tijd"
    x-axis ["sep '25", "okt '25", "nov '25", "dec '25", "jan '26", "feb '26", "mrt '26", "apr '26"]
    y-axis "Complexiteit (relatief)" 0 --> 10
    line [1, 2, 3, 5, 6, 8, 9, 10]
    bar  [1, 2, 3, 5, 6, 8, 9, 10]
```

| Fase | Periode | Complexiteit | Architectuur |
|---|---|---|---|
| 1 — Prototype | sep–okt 2025 | laag | Monoliet |
| 2 — Features & Calculators | okt–dec 2025 | middel | Emerging layers |
| 3 — Layered DI | dec 2025–feb 2026 | hoog | DI container |
| 4 — Hardening & CI/CD | feb–apr 2026 | hoog | Productie-klaar |

## Architectuurevolutie

```mermaid
flowchart TB
    subgraph F1["FASE 1 — Prototype"]
        direction TB
        F1U[Shiny Pages] --> F1S["DBService<br/><i>god-class</i>"] --> F1DB[(PostgreSQL)]
    end

    subgraph F2["FASE 2 — Functionele groei"]
        direction TB
        F2U[Shiny Pages] --> F2C["PhefCalc<br/>ExtService"]
        F2U --> F2S["DBService<br/><i>uitgebreid</i>"]
        F2C --> F2S
        F2S --> F2DB[(PostgreSQL)]
    end

    subgraph F34["FASE 3 & 4 — Layered + DevOps"]
        direction TB
        F3U["Shiny Pages (RBAC)"] --> F3C[Controllers]
        F3C --> F3S["Services<br/>+ Broker · + Mail"]
        F3S --> F3R["Repositories (async)"]
        F3R --> F3M["ORM Models<br/><i>polymorf</i>"]
        F3M --> F3DB[(PostgreSQL)]
    end

    F1 --> F2 --> F34

    classDef ui   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1;
    classDef svc  fill:#e0f7fa,stroke:#00838f,color:#006064;
    classDef repo fill:#fff3e0,stroke:#ef6c00,color:#e65100;
    classDef db   fill:#fce4ec,stroke:#ad1457,color:#880e4f;
    class F1U,F2U,F3U ui
    class F1S,F2S,F2C,F3C,F3S svc
    class F3R,F3M repo
    class F1DB,F2DB,F3DB db
```

> Fase 3 & 4 brengen bovendien: **DI Container · CI/CD pipeline · Docker · MkDocs**.

---

## Fase 1: Prototype (sep–okt 2025) — commits 1–~50

**Complexiteit: laag | Architectuur: monolithisch**

- Eén Shiny app met een paar pagina's, alles in een platte structuur
- `DBService` als god-class die alle database-operaties bevat
- Directe databasecalls vanuit UI-pagina's
- Geen DI, geen layering — pagina's praten rechtstreeks met de service
- Login/auth rudimentair (password hashing met Argon2 kwam al vroeg)
- Veel iteratief refactoren op dezelfde pagina's (PhefPage had tientallen commits)
- Eerste Alembic migratie, basismodellen met polymorphe `FitnessTest`

## Fase 2: Functionele groei (okt–dec 2025) — commits ~50–300

**Complexiteit: middel | Architectuur: emerging layers**

- Nieuwe pagina's: CombatPage, DashboardPage (met Plotly), SessionsPage
- `PhefCalculator` geïntroduceerd — eerste business logic buiten de UI
- `DefenseExternalService` (singleton) voor externe HR-integratie
- Role-based access control (6 rollen: ADMIN, PTI, APTI, etc.)
- Config via YAML, `Singleton` metaclass pattern
- Nog steeds veel logica in de pagina-classes zelf

## Fase 3: Architecturele refactor (dec 2025–feb 2026) — commits ~300–600

**Complexiteit: hoog | Architectuur: gelaagde DI-architectuur**

- **Grote omslag**: introductie van `dependency-injector` (`DeclarativeContainer`)
- Opsplitsing in duidelijke lagen: **UI → Controllers → Services → Repositories → Models**
- Repositories met `async_sessionmaker` / `AsyncSession`
- Message broker (`mom/broker.py`) voor async achtergrondverwerking (HR-integratie)
- Mail service met SMTP health checks
- Audit logging systeem
- Cross-run rapporten en PDF-generatie
- Reserveringssysteem toegevoegd
- Unit tests (pytest) met singleton isolation

## Fase 4: Hardening & DevOps (feb–apr 2026) — commits ~600–946

**Complexiteit: hoog | Architectuur: productie-klaar**

- CI/CD: GitHub Actions met Ruff, mypy strict mode, formatting checks
- Docker productie-configuratie (`SHINY_DEV_MODE=false`, secret management)
- MkDocs documentatie
- OWASP security review en fixes
- Code quality: `ruff check`, `mypy strict`, `black` formatting
- Type annotations over de hele codebase (al zijn er nog `# type: ignore`'s)
- PR-workflow via GitHub (merge requests, code review)

---

## Samenvatting

| Aspect | Begin | Nu |
|---|---|---|
| **Structuur** | Platte bestanden | 7+ packages, gelaagd |
| **DI** | Geen | `DeclarativeContainer` |
| **DB access** | God-class `DBService` | Repository pattern, async |
| **Business logic** | In UI-pagina's | Calculators, Services, Controllers |
| **Auth** | Simpele login | RBAC met 6 rollen |
| **Testing** | Geen | Pytest met DB isolation |
| **CI/CD** | Geen | GitHub Actions, Docker |
| **Docs** | Geen | MkDocs site |

Het patroon is klassiek en gezond: **werkend prototype → features toevoegen → architectureel herstructureren → hardenen voor productie**. De grootste sprong in maturiteit was de introductie van dependency injection en het layered architecture pattern — dat transformeerde het van een "script dat werkt" naar een onderhoudbare applicatie.
