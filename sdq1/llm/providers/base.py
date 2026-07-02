"""Contratto comune per tutti i provider LLM."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

try:
    import headroom as _headroom
    _HEADROOM_OK = True
    # compress_user_messages=True: di default Headroom protegge i messaggi
    # utente — qui li comprimiamo perché il "utente" del router SDQ-1 porta
    # spesso contesto assemblato (memoria recuperata, log, JSON), non solo
    # istruzione diretta. Il system prompt resta SEMPRE intatto: comprimerlo
    # romperebbe il prompt caching di Anthropic sui prefissi ripetuti.
    _HEADROOM_CONFIG = _headroom.CompressConfig(
        compress_user_messages=True,
        compress_system_messages=False,
        min_tokens_to_compress=400,
    )
except ImportError:
    _HEADROOM_OK = False
    _HEADROOM_CONFIG = None

# GUARDIA ANTI-PLACEHOLDER (critica). In modalità inline `compress()` — senza
# un HeadroomClient/proxy con store di retrieval — Headroom sostituisce il
# contenuto strutturato (JSON, log) con un placeholder tipo
# "[N lines compressed to 0. Retrieve more: hash=...]". Quel placeholder è
# utile SOLO se il modello può poi richiamare l'originale via lo store, che
# qui NON esiste: il modello riceverebbe testo inutilizzabile e produrrebbe
# risposte sbagliate. Finché non integriamo il proxy/client con store, se la
# compressione genera un placeholder di retrieval lo SCARTIAMO e usiamo
# l'originale. Verificato empiricamente 2026-07-02: JSON/log -> placeholder,
# prosa non strutturata -> nessuna compressione (router:noop). Di fatto,
# inline, Headroom oggi comprime in modo sicuro pochissimo — il suo vero
# valore richiede il proxy con retrieval (lavoro futuro, vedi CLAUDE.md).
_RETRIEVAL_PLACEHOLDER = re.compile(r"Retrieve more:\s*hash=")


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

    # Provider dove la compressione va DISATTIVATA di default:
    # - ollama: modelli locali, i token non costano nulla — solo latenza e
    #   rischio semantico in cambio di zero risparmio economico;
    # - stub: risponde per keyword-matching sul testo, il rewrite lo romperebbe.
    # Sovrascrivibile comunque con opts={"headroom": True/False}.
    _headroom_default = True

    def __init__(self, modello: str, api_key: str | None, **opts):
        self.modello = modello
        self.api_key = api_key
        self.opts = opts
        self.disponibile = self._inizializza()
        # Protocollo Headroom (obbligatorio, cfr. CLAUDE.md): compressione
        # del contesto prima di ogni chiamata. opts={"headroom": ...} ha la
        # precedenza; altrimenti vale il default della sottoclasse.
        self.headroom_attivo = _HEADROOM_OK and self.opts.get(
            "headroom", self._headroom_default
        )

    def _comprimi_utente(self, utente: str) -> tuple[str, dict[str, Any]]:
        """Applica Headroom al messaggio utente. Ritorna (testo, metriche).

        Tre garanzie di sicurezza, in ordine:
        1. Passthrough se Headroom assente/disattivo o se solleva eccezione —
           mai bloccare una chiamata reale per un problema di ottimizzazione.
        2. Guardia anti-placeholder: se la compressione produce un placeholder
           di retrieval CCR (che senza store non è risolvibile dal modello),
           SCARTA il risultato e usa l'originale — mai mandare al modello un
           contenuto che non può leggere.
        3. Metriche emesse solo quando la compressione è realmente avvenuta
           (tokens_before>0 e testo cambiato): niente zeri fuorvianti in
           telemetria quando Headroom fa noop o fallisce internamente.

        La latenza della compressione NON entra in latenza_ms del provider
        (che misura la chiamata di rete): è riportata a parte in
        headroom_latenza_ms quando presente.
        """
        if not self.headroom_attivo:
            return utente, {}
        try:
            t0 = time.time()
            risultato = _headroom.compress(
                [{"role": "user", "content": utente}],
                model=self.modello,
                config=_HEADROOM_CONFIG,
            )
            comp_ms = int((time.time() - t0) * 1000)
            testo_compresso = risultato.messages[0]["content"]

            # Guardia 2: placeholder di retrieval non risolvibile -> scarta
            if _RETRIEVAL_PLACEHOLDER.search(testo_compresso):
                return utente, {"headroom_scartato": "placeholder_retrieval_senza_store"}

            # Guardia 3: compressione non avvenuta -> nessuna metrica finta
            if risultato.tokens_before <= 0 or testo_compresso == utente:
                return utente, {}

            metriche = {
                "headroom_tokens_before": risultato.tokens_before,
                "headroom_tokens_after": risultato.tokens_after,
                "headroom_tokens_saved": risultato.tokens_saved,
                "headroom_ratio": round(risultato.compression_ratio, 4),
                "headroom_latenza_ms": comp_ms,
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
