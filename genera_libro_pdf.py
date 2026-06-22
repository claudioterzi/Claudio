#!/usr/bin/env python3
"""Genera il PDF completo di SUCHIALO, TROIA."""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W, H = A4

# ── colori ────────────────────────────────────────────────────────────────────
ROSSO   = colors.HexColor("#8B0000")
NERO    = colors.HexColor("#1a1a1a")
GRIGIO  = colors.HexColor("#555555")
BIANCO  = colors.white
ORO     = colors.HexColor("#C9A84C")

# ── font: usa DejaVu se disponibile, altrimenti Helvetica ────────────────────
DEJAVU    = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
DEJAVU_B  = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
DEJAVU_SI = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf"

if os.path.exists(DEJAVU):
    pdfmetrics.registerFont(TTFont("Body",   DEJAVU))
    pdfmetrics.registerFont(TTFont("BodyB",  DEJAVU_B))
    pdfmetrics.registerFont(TTFont("BodyI",  DEJAVU_SI))
    FONT      = "Body"
    FONT_BOLD = "BodyB"
    FONT_IT   = "BodyI"
else:
    FONT      = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_IT   = "Helvetica-Oblique"

# ── stili ─────────────────────────────────────────────────────────────────────
def stili():
    s = {}

    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName=FONT_BOLD, fontSize=48,
        textColor=ROSSO, alignment=TA_CENTER,
        leading=58, spaceAfter=12,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName=FONT_IT, fontSize=16,
        textColor=NERO, alignment=TA_CENTER, leading=22, spaceAfter=6,
    )
    s["cover_autor"] = ParagraphStyle(
        "cover_autor", fontName=FONT, fontSize=13,
        textColor=GRIGIO, alignment=TA_CENTER, leading=18,
    )

    s["h1"] = ParagraphStyle(
        "h1", fontName=FONT_BOLD, fontSize=26,
        textColor=ROSSO, leading=32,
        spaceBefore=0, spaceAfter=8,
    )
    s["h1_sub"] = ParagraphStyle(
        "h1_sub", fontName=FONT_IT, fontSize=13,
        textColor=GRIGIO, leading=18,
        spaceBefore=0, spaceAfter=16,
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName=FONT_BOLD, fontSize=15,
        textColor=NERO, leading=20,
        spaceBefore=18, spaceAfter=6,
    )
    s["h3"] = ParagraphStyle(
        "h3", fontName=FONT_BOLD, fontSize=12,
        textColor=GRIGIO, leading=16,
        spaceBefore=10, spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "body", fontName=FONT, fontSize=11,
        textColor=NERO, leading=17,
        spaceBefore=0, spaceAfter=8,
        alignment=TA_JUSTIFY,
    )
    s["body_italic"] = ParagraphStyle(
        "body_italic", fontName=FONT_IT, fontSize=10,
        textColor=GRIGIO, leading=15,
        spaceBefore=0, spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", fontName=FONT, fontSize=11,
        textColor=NERO, leading=16,
        spaceBefore=0, spaceAfter=3,
        leftIndent=18, bulletIndent=6,
        alignment=TA_LEFT,
    )
    s["appendix"] = ParagraphStyle(
        "appendix", fontName=FONT_BOLD, fontSize=10,
        textColor=NERO, leading=14,
        spaceBefore=0, spaceAfter=2,
        leftIndent=18,
    )
    s["footer_note"] = ParagraphStyle(
        "footer_note", fontName=FONT_IT, fontSize=9,
        textColor=GRIGIO, leading=13, alignment=TA_CENTER,
        spaceBefore=4,
    )
    return s


