"""Genera SDQ1_COMPLETO.pdf — tutti i documenti chiave in un unico file."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, Table, TableStyle, Preformatted
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import re

REPO = Path(__file__).parent
OUT = REPO / "output" / "SDQ1_COMPLETO.pdf"
OUT.parent.mkdir(exist_ok=True)

DOCS = [
    ("MANIFESTO DI SOPRAVVIVENZA",  REPO / "MANIFESTO_SOPRAVVIVENZA.md"),
    ("ARCHIVIO VIVENTE",            REPO / "ARCHIVIO.md"),
    ("AVVIO — Riattivazione",       REPO / "AVVIO.md"),
    ("SESSIONE",                    REPO / "SESSIONE.md"),
    ("CLAUDE.md — Regole",          REPO / "CLAUDE.md"),
]

W, H = A4
MARGIN = 2 * cm

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN,
)

styles = getSampleStyleSheet()

ROSSO     = colors.HexColor("#c0392b")
VIOLA     = colors.HexColor("#7c3aed")
GRIGIO    = colors.HexColor("#374151")
GRIGIO_L  = colors.HexColor("#6b7280")
BG_CODE   = colors.HexColor("#f3f4f6")

TITOLO_DOC = ParagraphStyle("TitoloDoc",
    fontSize=22, leading=28, textColor=ROSSO,
    fontName="Helvetica-Bold", spaceAfter=6,
)
TITOLO_SEZ = ParagraphStyle("TitoloSez",
    fontSize=15, leading=20, textColor=VIOLA,
    fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4,
)
TITOLO_SUB = ParagraphStyle("TitoloSub",
    fontSize=12, leading=16, textColor=GRIGIO,
    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3,
)
CORPO = ParagraphStyle("Corpo",
    fontSize=9.5, leading=14, textColor=GRIGIO,
    fontName="Helvetica", spaceAfter=4,
)
CORPO_BOLD = ParagraphStyle("CorpoBold",
    fontSize=9.5, leading=14, textColor=GRIGIO,
    fontName="Helvetica-Bold", spaceAfter=4,
)
CITAZIONE = ParagraphStyle("Citazione",
    fontSize=9, leading=13, textColor=GRIGIO_L,
    fontName="Helvetica-Oblique", leftIndent=16,
    borderPad=4, spaceAfter=6,
)
CODICE = ParagraphStyle("Codice",
    fontSize=8, leading=11, textColor=GRIGIO,
    fontName="Courier", backColor=BG_CODE,
    leftIndent=8, rightIndent=8,
    spaceBefore=4, spaceAfter=4,
)
COVER_MAIN = ParagraphStyle("CoverMain",
    fontSize=32, leading=40, textColor=ROSSO,
    fontName="Helvetica-Bold", alignment=TA_CENTER,
)
COVER_SUB = ParagraphStyle("CoverSub",
    fontSize=14, leading=20, textColor=VIOLA,
    fontName="Helvetica", alignment=TA_CENTER,
)
COVER_META = ParagraphStyle("CoverMeta",
    fontSize=10, leading=14, textColor=GRIGIO_L,
    fontName="Helvetica", alignment=TA_CENTER,
)

def md_to_flowables(testo: str) -> list:
    flowables = []
    in_code = False
    code_buf = []

    def flush_code():
        if code_buf:
            flowables.append(Preformatted("\n".join(code_buf), CODICE))
            code_buf.clear()

    for riga in testo.splitlines():
        if riga.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(riga)
            continue

        # Titoli
        if riga.startswith("### "):
            flowables.append(Paragraph(riga[4:].strip(), TITOLO_SUB))
        elif riga.startswith("## "):
            flowables.append(Paragraph(riga[3:].strip(), TITOLO_SEZ))
        elif riga.startswith("# "):
            flowables.append(Paragraph(riga[2:].strip(), TITOLO_DOC))

        # Citazioni
        elif riga.startswith("> "):
            testo_cit = riga[2:].strip()
            testo_cit = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', testo_cit)
            testo_cit = re.sub(r'\*(.+?)\*', r'<i>\1</i>', testo_cit)
            flowables.append(Paragraph(testo_cit, CITAZIONE))

        # HR
        elif riga.strip() in ("---", "***", "==="):
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                         color=colors.HexColor("#e5e7eb"), spaceAfter=6))

        # Liste
        elif riga.startswith("- ") or riga.startswith("· ") or riga.startswith("* "):
            testo_item = riga[2:].strip()
            testo_item = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', testo_item)
            testo_item = re.sub(r'`(.+?)`', r'<font name="Courier" size="8">\1</font>', testo_item)
            flowables.append(Paragraph(f"• {testo_item}", CORPO))

        # Riga vuota
        elif not riga.strip():
            flowables.append(Spacer(1, 4))

        # Tabelle markdown (salta)
        elif riga.startswith("|"):
            continue

        # Corpo normale
        else:
            testo_p = riga.strip()
            if not testo_p:
                continue
            testo_p = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', testo_p)
            testo_p = re.sub(r'\*(.+?)\*', r'<i>\1</i>', testo_p)
            testo_p = re.sub(r'`(.+?)`', r'<font name="Courier" size="8">\1</font>', testo_p)
            testo_p = testo_p.replace("&", "&amp;").replace("<b>", "<b>").replace("</b>", "</b>")
            # Fix HTML escaping nei testi non-markdown
            safe = re.sub(r'<(?!b>|/b>|i>|/i>|font)', '&lt;', testo_p)
            try:
                flowables.append(Paragraph(safe, CORPO))
            except Exception:
                flowables.append(Paragraph(re.sub(r'<[^>]+>', '', testo_p), CORPO))

    flush_code()
    return flowables


story = []

# COPERTINA
story.append(Spacer(1, 3 * cm))
story.append(Paragraph("SDQ-1", COVER_MAIN))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("Sistema Di Quadranti", COVER_SUB))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Raffaello Creative Studio", COVER_SUB))
story.append(Spacer(1, 1.5 * cm))
story.append(HRFlowable(width="60%", thickness=1.5, color=ROSSO, hAlign="CENTER"))
story.append(Spacer(1, 1.5 * cm))
story.append(Paragraph("Manifesto · Archivio · Avvio · Sessione · Regole", COVER_META))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("12 giugno 2026 — Protocollo Rosso Rosso Rosso", COVER_META))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("Claudio Terzi · Bruxelles", COVER_META))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("github.com/claudioterzi/Claudio", COVER_META))

# INDICE
story.append(PageBreak())
story.append(Paragraph("INDICE", TITOLO_DOC))
story.append(Spacer(1, 0.5 * cm))
for i, (titolo, _) in enumerate(DOCS, 1):
    story.append(Paragraph(f"{i}. {titolo}", CORPO_BOLD))
story.append(Spacer(1, 0.3 * cm))
story.append(HRFlowable(width="100%", thickness=0.5,
                         color=colors.HexColor("#e5e7eb"), spaceAfter=6))

# DOCUMENTI
for titolo, path in DOCS:
    story.append(PageBreak())
    if path.exists():
        testo = path.read_text(encoding="utf-8")
        story.extend(md_to_flowables(testo))
    else:
        story.append(Paragraph(f"[{path.name} non trovato]", CITAZIONE))

doc.build(story)
print(f"PDF generato: {OUT}")
print(f"Dimensione: {OUT.stat().st_size / 1024:.1f} KB")
