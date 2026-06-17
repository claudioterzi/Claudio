#!/usr/bin/env python3
"""
Studio Notturno SDQ-1
Ogni notte alle 2AM Brussels genera un Morning Brief per Claudio:
stato dei dossier, prossime azioni, insight dal sistema.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORIA = ROOT / "MEMORIA_PROGETTO.md"
TASK_FILE = ROOT / "TASK_AUTONOMI.md"
OUTPUT_DIR = ROOT / "output" / "morning_brief"

_TZ_BRUSSELS = timezone(timedelta(hours=2))  # CEST


def ora_brussels() -> str:
    return datetime.now(_TZ_BRUSSELS).strftime("%Y-%m-%d %H:%M CEST")


def data_oggi() -> str:
    return datetime.now(_TZ_BRUSSELS).strftime("%Y-%m-%d")


def leggi_file(path: Path, limite: int = 3000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")[:limite]


def costruisci_prompt_studio() -> str:
    memoria = leggi_file(MEMORIA, limite=3000)
    task_list = leggi_file(TASK_FILE, limite=2500)
    data = data_oggi()

    return f"""Sei lo Studio Notturno del sistema SDQ-1 di Claudio Terzi (Bruxelles).
Sono le 2AM del {data}. Prepara il Morning Brief che Claudio troverà domattina.

MEMORIA PROGETTO (estratto recente):
{memoria if memoria else '[file non trovato]'}

TASK CORRENTI:
{task_list if task_list else '[file non trovato]'}

Genera un Morning Brief strutturato che includa:

## 1. BUONGIORNO, CLAUDIO
Una frase di apertura personalizzata e motivante.

## 2. STATO DOSSIER APERTI
Per ogni dossier attivo (PORTS/Pelan, Allianz/Parigi, SkyRights, ecc.):
- Stato attuale in una riga
- Prossima azione urgente

## 3. AGENDA DEL GIORNO
Le 3-5 cose più importanti da fare oggi, in ordine di priorità.

## 4. TASK IN ESECUZIONE AUTOMATICA
Quali task l'Agente Orario eseguirà oggi (dalla lista ALTA PRIORITÀ PENDING).

## 5. INSIGHT NOTTURNO
Un'analisi, connessione o opportunità che il sistema ha elaborato stanotte.
Qualcosa di non ovvio, pratico, utile per Claudio.

## 6. AGENDA PROSSIMI 7 GIORNI
Scadenze, eventi, milestone importanti della settimana.

Il brief inizia con:
# Morning Brief SDQ-1 — {data}
*Generato dallo Studio Notturno alle {ora_brussels()}*

Scrivi in italiano. Sii diretto e pratico. Claudio legge questo a colazione.
"""


def chiama_anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def chiama_gemini(prompt: str) -> str:
    import google.genai as genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    resp = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
    return resp.text


def chiama_llm(prompt: str) -> tuple[str, str]:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return chiama_anthropic(prompt), "anthropic"
        except Exception as e:
            print(f"[studio_notturno] Anthropic fallito: {e}", file=sys.stderr)

    if os.environ.get("GOOGLE_API_KEY"):
        try:
            return chiama_gemini(prompt), "gemini"
        except Exception as e:
            print(f"[studio_notturno] Gemini fallito: {e}", file=sys.stderr)

    brief = (
        f"# Morning Brief — {data_oggi()}\n\n"
        "*Studio Notturno non disponibile: API key mancanti in questo ambiente.*"
    )
    return brief, "stub"


def main() -> int:
    print(f"[studio_notturno] Avvio — {ora_brussels()}")

    prompt = costruisci_prompt_studio()
    t0 = time.time()
    brief, provider = chiama_llm(prompt)
    durata = round(time.time() - t0, 1)
    print(f"[studio_notturno] Brief generato da {provider} in {durata}s")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUTPUT_DIR / f"brief_{data_oggi()}.md"
    dest.write_text(brief, encoding="utf-8")
    print(f"[studio_notturno] Salvato: {dest.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