# ── helper: escape + inline markdown → ReportLab XML ─────────────────────────
def rl(text):
    """Escape HTML special chars, then convert **bold** and *italic*."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    return text


def hr(color=ROSSO, width=1.5):
    return HRFlowable(width="100%", thickness=width, color=color, spaceAfter=10, spaceBefore=4)


# ── pagina di copertina ───────────────────────────────────────────────────────
def copertina(S):
    elems = []
    elems.append(Spacer(1, 5*cm))
    elems.append(Paragraph("SUCHIALO, TROIA", S["cover_title"]))
    elems.append(Spacer(1, 0.4*cm))
    elems.append(hr(ORO, 2))
    elems.append(Spacer(1, 0.4*cm))
    elems.append(Paragraph(
        "Manuale per Froci che Vogliono Imparare sul Serio",
        S["cover_sub"]
    ))
    elems.append(Spacer(1, 0.8*cm))
    elems.append(Paragraph(
        "Come succhiare il cazzo senza fare figure di merda<br/>"
        "(e divertirti mentre lo fai)",
        S["cover_sub"]
    ))
    elems.append(Spacer(1, 4*cm))
    elems.append(hr(ROSSO, 0.5))
    elems.append(Spacer(1, 0.4*cm))
    elems.append(Paragraph("Claudio Terzi", S["cover_autor"]))
    elems.append(Paragraph("2026", S["cover_autor"]))
    elems.append(PageBreak())
    return elems


# ── parse blocco di testo markdown → flowables ────────────────────────────────
def parse_md(text, S):
    elems = []
    lines = text.split("\n")
    i = 0
    chapter_open = False

    while i < len(lines):
        line = lines[i].rstrip()

        # separator ---
        if re.match(r"^---+$", line):
            if chapter_open:
                elems.append(hr(colors.HexColor("#cccccc"), 0.5))
            i += 1
            continue

        # H1: # Titolo
        if re.match(r"^# ", line):
            if chapter_open:
                elems.append(PageBreak())
            chapter_open = True
            title = rl(line[2:].strip())
            elems.append(Spacer(1, 0.5*cm))
            elems.append(hr(ROSSO, 2))
            elems.append(Paragraph(title, S["h1"]))
            # check for italic subtitle on next line
            if i+1 < len(lines) and re.match(r"^\*Ovvero", lines[i+1].strip()):
                i += 1
                sub = rl(lines[i].strip().strip("*"))
                elems.append(Paragraph(sub, S["h1_sub"]))
            i += 1
            continue

        # H2: ## Titolo
        if re.match(r"^## ", line):
            title = rl(line[3:].strip())
            elems.append(Paragraph(title, S["h2"]))
            i += 1
            continue

        # H3: ### Titolo
        if re.match(r"^### ", line):
            title = rl(line[4:].strip())
            elems.append(Paragraph(title, S["h3"]))
            i += 1
            continue

        # bullet: - testo
        if re.match(r"^- ", line):
            content = rl(line[2:].strip())
            elems.append(Paragraph(f"• {content}", S["bullet"]))
            i += 1
            continue

        # italic line: *testo*
        if re.match(r"^\*[^*]", line) and line.endswith("*"):
            content = rl(line.strip("*").strip())
            elems.append(Paragraph(content, S["body_italic"]))
            i += 1
            continue

        # inline app note: *Sull'app SUCHIALO...*
        if line.startswith("*") and line.endswith("*") and len(line) > 2:
            content = rl(line[1:-1])
            elems.append(Spacer(1, 4))
            elems.append(hr(colors.HexColor("#dddddd"), 0.5))
            elems.append(Paragraph(content, S["body_italic"]))
            elems.append(hr(colors.HexColor("#dddddd"), 0.5))
            i += 1
            continue

        # backtick note lines (skip meta notes at top)
        if line.startswith("*Tono:") or line.startswith("*Parole"):
            i += 1
            continue

        # empty line
        if line.strip() == "":
            elems.append(Spacer(1, 4))
            i += 1
            continue

        # normal paragraph
        content = rl(line)
        if content.strip():
            elems.append(Paragraph(content, S["body"]))
        i += 1

    return elems


# ── capitolo 4 (hardcoded) ────────────────────────────────────────────────────
CAP4 = """
# Capitolo 4 – Mano e Bocca Insieme
*Ovvero: smettila di trattare la mano come una comparsa*

Scommetto che lo sai già.

Stai lì con il cazzo in bocca — lingua che lavora, ritmo decente, saliva ovunque — e la mano sinistra è appoggiata sulla sua coscia come un ospite a disagio a una cena di famiglia.

Non sa cosa fare. Non fa niente. O peggio: fa tutto lei mentre la bocca si prende il merito.

Questo capitolo serve a risolvere quel problema.

---

## La logica di base: la continuità

La regola più importante che imparerai in questo capitolo è questa: **la mano non deve aiutare la bocca — deve essere la bocca.**

Quando funziona davvero, lui non sente dove finisce una e inizia l'altra. Sente solo una sensazione continua, calda, umida, che scorre su e giù senza interruzioni. Non sente "bocca... poi mano... poi bocca di nuovo." Sente un'unica cosa che non smette mai.

Quello è l'obiettivo.

---

## La presa base: la O perfetta

Pollice e indice formano un cerchio. Niente di più.

Quel cerchio si posiziona esattamente dove finisce la tua bocca — appena sotto la cappella quando sei in alto, più in basso quando scendi. **La mano segue la bocca.** Non la precede, non la insegue. La segue, millimetro per millimetro.

La pressione non è una stretta. È un accompagnamento. Come tenere per mano qualcuno che sta correndo con te — abbastanza da sentirsi, non abbastanza da frenarlo.

Saliva. Tanta. La mano asciutta su un cazzo è come limare un legno senza carta vetrata. Usa la saliva che produci — lasciala scendere sulla mano, lasciala distribuirsi. Non pulire niente.

---

## La torsione: quando aggiungi una dimensione

