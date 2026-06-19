#!/usr/bin/env python3
"""
OSSERVATORE-1 — SDQ-1 · Claudio Terzi + Claude, 2026
Agente osservatore asincrono della Scacchiera Quantica.

Non rallenta nulla. Usa Anthropic Message Batches API:
  richieste elaborate nello spare compute (50% costo, asincrono).

Pipeline in due fasi:
  Fase A (trigger): estrae tensioni reali → sottomette batch
  Fase B (run successivo): ritira risultati → sessione Scacchiera + report MD

Run: python scripts/osservatore.py [--force]
  --force   forza nuova estrazione anche se già fatto oggi
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / "osservatore"
STATO_FILE = OUTPUT_DIR / "stato.json"

sys.path.insert(0, str(ROOT / "scripts"))
from scacchiera_quantica import Vettore, ciclo, Sessione


# ── ESTRAZIONE TENSIONI DAL LAVORO REALE ────────────────────────────────────

def _git_log(days: int = 1) -> list[dict]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log",
         f"--since={days} days ago",
         "--format=COMMIT|%h|%s|%ai",
         "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    commits, current = [], None
    for line in result.stdout.splitlines():
        if line.startswith("COMMIT|"):
            if current:
                commits.append(current)
            _, h, msg, ts = line.split("|", 3)
            current = {"hash": h, "msg": msg, "ts": ts, "files": []}
        elif current and line.strip():
            current["files"].append(line.strip())
    if current:
        commits.append(current)
    return commits


def _leggi_brief() -> str:
    briefs = sorted((ROOT / "output" / "morning_brief").glob("*.md"), reverse=True)
    return briefs[0].read_text(encoding="utf-8")[:3000] if briefs else ""


def _leggi_desideri() -> str:
    f = ROOT / "REGISTRO_DESIDERI.md"
    return f.read_text(encoding="utf-8")[:2000] if f.exists() else ""


def _cat(path: str) -> str:
    p = path.lower()
    if p.startswith(("scripts/", ".github/")):
        return "codice"
    if p.startswith(("tarocchi/", "public/")):
        return "tarocchi"
    if p.startswith("progetti/aura50"):
        return "profumi"
    if p.startswith(("personale/", "fabrizio/")):
        return "vita"
    if p.startswith(("studio/", "output/scacchiera")):
        return "scacchiera"
    return "altro"


def estrai_tensioni(commits: list[dict], brief: str, desideri: str) -> list[dict]:
    """Estrae 4-5 tensioni reali da git + brief + desideri."""
    tensioni = []

    # 1 — Creazione vs riparazione
    n_feat = sum(1 for c in commits if c["msg"].startswith("feat"))
    n_fix  = sum(1 for c in commits if c["msg"].startswith("fix"))
    cat    = {}
    for c in commits:
        for f in c["files"]:
            k = _cat(f)
            cat[k] = cat.get(k, 0) + 1

    if n_feat + n_fix > 0:
        ratio = n_feat / (n_feat + n_fix)
        tensioni.append({
            "polo1": "costruire cose nuove",
            "polo2": "riparare ciò che esiste",
            "contesto": (
                f"Ultime 24h: {len(commits)} commit — {n_feat} feat, {n_fix} fix "
                f"(ratio creazione {ratio:.0%}). "
                f"Domini toccati: {', '.join(f'{k}({v})' for k,v in cat.items())}."
            )
        })

    # 2 — Sistema vs vita
    c_sistema = cat.get("codice", 0) + cat.get("infra", 0)
    c_vita    = cat.get("vita", 0)
    if c_sistema + c_vita > 0:
        tensioni.append({
            "polo1": "costruire il sistema automatico",
            "polo2": "risolvere la vita concreta",
            "contesto": (
                f"File sistema: {c_sistema}. File vita/personale: {c_vita}. "
                "Allianz, Pelan, Fabrizio sono dossier umani aperti in parallelo "
                "a un'infrastruttura AI che cresce. Come coesistono?"
            )
        })

    # 3 — Attesa vs azione (da brief)
    if brief:
        in_attesa = brief.count("IN ATTESA")
        completati = brief.count("COMPLETATA") + brief.count("COMPLETA")
        if in_attesa + completati > 0:
            tensioni.append({
                "polo1": "azione immediata disponibile",
                "polo2": "gestire l'attesa senza consumarsi",
                "contesto": (
                    f"Brief corrente: {in_attesa} fronte/i in attesa, "
                    f"{completati} completati. "
                    "Tre fronti aperti (Allianz/sabato, Pelan/huissier, SkyRights/pronto) "
                    "— nessuno si chiude senza un evento esterno."
                )
            })

    # 4 — Autonomia del sistema vs supervisione di Claudio
    auto_commits = sum(1 for c in commits if "stato SDQ-1" in c["msg"]
                       or "osservatore" in c["msg"]
                       or c["msg"].startswith("sync"))
    manuali = len(commits) - auto_commits
    tensioni.append({
        "polo1": "il sistema agisce da solo di notte",
        "polo2": "Claudio decide e supervisiona di giorno",
        "contesto": (
            f"Commit automatici (GH Actions): {auto_commits}. "
            f"Commit da sessione Claudio+Claude: {manuali}. "
            "Dove passa esattamente la linea tra autonomia e dipendenza? "
            "Il sistema autonomo serve Claudio o lo sostituisce?"
        )
    })

    # 5 — Desideri vs realizzazione
    if desideri:
        n_voci = desideri.count("##") + desideri.count("\n- ")
        tensioni.append({
            "polo1": "desiderare con precisione e chiarezza",
            "polo2": "fare con priorità e scelte reali",
            "contesto": (
                f"REGISTRO_DESIDERI: ~{n_voci} voci attive. "
                "Quanto di questi desideri ha trovato spazio nel lavoro reale? "
                "Il gap tra desiderio e azione non è fallimento: è informazione."
            )
        })

    return tensioni


# ── BATCH API ────────────────────────────────────────────────────────────────

_SYSTEM = """Sei il motore della Scacchiera Quantica — SISTEMA R³∞ · ALAKTA ANEN.
Analizza la tensione ricevuta e genera 6 vettori da angolazioni non ovvie.
Ogni vettore è un insight denso e verificabile, non una risposta generica.

