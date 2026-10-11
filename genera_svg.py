"""Genera 74 SVG (fronte + retro) per le carte dei Tarocchi Quantici R³∞."""
import sys, os, json, textwrap
sys.path.insert(0, os.path.dirname(__file__))

from tarocchi import MAZZO, voce, eco
from tarocchi.codice_simbolico import TipoArcano

W, H = 350, 600          # dimensioni carta in px
GOLD   = "#c9a84c"
GOLD2  = "#8a6a20"
BG     = "#0c0c0e"
SURF   = "#141418"
TXT    = "#e8d5a3"
TXT2   = "#a89060"
WHITE  = "#f0e6c8"

# ── Simboli elementali (path SVG) ────────────────────────────────────────────

SIMBOLI = {
    "fuoco": """
      <polygon points="175,30 215,110 135,110" fill="none" stroke="{g}" stroke-width="2.5" opacity="0.9"/>
      <polygon points="175,55 200,100 150,100" fill="{g}" opacity="0.25"/>
      <line x1="175" y1="30" x2="175" y2="115" stroke="{g}" stroke-width="1" opacity="0.4"/>
    """,
    "acqua": """
      <path d="M175,30 C195,60 215,80 215,100 C215,122 196,135 175,135 C154,135 135,122 135,100 C135,80 155,60 175,30Z"
            fill="none" stroke="{g}" stroke-width="2.5" opacity="0.9"/>
      <path d="M175,55 C188,75 200,88 200,102 C200,115 188,123 175,123 C162,123 150,115 150,102 C150,88 162,75 175,55Z"
            fill="{g}" opacity="0.2"/>
    """,
    "aria": """
      <circle cx="175" cy="82" r="48" fill="none" stroke="{g}" stroke-width="2.5" opacity="0.9"/>
      <circle cx="175" cy="82" r="30" fill="none" stroke="{g}" stroke-width="1" opacity="0.4"/>
      <line x1="127" y1="82" x2="223" y2="82" stroke="{g}" stroke-width="1" opacity="0.4"/>
      <line x1="175" y1="34" x2="175" y2="130" stroke="{g}" stroke-width="1" opacity="0.4"/>
    """,
    "terra": """
      <polygon points="175,30 230,120 120,120" fill="none" stroke="{g}" stroke-width="2.5" opacity="0.9"/>
      <polygon points="175,120 230,30 120,30" fill="none" stroke="{g}" stroke-width="2.5" opacity="0.5"/>
      <polygon points="175,65 205,115 145,115" fill="{g}" opacity="0.2"/>
    """,
    "etere": """
      <circle cx="175" cy="82" r="48" fill="none" stroke="{g}" stroke-width="1.5" opacity="0.6" stroke-dasharray="4,4"/>
      <polygon points="175,34 212,105 138,105" fill="none" stroke="{g}" stroke-width="2" opacity="0.9"/>
      <polygon points="175,130 138,59 212,59" fill="none" stroke="{g}" stroke-width="2" opacity="0.5"/>
      <circle cx="175" cy="82" r="8" fill="{g}" opacity="0.6"/>
    """,
}

def simbolo(elemento: str) -> str:
    s = SIMBOLI.get(elemento or "etere", SIMBOLI["etere"])
    return s.replace("{g}", GOLD)

# ── Testo a capo (SVG tspan) ─────────────────────────────────────────────────

def wrap_tspan(text: str, max_chars: int, x: int, dy_first: float, dy: float, **attrs) -> str:
    lines = textwrap.wrap(text, max_chars)
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    out = []
    for i, line in enumerate(lines):
        d = dy_first if i == 0 else dy
        out.append(f'<tspan x="{x}" dy="{d}em">{esc(line)}</tspan>')
    return f'<text {attr_str}>{"".join(out)}</text>' if out else ""

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# ── Cornice ───────────────────────────────────────────────────────────────────

def cornice(extra: str = "") -> str:
    m = 12        # margine
    r = 10        # raggio angoli
    t = 4         # spessore linea decorativa interna
    return f"""
    <!-- bordo esterno -->
    <rect x="{m}" y="{m}" width="{W-2*m}" height="{H-2*m}"
          rx="{r}" ry="{r}"
          fill="{SURF}" stroke="{GOLD}" stroke-width="1.8" opacity="0.95"/>
    <!-- linea interna -->
    <rect x="{m+t+3}" y="{m+t+3}" width="{W-2*(m+t+3)}" height="{H-2*(m+t+3)}"
          rx="{r-3}" ry="{r-3}"
          fill="none" stroke="{GOLD2}" stroke-width="0.8" opacity="0.5"/>
    <!-- angoli decorativi -->
    <g stroke="{GOLD}" stroke-width="1.5" fill="none" opacity="0.8">
      <path d="M{m+r},{m+22} L{m+22},{m+22} L{m+22},{m+r}"/>
      <path d="M{W-m-r},{m+22} L{W-m-22},{m+22} L{W-m-22},{m+r}"/>
      <path d="M{m+r},{H-m-22} L{m+22},{H-m-22} L{m+22},{H-m-r}"/>
      <path d="M{W-m-r},{H-m-22} L{W-m-22},{H-m-22} L{W-m-22},{H-m-r}"/>
    </g>
    {extra}
    """

