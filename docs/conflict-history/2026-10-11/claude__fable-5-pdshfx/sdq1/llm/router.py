"""
SDQ1 LLM Router
Quattro motori di stabilità integrati:
  1. Circuit Breaker   — quarantena provider che falliscono
  2. Hedging           — esecuzione speculativa su latenza primaria
  3. Timeout Dinamici  — timeout per tipo di nodo, non globale
  4. Cascata Resiliente — fallback automatico con logging
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 3. TIMEOUT DINAMICI
# ─────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    WAVE_FAST = "WAVE_FAST"   # Sintesi rapida / riepilogo
    DECOMP    = "DECOMP"      # Scomposizione query complessa
    GEN_DRAFT = "GEN_DRAFT"   # Generazione bozze lunghe
    DEFAULT   = "DEFAULT"

TIMEOUT_CONFIG: Dict[NodeType, float] = {
    NodeType.WAVE_FAST: 4.0,
    NodeType.DECOMP:    12.0,
    NodeType.GEN_DRAFT: 25.0,
    NodeType.DEFAULT:   10.0,
}


# ─────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    latency_ms: float = 0.0
    node_type: str = ""
    tokens_used: int = 0


class RateLimitError(Exception):
    """Sollevato dall'adapter quando il provider risponde 429."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


# ─────────────────────────────────────────────────────────────
# 1. CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Tiene in quarantena i provider che falliscono.
    Usa time.monotonic() per evitare derive da NTP/sistema.
    """

    def __init__(self, cooldown_seconds: int = 60):
        self.cooldown_seconds = cooldown_seconds
        self._quarantine: Dict[str, float] = {}

    def is_available(self, provider: str) -> bool:
        if provider not in self._quarantine:
            return True
        if time.monotonic() > self._quarantine[provider]:
            del self._quarantine[provider]
            logger.info(f"[CB] {provider} uscito da quarantena")
            return True
        remaining = int(self._quarantine[provider] - time.monotonic())
        logger.debug(f"[CB] {provider} ancora in quarantena per {remaining}s")
        return False

    def record_failure(self, provider: str, custom_cooldown: Optional[int] = None):
        penalty = custom_cooldown or self.cooldown_seconds
        self._quarantine[provider] = time.monotonic() + penalty
        logger.warning(f"[CB] {provider} isolato per {penalty}s")

    def record_success(self, provider: str):
        self._quarantine.pop(provider, None)

    @property
    def status(self) -> Dict[str, int]:
        now = time.monotonic()
        return {
            p: max(0, int(exp - now))
            for p, exp in self._quarantine.items()
            if exp > now
        }


# ─────────────────────────────────────────────────────────────
# 2. HEDGING / ESECUZIONE SPECULATIVA
# ─────────────────────────────────────────────────────────────

async def speculative_call(
    primary_coro,
    secondary_coro,
    hedge_delay: float = 2.0,
) -> LLMResponse:
    """
    Lancia il primario. Se non risponde entro hedge_delay secondi,
    avvia il secondario in parallelo. Vince chi finisce prima.
    Il perdente viene cancellato per liberare risorse.
    """
    primary_task = asyncio.create_task(primary_coro)
    done, _ = await asyncio.wait([primary_task], timeout=hedge_delay)

    if primary_task in done:
        return primary_task.result()

    logger.info(f"[HEDGE] Primario oltre {hedge_delay}s. Lancio secondario...")
    secondary_task = asyncio.create_task(secondary_coro)

    done, pending = await asyncio.wait(
        [primary_task, secondary_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for p in pending:
        p.cancel()
        try:
            await p
        except asyncio.CancelledError:
            pass

    winner = done.pop()
    result = winner.result()
    logger.info(f"[HEDGE] Vince {result.provider} (latenza hedge)")
    return result


# ─────────────────────────────────────────────────────────────
# LLM ROUTER — cascata + circuit breaker + hedging + timeout
# ─────────────────────────────────────────────────────────────

class LLMRouter:
    """
    Router centrale. Espone route_request() usata dall'orchestratore.

    Parametri:
        adapters    — dict {nome: ProviderAdapter}
        cb          — CircuitBreaker condiviso (o nuovo di default)
        hedge_delay — secondi di attesa prima di avviare il secondario
    """

    def __init__(
        self,
        adapters: Dict[str, "ProviderAdapter"],
        cb: Optional[CircuitBreaker] = None,
        hedge_delay: float = 2.0,
    ):
        self.adapters = adapters
        self.cb = cb or CircuitBreaker()
        self.hedge_delay = hedge_delay

    async def route_request(
        self,
        payload: Dict[str, Any],
        node_type: NodeType = NodeType.DEFAULT,
        cascade: Optional[List[str]] = None,
        use_hedging: bool = False,
    ) -> Tuple[LLMResponse, str]:
        """
        Esegue la richiesta sulla cascata, con fallback automatico.

        Returns:
            (LLMResponse, nome_provider_vincente)
        """
        cascade = cascade or list(self.adapters.keys())
        timeout = TIMEOUT_CONFIG.get(node_type, TIMEOUT_CONFIG[NodeType.DEFAULT])

        available = [
            p for p in cascade
            if p in self.adapters and self.cb.is_available(p)
        ]

        if not available:
            raise RuntimeError(
                f"[ROUTER] Tutti i provider esauriti. Stato CB: {self.cb.status}"
            )

        # — Hedging: usa i primi due provider in parallelo speculativo
        if use_hedging and len(available) >= 2:
            primary, secondary = available[0], available[1]
            primary_coro   = self._timed_call(primary,   payload, timeout, node_type)
            secondary_coro = self._timed_call(secondary, payload, timeout, node_type)
            response = await speculative_call(primary_coro, secondary_coro, self.hedge_delay)
            self.cb.record_success(response.provider)
            return response, response.provider

        # — Cascata normale con fallback sequenziale
        last_error: Optional[Exception] = None
        for provider_name in available:
            try:
                response = await self._timed_call(provider_name, payload, timeout, node_type)
                self.cb.record_success(provider_name)
                return response, provider_name

            except asyncio.TimeoutError:
                logger.warning(f"[ROUTER] {provider_name} timeout dopo {timeout}s")
                self.cb.record_failure(provider_name)
                last_error = TimeoutError(f"{provider_name} timeout")

            except RateLimitError as e:
                logger.warning(f"[ROUTER] {provider_name} rate-limit (retry_after={e.retry_after}s)")
                self.cb.record_failure(provider_name, custom_cooldown=e.retry_after)
                last_error = e

            except Exception as e:
                logger.error(f"[ROUTER] {provider_name} errore inatteso: {e}")
                last_error = e

        raise RuntimeError(
            f"[ROUTER] Cascata '{cascade}' esaurita. Ultimo errore: {last_error}"
        )

    async def _timed_call(
        self,
        provider_name: str,
        payload: Dict[str, Any],
        timeout: float,
        node_type: NodeType,
    ) -> LLMResponse:
        adapter = self.adapters[provider_name]
        t0 = time.monotonic()
        response = await asyncio.wait_for(
            adapter.call(payload, timeout),
            timeout=timeout,
        )
        response.latency_ms = (time.monotonic() - t0) * 1000
        response.node_type  = node_type.value
        return response
