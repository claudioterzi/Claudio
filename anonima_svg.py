"""ANONIMA-008 — Generatore SVG delle cornici Polaroid (vuote/velate).

Produce le cornici dell'archivio SENZA alcun contenuto esplicito: la finestra
resta velata per scelta curatoriale, non per censura. Coerente con la tesi del
progetto — ciò che si mostra è la cornice, ciò che si tace è l'opera.

Fronte  = cornice bianca + finestra velata (tratteggio + sfumatura d'epoca).
Retro   = cornice + grafia sul bordo (data stimata, formato) come nell'originale.

Zero dipendenze esterne. Output in public/anonima/.
"""
import os, json

# ── Dimensioni Polaroid classica (proporzioni reali ~ 88x107mm inquadratura 79x79) ──
W, H = 320, 384
PAD_X = 26          # margine cornice sinistra/destra
PAD_TOP = 26        # margine cornice alto
WIN = W - 2 * PAD_X # lato della finestra quadrata
WIN_Y = PAD_TOP

FRAME  = "#fbfaf6"
FRAME2 = "#efe9dc"
EDGE   = "#e2dccb"
INK    = "#6a5f49"
VEIL   = "#b4ab99"

# Palette per decennio: viraggio della pellicola nel tempo.
DECENNI = {
    "1968-1979": {"warm": "#b9a273", "cool": "#8f8676", "nota": "viraggio caldo"},
    "1980-1999": {"warm": "#c3b89f", "cool": "#9a917d", "nota": "grana fine"},
    "2000-oggi": {"warm": "#b7b3a6", "cool": "#8d8a80", "nota": "colore freddo"},
}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _finestra_velata(warm: str, cool: str) -> str:
    """La finestra: sfumatura d'epoca + tratteggio + velatura. Mai un soggetto."""
    return f"""
  <defs>
    <linearGradient id="emul" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{warm}"/>
      <stop offset="1" stop-color="{cool}"/>
    </linearGradient>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45)"
             patternUnits="userSpaceOnUse">
      <rect width="8" height="8" fill="url(#emul)"/>
      <line x1="0" y1="0" x2="0" y2="8" stroke="#c9c1b0" stroke-width="2" opacity="0.5"/>
    </pattern>
    <radialGradient id="flash" cx="0.5" cy="0.2" r="0.8">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.35"/>
      <stop offset="0.55" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="{PAD_X}" y="{WIN_Y}" width="{WIN}" height="{WIN}" fill="url(#hatch)"/>
  <rect x="{PAD_X}" y="{WIN_Y}" width="{WIN}" height="{WIN}" fill="url(#flash)"/>
  <text x="{W/2:.0f}" y="{WIN_Y + WIN/2:.0f}" text-anchor="middle"
        font-family="ui-monospace, Menlo, monospace" font-size="12"
        letter-spacing="4" fill="#ffffff" opacity="0.85">SENZA VOLTO</text>
"""


def svg_fronte(id_pezzo: str, decennio: str, caption: str) -> str:
    d = DECENNI.get(decennio, DECENNI["2000-oggi"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" role="img" aria-label="Cornice Polaroid velata {esc(id_pezzo)}">
  <rect width="{W}" height="{H}" fill="{FRAME}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{EDGE}"/>
  <rect x="{PAD_X-3}" y="{WIN_Y-3}" width="{WIN+6}" height="{WIN+6}" fill="{FRAME2}"/>
  {_finestra_velata(d['warm'], d['cool'])}
  <text x="{W/2:.0f}" y="{H-34}" text-anchor="middle"
        font-family="'Segoe Script','Bradley Hand',cursive" font-size="16" fill="{INK}">
    {esc(caption)}</text>
  <text x="{W/2:.0f}" y="{H-16}" text-anchor="middle"
        font-family="ui-monospace, monospace" font-size="8" letter-spacing="3"
        fill="{VEIL}">ANONIMA · {esc(id_pezzo)}</text>
</svg>"""


def svg_retro(id_pezzo: str, decennio: str, formato: str) -> str:
    """Il retro: la grafia sul bordo è parte dell'opera quanto il fronte."""
    d = DECENNI.get(decennio, DECENNI["2000-oggi"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" role="img" aria-label="Retro Polaroid {esc(id_pezzo)}">
  <rect width="{W}" height="{H}" fill="{FRAME}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{EDGE}"/>
  <rect x="{PAD_X}" y="{WIN_Y}" width="{WIN}" height="{WIN}" fill="none"
        stroke="{FRAME2}" stroke-width="2"/>
  <text x="{PAD_X+8}" y="{WIN_Y+46}" font-family="'Segoe Script','Bradley Hand',cursive"
        font-size="22" fill="{INK}" transform="rotate(-4 {PAD_X+8} {WIN_Y+46})">
    {esc(decennio)}</text>
  <text x="{PAD_X+14}" y="{WIN_Y+92}" font-family="'Segoe Script','Bradley Hand',cursive"
        font-size="16" fill="{INK}" opacity="0.8"
        transform="rotate(-2 {PAD_X+14} {WIN_Y+92})">{esc(d['nota'])}</text>
  <text x="{PAD_X+10}" y="{WIN_Y+WIN-20}" font-family="'Segoe Script','Bradley Hand',cursive"
        font-size="15" fill="{INK}" opacity="0.7">{esc(formato)}</text>
  <text x="{W/2:.0f}" y="{H-16}" text-anchor="middle"
        font-family="ui-monospace, monospace" font-size="8" letter-spacing="3"
        fill="{VEIL}">ANONIMA · {esc(id_pezzo)} · retro</text>
</svg>"""


# ── Main ────────────────────────────────────────────────────────────────────

# Set minimo dimostrativo: 4 pezzi per decennio, tutti anonimi e senza contenuto.
FORMATI = {"1968-1979": "SX-70", "1980-1999": "600 film", "2000-oggi": "i-Type"}
CAPTIONS = ["est. anni '60", "bordo scritto", "viraggio", "non datato",
            "grana fine", "ingiallito", "bordo bianco", "colore freddo"]

OUT = "public/anonima"


def main():
    os.makedirs(OUT, exist_ok=True)
    indice = []
    n = 0
    for decennio in DECENNI:
        for i in range(4):
            n += 1
            id_pezzo = f"{n:03d}"
            cap = CAPTIONS[(n - 1) % len(CAPTIONS)]
            fronte = f"{id_pezzo}_fronte.svg"
            retro = f"{id_pezzo}_retro.svg"
            with open(os.path.join(OUT, fronte), "w", encoding="utf-8") as f:
                f.write(svg_fronte(id_pezzo, decennio, cap))
            with open(os.path.join(OUT, retro), "w", encoding="utf-8") as f:
                f.write(svg_retro(id_pezzo, decennio, FORMATI[decennio]))
            indice.append({
                "id": id_pezzo,
                "decennio": decennio,
                "formato": FORMATI[decennio],
                "fronte": f"/anonima/{fronte}",
                "retro": f"/anonima/{retro}",
                "livello_esposizione": "dettaglio-astratto",
            })
    with open(os.path.join(OUT, "indice.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)
    print(f"ANONIMA → {n} cornici (fronte+retro) generate in {OUT}/")
    print(f"indice → {OUT}/indice.json ({len(indice)} voci)")


if __name__ == "__main__":
    main()
