#!/usr/bin/env python3
"""Riepilogo dell'ultimo giro di studio della biblioteca.

Sostituisce il one-liner bash: stampa il log del giro (senza le righe
"Loading weights"), i campi principali dell'ultima ricevuta JSON, il
confronto prima/dopo per ogni prova e se il modello `seme:latest` e'
presente in Ollama.

Regge le ricevute di un giro fallito: campi mancanti o a null
(`dopo: null`, `confusione: null`, `cuore` assente) non fanno crashare.

Uso (dalla radice del repo, sul PC dove gira la biblioteca):
    python scripts/biblioteca_ultima_ricevuta.py
    python scripts/biblioteca_ultima_ricevuta.py --cartella percorso/biblioteca
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CAMPI = ("esito", "inizio", "fine", "lezione", "cervello_prima",
         "cervello_dopo", "ollama", "errore", "dimenticate")


def stampa_log(log: Path) -> None:
    if not log.is_file():
        print(f"(log assente: {log})")
        return
    with log.open(encoding="utf-8", errors="replace") as fh:
        for riga in fh:
            if "Loading weights" not in riga:
                print(riga, end="")


def ultima_ricevuta(cartella: Path) -> Path | None:
    ricevute = list(cartella.glob("*.json"))
    if not ricevute:
        return None
    return max(ricevute, key=lambda p: p.stat().st_mtime)


def stampa_ricevuta(f: Path) -> None:
    print(f"== {f}")
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ricevuta illeggibile: {exc}")
        return
    if not isinstance(r, dict):
        print(f"ricevuta inattesa (non e' un oggetto): {type(r).__name__}")
        return
    for k in CAMPI:
        print(k, ":", r.get(k))
    print("studio:", (r.get("studio") or "")[-400:])
    dopo = r.get("dopo") or {}
    for prova, v in (r.get("prima") or {}).items():
        v = v or {}
        d = dopo.get(prova) or {}
        print(f"  {prova:32} prima {str(v.get('confusione')):6} "
              f"dopo {d.get('confusione')}  cuore={v.get('cuore')}")


def controlla_seme() -> None:
    if not shutil.which("ollama"):
        print("ollama: comando non trovato")
        return
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace",
                             timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"ollama list fallito: {exc}")
        return
    righe = [r for r in out.stdout.splitlines() if "seme:latest" in r]
    print("\n".join(righe) if righe else "seme:latest: non presente in ollama")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cartella", default="biblioteca", type=Path,
                    help="cartella della biblioteca (default: ./biblioteca)")
    ap.add_argument("--senza-ollama", action="store_true",
                    help="salta il controllo di seme:latest")
    a = ap.parse_args()

    stampa_log(a.cartella / "primo-giro.log")
    f = ultima_ricevuta(a.cartella / "ricevute")
    if f is None:
        print(f"== nessuna ricevuta in {a.cartella / 'ricevute'}")
    else:
        stampa_ricevuta(f)
    if not a.senza_ollama:
        controlla_seme()
    return 0


if __name__ == "__main__":
    sys.exit(main())
