#!/usr/bin/env python3
"""
Suno — generazione automatica della colonna sonora R3∞
Claudio Terzi [CT-LGAI-001] — progetto R3∞ / Archivio Cosmico

Legge i prompt da r3/archivio/MUSICA_TRACCE_SUNO.md, genera le tracce
via API Suno, e riscrive i link definitivi negli slot [inserire link]
del documento stesso.

Progettato con la stessa filosofia di r3_sentinella.py:
  - RESUMABILE: lo stato vive in scripts/suno_tracce_stato.json.
    Se la sessione muore a metà, si rilancia e riprende da dove era.
  - PRUDENTE: di default è dry-run (mostra cosa farebbe senza chiamare
    l'API né spendere crediti). Serve --esegui per generare davvero.
  - INCREMENTALE: genera una traccia alla volta, salva lo stato dopo
    ognuna, aggiorna il documento solo a traccia confermata.

Configurazione (variabili d'ambiente, metterle in .env — MAI nel repo):
  SUNO_API_KEY   token API Suno (tier sviluppatori, suno.com)
  SUNO_API_BASE  base URL API (default: https://api.suno.com/v1)
                 — se usi un provider proxy compatibile, cambia qui.

Uso:
  python3 scripts/suno_genera_tracce.py                # dry-run: elenca i prompt
  python3 scripts/suno_genera_tracce.py --esegui       # genera le tracce mancanti
  python3 scripts/suno_genera_tracce.py --esegui --solo TRK-I-01
  python3 scripts/suno_genera_tracce.py --stato        # mostra lo stato corrente
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "r3" / "archivio" / "MUSICA_TRACCE_SUNO.md"
STATO = REPO / "scripts" / "suno_tracce_stato.json"

API_BASE = os.environ.get("SUNO_API_BASE", "https://api.suno.com/v1")
API_KEY = os.environ.get("SUNO_API_KEY", "")

# Quante varianti generare per traccia (la regola del documento: 3-4,
# poi si sceglie; via API partiamo con 2 per non bruciare crediti).
VARIANTI = 2
POLL_SECONDI = 15
POLL_MAX_TENTATIVI = 40  # ~10 minuti a traccia


# Tracce con testo cantato reale (citazioni canoniche già esistenti nell'archivio,
# cfr. §2 e §6 del documento). Tutte le altre sono strumentali con struttura piena.
TRACCE_VOCALI = {"TRK-IV-04", "TRK-VII-02"}


def carica_tracce():
    """Estrae dal documento: ID traccia, titolo, link, blocco STYLE, blocco LYRICS."""
    testo = DOC.read_text(encoding="utf-8")
    tracce = {}
    # Righe tabella, elaborate una per volta (mai su più righe: le tabelle dei
    # libri hanno 5 colonne — Ancora, Pagina, Link — quelle dei personaggi ne
    # hanno 4 — Fonte, Link. Un regex "globale" con [^|]* può scavalcare la
    # newline e mescolare celle di righe diverse quando il numero di colonne
    # non è uniforme; riga per riga questo non può succedere).
    riga_rx = re.compile(r'^\|\s*(TRK-[IVP]+-\d+)\s*\|\s*"([^"]+)"\s*\|(.*)\|\s*$')
    for riga in testo.splitlines():
        m = riga_rx.match(riga.strip())
        if not m:
            continue
        tid, titolo, resto = m.group(1), m.group(2), m.group(3)
        celle = [c.strip() for c in resto.split("|")]
        cella_link = celle[-1] if celle else ""
        tracce[tid] = {
            "titolo": titolo,
            "link_presente": "[inserire link]" not in cella_link,
        }
    # Blocchi: **TRK-I-01 — "Titolo"** [nota corsiva opzionale] STYLE:```...``` LYRICS:```...```
    # Il ".*?STYLE:" (non ".*?\*\*\s*STYLE:") è deliberato: alcune tracce (es.
    # TRK-IV-04, TRK-VII-02) hanno un paragrafo corsivo tra il titolo e STYLE —
    # richiedere "**" subito prima di STYLE fa saltare il match fino al blocco
    # STYLE della traccia SUCCESSIVA. Il non-greedy si ferma al primo "STYLE:"
    # letterale dopo il titolo, che è sempre quello corretto della propria traccia.
    for m in re.finditer(
        r"\*\*(TRK-[IVP]+-\d+)\s*—.*?\*\*.*?"
        r"STYLE:\s*```\s*(.*?)\s*```\s*"
        r"LYRICS:\s*```\s*(.*?)\s*```",
        testo, re.DOTALL,
    ):
        tid, style, lyrics = m.group(1), m.group(2).strip(), m.group(3).strip()
        if tid in tracce:
            tracce[tid]["style"] = style
            tracce[tid]["lyrics"] = lyrics
            tracce[tid]["instrumental"] = tid not in TRACCE_VOCALI
    return {k: v for k, v in tracce.items() if v.get("style")}


def carica_stato():
    if STATO.exists():
        return json.loads(STATO.read_text(encoding="utf-8"))
    return {"generate": {}, "in_corso": {}}


def salva_stato(stato):
    STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=2), encoding="utf-8")


def api(percorso, payload=None):
    url = f"{API_BASE}{percorso}"
    dati = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=dati, method="POST" if dati else "GET",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def genera_traccia(tid, info):
    """Lancia la generazione e attende il link. Ritorna l'URL della traccia.

    Campo `tags` = blocco STYLE del documento (genere/strumenti/mood, tag brevi).
    Campo `prompt` = blocco LYRICS del documento (struttura a sezioni, testo
    cantato solo per le tracce in TRACCE_VOCALI — cfr. carica_tracce()).
    """
    print(f"  → genero {tid} — \"{info['titolo']}\" ({'strumentale' if info['instrumental'] else 'con testo cantato'})")
    esito = api("/generate", {
        "prompt": info["lyrics"],
        "tags": info["style"],
        "title": f"{info['titolo']} (R3∞ {tid})",
        "instrumental": info["instrumental"],
        "custom_mode": True,
        "n": VARIANTI,
    })
    job_id = esito.get("id") or esito.get("job_id") or (esito.get("clips") or [{}])[0].get("id")
    if not job_id:
        raise RuntimeError(f"risposta API senza id job: {esito}")

    for _ in range(POLL_MAX_TENTATIVI):
        time.sleep(POLL_SECONDI)
        stato_job = api(f"/generate/{job_id}")
        s = stato_job.get("status", "")
        if s in ("complete", "completed", "streaming"):
            clips = stato_job.get("clips") or [stato_job]
            url = clips[0].get("audio_url") or clips[0].get("url")
            pagina = clips[0].get("page_url") or f"https://suno.com/song/{clips[0].get('id', job_id)}"
            return pagina if pagina else url
        if s in ("error", "failed"):
            raise RuntimeError(f"generazione fallita: {stato_job}")
    raise TimeoutError(f"{tid}: generazione non completata entro il timeout")


def inserisci_link(tid, url):
    """Sostituisce lo slot [inserire link] SOLO nella riga della traccia giusta."""
    testo = DOC.read_text(encoding="utf-8")
    righe = testo.splitlines()
    for i, r in enumerate(righe):
        if re.search(rf"\|\s*{re.escape(tid)}\s*\|", r) and "[inserire link]" in r:
            righe[i] = r.replace("[inserire link]", f"[{tid}]({url})")
            DOC.write_text("\n".join(righe) + "\n", encoding="utf-8")
            return True
    return False


def main():
    args = sys.argv[1:]
    tracce = carica_tracce()
    stato = carica_stato()

    if "--stato" in args:
        print(json.dumps(stato, ensure_ascii=False, indent=2))
        return

    solo = None
    if "--solo" in args:
        solo = args[args.index("--solo") + 1]

    da_fare = {
        tid: info for tid, info in tracce.items()
        if not info["link_presente"]
        and tid not in stato["generate"]
        and (solo is None or tid == solo)
    }

    print(f"Tracce con STYLE+LYRICS nel documento: {len(tracce)}")
    print(f"Già generate (stato locale): {len(stato['generate'])}")
    print(f"Da generare ora: {len(da_fare)}")

    if "--esegui" not in args:
        print("\n[DRY-RUN] Nessuna chiamata API. Cosa verrebbe generato:")
        for tid, info in da_fare.items():
            tipo = "strumentale" if info["instrumental"] else "con testo cantato"
            print(f"  {tid} — \"{info['titolo']}\" [{tipo}]")
            print(f"     STYLE:  {info['style'][:80]}")
            print(f"     LYRICS: {info['lyrics'].splitlines()[0][:80]}...")
        print("\nPer generare davvero: --esegui (richiede SUNO_API_KEY in ambiente)")
        return

    if not API_KEY:
        print("ERRORE: SUNO_API_KEY non impostata. Aggiungila a .env (non committarla).")
        sys.exit(1)

    for tid, info in da_fare.items():
        try:
            url = genera_traccia(tid, info)
            stato["generate"][tid] = {"url": url, "quando": time.strftime("%Y-%m-%d %H:%M")}
            salva_stato(stato)  # salva subito: resumabilità prima di tutto
            if inserisci_link(tid, url):
                print(f"  ✓ {tid} → {url} (link inserito nel documento)")
            else:
                print(f"  ✓ {tid} → {url} (ATTENZIONE: slot non trovato nel documento, link solo nello stato)")
        except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
            print(f"  ✗ {tid}: {e}")
            stato["in_corso"][tid] = str(e)
            salva_stato(stato)
            # non ci si ferma: si prova la traccia successiva

    print("\nFatto. Rilanciare lo script riprende le tracce fallite.")
    print("Ricorda: dopo la generazione, copia MUSICA_TRACCE_SUNO.md aggiornato su Drive (posto madre).")


if __name__ == "__main__":
    main()