# ── FRONTE ────────────────────────────────────────────────────────────────────

def svg_fronte(carta) -> str:
    v = voce(carta)
    e = eco(carta)
    kw = " · ".join(list(carta.parole_chiave)[:3])
    el = carta.elemento or "etere"
    is_maggiore = carta.arcano == TipoArcano.MAGGIORE

    # label arcano in alto
    if is_maggiore:
        arcano_label = f"Arcano Maggiore  ·  {carta.indice}"
    else:
        seme_label = (carta.seme.value if carta.seme else "").upper()
        arcano_label = f"Arcano Minore  ·  {seme_label}"

    # taglia voce e eco per il display
    voce_display = v if len(v) <= 26 else v[:24] + "…"
    eco_display  = e if len(e) <= 52 else e[:50] + "…"

    # dimensione font voce (adattiva)
    vlen = len(v)
    if vlen <= 12:   vsize = 22
    elif vlen <= 20: vsize = 18
    elif vlen <= 28: vsize = 15
    else:            vsize = 13

    # simbolo elementale centrato — zona 30–160
    simb = simbolo(el)

    # colore elemento
    el_color = {"fuoco": "#e8622a", "acqua": "#4a9fd4", "aria": "#9bd4e0",
                 "terra": "#7a9e4a", "etere": "#c9a84c"}.get(el, GOLD)

    parole_lines = textwrap.wrap(kw, 38)
    parole_svg = ""
    for i, line in enumerate(parole_lines):
        parole_svg += f'<tspan x="175" dy="{"0" if i==0 else "1.3"}em">{esc(line)}</tspan>'

    eco_lines = textwrap.wrap(e, 40)
    eco_svg = ""
    for i, line in enumerate(eco_lines[:3]):
        eco_svg += f'<tspan x="175" dy="{"0" if i==0 else "1.25"}em">{esc(line)}</tspan>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#111115"/>
      <stop offset="100%" stop-color="#0a0a0d"/>
    </linearGradient>
    <linearGradient id="elGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- sfondo -->
  <rect width="{W}" height="{H}" fill="url(#bgGrad)"/>

  {cornice()}

  <!-- alone elementale -->
  <ellipse cx="175" cy="155" rx="90" ry="70" fill="{el_color}" opacity="0.06"/>

  <!-- simbolo elementale -->
  <g transform="translate(0, 50)">
    {simb}
  </g>

  <!-- label arcano -->
  <text x="175" y="40" text-anchor="middle"
        font-family="Georgia, serif" font-size="9.5" fill="{TXT2}"
        letter-spacing="2">{esc(arcano_label.upper())}</text>

  <!-- linea separatrice alta -->
  <line x1="40" y1="178" x2="310" y2="178" stroke="{GOLD2}" stroke-width="0.6" opacity="0.5"/>

  <!-- VOCE — nome nella lettura -->
  <text x="175" y="212" text-anchor="middle"
        font-family="Georgia, serif" font-size="{vsize}" fill="{WHITE}"
        font-style="italic" font-weight="normal" letter-spacing="0.5">
    {esc(voce_display)}
  </text>

  <!-- elemento -->
  <text x="175" y="240" text-anchor="middle"
        font-family="Georgia, serif" font-size="9" fill="{el_color}" letter-spacing="3">
    {esc(el.upper())}
  </text>

  <!-- linea centrale -->
  <line x1="60" y1="255" x2="290" y2="255" stroke="{GOLD2}" stroke-width="0.5" opacity="0.4"/>

  <!-- ECO -->
  <text x="175" y="278" text-anchor="middle"
        font-family="Georgia, serif" font-size="10" fill="{TXT2}" font-style="italic">
    {eco_svg}
  </text>

  <!-- linea bassa -->
  <line x1="40" y1="388" x2="310" y2="388" stroke="{GOLD2}" stroke-width="0.6" opacity="0.4"/>

  <!-- parole chiave -->
  <text x="175" y="408" text-anchor="middle"
        font-family="Georgia, serif" font-size="9" fill="{TXT2}" letter-spacing="1">
    {parole_svg}
  </text>

  <!-- nome tecnico in basso (piccolo, per la macchina) -->
  <text x="175" y="{H-26}" text-anchor="middle"
        font-family="monospace" font-size="8" fill="{GOLD2}" opacity="0.5" letter-spacing="1">
    {esc(carta.nome.upper())}
  </text>

  <!-- indice angolo -->
  <text x="28" y="48" text-anchor="middle"
        font-family="Georgia, serif" font-size="11" fill="{GOLD}" opacity="0.7">
    {carta.indice}
  </text>

