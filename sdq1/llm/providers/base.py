"""Contratto comune per tutti i provider LLM."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

try:
    import headroom as _headroom
    _HEADROOM_OK = True
    # compress_user_messages=True: di default Headroom protegge i messaggi
    # utente (contengono l'intento, non solo dati) — ma qui "utente" spesso
    # porta contesto assemblato (memoria recuperata, log, JSON) più che
    # istruzioni dirette, quindi lo abilitiamo. Soglia alta per non toccare
    # prompt brevi. Il system prompt resta intatto: comprimerlo romperebbe
    # il prompt caching di Anthropic sui prefissi ripetuti.
    _HEADROOM_CONFIG = _headroom.CompressConfig(
        compress_user_messages=True,
        compress_system_messages=False,
        min_tokens_to_compress=400,
    )
except ImportError:
    _HEADROOM_OK = False
    _HEADROOM_CONFIG = None


@dataclass
class RispostaProvider:
    testo: str
    provider: str
    modello: str
    via_api: bool
    latenza_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    errore: str | None = None


class ProviderBase(ABC):
    nome: str = "base"

    def __init__(self, modello: str, api_key: str | None, **opts):
        self.modello = modello
        self.api_key = api_key
        self.opts = opts
        self.disponibile = self._inizializza()
        # Protocollo Headroom (obbligatorio, cfr. CLAUDE.md): compressione
        # del contesto prima di ogni chiamata. Disattivabile per singolo
        # provider con opts={"headroom": False} se necessario in casi specifici.
        self.headroom_attivo = _HEADROOM_OK and self.opts.get("headroom", True)

    def _comprimi_utente(self, utente: str) -> tuple[str, dict[str, Any]]:
        """Applica Headroom al messaggio utente. Ritorna (testo, metriche).

        Fallisce in modo silenzioso e passthrough: se Headroom non è
        installato, non è attivo per questo provider, o la compressione
        stessa solleva un'eccezione, il testo originale passa invariato —
        mai bloccare una chiamata reale per un problema di ottimizzazione.
        """
        if not self.headroom_attivo:
            return utente, {}
        try:
            risultato = _headroom.compress(
                [{"role": "user", "content": utente}],
                model=self.modello,
                config=_HEADROOM_CONFIG,
            )
            testo_compresso = risultato.messages[0]["content"]
            metriche = {
                "headroom_tokens_before": risultato.tokens_before,
                "headroom_tokens_after": risultato.tokens_after,
                "headroom_tokens_saved": risultato.tokens_saved,
                "headroom_ratio": round(risultato.compression_ratio, 4),
            }
            return testo_compresso, metriche
        except Exception:  # noqa: BLE001 — mai bloccare la chiamata per l'ottimizzazione
            return utente, {}

    @abstractmethod
    def _inizializza(self) -> bool:
        """Inizializza il client. Restituisce True se utilizzabile."""

    @abstractmethod
    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        """Esegue la chiamata. Restituisce (testo, metadata)."""

    def completa(self, sistema: str, utente: str) -> RispostaProvider:
        if not self.disponibile:
            return RispostaProvider(
                testo="",
                provider=self.nome,
                modello=self.modello,
                via_api=False,
                latenza_ms=0,
                errore="provider non disponibile",
            )
        inizio = time.time()
        try:
            utente, meta_headroom = self._comprimi_utente(utente)
            testo, meta = self._completa_impl(sistema, utente)
            return RispostaProvider(
                testo=testo,
                provider=self.nome,
                modello=self.modello,
                via_api=True,
                latenza_ms=int((time.time() - inizio) * 1000),
                metadata={**meta, **meta_headroom},
            )
        except Exception as exc:  # noqa: BLE001
            return RispostaProvider(
                testo="",
                provider=self.nome,
                modello=self.modello,
                via_api=False,
                latenza_ms=int((time.time() - inizio) * 1000),
                errore=str(exc),
            )

    def ping(self) -> RispostaProvider:
        """Smoke test: chiamata minima per verificare connettività."""
        return self.completa("Sei un servizio di echo.", "ping")
