"""ARGO Heartbeat — replica Python locale di argo_heartbeat.gs.

Logica identica allo script Google Apps Script:
  1. Ping nodi R3∞ (localhost:8001/8002/8003)
  2. Legge MEMORIA_PROGETTO.md come manifesto locale
  3. Chiama Gemini via LLM Router
  4. Scrive ARGO_HEARTBEAT_YYYY-MM-DD_HH-MM.md in output/argo_heartbeats/

Modalità multi-provider (--argo-multi):
  Chiama in parallelo tutti i provider configurati.
  Ogni AI contribuisce con la propria riflessione.
  Il heartbeat finale è un coro, non un assolo.

Attivazione:
  python -m sdq1 --argo            # singolo (Gemini)
  python -m sdq1 --argo-multi      # tutti i provider attivi in parallelo
"""

from __future__ import annotations

import concurrent.futures
import urllib.request
import urllib.error
from dataclasses import dataclass, field
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

# Modello di riferimento per ogni provider nel heartbeat
_MODELLI_HEARTBEAT: dict[str, str] = {
    "gemini":     "gemini-2.5-flash",
    "anthropic":  "claude-fable-5",
    "openai":     "gpt-4o-mini",
    "deepseek":   "deepseek-chat",
    "grok":       "grok-3",
    "perplexity": "sonar-pro",
    "ollama":     "llama3.2",
}


@dataclass
class StatoNodo:
    nome: str
    stato: str          # VERDE | ROSSO
    codice: int | None
    errore: str | None


@dataclass
class RispostaAI:
    provider: str
    modello: str
    testo: str
    latenza_ms: float
    errore: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.testo) and not self.errore


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
        f"Scrivi una riflessione breve (100-150 parole) in italiano su: "
        f"stato del sistema, nodi offline se presenti, una cosa concreta per Claudio. "
        f"Tono diretto, nessuna metafora."
    )


def _chiama_provider(router, nome: str, sistema: str, utente: str) -> RispostaAI:
    """Chiama un singolo provider via router, restituisce RispostaAI."""
    import time
    modello = _MODELLI_HEARTBEAT.get(nome, "")
    t0 = time.time()
    try:
        esito = router.chiama(sistema, utente, profilo="default", provider_vincolo=nome)
        r = esito.risposta
        return RispostaAI(
            provider=nome,
            modello=r.modello or modello,
            testo=r.testo,
            latenza_ms=round((time.time() - t0) * 1000, 0),
            errore=r.errore if not r.via_api else None,
        )
    except Exception as exc:
        return RispostaAI(
            provider=nome,
            modello=modello,
            testo="",
            latenza_ms=round((time.time() - t0) * 1000, 0),
            errore=str(exc)[:120],
        )


def esegui(llm_fn: Callable[[str, str], str]) -> dict[str, Any]:
    """Heartbeat singolo — usa il provider di default (Gemini)."""
    import time as _time
    now = datetime.now(_TZ)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    data_ora = now.strftime("%Y-%m-%d %H:%M")

    nodi = _ping_nodi()
    manifesto = _leggi_manifesto()
    prompt = _costruisci_prompt(manifesto, data_ora, nodi)

    t0 = _time.time()
    risposta = llm_fn(
        "Sei SDQ-1, sistema autonomo di Claudio Terzi. Rispondi sempre in italiano.",
        prompt,
    )
    latenza = round((_time.time() - t0) * 1000)

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
        f"*Generato automaticamente — {data_ora} (Europe/Brussels) — latenza {latenza}ms*",
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
        "latenza_ms": latenza,
    }


def esegui_multi(router, timeout_per_provider: float = 45.0) -> dict[str, Any]:
    """Heartbeat multi-provider — chiama tutte le AI attive in parallelo.

    Ogni provider contribuisce con la propria voce.
    Il heartbeat risultante è un coro: stesso prompt, risposte diverse.
    """
    import time as _time
    now = datetime.now(_TZ)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    data_ora = now.strftime("%Y-%m-%d %H:%M")

    nodi = _ping_nodi()
    manifesto = _leggi_manifesto()
    sistema = "Sei SDQ-1, sistema autonomo di Claudio Terzi. Rispondi sempre in italiano."
    prompt = _costruisci_prompt(manifesto, data_ora, nodi)

    # Provider da chiamare: tutti quelli con API key configurata
    attivi = router.provider_attivi()
    provider_da_chiamare = [
        nome for nome, ok in attivi.items()
        if ok and nome not in ("stub",)
    ]

    # Chiamate parallele
    risposte: list[RispostaAI] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(provider_da_chiamare) or 1) as pool:
        futures = {
            pool.submit(_chiama_provider, router, nome, sistema, prompt): nome
            for nome in provider_da_chiamare
        }
        for fut in concurrent.futures.as_completed(futures, timeout=timeout_per_provider + 5):
            try:
                risposte.append(fut.result(timeout=1))
            except Exception as exc:
                nome = futures[fut]
                risposte.append(RispostaAI(nome, "", "", 0, str(exc)[:80]))

    risposte.sort(key=lambda r: (not r.ok, r.provider))

    # Costruisci il documento heartbeat
    stato_nodi_txt = "\n".join(
        f"[{n.stato}] {n.nome}"
        + (f" (HTTP {n.codice})" if n.codice else f" — {n.errore or 'timeout'}")
        for n in nodi
    )

    sezioni_ai = []
    for r in risposte:
        icona = "✅" if r.ok else "❌"
        sezioni_ai.append(f"### {icona} {r.provider.upper()} ({r.modello}) — {r.latenza_ms:.0f}ms")
        sezioni_ai.append("")
        if r.ok:
            sezioni_ai.append(r.testo)
        else:
            sezioni_ai.append(f"*(non risposto: {r.errore})*")
        sezioni_ai.append("")

    ok_count = sum(1 for r in risposte if r.ok)
    contenuto = "\n".join([
        f"# ARGO HEARTBEAT MULTI — {data_ora}",
        f"*{ok_count}/{len(risposte)} AI hanno risposto — SDQ-1 di Claudio Terzi, Bruxelles*",
        "",
        "---",
        "",
        "## Stato Nodi R3∞",
        "",
        stato_nodi_txt,
        "",
        "---",
        "",
        "## Voci delle AI",
        "",
        *sezioni_ai,
        "---",
        "",
        f"*Generato automaticamente — {data_ora} (Europe/Brussels)*",
    ])

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / f"ARGO_HEARTBEAT_MULTI_{timestamp}.md"
    out_path.write_text(contenuto, encoding="utf-8")

    return {
        "timestamp": data_ora,
        "file": str(out_path),
        "nodi": [{"nome": n.nome, "stato": n.stato} for n in nodi],
        "provider_chiamati": len(provider_da_chiamare),
        "provider_ok": ok_count,
        "risposte": [
            {"provider": r.provider, "ok": r.ok, "latenza_ms": r.latenza_ms,
             "errore": r.errore, "preview": r.testo[:100] if r.ok else ""}
            for r in risposte
        ],
    }



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