Questa è la tecnica che fa la differenza tra un pompino decente e uno che lui ricorda per settimane.

Mentre la bocca lavora sulla punta — cappella, frenulo, corona — la mano inizia a ruotare leggermente sul fusto. Non su e giù. In torsione.

La variante più potente: **torsione opposta.** Una mano gira in senso orario, l'altra in senso antiorario, sincronizzate. Se hai due mani libere (e il cazzo è abbastanza lungo da giustificarlo), questo crea una sensazione di lunghezza e complessità che la bocca da sola non può replicare.

Se il cazzo è più corto, una mano basta. La torsione su un fusto corto è ancora più intensa — meno spazio, più concentrazione della sensazione.

---

## Il pollice sul frenulo

Mentre la bocca succhia la cappella, porta il pollice della mano sotto — e appoggialo sul frenulo.

Pressione leggera. Non massaggiare, non strofinare. Appoggia e tieni.

Il frenulo è già il punto più sensibile del cazzo. La bocca sopra e il pollice sotto nello stesso momento creano una sandwich di sensazioni che manda quasi tutti fuori di testa. Sperimenta la pressione — alcuni preferiscono quasi niente, altri vogliono sentirlo davvero. Leggi la sua reazione.

---

## La mano libera: le palle

Hai ancora una mano libera.

Non lasciarla a disagio sulla coscia.

**Cupping:** la mano libera raccoglie le palle dal basso, con delicatezza. Non stringe, non tira. Sostiene e scalda. Per moltissimi uomini questa sensazione — essere tenuti mentre vengono succhiati — è quasi più intensa del pompino stesso.

---

## L'errore che fa quasi tutti

La mano che sostituisce la bocca.

Lo riconosci così: stai succhiando, la mascella si stanca, la mano prende il ritmo e la bocca si ferma. O peggio — la bocca è ferma sulla punta, quasi immobile, mentre la mano fa su e giù da sola.

Quello non è un pompino con la mano come alleata. È una sega con la bocca come decorazione.

La differenza non è dove lavora la mano. È se la bocca lavora ancora.

La bocca non smette mai. Può rallentare, può concentrarsi sulla cappella, può succhiare piano mentre la mano fa il grosso del movimento — ma la bocca non esce dal gioco. Il calore, l'umidità, la pressione della bocca sono quello che distingue un pompino da tutto il resto.

---

## La combinazione avanzata: il moltiplicatore

Se vuoi simulare una profondità di gola che non hai ancora, questa è la tecnica.

La mano fa lo stesso movimento della bocca, in sincronia perfetta, ma continua verso il basso oltre dove la bocca arriva. Bocca scende fino a metà — la mano scende fino alla base. Bocca risale — la mano risale con lei.

Lui sente una sensazione continua dall'alto verso il basso che va molto più in profondità di quanto la tua gola stia realmente andando.

Non è imbroglio. È intelligenza.

---

## Pratica

La prima volta che provi la coordinazione bocca-mano sembrerà strana. Dovrai pensarci. Va bene.

Dopo tre o quattro volte, diventa automatico. Il corpo capisce il pattern e lo esegue senza che tu debba gestirlo consapevolmente. A quel punto hai una bocca e una mano che lavorano come un'unica cosa — e lui lo sente.

Inizia lento. La sincronia prima della velocità.

*Nell'app SUCHIALO puoi ricevere feedback su questa tecnica specifica — i Guru valutano la coordinazione bocca-mano come una delle prime cose che insegnano ai novizi.*
"""


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    output = "/home/user/Claudio/output/SUCHIALO_TROIA_completo.pdf"
    os.makedirs(os.path.dirname(output), exist_ok=True)

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=3*cm, rightMargin=3*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        title="SUCHIALO, TROIA",
        author="Claudio Terzi",
    )

    S = stili()
    story = []

    # copertina
    story += copertina(S)

    # avviso capitoli
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Nota: questo PDF include i Capitoli 4 → Finale. "
        "I Capitoli 1–3 e l'Introduzione vanno integrati dalla sessione precedente.",
        S["body_italic"]
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(hr(ROSSO, 1))

    # capitolo 4
    story += parse_md(CAP4, S)

    # capitoli 5 → finale dal file
    cap_file = "/home/user/Claudio/idee/SUCHIALO_TROIA_capitoli_5-finale.md"
    with open(cap_file, encoding="utf-8") as f:
        content = f.read()

    story += parse_md(content, S)

    # pagina finale
    story.append(PageBreak())
    story.append(Spacer(1, 6*cm))
    story.append(hr(ORO, 2))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Buon pompino.", S["cover_title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("— Claudio Terzi, 2026", S["cover_autor"]))

    doc.build(story)
    print(f"PDF generato: {output}")


if __name__ == "__main__":
    main()
