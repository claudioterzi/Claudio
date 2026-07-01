#!/usr/bin/env python3
"""
R3∞ Sentinella — strumento di prevenzione limiti e problemi
Claudio Terzi [CT-LGAI-001] — progetto R3∞ / Archivio Cosmico

Prevede i problemi ricorrenti delle sessioni di lavoro sull'archivio:
  1. Sessioni interrotte (limite API/sessione) → genera STATO_LAVORO.md
     così la sessione successiva riparte senza ricostruire il contesto.
  2. File sottili o incompleti → segnala documenti sotto soglia.
  3. Cartelle vuote → fasi dichiarate ma mai popolate.
  4. Incoerenze master/disco → fasi marcate ✅ senza file corrispondente.
  5. Violazioni delle regole editoriali → pattern proibiti nei documenti
     (misteri permanenti risolti, acronimo KAOS rivelato).
  6. Gap di sincronizzazione Drive → confronto con manifest locale
     (drive_manifest.json) aggiornato a ogni upload riuscito.
  7. Igiene git → file non tracciati/non committati nell'archivio.

Uso:
  python3 scripts/r3_sentinella.py            # report completo
  python3 scripts/r3_sentinella.py --snapshot # scrive anche STATO_LAVORO.md
  python3 scripts/r3_sentinella.py --json     # output machine-readable
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARCHIVIO = REPO / "r3" / "archivio"
MASTER = ARCHIVIO / "ARCHIVIO_MASTER.md"
MANIFEST = REPO / "scripts" / "drive_manifest.json"
SNAPSHOT = ARCHIVIO / "STATO_LAVORO.md"

# Soglia minima di righe per un documento "completo".
# I file INDEX e le sintesi possono essere più corti.
SOGLIA_RIGHE = 60
ESENTI_SOGLIA = {"INDEX.md", "STATO_LAVORO.md"}

# Pattern che non devono MAI comparire nell'archivio (regole editoriali).
# Ogni voce: (regex, spiegazione, flags regex).
PATTERN_PROIBITI = [
    # Case-SENSITIVE: scatta solo su un'espansione reale (due parole con
    # iniziale maiuscola), non su "acronimo di qualcosa che...".
    (r"KAOS\s+(?:è l'acronimo di|significa|sta per)\s+[A-Z]\w+\s+[A-Z]\w+",
     "L'acronimo esteso di KAOS è riservato al Libro V — non va scritto nell'archivio",
     0),
    (r"gli Architetti (?:sono stati|furono) creati da\s+\w+",
     "M-001 (chi ha creato gli Architetti) è un mistero permanente — mai risolverlo",
     re.IGNORECASE),
    (r"il Primo Osservatore è\s+\w+",
     "M-004 (il Primo Osservatore) è un mistero permanente — mai identificarlo",
     re.IGNORECASE),
]


def leggi_fasi_master():
    """Estrae dal master le fasi ✅ con nome file citato, per verificarne l'esistenza."""
    if not MASTER.exists():
        return []
    fasi = []
    for line in MASTER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([\d\-/]+)\s*\|(.+?)\|\s*(✅|🔄)(.*)\|", line)
        if not m:
            continue
        fase, titolo, stato, dettaglio = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
        file_citati = re.findall(r"([A-Z][A-Z0-9_]+\.md)", dettaglio)
        fasi.append({"fase": fase, "titolo": titolo, "stato": stato, "file": file_citati})
    return fasi


def check_master_vs_disco():
    """Fasi ✅ che citano file inesistenti = incoerenza master/disco."""
    problemi = []
    for f in leggi_fasi_master():
        if f["stato"] != "✅":
            continue
        for nome in f["file"]:
            trovati = list(ARCHIVIO.rglob(nome))
            if not trovati:
                problemi.append(f"FASE {f['fase']}: marcata ✅ ma {nome} non esiste su disco")
    return problemi


def check_file_sottili():
    problemi = []
    for md in sorted(ARCHIVIO.rglob("*.md")):
        if md.name in ESENTI_SOGLIA:
            continue
        righe = md.read_text(encoding="utf-8").count("\n") + 1
        if righe < SOGLIA_RIGHE:
            rel = md.relative_to(ARCHIVIO)
            problemi.append(f"{rel}: solo {righe} righe (soglia {SOGLIA_RIGHE}) — possibile documento incompleto")
    return problemi


def check_cartelle_vuote():
    problemi = []
    for d in sorted(p for p in ARCHIVIO.rglob("*") if p.is_dir()):
        if not any(d.iterdir()):
            problemi.append(f"{d.relative_to(ARCHIVIO)}/: cartella vuota — fase dichiarata ma mai popolata")
    return problemi


