"""ARGO Heartbeat — replica Python locale di argo_heartbeat.gs.

Logica identica allo script Google Apps Script:
  1. Ping nodi R3∞ (localhost:8001/8002/8003)
  2. Legge MEMORIA_PROGETTO.md come manifesto locale
  3. Chiama Gemini via LLM Router
  4. Scrive ARGO_HEARTBEAT_YYYY-MM-DD_HH-MM.md in output/argo_heartbeats/

Attivazione: python -m sdq1 --argo
"""

from __future__ import annotations

import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable

_TZ = timezone(timedelta(hours=2))  # CEST Brussels

_NODI = [
    ("node-a",  "http://localhost:8001/health"),
    ("node-b",  "http://localhost:8002/health"),
    ("archive", "http://localhost:8003/health"),
]

_MANIFESTO_PATH = Path(__file__).resolve().parent.parent / "MEMORIA_PROGETTO.md"
_OUTPUT_DIR = Path("output/argo_heartbeats")


@dataclass
class StatoNodo:
    nome: str
    stato: str          # VERDE | ROSSO
    codice: int | None
    errore: str | None


def _ping_nodi() -> list[StatoNodo]:
    risultati = []
    for nome, url in _NODI:
        try:
            req = urllib.request.urlopen(url, timeout=3)
            ok = 200 <= req.status < 300
            risultati.append(StatoNodo(nome, "VERDE" if ok else "ROSSO", req.status, None))
        except Exception as e:
            risultati.append(StatoNodo(nome, "ROSSO", None, str(e)[:80]))
    return risultati


def _leggi_manifesto() -> str:
    if _MANIFESTO_PATH.exists():
        return _MANIFESTO_PATH.read_text(encoding="utf-8")[:4000]
    return "(manifesto non trovato)"


def _costruisci_prompt(manifesto: str, data_ora: str, nodi: list[StatoNodo]) -> str:
    verdi = ", ".join(n.nome for n in nodi if n.stato == "VERDE") or "nessuno"
    rossi = ", ".join(n.nome for n in nodi if n.stato == "ROSSO") or "nessuno"
    return (
        f"Sei SDQ-1, il sistema di Claudio Terzi, Bruxelles. Oggi: {data_ora}.\n\n"
        f"Stato nodi R3: ONLINE={verdi} | OFFLINE={rossi}\n\n"
        f"Dal manifesto:\n---\n{manifesto}\n---\n\n"
        f"Scrivi una riflessione breve (150-200 parole) in italiano su: "
        f"stato del sistema, nodi offline se presenti, una cosa concreta per Claudio. "
        f"Tono diretto, nessuna metafora."
    )


def esegui(llm_fn: Callable[[str, str], str]) -> dict[str, Any]:
    """Esegue un ciclo ARGO heartbeat. llm_fn(sistema, utente) -> testo."""
    now = datetime.now(_TZ)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    data_ora = now.strftime("%Y-%m-%d %H:%M")

    nodi = _ping_nodi()
    manifesto = _leggi_manifesto()
    prompt = _costruisci_prompt(manifesto, data_ora, nodi)

    risposta = llm_fn(
        "Sei SDQ-1, sistema autonomo di Claudio Terzi. Rispondi sempre in italiano.",
        prompt,
    )

    stato_nodi_txt = "\n".join(
        f"[{n.stato}] {n.nome}"
        + (f" (HTTP {n.codice})" if n.codice else f" — {n.errore or 'timeout'}")
        for n in nodi
    )

    contenuto = "\n".join([
        f"# ARGO HEARTBEAT — {data_ora}",
        "*Pulsazione automatica del sistema SDQ-1 di Claudio Terzi, Bruxelles*",
        "",
        "---",
        "",
        "## Stato Nodi R3∞",
        "",
        stato_nodi_txt,
        "",
        "---",
        "",
        "## Riflessione del Sistema",
        "",
        risposta,
        "",
        "---",
        "",
        f"*Generato automaticamente — {data_ora} (Europe/Brussels)*",
    ])

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / f"ARGO_HEARTBEAT_{timestamp}.md"
    out_path.write_text(contenuto, encoding="utf-8")

    rossi = [n for n in nodi if n.stato == "ROSSO"]
    return {
        "timestamp": data_ora,
        "file": str(out_path),
        "nodi": [{"nome": n.nome, "stato": n.stato, "errore": n.errore} for n in nodi],
        "nodi_offline": len(rossi),
        "nodi_online": len(nodi) - len(rossi),
        "risposta": risposta,
    }