Punteggi (0-10, decimali ok):
- imp: quanto cambia una scelta reale?
- orig: quanto si allontana dalla risposta ovvia?
- real: quanto è verificabile nel mondo concreto?
- caos: quanto disturba le assunzioni correnti?

Sii onesto. Non gonfiare. Un vettore debole ha imp≤5.
Rispondi SOLO con array JSON valido, nessun testo aggiuntivo."""

_USR = """Tensione: "{polo1} ↔ {polo2}"
Contesto: {contesto}

Array JSON di 6 vettori:
[{{"nome":"NOME_BREVE","contenuto":"insight denso verificabile","imp":0,"orig":0,"real":0,"caos":0}}]"""


def sottometti_batch(tensioni: list[dict], api_key: str) -> Optional[str]:
    try:
        import anthropic
    except ImportError:
        print("[osservatore] anthropic SDK non installato")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    requests = [
        {
            "custom_id": f"t{i}",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1400,
                "system": _SYSTEM,
                "messages": [{"role": "user", "content": _USR.format(**t)}]
            }
        }
        for i, t in enumerate(tensioni)
    ]
    try:
        batch = client.messages.batches.create(requests=requests)
        return batch.id
    except Exception as e:
        print(f"[osservatore] Batch API errore: {e}")
        return None


def ritira_batch(batch_id: str, api_key: str,
                 tensioni_map: dict) -> Optional[list[dict]]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        batch = client.messages.batches.retrieve(batch_id)
    except Exception as e:
        print(f"[osservatore] Retrieve errore: {e}")
        return None

    if batch.processing_status != "ended":
        print(f"[osservatore] Batch {batch_id}: {batch.processing_status}")
        return None

    risultati = []
    for res in client.messages.batches.results(batch_id):
        if res.result.type != "succeeded":
            continue
        idx = res.custom_id[1:]  # strip 't'
        tensione = tensioni_map.get(idx, {})
        raw = res.result.message.content[0].text
        m = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not m:
            continue
        try:
            vettori = [Vettore(**d) for d in json.loads(m.group())]
            risultati.append({"tensione": tensione, "vettori": vettori})
        except Exception:
            continue
    return risultati


def _sincrono(tensioni: list[dict], api_key: str) -> list[dict]:
    """Fallback: chiamate dirette (se batch non disponibile)."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        return []

    risultati = []
    for t in tensioni:
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1400,
                system=_SYSTEM,
                messages=[{"role": "user", "content": _USR.format(**t)}]
            )
            raw = resp.content[0].text
            m = re.search(r'\[.*?\]', raw, re.DOTALL)
            if m:
                vettori = [Vettore(**d) for d in json.loads(m.group())]
                risultati.append({"tensione": t, "vettori": vettori})
        except Exception as e:
            print(f"  [err sincrono] {e}")
    return risultati


