#!/usr/bin/env python3
"""
Suno — travaso link da inbox a documento definitivo
Claudio Terzi [CT-LGAI-001] — progetto R3∞ / Archivio Cosmico

Legge r3/archivio/inbox/LINK_SUNO_DA_INSERIRE.md (lo spazio di incollaggio
manuale) e sposta ogni link trovato nella cella giusta della tabella
corrispondente in r3/archivio/MUSICA_TRACCE_SUNO.md.

Uso:
  python3 scripts/suno_inserisci_da_inbox.py            # mostra cosa farebbe
  python3 scripts/suno_inserisci_da_inbox.py --esegui   # applica le modifiche
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INBOX = REPO / "r3" / "archivio" / "inbox" / "LINK_SUNO_DA_INSERIRE.md"
DOC = REPO / "r3" / "archivio" / "MUSICA_TRACCE_SUNO.md"

RIGA_RX = re.compile(r"^(TRK-[IVP]+-\d+)\s*\|\s*([^|]+?)\s*\|\s*(\S.*)?$")


def leggi_inbox():
    trovati = {}
    for riga in INBOX.read_text(encoding="utf-8").splitlines():
        m = RIGA_RX.match(riga.strip())
        if not m:
            continue
        tid, titolo, link = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        if link:
            trovati[tid] = {"titolo": titolo, "link": link}
    return trovati


def applica(trovati, esegui):
    testo = DOC.read_text(encoding="utf-8")
    righe = testo.splitlines()
    inseriti, non_trovati = [], []

    for tid, info in trovati.items():
        fatto = False
        for i, r in enumerate(righe):
            if re.search(rf"\|\s*{re.escape(tid)}\s*\|", r) and "[inserire link]" in r:
                nuova = r.replace("[inserire link]", f"[{tid}]({info['link']})")
                if esegui:
                    righe[i] = nuova
                inseriti.append((tid, info["titolo"], info["link"]))
                fatto = True
                break
        if not fatto:
            non_trovati.append(tid)

    if esegui and inseriti:
        DOC.write_text("\n".join(righe) + "\n", encoding="utf-8")

    return inseriti, non_trovati


def main():
    esegui = "--esegui" in sys.argv
    trovati = leggi_inbox()

    if not trovati:
        print("Nessun link trovato in inbox/LINK_SUNO_DA_INSERIRE.md — niente da fare.")
        return

    inseriti, non_trovati = applica(trovati, esegui)

    verbo = "Inseriti" if esegui else "[DRY-RUN] Verrebbero inseriti"
    print(f"{verbo} {len(inseriti)} link:")
    for tid, titolo, link in inseriti:
        print(f"  {tid} — \"{titolo}\" → {link}")

    if non_trovati:
        print(f"\nNon trovati nel documento (controllare gli ID): {non_trovati}")

    if not esegui and inseriti:
        print("\nPer applicare davvero: --esegui")


if __name__ == "__main__":
    main()