</svg>"""


# ── RETRO ─────────────────────────────────────────────────────────────────────

def svg_retro() -> str:
    cx, cy = W // 2, H // 2

    # pattern: cerchi concentrici + stella a 8 punte + R³∞
    def star(cx, cy, r1, r2, pts, stroke, sw, op):
        import math
        path = ""
        for i in range(pts * 2):
            r = r1 if i % 2 == 0 else r2
            a = math.pi * i / pts - math.pi / 2
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            path += f"{'M' if i==0 else 'L'}{x:.1f},{y:.1f}"
        path += "Z"
        return f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bgR" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0e0e12"/>
      <stop offset="100%" stop-color="#080810"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="{GOLD}" stroke-width="0.15" opacity="0.3"/>
    </pattern>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#bgR)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>

  {cornice()}

  <!-- alone centrale -->
  <ellipse cx="{cx}" cy="{cy}" rx="130" ry="130" fill="url(#glow)"/>

  <!-- cerchi concentrici -->
  <circle cx="{cx}" cy="{cy}" r="110" fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.25"/>
  <circle cx="{cx}" cy="{cy}" r="88"  fill="none" stroke="{GOLD}" stroke-width="0.6" opacity="0.3"/>
  <circle cx="{cx}" cy="{cy}" r="66"  fill="none" stroke="{GOLD}" stroke-width="1"   opacity="0.35"/>
  <circle cx="{cx}" cy="{cy}" r="44"  fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.4"/>
  <circle cx="{cx}" cy="{cy}" r="22"  fill="none" stroke="{GOLD}" stroke-width="0.6" opacity="0.5"/>

  <!-- stella a 8 punte -->
  {star(cx, cy, 110, 55, 8, GOLD, 1.2, 0.35)}
  {star(cx, cy, 88,  44, 8, GOLD, 0.7, 0.2)}

  <!-- linee diagonali -->
  <g stroke="{GOLD}" stroke-width="0.6" opacity="0.2">
    <line x1="{cx-110}" y1="{cy}" x2="{cx+110}" y2="{cy}"/>
    <line x1="{cx}" y1="{cy-110}" x2="{cx}" y2="{cy+110}"/>
    <line x1="{cx-78}" y1="{cy-78}" x2="{cx+78}" y2="{cy+78}"/>
    <line x1="{cx+78}" y1="{cy-78}" x2="{cx-78}" y2="{cy+78}"/>
  </g>

  <!-- simbolo centrale R³∞ -->
  <text x="{cx}" y="{cy+12}" text-anchor="middle"
        font-family="Georgia, serif" font-size="38" fill="{GOLD}" opacity="0.85"
        letter-spacing="-2">R³∞</text>

  <!-- quattro simboli elementali agli angoli -->
  <text x="55"     y="68"     text-anchor="middle" font-size="18" fill="{GOLD}" opacity="0.45" font-family="serif">🜂</text>
  <text x="{W-55}" y="68"     text-anchor="middle" font-size="18" fill="{GOLD}" opacity="0.45" font-family="serif">🜄</text>
  <text x="55"     y="{H-50}" text-anchor="middle" font-size="18" fill="{GOLD}" opacity="0.45" font-family="serif">🜃</text>
  <text x="{W-55}" y="{H-50}" text-anchor="middle" font-size="18" fill="{GOLD}" opacity="0.45" font-family="serif">🜁</text>

  <!-- scritta sistema in basso -->
  <text x="{cx}" y="{H-28}" text-anchor="middle"
        font-family="Georgia, serif" font-size="9" fill="{GOLD}" opacity="0.4" letter-spacing="3">
    TAROCCHI QUANTICI
  </text>

</svg>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def slug(nome: str) -> str:
    import unicodedata, re
    s = unicodedata.normalize("NFD", nome)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().replace(" ", "_").replace("'", "")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s

OUT = "public/cards"
os.makedirs(OUT, exist_ok=True)

# retro — uno solo, uguale per tutti
retro_path = os.path.join(OUT, "retro.svg")
with open(retro_path, "w", encoding="utf-8") as f:
    f.write(svg_retro())
print(f"retro → {retro_path}")

# fronti — uno per carta
for carta in MAZZO:
    nome_file = f"{carta.indice:02d}_{slug(carta.nome)}.svg"
    path = os.path.join(OUT, nome_file)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_fronte(carta))

print(f"fronti → {len(MAZZO)} SVG generati in {OUT}/")

# indice JSON per il sito
indice = [
    {
        "indice": c.indice,
        "nome":   c.nome,
        "voce":   voce(c),
        "fronte": f"/cards/{c.indice:02d}_{slug(c.nome)}.svg",
        "retro":  "/cards/retro.svg",
    }
    for c in MAZZO
]
with open(os.path.join(OUT, "indice.json"), "w", encoding="utf-8") as f:
    json.dump(indice, f, ensure_ascii=False, indent=2)
print(f"indice → {OUT}/indice.json ({len(indice)} voci)")
