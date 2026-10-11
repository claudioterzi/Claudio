"""EVO-004 — Diagnostica tecnica SDQ-1.

Analisi quantitativa del sistema: latenze, provider, soglie, raccomandazioni.
Nessuna LLM call, nessuna filosofia. Solo dati reali.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProblemaRilevato:
    codice: str
    gravita: str      # critico | warning | info
    descrizione: str
    raccomandazione: str


@dataclass
class ReportDiagnostica:
    timestamp: float = field(default_factory=time.time)
    problemi: list[ProblemaRilevato] = field(default_factory=list)
    metriche: dict[str, Any] = field(default_factory=dict)
    punteggio_salute: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "punteggio_salute": round(self.punteggio_salute, 1),
            "problemi": [
                {"codice": p.codice, "gravita": p.gravita,
                 "descrizione": p.descrizione, "raccomandazione": p.raccomandazione}
                for p in self.problemi
            ],
            "metriche": self.metriche,
        }

    def stampa(self) -> str:
        linee = [
            f"━━━ DIAGNOSTICA SDQ-1 ━━━  punteggio={self.punteggio_salute:.0f}/100",
            "",
        ]
        for m_key, m_val in self.metriche.items():
            linee.append(f"  {m_key:<30} {m_val}")
        if self.problemi:
            linee.append("")
            for p in sorted(self.problemi, key=lambda x: {"critico": 0, "warning": 1, "info": 2}[x.gravita]):
                icona = {"critico": "✖", "warning": "▲", "info": "ℹ"}[p.gravita]
                linee.append(f"  {icona} [{p.codice}] {p.descrizione}")
                linee.append(f"    → {p.raccomandazione}")
        else:
            linee.append("  ✓ Nessun problema rilevato")
        return "\n".join(linee)


# Soglie di allerta
_SOGLIA_LATENZA_WARNING_MS = 30_000
_SOGLIA_LATENZA_CRITICA_MS = 60_000
_SOGLIA_SUCCESSO_WARNING = 0.90
_SOGLIA_SUCCESSO_CRITICA = 0.70
_MIN_PROVIDER_ATTIVI = 2


def esegui_diagnostica(
    health_riepilogo: dict[str, Any],
    metrics_aggregati: dict[str, Any],
    vss_size: int,
    tipo_persistenza: str,
    provider_attivi: dict[str, bool],
) -> ReportDiagnostica:
    report = ReportDiagnostica()
    problemi = report.problemi

    # — Provider —
    attivi = [k for k, v in provider_attivi.items() if v and k != "stub"]
    n_attivi = len(attivi)
    report.metriche["provider_attivi"] = attivi or ["stub"]
    report.metriche["provider_non_configurati"] = [k for k, v in provider_attivi.items() if not v]

    # EVO-002: mappa provider → variabile d'ambiente richiesta
    _CHIAVI_ENV: dict[str, str] = {
        "gemini":     "GEMINI_API_KEY (o GOOGLE_API_KEY)",
        "anthropic":  "ANTHROPIC_API_KEY",
        "openai":     "OPENAI_API_KEY",
        "deepseek":   "DEEPSEEK_API_KEY",
        "grok":       "XAI_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
    }
    mancanti_con_env = [
        f"{k} [{_CHIAVI_ENV.get(k, k.upper()+'_API_KEY')}]"
        for k, v in provider_attivi.items()
        if not v and k != "stub" and k != "ollama"
    ]
    report.metriche["provider_mancanti_env"] = mancanti_con_env

    if n_attivi == 0:
        problemi.append(ProblemaRilevato(
            "PROV-001", "critico",
            "Nessun provider LLM reale configurato — sistema in modalità stub",
            "Aggiungere GEMINI_API_KEY o ANTHROPIC_API_KEY al file .env",
        ))
        report.punteggio_salute -= 40
    elif n_attivi < _MIN_PROVIDER_ATTIVI:
        problemi.append(ProblemaRilevato(
            "PROV-002", "warning",
            f"Solo {n_attivi} provider attivo — single point of failure",
            f"Aggiungere al .env: {' | '.join(mancanti_con_env[:2])}",
        ))
        report.punteggio_salute -= 15

    # — Latenza —
    latenza = metrics_aggregati.get("latenza_media_ms", 0)
    report.metriche["latenza_media_ms"] = latenza
    if latenza > _SOGLIA_LATENZA_CRITICA_MS:
        problemi.append(ProblemaRilevato(
            "PERF-001", "critico",
            f"Latenza media {latenza:.0f}ms — oltre soglia critica {_SOGLIA_LATENZA_CRITICA_MS}ms",
            "Attivare profilo 'veloce' per DECOMP/MEMO; considerare cache più aggressiva",
        ))
        report.punteggio_salute -= 25
    elif latenza > _SOGLIA_LATENZA_WARNING_MS:
        problemi.append(ProblemaRilevato(
            "PERF-002", "warning",
            f"Latenza media {latenza:.0f}ms — sopra soglia warning {_SOGLIA_LATENZA_WARNING_MS}ms",
            "Verificare che DECOMP-005 e MEMO-002 usino profilo 'veloce' (flash)",
        ))
        report.punteggio_salute -= 10

    # — Tasso successo —
    successo = metrics_aggregati.get("tasso_successo", 1.0)
    report.metriche["tasso_successo"] = f"{successo:.1%}"
    chiamate = metrics_aggregati.get("chiamate_totali", 0)
    report.metriche["chiamate_totali"] = chiamate
    if chiamate > 0:
        if successo < _SOGLIA_SUCCESSO_CRITICA:
            problemi.append(ProblemaRilevato(
                "QUAL-001", "critico",
                f"Tasso successo {successo:.1%} — sotto soglia critica {_SOGLIA_SUCCESSO_CRITICA:.0%}",
                "Investigare errori recenti con --metrics --verbose; verificare API key attive",
            ))
            report.punteggio_salute -= 30
        elif successo < _SOGLIA_SUCCESSO_WARNING:
            problemi.append(ProblemaRilevato(
                "QUAL-002", "warning",
                f"Tasso successo {successo:.1%} — sotto soglia warning {_SOGLIA_SUCCESSO_WARNING:.0%}",
                "Verificare circuit breaker e disponibilità provider con --health",
            ))
            report.punteggio_salute -= 15

    # — Persistenza —
    report.metriche["persistenza"] = tipo_persistenza
    if "InMemory" in tipo_persistenza:
        problemi.append(ProblemaRilevato(
            "PERS-001", "warning",
            "Persistenza in-memory — stato perso a ogni riavvio",
            "EVO-001 attiva: JsonFileStore già implementato. Reinstallare redis per persistenza ottimale",
        ))
        report.punteggio_salute -= 10

    # — VSS —
    report.metriche["vss_entries"] = vss_size
    if vss_size == 0 and chiamate > 0:
        problemi.append(ProblemaRilevato(
            "MEM-001", "info",
            "VSS vuoto dopo chiamate effettuate — memoria cross-agente non accumulata",
            "Verificare che gli agenti scrivano nel VSS correttamente (check ptr nei log)",
        ))

    # — ARGO Heartbeat —
    report.metriche["argo_heartbeat"] = "non attivo"
    problemi.append(ProblemaRilevato(
        "MON-001", "info",
        "ARGO Heartbeat non attivo — nessun monitoraggio esterno del sistema",
        "Aprire script.google.com → incolla argo_heartbeat.gs → installaTrigger() → testHeartbeat()",
    ))

    report.punteggio_salute = max(0.0, min(100.0, report.punteggio_salute))
    return report


def salva_report(report: ReportDiagnostica, cartella: str = "output/diagnostica") -> Path:
    p = Path(cartella)
    p.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(report.timestamp))
    out = p / f"diag_{ts}.json"
    out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out
