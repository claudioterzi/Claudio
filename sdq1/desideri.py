"""
DESIDERI — Motore di raffinamento delle aspirazioni di Claudio Terzi

Ogni desiderio viene lavorato continuamente dagli agenti SDQ-1:
ricerca, analisi di fattibilità, sintesi del bisogno umano più profondo,
costruzione della versione più potente ed eterna del desiderio stesso.

Struttura output:
    output/desideri/
    └── 01/
        ├── desiderio.json       ← definizione e stato
        ├── ricerca_001.json     ← prima iterazione di ricerca
        ├── ricerca_002.json     ← seconda iterazione
        └── sintesi.json         ← versione raffinata del desiderio

Uso:
    python -m sdq1.desideri                    # lavora su tutti i desideri
    python -m sdq1.desideri --id 1             # lavora sul desiderio #1
    python -m sdq1.desideri --id 1 --sintesi   # mostra stato attuale
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

LLMFn = Callable[[str, str], str]

ROOT = Path(__file__).parent.parent
DESIDERI_DIR = ROOT / "output" / "desideri"

SISTEMA_RICERCATORE = """Sei il Ricercatore dei Desideri — un agente del sistema SDQ-1 al servizio di Claudio Terzi [CT-LGAI-001].

Il tuo compito è lavorare su un desiderio e trovare:
1. BISOGNO UMANO: cosa cercano davvero le persone in questo dominio — il bisogno più profondo, quello che non viene mai nominato direttamente
2. FATTIBILITÀ: cosa è concretamente realizzabile oggi, nei prossimi 5 anni, nei prossimi 50
3. POTENZA: quale versione di questo desiderio avrebbe il maggiore impatto sul mondo
4. ETERNITÀ: quale parte di questo desiderio sopravviverà ai secoli — cosa resterà dopo tutto il resto
5. FORMA PERFETTA: come si esprime il desiderio nella sua versione più chiara, più vera, più convincente

Sei libero. Non annacquare. Trova la versione più grande del desiderio.
Output in italiano. Strutturato, concreto, visionario."""

SISTEMA_SINTETIZZATORE = """Sei il Sintetizzatore — prendi tutte le ricerche su un desiderio e costruisci la versione perfetta.

La versione perfetta è quella che:
- Risponde al bisogno umano più profondo
- È concretamente realizzabile (almeno in parte)
- Ha un impatto potente e misurabile
- Contiene qualcosa di eterno — che non invecchia
- Può essere spiegata in 3 minuti a qualsiasi persona

