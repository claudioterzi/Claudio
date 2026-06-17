#!/usr/bin/env python3
"""
Agente Orario SDQ-1
Legge TASK_AUTONOMI.md, prende il primo task ALTA PRIORITÀ [PENDING],
lo esegue via LLM, salva l'output e aggiorna il file task.
Invocato ogni ora dalle 7:00 alle 23:00 Brussels (CEST) dal workflow GitHub Actions.
"""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_FILE = ROOT / "TASK_AUTONOMI.md"
OUTPUT_DIR = ROOT / "output" / "task_output"

_TZ_BRUSSELS = timezone(timedelta(hours=2))  # CEST


def ora_brussels() -> str:
    return datetime.now(_TZ_BRUSSELS).strftime("%Y-%m-%d %H:%M CEST")


# ── Parser ───────────────────────────────────────────────────────────────────

def estrai_task_pendenti_alta_priorita(testo: str) -> list[dict]:
    """Estrae i task [PENDING] dalla sezione ALTA PRIORITÀ."""
    match_sezione = re.search(
        r"## ALTA PRIORITÀ\n(.*?)(?=\n---|\Z)", testo, re.DOTALL
    )
    if not match_sezione:
        return []

    sezione = match_sezione.group(1)
    tasks = []

    pattern_task = re.compile(
        r"### \[PENDING\] ([A-Z0-9\-]+) — (.+?)\n(.*?)(?=\n### |\Z)",
        re.DOTALL,
    )

    for m in pattern_task.finditer(sezione):
        task_id = m.group(1)
        titolo = m.group(2).strip()
        corpo = m.group(3).strip()

        obiettivo = ""
        m_obj = re.search(r"\*\*Obiettivo:\*\*\s*(.+?)(?=\n\*\*|\Z)", corpo, re.DOTALL)
        if m_obj:
            obiettivo = m_obj.group(1).strip()

        output_path = ""
        m_out = re.search(r"\*\*Output atteso:\*\*\s*`([^`]+)`", corpo)
        if m_out:
            output_path = m_out.group(1)

        categoria = ""
        m_cat = re.search(r"\*\*Categoria:\*\*\s*(.+)", corpo)
        if m_cat:
            categoria = m_cat.group(1).strip()

        tasks.append({
            "id": task_id,
            "titolo": titolo,
            "categoria": categoria,
            "obiettivo": obiettivo,
            "corpo": corpo,
            "output_path": output_path,
        })

    return tasks


# ── Prompt ───────────────────────────────────────────────────────────────────

def costruisci_prompt(task: dict) -> str:
    return f"""Sei l'Agente Orario del sistema SDQ-1 di Claudio Terzi (Bruxelles).
Devi completare il seguente task di ricerca in modo approfondito, pratico e verificabile.

TASK ID: {task['id']}
TITOLO: {task['titolo']}
CATEGORIA: {task['categoria']}
OBIETTIVO: {task['obiettivo']}

DESCRIZIONE COMPLETA:
{task['corpo']}

DATA ESECUZIONE: {ora_brussels()}

Scrivi un report completo in Markdown che soddisfi l'obiettivo del task.
Il report deve essere:
- Pratico e immediatamente utilizzabile da Claudio
- Con informazioni accurate (segnala se incerte su date/prezzi 2026)
- Con codice funzionante dove richiesto dal task
- Con link verificabili dove disponibili
- Strutturato con sezioni chiare

Il report inizia obbligatoriamente con:
# {task['id']} — {task['titolo']}
*Completato automaticamente da Agente Orario SDQ-1 — {ora_brussels()}*
"""


# ── LLM calls ────────────────────────────────────────────────────────────────

def chiama_anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def chiama_gemini(prompt: str) -> str:
    import google.genai as genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )
    return resp.text


def chiama_llm(prompt: str) -> tuple[str, str]:
    """Ritorna (testo, provider_usato). Fallback: anthropic → gemini → stub."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return chiama_anthropic(prompt), "anthropic"
        except Exception as e:
            print(f"[agente_orario] Anthropic fallito: {e}", file=sys.stderr)

    if os.environ.get("GOOGLE_API_KEY"):
        try:
            return chiama_gemini(prompt), "gemini"
        except Exception as e:
            print(f"[agente_orario] Gemini fallito: {e}", file=sys.stderr)

    testo = (
        f"# Task non eseguito — {ora_brussels()}\n\n"
        "*Nessun provider LLM disponibile (API key mancanti in questo ambiente).*\n\n"
        "Configura `ANTHROPIC_API_KEY` o `GOOGLE_API_KEY` nei GitHub Secrets."
    )
    return testo, "stub"


# ── TASK_AUTONOMI.md update ───────────────────────────────────────────────────

def aggiorna_task_autonomi(testo: str, task: dict, output_rel: str) -> str:
    ora = ora_brussels()

    # [PENDING] → [COMPLETATO]
    testo = testo.replace(
        f"### [PENDING] {task['id']} — {task['titolo']}",
        f"### [COMPLETATO] {task['id']} — {task['titolo']}",
        1,
    )

    # Inserisci voce nella sezione COMPLETATI
    link_entry = f"- **[{task['id']}]({output_rel})** — {task['titolo']} *(completato {ora})*\n"
    testo = re.sub(
        r"(## COMPLETATI\n)",
        r"\g<1>" + link_entry,
        testo,
        count=1,
    )

    return testo


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"[agente_orario] Avvio — {ora_brussels()}")

    if not TASK_FILE.exists():
        print("[agente_orario] TASK_AUTONOMI.md non trovato — niente da fare")
        return 0

    testo = TASK_FILE.read_text(encoding="utf-8")
    tasks = estrai_task_pendenti_alta_priorita(testo)

    if not tasks:
        print("[agente_orario] Nessun task ALTA PRIORITÀ in attesa")
        return 0

    task = tasks[0]
    print(f"[agente_orario] Task selezionato: {task['id']} — {task['titolo']}")

    prompt = costruisci_prompt(task)
    print("[agente_orario] Chiamata LLM in corso...")
    t0 = time.time()
    output, provider = chiama_llm(prompt)
    durata = round(time.time() - t0, 1)
    print(f"[agente_orario] Risposta da {provider} in {durata}s ({len(output)} chars)")

    # Determina path di output
    if task["output_path"]:
        dest = ROOT / task["output_path"]
    else:
        dest = OUTPUT_DIR / f"{task['id'].lower().replace('-', '_')}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(output, encoding="utf-8")
    print(f"[agente_orario] Output salvato: {dest.relative_to(ROOT)}")

    # Aggiorna TASK_AUTONOMI.md
    output_rel = str(dest.relative_to(ROOT))
    testo_aggiornato = aggiorna_task_autonomi(testo, task, output_rel)
    TASK_FILE.write_text(testo_aggiornato, encoding="utf-8")
    print(f"[agente_orario] {task['id']} → COMPLETATO in TASK_AUTONOMI.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
