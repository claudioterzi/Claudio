"""Health check per provider LLM."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from ..llm.router import LLMRouter, PROVIDER_REGISTRY


@dataclass
class StatoSalute:
    provider: str
    modello: str
    configurato: bool        # SDK + credenziali presenti
    raggiungibile: bool      # ping ha avuto successo
    latenza_ms: int
    errore: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "modello": self.modello,
            "configurato": self.configurato,
            "raggiungibile": self.raggiungibile,
            "latenza_ms": self.latenza_ms,
            "errore": self.errore,
            "timestamp": self.timestamp,
        }


class HealthChecker:
    """Esegue ping in parallelo verso tutti i provider."""

    def __init__(self, router: LLMRouter, timeout_ping_secondi: int = 10):
        self.router = router
        self.timeout = timeout_ping_secondi

    def _ping_provider(self, name: str) -> StatoSalute:
        cls, modello_default = PROVIDER_REGISTRY[name]
        try:
            prov = self.router._ottieni(name, modello_default)
        except Exception as exc:  # noqa: BLE001
            return StatoSalute(name, modello_default, False, False, 0, str(exc))

        if not prov.disponibile:
            return StatoSalute(name, modello_default, False, False, 0, "non configurato")

        if name == "stub":
            r = prov.completa("ping", "ping")
            return StatoSalute(name, modello_default, True, True, r.latenza_ms)

        r = prov.ping()
        return StatoSalute(
            provider=name,
            modello=modello_default,
            configurato=True,
            raggiungibile=r.via_api and bool(r.testo),
            latenza_ms=r.latenza_ms,
            errore=r.errore,
        )

    def controlla_tutti(self) -> list[StatoSalute]:
        provider_names = list(PROVIDER_REGISTRY.keys())
        risultati: list[StatoSalute] = []
        with ThreadPoolExecutor(max_workers=len(provider_names)) as ex:
            futures = {ex.submit(self._ping_provider, n): n for n in provider_names}
            for fut in as_completed(futures, timeout=self.timeout * len(provider_names)):
                risultati.append(fut.result())
        risultati.sort(key=lambda s: s.provider)
        return risultati

    def aggiorna_circuit_breaker(self) -> dict[str, str]:
        """Ping tutti i provider e apre il circuit breaker su quelli morti.

        Restituisce un dict provider -> azione ('aperto' | 'ripristinato' | 'ok').
        """
        stati = self.controlla_tutti()
        azioni: dict[str, str] = {}
        for s in stati:
            if not s.configurato:
                continue
            if s.raggiungibile:
                # provider vivo: rimuovi eventuale circuit aperto
                self.router._circuit.pop(s.provider, None)
                azioni[s.provider] = "ok"
            else:
                # provider morto: apri circuit con durata appropriata
                errore = (s.errore or "").lower()
                if any(k in errore for k in ("credit", "billing", "too low", "payment")):
                    delay = 86400  # crediti esauriti → aspetta 24h
                elif any(k in errore for k in ("429", "rate limit", "quota", "resource_exhausted")):
                    delay = 3600   # rate limit → aspetta 1h
                else:
                    delay = 300    # errore generico → riprova tra 5min
                self.router._circuit[s.provider] = time.time() + delay
                azioni[s.provider] = f"aperto_{delay}s"
        return azioni

    def riepilogo(self) -> dict[str, Any]:
        stati = self.controlla_tutti()
        configurati = sum(1 for s in stati if s.configurato)
        raggiungibili = sum(1 for s in stati if s.raggiungibile)
        return {
            "provider_totali": len(stati),
            "provider_configurati": configurati,
            "provider_raggiungibili": raggiungibili,
            "dettagli": [s.to_dict() for s in stati],
        }
