"""Build WarriorFit_Presentatie_10min_NL.pptx — 17 slides, 10-minute deck.

Slide map
---------
 1  Titel
 2  Probleemstelling
 3  Oplossing & Ecosysteem  (+img_1.png — system context)
 4  Architectuur overview    (overview-WARRIORFIT_Architectuur.png)
 5  Architectuur detail      (overview.png)
 6  Data Model / ERD         (erd.png + datamodel.png)
 7  Rollen & RBAC
 8  Testtypes                (+side-bridge-proef-tabel.png)
 9  Dataflow & Broker        (img.png on right)
10  Volledige testflow       (diagrams/test_flow_ui_db_broker.png)
11  Agile / Scrum
12  Kwaliteit & Testing
13  Beveiliging OWASP
14  AVG / GDPR
15  Technologiestapel
16  Routekaart
17  Vragen
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
IMG = Path("/Users/benoit/PycharmProjects/WarriorFit/documentation")
IMG_ARCH_NL  = str(IMG / "overview-WARRIORFIT_Architectuur.png")
IMG_ARCH_EN  = str(IMG / "overview.png")
IMG_ERD      = str(IMG / "erd.png")
IMG_DATAMODEL= str(IMG / "datamodel.png")
IMG_CTX      = str(IMG / "img_1.png")          # system context (PTI/Admin/Guest)
IMG_BROKER   = str(IMG / "img.png")             # simple broker sequence
IMG_FLOW     = str(IMG / "diagrams/test_flow_ui_db_broker.png")
IMG_SIDEBRIDGE = str(IMG / "side-bridge-proef-tabel.png")

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
C_BG     = RGBColor(0x1E, 0x2D, 0x1E)
C_PANEL  = RGBColor(0x2A, 0x40, 0x2A)
C_AMBER  = RGBColor(0xC8, 0xA0, 0x20)
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_KHAKI  = RGBColor(0xB0, 0xC0, 0x9A)
C_TBLHDR = RGBColor(0x3A, 0x5A, 0x3A)
C_TBLALT = RGBColor(0x24, 0x38, 0x24)
C_RED    = RGBColor(0xC0, 0x39, 0x2B)
C_GREEN  = RGBColor(0x28, 0xB4, 0x63)
C_BLUE   = RGBColor(0x21, 0x6A, 0xAB)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, x, y, w, h, fill=None):
    s = slide.shapes.add_shape(1, x, y, w, h)
    s.line.fill.background()
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    else:
        s.fill.background()
    return s


def tb(slide, text, x, y, w, h, size=18, bold=False, color=C_WHITE,
       align=PP_ALIGN.LEFT, italic=False):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf  = box.text_frame; tf.word_wrap = True
    p   = tf.paragraphs[0]; p.alignment = align
    r   = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.italic = italic; r.font.color.rgb = color
    r.font.name = "Calibri"
    return box


def tb_lines(slide, lines, x, y, w, h, size=16, color=C_WHITE,
             align=PP_ALIGN.LEFT, sa=6, lc=None):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf  = box.text_frame; tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(sa)
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.name = "Calibri"
        r.font.color.rgb = (lc[i] if isinstance(lc, list) and i < len(lc) else
                            lc if lc else color)
    return box


def title_bar(slide, title, subtitle=None):
    rect(slide, 0, 0, SLIDE_W, Inches(1.2), fill=C_AMBER)
    tb(slide, title, Inches(0.35), Inches(0.08), Inches(12.5), Inches(0.75),
       size=30, bold=True, color=C_BG)
    if subtitle:
        tb(slide, subtitle, Inches(0.35), Inches(0.78), Inches(12.5), Inches(0.38),
           size=14, color=C_BG)


def kpi_row(slide, kpis, y=Inches(5.8)):
    n  = len(kpis)
    bw = Inches(13.33 / n)
    for i, (val, lbl) in enumerate(kpis):
        x = Inches(i * 13.33 / n)
        rect(slide, x, y, bw, Inches(1.2), fill=C_PANEL)
        tb(slide, val, x, y + Inches(0.08), bw, Inches(0.62),
           size=28, bold=True, color=C_AMBER, align=PP_ALIGN.CENTER)
        tb(slide, lbl, x, y + Inches(0.65), bw, Inches(0.42),
           size=12, color=C_KHAKI, align=PP_ALIGN.CENTER)


def bullet(slide, items, x, y, w, h, size=18, bc=C_AMBER, tc=C_WHITE, sa=8):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf  = box.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(sa)
        rb = p.add_run(); rb.text = "▶  "; rb.font.size = Pt(size)
        rb.font.color.rgb = bc; rb.font.name = "Calibri"
        rt = p.add_run()
        if isinstance(item, tuple): rt.text, rt.font.color.rgb = item[0], item[1]
        else: rt.text = item; rt.font.color.rgb = tc
        rt.font.size = Pt(size); rt.font.name = "Calibri"
    return box


def add_tbl(slide, headers, rows, x, y, w, h, cw=None, hs=14, rs=13):
    tbl = slide.shapes.add_table(len(rows)+1, len(headers), x, y, w, h).table
    if cw:
        for i, c in enumerate(cw): tbl.columns[i].width = c
    for ci, hdr in enumerate(headers):
        cell = tbl.cell(0, ci); cell.text = hdr
        cell.fill.solid(); cell.fill.fore_color.rgb = C_TBLHDR
        p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.runs[0]; r.font.bold=True; r.font.size=Pt(hs)
        r.font.color.rgb=C_AMBER; r.font.name="Calibri"
        _cm(cell)
    for ri, row in enumerate(rows):
        bg = C_TBLALT if ri%2==0 else C_PANEL
        for ci, val in enumerate(row):
            cell = tbl.cell(ri+1, ci); cell.text = str(val)
            cell.fill.solid(); cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if ci>0 else PP_ALIGN.LEFT
            r = p.runs[0]; r.font.size=Pt(rs)
            r.font.color.rgb=C_WHITE; r.font.name="Calibri"
            _cm(cell)
    return tbl


def _cm(cell):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    for a,v in [("marT",int(Pt(3))),("marB",int(Pt(3))),
                ("marL",int(Pt(5))),("marR",int(Pt(5)))]:
        tcPr.set(a, str(v))


def pic(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(path, x, y, width=w, height=h)


def image_slide(title, subtitle, img_path, caption=None):
    """Full-screen image slide with title bar."""
    s = prs.slides.add_slide(blank)
    set_bg(s, C_BG)
    title_bar(s, title, subtitle)
    # image fills the remaining area
    img_h = Inches(6.1)
    img_w = SLIDE_W - Inches(0.6)
    p = pic(s, img_path, Inches(0.3), Inches(1.3), w=img_w)
    # scale to fit height
    if p.height > img_h:
        ratio = img_h / p.height
        p.height = img_h
        p.width  = int(p.width * ratio)
        p.left   = int((SLIDE_W - p.width) / 2)
    if caption:
        tb(s, caption, Inches(0.4), Inches(7.1), Inches(12.5), Inches(0.35),
           size=11, italic=True, color=C_KHAKI, align=PP_ALIGN.CENTER)
    return s


# ===========================================================================
# SLIDE 1 — Titel
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
rect(s, Inches(0.5), Inches(1.5), Inches(12.33), Inches(4.8), fill=C_PANEL)
tb(s, "⚔", Inches(5.8), Inches(1.6), Inches(1.7), Inches(1.2),
   size=60, color=C_AMBER, align=PP_ALIGN.CENTER)
tb(s, "WarriorFit", Inches(1), Inches(2.7), Inches(11.33), Inches(1.1),
   size=54, bold=True, color=C_AMBER, align=PP_ALIGN.CENTER)
tb(s, "Digitalisering van militaire fysieke fitheidstesten",
   Inches(1), Inches(3.75), Inches(11.33), Inches(0.65),
   size=22, color=C_WHITE, align=PP_ALIGN.CENTER)
tb(s, "Benoit Goethals  |  mei 2026",
   Inches(1), Inches(4.45), Inches(11.33), Inches(0.5),
   size=16, color=C_KHAKI, align=PP_ALIGN.CENTER)
kpi_row(s, [("1.012","commits"),("25.800","lijnen Python"),
            ("231","story points"),("19","sprints"),("80","user stories")])


# ===========================================================================
# SLIDE 2 — Probleemstelling
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Probleemstelling",
          "Manuele, papieren registratie van militaire fitheidstesten")
cx1, cw = Inches(0.4), Inches(6.2)
rect(s, cx1, Inches(1.3), cw, Inches(5.9), fill=C_PANEL)
tb(s, "Huidige situatie", cx1+Inches(0.2), Inches(1.38), cw-Inches(0.3), Inches(0.45),
   size=16, bold=True, color=C_AMBER)
bullet(s, ["Papieren fiches — geen centraal overzicht",
           "5 testtypes met elk eigen scoringsregels",
           "Manuele HR-synchronisatie (foutgevoelig)",
           "Geen historisch inzicht per militair",
           "Geen AVG-compliance (gezondheidsdata Art. 9)",
           "Geen RBAC — iedereen ziet alles",
           "Geen audit trail"],
       cx1+Inches(0.2), Inches(1.9), cw-Inches(0.3), Inches(5.0),
       size=17, sa=9)
cx2 = Inches(7.0)
rect(s, cx2, Inches(1.3), cw, Inches(5.9), fill=C_PANEL)
tb(s, "Impact", cx2+Inches(0.2), Inches(1.38), cw-Inches(0.3), Inches(0.45),
   size=16, bold=True, color=C_AMBER)
bullet(s, [("Vertraging in HR-rapportage", C_RED),
           ("Dataverlies door papieren archief", C_RED),
           ("Geen audit trail — compliancerisico", C_RED),
           ("PTI's verliezen uren aan manueel werk", C_RED),
           ("Commandanten missen realtimezicht", C_RED)],
       cx2+Inches(0.2), Inches(1.9), cw-Inches(0.3), Inches(3.5), size=17, sa=12)
tb(s, "→  WarriorFit digitaliseert het volledige proces",
   cx2+Inches(0.2), Inches(5.9), cw-Inches(0.3), Inches(0.75),
   size=16, bold=True, color=C_GREEN)


# ===========================================================================
# SLIDE 3 — Oplossing & Ecosysteem  (+img_1.png)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Oplossing — WarriorFit Ecosysteem",
          "Intranetwebplatform · geen publieke blootstelling")
kpi_row(s, [("24","pagina's"),("6","rollen"),("5","testtypes"),
            ("40+","DI-singletons"),("100 %","async I/O")], y=Inches(1.3))

# Left: system-context image
img = pic(s, IMG_CTX, Inches(0.3), Inches(2.6))
img.height = Inches(4.5)
img.width  = int(img.width * (Inches(4.5) / img.height)
                 if img.height > 0 else img.width)
img.left = Inches(0.3)

# Right: component list
cx = Inches(5.5)
cw2 = Inches(7.5)
components = [
    ("Shiny for Python",       "Reactieve web-UI · 24 pagina's · RBAC-beschermd"),
    ("PostgreSQL + asyncpg",   "Async ORM (SQLAlchemy 2.0) · Alembic-migraties"),
    ("Broker (MOM)",           "Transactionele outbox · exp. backoff · dead-letter"),
    ("FastAPI",                "MOM REST-endpoint · X-API-Key · CORS-vergrendeling"),
    ("HR Simulator + Mailpit", "Dev/test omgeving · HR-mock · e-mailpreview"),
]
for i, (title, desc) in enumerate(components):
    y0 = Inches(2.65 + i * 0.88)
    rect(s, cx, y0, cw2, Inches(0.82), fill=C_PANEL)
    tb(s, title, cx+Inches(0.15), y0+Inches(0.05), Inches(2.8), Inches(0.75),
       size=14, bold=True, color=C_AMBER)
    tb(s, desc,  cx+Inches(3.0),  y0+Inches(0.12), Inches(4.3), Inches(0.65),
       size=13, color=C_KHAKI)


# ===========================================================================
# SLIDE 4 — Architectuur (overview-WARRIORFIT_Architectuur.png)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Architectuur — WarriorFit Lagen",
          "UI-laag → Controller-laag → Service-laag → Repository-laag → PostgreSQL")

img = pic(s, IMG_ARCH_NL, Inches(0.3), Inches(1.3))
# scale to fit slide height
max_h = Inches(5.95)
max_w = Inches(12.7)
ratio_h = max_h / img.height
ratio_w = max_w / img.width
ratio = min(ratio_h, ratio_w)
img.height = int(img.height * ratio)
img.width  = int(img.width  * ratio)
img.left = int((SLIDE_W - img.width) / 2)
img.top  = Inches(1.35)


# ===========================================================================
# SLIDE 5 — Architectuur detail (overview.png)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Architectuur — Gedetailleerde lagenstructuur",
          "Presentation · Service · Integration · Data Access · Core · Infrastructure")

# Left: image
img = pic(s, IMG_ARCH_EN, Inches(0.3), Inches(1.3))
max_h2 = Inches(5.9)
max_w2 = Inches(7.5)
r2 = min(max_h2/img.height, max_w2/img.width)
img.height = int(img.height * r2)
img.width  = int(img.width  * r2)
img.left   = Inches(0.3)
img.top    = Inches(1.35)

# Right: DI container detail
rx = Inches(8.2)
rect(s, rx, Inches(1.35), Inches(4.85), Inches(5.9), fill=C_PANEL)
tb(s, "DI Container — 40+ singletons", rx+Inches(0.2), Inches(1.45),
   Inches(4.5), Inches(0.5), size=15, bold=True, color=C_AMBER)
tb_lines(s, [
    "providers.Singleton(…) — gedeeld over proceslevensduur",
    "",
    "Repositories (8):  UserRepository, FitnessTestRepository …",
    "Services (12+):    ServiceTest, GdprService, RetentionService …",
    "Controllers (5):   PhefController, CrossController …",
    "External:          BEMILService, MailService, NotifyMail",
    "Broker:            Transactionele outbox singleton",
    "",
    "Wiring: containers.WiringConfiguration(modules=[…])",
    "  → 25 UI-modules gepatch bij opstart",
    "  → @inject + Provide[Container.xxx] op page __init__",
], rx+Inches(0.2), Inches(2.05), Inches(4.5), Inches(4.9),
   size=12, color=C_KHAKI, sa=5)


# ===========================================================================
# SLIDE 6 — Data Model / ERD
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Data Model & ERD",
          "PostgreSQL · SQLAlchemy ORM · polymorf FitnessTest")

# ERD image (left)
img_e = pic(s, IMG_ERD, Inches(0.3), Inches(1.3))
max_h3 = Inches(5.9)
max_w3 = Inches(5.8)
r3 = min(max_h3/img_e.height, max_w3/img_e.width)
img_e.height = int(img_e.height * r3)
img_e.width  = int(img_e.width  * r3)
img_e.left   = Inches(0.3)
img_e.top    = Inches(1.35)

# Data model image (right)
img_d = pic(s, IMG_DATAMODEL, Inches(6.5), Inches(1.3))
max_h4 = Inches(5.9)
max_w4 = Inches(6.5)
r4 = min(max_h4/img_d.height, max_w4/img_d.width)
img_d.height = int(img_d.height * r4)
img_d.width  = int(img_d.width  * r4)
img_d.left   = int(SLIDE_W - Inches(0.3) - img_d.width)
img_d.top    = Inches(1.35)

# Labels
tb(s, "ERD (databasetabellen)", Inches(0.3), Inches(7.1), Inches(5.8), Inches(0.35),
   size=11, italic=True, color=C_KHAKI, align=PP_ALIGN.CENTER)
tb(s, "ORM-klassendiagram", Inches(6.5), Inches(7.1), Inches(6.5), Inches(0.35),
   size=11, italic=True, color=C_KHAKI, align=PP_ALIGN.CENTER)


# ===========================================================================
# SLIDE 7 — Rollen & RBAC
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Rollen & Toegangscontrole (RBAC)",
          "6 rollen · PageSpec(allowed_roles=[…]) per module")
add_tbl(s,
    ["Rol","Omschrijving","Toegang"],
    [("ADMIN",   "Systeembeheerder",     "Volledige toegang + gebruikersbeheer"),
     ("PTI",     "Fitheidsinstructeur",  "Testresultaten invoeren & bekijken"),
     ("APTI",    "Adjunct PTI",          "Beperkt invoer, volledige lezing"),
     ("PLANNER", "Planningsofficial",    "Sessies & fitnessruimte plannen"),
     ("GUEST",   "Gast / bezoeker",      "Alleen eigen profiel (read-only)"),
     ("USER",    "Militair (serviceman)","Eigen fiche + privacypagina")],
    Inches(0.4), Inches(1.35), Inches(7.8), Inches(4.7),
    cw=[Inches(1.6), Inches(2.5), Inches(3.7)], hs=15, rs=14)
rx2 = Inches(8.5)
rect(s, rx2, Inches(1.35), Inches(4.5), Inches(5.85), fill=C_PANEL)
tb(s, "Implementatie", rx2+Inches(0.2), Inches(1.45), Inches(4.1), Inches(0.45),
   size=15, bold=True, color=C_AMBER)
bullet(s, ["PageSpec(allowed_roles=[…]) per pagina",
           "Sessiecontrole bij elke navigatie",
           "10-min inactiviteitstime-out",
           "Argon2id wachtwoordhashing",
           "Rate-limiting op login",
           "Audit trail — alle CRUD-acties gelogd",
           "UserStore scoped per Shiny-sessie (PR #217)",
           "IDOR-fix: _assert_can_modify_tests()"],
       rx2+Inches(0.2), Inches(2.0), Inches(4.1), Inches(4.8),
       size=14, sa=7)


# ===========================================================================
# SLIDE 8 — Testtypes  (+side-bridge scoring table)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "5 Testtypes — volledig gedigitaliseerd",
          "ORM-polymorfisme · FitnessTest-basisklasse + subtypes")

tests = [
    ("PHEF",       C_AMBER,                     "2400 m looptijd\nZijbrug (L+R)\nLeeftijds-/gendercorrectie\nScores A/B/C/D/F"),
    ("Functioneel",RGBColor(0x27,0xAE,0x60),     "Functionele fitheid\nKomplexe oefeningen\nRij scores 1–5"),
    ("Gevecht",    C_RED,                        "Paraat (paratrooper)\nHarde drempelwaarden\nBinaire uitkomst"),
    ("Mars",       C_BLUE,                       "Timed march + uitrusting\nAfstand + gewicht\nEenheidsprestatie"),
    ("Cross",      RGBColor(0x8E,0x44,0xAD),     "Tijdmetingen per loper\nChronos XML-import\n8 statistiekatabladen"),
]
bw = Inches(2.3); by = Inches(1.3); bh = Inches(3.5)
for i, (name, color, desc) in enumerate(tests):
    bx = Inches(0.2 + i * 2.46)
    rect(s, bx, by, bw, Inches(0.52), fill=color)
    tb(s, name, bx, by, bw, Inches(0.52), size=18, bold=True,
       color=C_BG, align=PP_ALIGN.CENTER)
    rect(s, bx, by+Inches(0.52), bw, bh-Inches(0.52), fill=C_PANEL)
    tb_lines(s, desc.split("\n"),
             bx+Inches(0.1), by+Inches(0.6),
             bw-Inches(0.2), bh-Inches(0.7),
             size=13, color=C_KHAKI, sa=5)

# Side-bridge scoring table (bottom strip)
tb(s, "Zijbrugscoringtabel (PHEF) — leeftijds- en gendercorrectie:",
   Inches(0.3), Inches(4.95), Inches(5.5), Inches(0.38),
   size=12, bold=True, color=C_AMBER)
img_sb = pic(s, IMG_SIDEBRIDGE, Inches(0.3), Inches(5.35))
max_hw = Inches(2.9)
max_ww = Inches(6.2)
rsb = min(max_hw/img_sb.height, max_ww/img_sb.width)
img_sb.height = int(img_sb.height * rsb)
img_sb.width  = int(img_sb.width  * rsb)
img_sb.left   = Inches(0.3)
img_sb.top    = Inches(5.35)

# Right note
tb_lines(s, ["Gemeenschappelijk voor alle types:",
             "▶  ORM-polymorfisme (FitnessTest-base)",
             "▶  Async repository (SQLAlchemy 2.0)",
             "▶  Audit trail bij elke opslag",
             "▶  Automatische HR-forwarding via broker"],
         Inches(6.7), Inches(5.0), Inches(6.4), Inches(2.3),
         size=13, color=C_KHAKI, sa=5)


# ===========================================================================
# SLIDE 9 — Dataflow & Broker  (+img.png)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Dataflow — PHEF-invoer & Broker (MOM)",
          "Transactionele outbox · exp. backoff 5 s→10 min · dead-letter")

# Left text
tb(s, "Synchroon pad  (PTI wacht)", Inches(0.4), Inches(1.3), Inches(5.8), Inches(0.4),
   size=14, bold=True, color=C_AMBER)
sync_steps = ["Browser: PTI klikt 'Add'",
              "→  PhefPage (Shiny reactive)",
              "→  PhefController.add_phef()",
              "→  ServiceTest.add_phef_test()",
              "→  FitnessTestRepository.add()",
              "→  PostgreSQL — INSERT",
              "←  OK · grid refresh"]
rect(s, Inches(0.4), Inches(1.75), Inches(5.8), Inches(3.3), fill=C_PANEL)
tb_lines(s, sync_steps, Inches(0.6), Inches(1.85), Inches(5.4), Inches(3.1),
         size=15, color=C_WHITE, sa=9)

tb(s, "Asynchroon pad  (broker — PTI wacht NIET)", Inches(0.4), Inches(5.2),
   Inches(5.8), Inches(0.4), size=14, bold=True, color=C_GREEN)
broker_steps = ["Service → Broker.send_message(test)",
                "→  asyncio.Queue (in-memory)",
                "→  _process_cycle()  elke 5 s",
                "→  hr_messages (duurzame opslag)",
                "→  POST naar HR-systeem (BEMIL)"]
rect(s, Inches(0.4), Inches(5.65), Inches(5.8), Inches(1.65), fill=C_PANEL)
tb_lines(s, broker_steps, Inches(0.6), Inches(5.72), Inches(5.5), Inches(1.55),
         size=14, color=C_WHITE, sa=5)

# Right: broker sequence image
img_b = pic(s, IMG_BROKER, Inches(6.5), Inches(1.3))
max_hb = Inches(6.0)
max_wb = Inches(6.5)
rb = min(max_hb/img_b.height, max_wb/img_b.width)
img_b.height = int(img_b.height * rb)
img_b.width  = int(img_b.width  * rb)
img_b.left   = int(SLIDE_W - Inches(0.3) - img_b.width)
img_b.top    = Inches(1.35)


# ===========================================================================
# SLIDE 10 — Volledige testflow (diagrams/test_flow_ui_db_broker.png)
# ===========================================================================
image_slide("Volledige Testflow — UI → Service → DB → Broker → HR",
            "End-to-end PHEF-flow incl. foutpaden, retry en dead-letter",
            IMG_FLOW,
            "Bron: documentation/diagrams/test_flow_ui_db_broker.png")


# ===========================================================================
# SLIDE 11 — Agile / Scrum
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Agile Methodologie — Scrum metrics",
          "Sep 2025 – mei 2026 · 1 developer · 2-weekse sprints")
kpi_row(s, [("20","epics"),("80","stories"),("231","SP"),
            ("12,2","gem. velocity"),("1.012","commits"),("720 h","geschatte inspanning")],
        y=Inches(1.3))
add_tbl(s,
    ["Sprint","Periode","SP","Cumul.","Focus"],
    [("S1",  "sep 01–14",     "10","10",  "Opzet, auth, login (E1, E19)"),
     ("S2",  "sep 15–28",     "13","23",  "Gebruikersbeheer, BEMIL (E1, E9)"),
     ("S5",  "okt 27–nov 09", "18","74",  "4 epics — hoogste commit-dichtheid (160)"),
     ("S7",  "nov 24–dec 07", "16","110", "Cross sessies & statistieken (E8)"),
     ("S12", "feb 02–15",     "12","162", "DI-container refactor"),
     ("S17", "apr 13–26",     "25","221", "GDPR + cross-stats redesign (E20)"),
     ("S19", "mei 11–24",     "10","231", "Beveiliging, DPIA, finale (E19)")],
    Inches(0.4), Inches(2.8), Inches(8.8), Inches(4.3),
    cw=[Inches(0.9),Inches(1.5),Inches(0.7),Inches(0.85),Inches(4.85)],
    hs=14, rs=12)
rx3 = Inches(9.5)
rect(s, rx3, Inches(2.8), Inches(3.6), Inches(4.3), fill=C_PANEL)
tb(s, "Top 5 epics", rx3+Inches(0.15), Inches(2.9), Inches(3.3), Inches(0.38),
   size=13, bold=True, color=C_AMBER)
for i, (ep, sp) in enumerate([("E8  Cross & Statistieken","28 SP"),
                               ("E20 GDPR / Privacy","25 SP"),
                               ("E1  Gebruikersbeheer","18 SP"),
                               ("E3  PHEF-invoer","18 SP"),
                               ("E2  Sessieplanning","15 SP")]):
    y0 = Inches(3.35 + i * 0.62)
    rect(s, rx3+Inches(0.1), y0, Inches(3.4), Inches(0.55), fill=C_TBLALT)
    tb(s, ep, rx3+Inches(0.2), y0+Inches(0.05), Inches(2.4), Inches(0.45),
       size=12, color=C_WHITE)
    tb(s, sp, rx3+Inches(2.65), y0+Inches(0.05), Inches(0.85), Inches(0.45),
       size=13, bold=True, color=C_AMBER, align=PP_ALIGN.RIGHT)


# ===========================================================================
# SLIDE 12 — Kwaliteit & Testing
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Kwaliteit & Testing",
          "pytest-asyncio · mypy strict · ruff · pre-commit · GitHub Actions")
for cx, title_t, items in [
    (Inches(0.4), "Testpatronen",
     ["pytest + pytest-asyncio (async tests)",
      "AsyncMock / MagicMock via unittest.mock",
      "Constructor-injectie: mocking zonder patching",
      "container.override(mock) + reset_override()",
      "Singleton._instances wissen in fixtures",
      "Voorbeeld:",
      "  PhefController(service=mock, mil=mock)"]),
    (Inches(6.9), "Tooling & CI/CD",
     ["mypy — strict typechecking",
      "ruff — linting (E/F/W/I, regellengte 100)",
      "black — codeformattering",
      "pre-commit — auto-update version.yaml",
      "GitHub Actions — CI: lint + mypy + tests",
      "Docker — productie-image (geen secrets)",
      "Alembic — versiebeheerde DB-migraties"])]:
    rect(s, cx, Inches(1.35), Inches(6.0), Inches(5.85), fill=C_PANEL)
    tb(s, title_t, cx+Inches(0.2), Inches(1.45), Inches(5.6), Inches(0.45),
       size=16, bold=True, color=C_AMBER)
    tb_lines(s, items, cx+Inches(0.2), Inches(2.0), Inches(5.6), Inches(5.0),
             size=15, color=C_WHITE, sa=9)


# ===========================================================================
# SLIDE 13 — Beveiliging (OWASP)
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Beveiliging — OWASP Top 10 evaluatie",
          "Defense-in-depth · intranet-deployment · Argon2id")
tbl = add_tbl(s,
    ["OWASP risico","Maatregel in WarriorFit","Status"],
    [("A01 — Broken Access Control", "RBAC per PageSpec · IDOR-fix · sessie-scoped UserStore", "✓"),
     ("A02 — Cryptographic Failures","Argon2id · PostgreSQL TLS verify-full (productie)",       "✓"),
     ("A03 — Injection",             "SQLAlchemy geparametriseerde queries — geen raw SQL",      "✓"),
     ("A05 — Misconfiguration",      "CORS-vergrendeling · X-API-Key op MOM · strict CSP",      "✓"),
     ("A07 — Auth Failures",         "Rate-limiting login · 10-min timeout · audit trail",       "✓"),
     ("A09 — Logging & Monitoring",  "Volledige CRUD-audit log · broker-health card",            "✓"),
     ("A10 — SSRF",                  "HR-URL allowlist (config) — HTTPS validatie open punt",   "⚠")],
    Inches(0.4), Inches(1.35), Inches(12.6), Inches(5.85),
    cw=[Inches(3.0),Inches(7.3),Inches(2.3)], hs=14, rs=13)
# colour status column
for ri in range(1, 8):
    cell = tbl.cell(ri, 2)
    ok   = cell.text_frame.paragraphs[0].runs[0].text.startswith("✓")
    cell.fill.solid()
    cell.fill.fore_color.rgb = C_GREEN if ok else C_RED
    cell.text_frame.paragraphs[0].runs[0].font.color.rgb = C_BG


# ===========================================================================
# SLIDE 14 — AVG / GDPR
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "AVG / GDPR Compliance",
          "DPIA Art. 35 · gezondheidsdata Art. 9 · zelfservice privacypagina")
for cx, title_t, items in [
    (Inches(0.4), "Rechtsgrond & scope",
     ["Art. 6(1)(c) — wettelijke verplichting (militaire opleiding)",
      "Art. 6(1)(e) — taak van algemeen belang",
      "Art. 9(2)(b) — gezondheidsdata in arbeidscontext",
      "DPIA uitgevoerd (Art. 35) — versie 1.1, 30 apr 2026",
      "Verwerkingsverantwoordelijke: Belgische Defensie",
      "Uitsluitend intranet — geen publieke blootstelling"]),
    (Inches(6.9), "Geïmplementeerde rechten",
     ["Art. 15 — Inzage: volledig exporteerbaar",
      "Art. 17 — Verwijdering: GdprService + FK CASCADE",
      "Art. 20 — Portabiliteit: JSON-export",
      "Art. 7  — Toestemming: user_consents tabel",
      "RetentionService: automatische verwijdering",
      "Audit trail: alle CRUD-acties (Art. 32)"])]:
    rect(s, cx, Inches(1.35), Inches(6.0), Inches(5.85), fill=C_PANEL)
    tb(s, title_t, cx+Inches(0.2), Inches(1.45), Inches(5.6), Inches(0.45),
       size=15, bold=True, color=C_AMBER)
    bullet(s, items, cx+Inches(0.2), Inches(2.0), Inches(5.6), Inches(4.8),
           size=14, sa=9)


# ===========================================================================
# SLIDE 15 — Technologiestapel
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Technologiestapel",
          "Python 3.13+ · moderne async stack · volledig open source")
groups = [
    ("Frontend / UI",     C_AMBER, ["Shiny for Python — reactieve server-side UI",
                                     "Plotly — interactieve grafieken",
                                     "Rajdhani + JetBrains Mono",
                                     "CSS-thema: olive / khaki / amber"]),
    ("Backend / Data",    C_GREEN, ["PostgreSQL + asyncpg",
                                    "SQLAlchemy 2.0 Async ORM",
                                    "Alembic — DB-migratiebeheer",
                                    "dependency-injector (DI-container)"]),
    ("Beveiliging",       C_RED,   ["Argon2id — wachtwoordhashing",
                                    "RBAC per PageSpec (6 rollen)",
                                    "TLS verify-full (productie)",
                                    "X-API-Key + CORS-vergrendeling"]),
    ("Infra / Dev",       C_BLUE,  ["Docker + GitHub Actions CI/CD",
                                    "FastAPI — MOM REST endpoint",
                                    "Mailpit — e-mailpreview (dev)",
                                    "uv · ruff · mypy · black · pre-commit"]),
]
gw = Inches(6.2); gh = Inches(2.6)
for idx, (grp, color, items) in enumerate(groups):
    col = idx % 2; row = idx // 2
    gx = Inches(0.4 + col * 6.5); gy = Inches(1.45 + row * 2.85)
    rect(s, gx, gy, gw, gh, fill=C_PANEL)
    rect(s, gx, gy, gw, Inches(0.45), fill=color)
    tb(s, grp, gx+Inches(0.15), gy+Inches(0.05), gw-Inches(0.2), Inches(0.38),
       size=14, bold=True, color=C_BG)
    tb_lines(s, items, gx+Inches(0.15), gy+Inches(0.5), gw-Inches(0.2), gh-Inches(0.6),
             size=13, color=C_KHAKI, sa=4)


# ===========================================================================
# SLIDE 16 — Routekaart
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
title_bar(s, "Routekaart — verdere ontwikkeling",
          "Open punten & toekomstige iteraties")
items_rk = [
    (C_RED,   "Hoog",    "SSO / SAML-integratie",
     "Eenmalige aanmelding via Defensie-identiteitsprovider"),
    (C_RED,   "Hoog",    "HR-URL HTTPS allowlist (OWASP A10)",
     "Whitelist + HTTPS-verificatie op uitgaand HR-verkeer"),
    (C_AMBER, "Gemiddeld","Serviceman login — wachtwoordverificatie",
     "SSO of eigen credentials afwachten (GitHub-issue geopend)"),
    (C_AMBER, "Gemiddeld","Responsief ontwerp (mobiel)",
     "Tablet-/smartphoneweergave voor PTI's op terrein"),
    (C_BLUE,  "Laag",    "Realtimenotificaties",
     "WebSocket push voor sessiewijzigingen & broker-alerts"),
    (C_BLUE,  "Laag",    "Multi-eenheid ondersteuning",
     "Uitbreiding naar meerdere regimenten / compagnieën"),
    (C_GREEN, "Laag",    "Uitgebreid rapportagepakket",
     "PDF-exports per test, eenheid en tijdsperiode"),
]
for i, (color, prio, title_r, desc_r) in enumerate(items_rk):
    y0 = Inches(1.4 + i * 0.73)
    rect(s, Inches(0.4), y0, Inches(1.3), Inches(0.62), fill=color)
    tb(s, prio, Inches(0.4), y0+Inches(0.07), Inches(1.3), Inches(0.5),
       size=12, bold=True, color=C_BG, align=PP_ALIGN.CENTER)
    rect(s, Inches(1.75), y0, Inches(11.0), Inches(0.62), fill=C_PANEL)
    tb(s, title_r, Inches(1.9), y0+Inches(0.07), Inches(3.3), Inches(0.5),
       size=14, bold=True, color=C_WHITE)
    tb(s, desc_r, Inches(5.25), y0+Inches(0.1), Inches(7.3), Inches(0.47),
       size=13, color=C_KHAKI, italic=True)


# ===========================================================================
# SLIDE 17 — Vragen / Afsluiting
# ===========================================================================
s = prs.slides.add_slide(blank)
set_bg(s, C_BG)
rect(s, Inches(0.5), Inches(1.2), Inches(12.33), Inches(5.2), fill=C_PANEL)
tb(s, "⚔", Inches(5.8), Inches(1.3), Inches(1.7), Inches(1.0),
   size=52, color=C_AMBER, align=PP_ALIGN.CENTER)
tb(s, "Bedankt!", Inches(1), Inches(2.2), Inches(11.33), Inches(1.1),
   size=52, bold=True, color=C_AMBER, align=PP_ALIGN.CENTER)
tb(s, "Vragen?", Inches(1), Inches(3.1), Inches(11.33), Inches(0.7),
   size=28, color=C_WHITE, align=PP_ALIGN.CENTER)
tb(s, "Benoit Goethals  ·  benoit.goethals@gmail.com",
   Inches(1), Inches(4.0), Inches(11.33), Inches(0.5),
   size=17, color=C_KHAKI, align=PP_ALIGN.CENTER)
tb(s, "github.com/BenoitGoethals/WarriorFit",
   Inches(1), Inches(4.5), Inches(11.33), Inches(0.45),
   size=15, italic=True, color=C_KHAKI, align=PP_ALIGN.CENTER)
kpi_row(s, [("20","epics"),("80","stories"),("231 SP","geleverd"),
            ("1.012","commits"),("25.800","lijnen Python"),("8,5 mnd","solo")])

# ---------------------------------------------------------------------------
out = "/Users/benoit/PycharmProjects/WarriorFit/documentation/WarriorFit_Presentatie_10min_NL.pptx"
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides)} slides)")