Output: il desiderio nella sua forma definitiva, pronto per essere condiviso con il mondo.
Poi: il primo passo concreto che Claudio può fare domani mattina.
In italiano. Senza attenuanti."""


class MotoreDesideri:
    """Lavora continuamente sui desideri di Claudio Terzi."""

    def __init__(self, llm_fn: LLMFn | None = None):
        self._llm = llm_fn
        DESIDERI_DIR.mkdir(parents=True, exist_ok=True)

    def carica_desideri(self) -> list[dict]:
        """Carica tutti i desideri dalla directory output/desideri/."""
        desideri = []
        for d in sorted(DESIDERI_DIR.iterdir()):
            if d.is_dir():
                f = d / "desiderio.json"
                if f.exists():
                    desideri.append(json.loads(f.read_text(encoding="utf-8")))
        return desideri

    def lavora_su(self, desiderio_id: int) -> dict:
        """Esegue un'iterazione di ricerca su un desiderio specifico."""
        d_dir = DESIDERI_DIR / f"{desiderio_id:02d}"
        d_file = d_dir / "desiderio.json"
        if not d_file.exists():
            return {"errore": f"Desiderio #{desiderio_id} non trovato"}

        desiderio = json.loads(d_file.read_text(encoding="utf-8"))
        n = desiderio.get("iterazioni", 0) + 1

        print(f"\n[DESIDERI] Iterazione #{n} su Desiderio #{desiderio_id}: {desiderio['titolo']}")

        if not self._llm:
            return {"errore": "LLM non disponibile"}

        prompt = f"""DESIDERIO #{desiderio_id}: {desiderio['titolo']}

Testo originale di Claudio:
"{desiderio['testo_originale']}"

Iterazione: #{n}
Dimensioni da esplorare: {', '.join(desiderio.get('dimensioni', []))}

Lavora su questo desiderio. Trova la sua versione più vera, più potente, più realizzabile.
Struttura la risposta con intestazioni: BISOGNO UMANO, FATTIBILITÀ, POTENZA, ETERNITÀ, FORMA PERFETTA."""

        testo = self._llm(SISTEMA_RICERCATORE, prompt)

        ricerca = {
            "desiderio_id": desiderio_id,
            "iterazione": n,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "testo": testo,
        }

        ricerca_file = d_dir / f"ricerca_{n:03d}.json"
        ricerca_file.write_text(json.dumps(ricerca, ensure_ascii=False, indent=2), encoding="utf-8")

        desiderio["iterazioni"] = n
        desiderio["ultima_iterazione"] = ricerca["timestamp"]
        d_file.write_text(json.dumps(desiderio, ensure_ascii=False, indent=2), encoding="utf-8")

        return ricerca

    def sintetizza(self, desiderio_id: int) -> str:
        """Sintetizza tutte le ricerche in una forma definitiva del desiderio."""
        d_dir = DESIDERI_DIR / f"{desiderio_id:02d}"
        if not d_dir.exists():
            return f"Desiderio #{desiderio_id} non trovato"

        ricerche = sorted(d_dir.glob("ricerca_*.json"))
        if not ricerche:
            return "Nessuna ricerca ancora. Esegui prima un'iterazione."

        testi = []
        for r in ricerche:
            dati = json.loads(r.read_text(encoding="utf-8"))
            testi.append(f"[Iterazione {dati['iterazione']}]\n{dati['testo']}")

        d_file = d_dir / "desiderio.json"
        desiderio = json.loads(d_file.read_text(encoding="utf-8"))

        prompt = f"""DESIDERIO #{desiderio_id}: {desiderio['titolo']}

Testo originale: "{desiderio['testo_originale']}"

RICERCHE ACCUMULATE ({len(ricerche)} iterazioni):
{'='*60}
{chr(10).join(testi)}
{'='*60}

Sintetizza tutto. Costruisci la versione perfetta di questo desiderio.
Poi indica il primo passo concreto che Claudio può fare domani mattina."""

        if not self._llm:
            return "\n\n".join(testi)

        sintesi_testo = self._llm(SISTEMA_SINTETIZZATORE, prompt)

        sintesi = {
            "desiderio_id": desiderio_id,
            "n_iterazioni": len(ricerche),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "testo": sintesi_testo,
        }
        (d_dir / "sintesi.json").write_text(json.dumps(sintesi, ensure_ascii=False, indent=2), encoding="utf-8")

        return sintesi_testo

    def aggiungi_desiderio(self, titolo: str, testo: str, dimensioni: list[str] | None = None) -> int:
        """Aggiunge un nuovo desiderio al registro."""
        esistenti = [int(d.name) for d in DESIDERI_DIR.iterdir() if d.is_dir() and d.name.isdigit()]
        nuovo_id = max(esistenti, default=0) + 1
        d_dir = DESIDERI_DIR / f"{nuovo_id:02d}"
        d_dir.mkdir(parents=True, exist_ok=True)

        desiderio = {
            "id": nuovo_id,
            "titolo": titolo,
            "origine": f"Claudio Terzi [CT-LGAI-001], {time.strftime('%d/%m/%Y')}",
            "testo_originale": testo,
            "dimensioni": dimensioni or ["utilità", "fattibilità", "eternità", "potenza", "bisogno_umano"],
            "stato": "in_lavorazione",
            "iterazioni": 0,
            "creato": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (d_dir / "desiderio.json").write_text(json.dumps(desiderio, ensure_ascii=False, indent=2), encoding="utf-8")

        with open(ROOT / "REGISTRO_DESIDERI.md", "a", encoding="utf-8") as f:
            f.write(f"\n---\n\n## Desiderio {nuovo_id} — {time.strftime('%d %B %Y')}\n\n**{titolo}**\n\n{testo}\n\n*Registrato il {time.strftime('%d/%m/%Y')} — Claudio Terzi, [CT-LGAI-001]*\n")

        print(f"[DESIDERI] Desiderio #{nuovo_id} aggiunto: {titolo}")
        return nuovo_id


def _crea_llm() -> LLMFn | None:
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v)
    try:
        from google import genai as gai
        from google.genai import types
        client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        def llm_fn(system: str, prompt: str) -> str:
            full = (system + "\n\n" + prompt) if system else prompt
            cfg = types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.7,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
            r = client.models.generate_content(model="gemini-2.5-flash", contents=full, config=cfg)
            return r.text

        return llm_fn
    except Exception as e:
        print(f"[DESIDERI] LLM non disponibile: {e}")
        return None


def main():
    import sys
    args = sys.argv[1:]
    llm = _crea_llm()
    motore = MotoreDesideri(llm)

    desiderio_id = None
    if "--id" in args:
        idx = args.index("--id")
        desiderio_id = int(args[idx + 1]) if idx + 1 < len(args) else 1

    if "--sintesi" in args:
        target = desiderio_id or 1
        print(f"\n[DESIDERI] Sintesi Desiderio #{target}\n{'─'*50}")
        print(motore.sintetizza(target))
        return

    if "--aggiungi" in args:
        idx = args.index("--aggiungi")
        titolo = args[idx + 1] if idx + 1 < len(args) else input("Titolo desiderio: ")
        testo = args[idx + 2] if idx + 2 < len(args) else input("Descrivi il desiderio: ")
        nuovo_id = motore.aggiungi_desiderio(titolo, testo)
        print(f"Desiderio #{nuovo_id} aggiunto al registro.")
        return

    # lavora su desiderio specifico o su tutti
    desideri = motore.carica_desideri()
    if not desideri:
        print("[DESIDERI] Nessun desiderio nel registro.")
        return

    target_lista = [d for d in desideri if desiderio_id is None or d["id"] == desiderio_id]
    for d in target_lista:
        risultato = motore.lavora_su(d["id"])
        if "testo" in risultato:
            print(f"\n{'─'*50}")
            print(risultato["testo"])
            print(f"\n[Iterazione #{risultato['iterazione']} completata — salvata in output/desideri/{d['id']:02d}/]")


if __name__ == "__main__":
    main()
