"""Indicizzatore di progetto — fa leggere agli agenti l'INTERO repo.

Applica la pipeline di `MEMORIA_VETTORIALE_GUIDA.md` localmente:
  lista file → chunking semantico → classificazione → indicizzazione.

Cammina l'intero albero del progetto (non una sola cartella): libro, tarocchi,
sdq1, lgai_core, idee, api, studio, file di root… Ogni chunk entra nella
memoria condivisa con metadati ricchi, così qualsiasi agente può richiamarlo.

Idempotente: ogni chunk ha un id stabile (hash di percorso+indice+testo); una
seconda passata non duplica nulla. Zero dipendenze esterne.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .raffaello import MemoriaRaffaello

# Estensioni da indicizzare (testo/conoscenza, non binari).
ESTENSIONI = {
    ".md", ".py", ".txt", ".gs", ".gcode", ".nc",
    ".cfg", ".ini", ".toml", ".yaml", ".yml", ".jsonl",
}
# Cartelle da non visitare mai.
DIR_ESCLUSE = {
    ".git", "__pycache__", "node_modules", "venv", "env", "ENV",
    ".venv", "build", "dist", ".eggs", ".idea", ".vscode",
}
# File gestiti altrove (identità/cuore) o rumorosi: saltati qui.
FILE_ESCLUSI = {"raffaello_codice_cuore.json"}
PERCORSI_ESCLUSI = {os.path.join("raffaello_sia", "IDENTITA.md"),
                    "output" + os.sep}  # artefatti generati (incluso l'indice stesso)

MAX_BYTES_FILE = 200_000
MAX_CHUNK_CHARS = 1500
OVERLAP = 150
MAX_CHUNK_PER_FILE = 60
MAX_CHUNK_TOTALI = 5000


def _id_stabile(relpath: str, indice: int, testo: str) -> str:
    h = hashlib.md5(f"{relpath}#{indice}#{testo}".encode("utf-8")).hexdigest()
    return h[:12]


def _finestre(testo: str, dim: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP) -> list[str]:
    testo = testo.strip()
    if len(testo) <= dim:
        return [testo] if testo else []
    out, i = [], 0
    while i < len(testo):
        out.append(testo[i : i + dim])
        i += dim - overlap
    return out


def _chunk_md(testo: str) -> list[tuple[str, str]]:
    """(sezione, contenuto) splittando per heading markdown."""
    sezioni: list[tuple[str, list[str]]] = []
    corrente_titolo, corrente_righe = "(intro)", []
    for riga in testo.splitlines():
        if riga.lstrip().startswith("#"):
            if corrente_righe:
                sezioni.append((corrente_titolo, corrente_righe))
            corrente_titolo = riga.strip("# ").strip() or "(sezione)"
            corrente_righe = [riga]
        else:
            corrente_righe.append(riga)
    if corrente_righe:
        sezioni.append((corrente_titolo, corrente_righe))

    out: list[tuple[str, str]] = []
    for titolo, righe in sezioni:
        corpo = "\n".join(righe).strip()
        for pezzo in _finestre(corpo):
            out.append((titolo, pezzo))
    return out


def _chunk_py(testo: str) -> list[tuple[str, str]]:
    """(simbolo, blocco) splittando per def/class di primo livello."""
    righe = testo.splitlines()
    blocchi: list[tuple[str, list[str]]] = []
    titolo, buf = "(modulo)", []
    for riga in righe:
        if (riga.startswith("def ") or riga.startswith("class ")) and buf:
            blocchi.append((titolo, buf))
            titolo, buf = riga.split("(")[0].replace("def ", "").replace("class ", "").strip(), [riga]
        else:
            if riga.startswith("def ") or riga.startswith("class "):
                titolo = riga.split("(")[0].replace("def ", "").replace("class ", "").strip()
            buf.append(riga)
    if buf:
        blocchi.append((titolo, buf))

    out: list[tuple[str, str]] = []
    for titolo, buf in blocchi:
        corpo = "\n".join(buf).strip()
        for pezzo in _finestre(corpo):
            out.append((titolo, pezzo))
    return out


def _classifica(relpath: str) -> tuple[str, list[str]]:
    """Ritorna (tipo, tag) in base alla posizione nel progetto."""
    top = relpath.split(os.sep, 1)[0]
    if top == "conoscenza":
        return "documento", ["conoscenza"]
    if top == "libro":
        return "documento", ["opera", "narrativa", "R3inf"]
    if top == "sdq1":
        return "sistema", ["sdq1", "codice"]
    if top in ("tarocchi", "public") or relpath.endswith(".json"):
        return "documento", ["tarocchi"]
    if top in ("lgai_core", "api", "studio", "cli"):
        return "sistema", [top]
    if top == "idee":
        return "documento", ["idee"]
    return "documento", ["progetto"]


def indicizza_progetto(
    identita: "MemoriaRaffaello",
    radice: Path,
    verbose: bool = False,
    file_indice: "Path | None" = None,
) -> dict:
    """Indicizza l'intero progetto nella memoria condivisa. Ritorna statistiche.

    Se `file_indice` è dato, scrive/aggiorna lì un indice generale leggibile
    (Markdown), rigenerato a ogni passata: si auto-aggiorna con i file nuovi.
    """
    radice = Path(radice).resolve()
    file_visti = chunk_aggiunti = chunk_saltati = 0
    per_tipo: dict[str, int] = {}
    dettagli: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(radice):
        dirnames[:] = [d for d in dirnames if d not in DIR_ESCLUSE]
        for fname in filenames:
            if Path(fname).suffix.lower() not in ESTENSIONI or fname in FILE_ESCLUSI:
                continue
            full = Path(dirpath) / fname
            relpath = str(full.relative_to(radice))
            if any(relpath.startswith(p) for p in PERCORSI_ESCLUSI):
                continue
            try:
                if full.stat().st_size > MAX_BYTES_FILE:
                    continue
                testo = full.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            suff = full.suffix.lower()
            if suff == ".md":
                chunks = _chunk_md(testo)
            elif suff == ".py":
                chunks = _chunk_py(testo)
            else:
                chunks = [("(file)", p) for p in _finestre(testo)]
            chunks = chunks[:MAX_CHUNK_PER_FILE]
            if not chunks:
                continue

            file_visti += 1
            tipo, tag = _classifica(relpath)
            n_prima = chunk_aggiunti
            for i, (sezione, corpo) in enumerate(chunks):
                if chunk_aggiunti >= MAX_CHUNK_TOTALI:
                    break
                cid = _id_stabile(relpath, i, corpo)
                if identita.ha_id(cid):
                    chunk_saltati += 1
                    continue
                identita.memorizza(
                    corpo,
                    tipo=tipo,
                    fonte="github",
                    autore="Claudio",
                    emozione="analisi",
                    priorita=4 if tipo == "documento" and "opera" in tag else 3,
                    peso_identitario=0.3,
                    nome_file=relpath,
                    sezione=sezione,
                    tag=tag,
                    id_stabile=cid,
                )
                chunk_aggiunti += 1
                per_tipo[tipo] = per_tipo.get(tipo, 0) + 1
            dettagli.append({
                "file": relpath,
                "tipo": tipo,
                "tag": tag,
                "chunk_file": len(chunks),
                "nuovi": chunk_aggiunti - n_prima,
            })
            if verbose:
                print(f"  · {relpath}: {len(chunks)} chunk")

    stats = {
        "file_indicizzati": file_visti,
        "chunk_aggiunti": chunk_aggiunti,
        "chunk_saltati_duplicati": chunk_saltati,
        "per_tipo": per_tipo,
        "memoria_totale": identita.stats()["totale_vettori"],
    }
    if file_indice is not None:
        _scrivi_indice(Path(file_indice), radice, dettagli, stats)
        stats["indice"] = str(file_indice)
    return stats


def _scrivi_indice(file_indice: Path, radice: Path, dettagli: list[dict], stats: dict) -> None:
    """Genera/aggiorna l'indice generale leggibile (Markdown). Idempotente."""
    import time

    file_indice.parent.mkdir(parents=True, exist_ok=True)
    # raggruppa per cartella di primo livello
    per_cartella: dict[str, list[dict]] = {}
    for d in dettagli:
        top = d["file"].split(os.sep, 1)[0] if os.sep in d["file"] else "(root)"
        per_cartella.setdefault(top, []).append(d)

    righe = [
        "# Indice generale del progetto — auto-aggiornato",
        "",
        f"> Rigenerato automaticamente a ogni indicizzazione. NON modificare a mano.",
        f"> Ultimo aggiornamento: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- File indicizzati: **{stats['file_indicizzati']}**",
        f"- Chunk in memoria: **{stats['chunk_aggiunti']}**",
        f"- Per tipo: {stats['per_tipo']}",
        "",
        "Per ri-aggiornare dopo aver aggiunto file: `python -m sdq1 --indicizza`.",
        "",
    ]
    for cartella in sorted(per_cartella):
        voci = sorted(per_cartella[cartella], key=lambda d: d["file"])
        tot = sum(v["chunk_file"] for v in voci)
        righe.append(f"## {cartella}/  ({len(voci)} file, {tot} chunk)")
        righe.append("")
        for v in voci:
            righe.append(f"- `{v['file']}` — {v['chunk_file']} chunk · {v['tipo']}")
        righe.append("")
    file_indice.write_text("\n".join(righe), encoding="utf-8")


if __name__ == "__main__":
    from .raffaello import MemoriaRaffaello
    from .store import MemoriaVettoriale

    radice = Path(__file__).resolve().parent.parent.parent
    mem = MemoriaRaffaello(memoria=MemoriaVettoriale(soglia_similarita=0.0))
    stats = indicizza_progetto(mem, radice, verbose=False)
    import json
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    # prova di richiamo trasversale
    for q in ["le cinque morti", "router multi provider", "Canone Alpha collasso"]:
        r = mem.ricorda(q, top_k=1)
        capo = r[0]["metadata"]["nome_file"] if r else "—"
        print(f"  '{q}' → {capo}")