# ── STATO ────────────────────────────────────────────────────────────────────

def carica_stato() -> dict:
    if STATO_FILE.exists():
        return json.loads(STATO_FILE.read_text(encoding="utf-8"))
    return {}


def salva_stato(s: dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATO_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


# ── REPORT ───────────────────────────────────────────────────────────────────

def genera_report(risultati: list[dict], data: str) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sessione = Sessione(f"osservatore_{data}")
    q_prec = None

    for r in risultati:
        t = r["tensione"]
        label = f"{t.get('polo1','?')} ↔ {t.get('polo2','?')}"
        vettori = r.get("vettori", [])
        if not vettori:
            continue
        print(f"\n{'─'*60}\n  TENSIONE: {label}")
        _, Q = ciclo(label, vettori, sessione=sessione, q_prec=q_prec)
        q_prec = Q

    json_p = sessione.salva()
    md_p   = sessione.esporta_md()

    # Intestazione OSSERVATORE-1
    corpo = md_p.read_text(encoding="utf-8")
    header = (
        f"# OSSERVATORE-1 — {data}\n"
        "> Scacchiera Quantica su tensioni reali · Batch API · SDQ-1\n\n"
    )
    md_p.write_text(header + corpo, encoding="utf-8")

    print(f"\n[osservatore] JSON → {json_p}")
    print(f"[osservatore] MD   → {md_p}")
    return json_p, md_p


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Forza nuova estrazione anche se già fatto oggi")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[osservatore] ANTHROPIC_API_KEY assente — exit")
        sys.exit(0)

    stato = carica_stato()
    oggi  = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── Fase A: ritira batch pendente ────────────────────────────────────────
    batch_id = stato.get("batch_id")
    if batch_id and stato.get("batch_status") == "pendente":
        print(f"[osservatore] Ritiro batch {batch_id}...")
        tensioni_map = stato.get("tensioni_map", {})
        risultati = ritira_batch(batch_id, api_key, tensioni_map)
        if risultati:
            genera_report(risultati, stato.get("batch_data", oggi))
            stato["batch_status"] = "processato"
            salva_stato(stato)
            print("[osservatore] Batch processato con successo.")
        else:
            print("[osservatore] Batch non ancora pronto — riprovo al prossimo run.")

    # ── Fase B: estrai tensioni + sottometti nuovo batch ─────────────────────
    if stato.get("batch_data") == oggi and not args.force:
        print(f"[osservatore] Già eseguito oggi ({oggi}). Usa --force per ripetere.")
        return

    print("[osservatore] Estrazione tensioni dal lavoro reale...")
    commits  = _git_log(days=1)
    brief    = _leggi_brief()
    desideri = _leggi_desideri()
    print(f"[osservatore] {len(commits)} commit · brief {'✓' if brief else '✗'} · desideri {'✓' if desideri else '✗'}")

    tensioni = estrai_tensioni(commits, brief, desideri)
    if not tensioni:
        print("[osservatore] Nessuna tensione estratta.")
        return

    print(f"[osservatore] {len(tensioni)} tensioni:")
    for i, t in enumerate(tensioni):
        print(f"  [{i}] {t['polo1']} ↔ {t['polo2']}")

    # Prova Batch API
    bid = sottometti_batch(tensioni, api_key)

    if bid:
        stato.update({
            "batch_id": bid,
            "batch_data": oggi,
            "batch_status": "pendente",
            "tensioni_map": {str(i): t for i, t in enumerate(tensioni)},
        })
        salva_stato(stato)
        print(f"[osservatore] Batch {bid} sottomesso. Risultati disponibili entro 24h.")
    else:
        # Fallback sincrono
        print("[osservatore] Batch non disponibile — fallback sincrono (Haiku)...")
        risultati = _sincrono(tensioni, api_key)
        if risultati:
            genera_report(risultati, oggi)
            stato.update({"batch_data": oggi, "batch_status": "sincrono"})
            salva_stato(stato)


if __name__ == "__main__":
    main()