def check_pattern_proibiti():
    problemi = []
    for md in sorted(ARCHIVIO.rglob("*.md")):
        testo = md.read_text(encoding="utf-8")
        for rx, spiegazione, flags in PATTERN_PROIBITI:
            if re.search(rx, testo, flags):
                rel = md.relative_to(ARCHIVIO)
                problemi.append(f"{rel}: pattern proibito — {spiegazione}")
    return problemi


def check_drive_gap():
    """Confronta i .md dell'archivio con il manifest degli upload Drive riusciti."""
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        sincronizzati = set(manifest.get("synced", []))
    else:
        sincronizzati = set()
    mancanti = []
    for md in sorted(ARCHIVIO.rglob("*.md")):
        rel = str(md.relative_to(ARCHIVIO))
        if rel not in sincronizzati and md.name != "STATO_LAVORO.md":
            mancanti.append(rel)
    return mancanti


def check_git():
    problemi = []
    try:
        out = subprocess.run(
            ["git", "status", "--short", "--", "r3/archivio"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        if out:
            n = len(out.splitlines())
            problemi.append(f"{n} file dell'archivio non committati — un limite di sessione ora perderebbe lavoro")
        ahead = subprocess.run(
            ["git", "rev-list", "@{u}..HEAD", "--count"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        if ahead and ahead != "0":
            problemi.append(f"{ahead} commit non pushati — un limite di sessione ora li lascerebbe solo in locale")
    except Exception as e:
        problemi.append(f"controllo git fallito: {e}")
    return problemi


def genera_report():
    fasi = leggi_fasi_master()
    incomplete = [f for f in fasi if f["stato"] == "🔄"]
    drive_gap = check_drive_gap()
    return {
        "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fasi_totali": len(fasi),
        "fasi_incomplete": [f"FASE {f['fase']}: {f['titolo']}" for f in incomplete],
        "master_vs_disco": check_master_vs_disco(),
        "file_sottili": check_file_sottili(),
        "cartelle_vuote": check_cartelle_vuote(),
        "pattern_proibiti": check_pattern_proibiti(),
        "git": check_git(),
        "drive_non_sincronizzati": len(drive_gap),
        "drive_gap_dettaglio": drive_gap,
    }


def scrivi_snapshot(report):
    """STATO_LAVORO.md — il paracadute per la sessione successiva.

    Se la sessione corrente viene interrotta da un limite, la successiva legge
    questo file e riparte esattamente da qui, senza ricostruire il contesto.
    """
    righe = [
        "# STATO LAVORO — snapshot automatico (r3_sentinella)",
        f"*Generato: {report['generato']} — rigenerare con `python3 scripts/r3_sentinella.py --snapshot`*",
        "",
        "> Paracadute anti-interruzione: se la sessione si ferma per un limite,",
        "> la sessione successiva riparte da questo file.",
        "",
        "## Fasi ancora incomplete (🔄 nel master)",
    ]
    righe += [f"- {f}" for f in report["fasi_incomplete"]] or ["- nessuna"]
    righe += ["", "## Problemi rilevati"]
    for chiave, etichetta in [
        ("master_vs_disco", "Incoerenze master/disco"),
        ("file_sottili", "File sotto soglia"),
        ("cartelle_vuote", "Cartelle vuote"),
        ("pattern_proibiti", "Violazioni regole editoriali"),
        ("git", "Igiene git"),
    ]:
        voci = report[chiave]
        righe.append(f"### {etichetta} ({len(voci)})")
        righe += [f"- {v}" for v in voci] or ["- ok"]
        righe.append("")
    righe += [
        "## Sincronizzazione Drive",
        f"- File non ancora su Drive: **{report['drive_non_sincronizzati']}**",
        "- Dettaglio nel report JSON (`--json`) o in scripts/drive_manifest.json",
        "",
    ]
    SNAPSHOT.write_text("\n".join(righe), encoding="utf-8")


def main():
    report = genera_report()
    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    if "--snapshot" in sys.argv:
        scrivi_snapshot(report)
        print(f"Snapshot scritto: {SNAPSHOT.relative_to(REPO)}")

    print(f"R3∞ Sentinella — {report['generato']}")
    print(f"Fasi nel master: {report['fasi_totali']} (incomplete: {len(report['fasi_incomplete'])})")
    sezioni = [
        ("Incoerenze master/disco", report["master_vs_disco"]),
        ("File sotto soglia", report["file_sottili"]),
        ("Cartelle vuote", report["cartelle_vuote"]),
        ("Violazioni regole editoriali", report["pattern_proibiti"]),
        ("Igiene git", report["git"]),
    ]
    exit_code = 0
    for titolo, voci in sezioni:
        print(f"\n[{titolo}] {'OK' if not voci else str(len(voci)) + ' problemi'}")
        for v in voci:
            print(f"  - {v}")
        if voci:
            exit_code = 1
    print(f"\n[Drive] {report['drive_non_sincronizzati']} file non ancora sincronizzati")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
