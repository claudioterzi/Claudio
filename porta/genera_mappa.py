"""Genera porta/mappa.json: per ogni file locale usato da una pagina, le aree che lo aprono.

Uso:  python porta/genera_mappa.py          (riscrive la mappa)
      python porta/genera_mappa.py --check  (esce 1 se la mappa è da rigenerare)

Una pagina appartiene alle aree i cui percorsi corrispondono a "/<pagina>.html".
I file che la pagina richiama (src, href, url(), stringhe "/x.js"…) ereditano
quelle aree; i link verso altre pagine .html no. Un file usato da pagine di aree diverse è aperto a ciascuna di esse.
I file non raggiunti da nessuna pagina restano solo del proprietario.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PUBLIC = RADICE / "public"
AREE = RADICE / "porta" / "aree.json"
MAPPA = RADICE / "porta" / "mappa.json"
DATI_MJS = RADICE / "porta" / "dati.mjs"

_RIF = re.compile(
    r"""(?:src|href|data-src|poster)\s*=\s*["']([^"'#?]+)"""
    r"""|url\(\s*["']?([^"')#?]+)"""
    r"""|["'](/[A-Za-z0-9_./-]+\.(?:js|mjs|json|css|png|jpe?g|webp|svg|gif|mp3|mp4|pdf|txt|woff2?))["']"""
)
_TESTO = {".js", ".mjs", ".css"}


def _riferimenti(file: Path) -> set[str]:
    try:
        testo = file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    trovati = set()
    for m in _RIF.finditer(testo):
        rif = next(g for g in m.groups() if g)
        if rif.startswith(("http:", "https:", "//", "data:", "mailto:", "tel:", "javascript:")):
            continue
        trovati.add(rif)
    return trovati


def _risolvi(rif: str, da: Path) -> Path | None:
    if rif.startswith("/"):
        rel = rif[len("/public/"):] if rif.startswith("/public/") else rif.lstrip("/")
        cand = PUBLIC / rel
    else:
        cand = (da.parent / rif).resolve()
    try:
        cand.relative_to(PUBLIC)
    except ValueError:
        return None
    return cand if cand.is_file() else None


def _aree_pagina(pagina: Path, aree: list[dict]) -> set[str]:
    url = "/" + pagina.relative_to(PUBLIC).as_posix()
    return {
        a["id"] for a in aree
        if any(re.search(p, url) for p in a["percorsi"])
    }


def genera() -> dict[str, list[str]]:
    catalogo = json.loads(AREE.read_text(encoding="utf-8"))
    aree = catalogo["aree"]
    non_esplorare = set(catalogo.get("non_esplorare", {}).get("file", []))
    mappa: dict[str, set[str]] = {}
    for pagina in sorted(PUBLIC.rglob("*.html")):
        ids = _aree_pagina(pagina, aree)
        if not ids:
            continue
        coda, visti = [pagina], {pagina}
        while coda:
            corrente = coda.pop()
            for rif in _riferimenti(corrente):
                file = _risolvi(rif, corrente)
                # Un link a un'altra pagina è navigazione: quella pagina ha le sue aree.
                if file is None or file in visti or file.suffix == ".html":
                    continue
                visti.add(file)
                chiave = "/" + file.relative_to(PUBLIC).as_posix()
                mappa.setdefault(chiave, set()).update(ids)
                if file.suffix in _TESTO and chiave not in non_esplorare:
                    coda.append(file)
    return {k: sorted(v) for k, v in sorted(mappa.items())}


def _modulo(mappa: dict[str, list[str]]) -> str:
    catalogo = json.loads(AREE.read_text(encoding="utf-8"))
    return (
        "// Generato da porta/genera_mappa.py — non modificare a mano.\n"
        f"export const CATALOGO = {json.dumps(catalogo, ensure_ascii=False)};\n"
        f"export const MAPPA = {json.dumps(mappa, ensure_ascii=False)};\n"
    )


def main(argv: list[str]) -> int:
    nuova = genera()
    testo = json.dumps(nuova, ensure_ascii=False, indent=1) + "\n"
    modulo = _modulo(nuova)
    if "--check" in argv:
        attuale = MAPPA.read_text(encoding="utf-8") if MAPPA.exists() else ""
        mod_att = DATI_MJS.read_text(encoding="utf-8") if DATI_MJS.exists() else ""
        if attuale != testo or mod_att != modulo:
            print("porta/mappa.json o porta/dati.mjs non aggiornati: esegui python porta/genera_mappa.py")
            return 1
        print(f"porta/mappa.json aggiornata ({len(nuova)} file)")
        return 0
    MAPPA.write_text(testo, encoding="utf-8")
    DATI_MJS.write_text(modulo, encoding="utf-8")
    print(f"Scritta porta/mappa.json: {len(nuova)} file assegnati ad aree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
