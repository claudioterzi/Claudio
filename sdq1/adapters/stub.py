"""
SDQ1 StubAdapter — adapter deterministico per test e sviluppo.

Simula latenza configurabile, fallimenti, rate-limit e timeout
senza chiamate di rete reali.
"""

import asyncio
from typing import Any, Dict, Optional

from sdq1.llm.router import LLMResponse, RateLimitError
from .base import ProviderAdapter


class StubAdapter(ProviderAdapter):
    """
    Adapter stub per test. Comportamento configurabile:

        stub_ok    = StubAdapter("stub_ok", latency=0.1)
        stub_slow  = StubAdapter("stub_slow", latency=5.0)
        stub_429   = StubAdapter("stub_429", fail_with="rate_limit")
        stub_error = StubAdapter("stub_error", fail_with="error")

    Utile per testare circuit breaker, hedging e cascata
    senza spendere token reali.
    """

    def __init__(
        self,
        name: str = "stub",
        model: str = "stub-v1",
        latency: float = 0.05,
        response_text: Optional[str] = None,
        fail_with: Optional[str] = None,  # "rate_limit" | "timeout" | "error"
        rate_limit_retry_after: int = 10,
    ):
        self.name  = name
        self.model = model
        self._latency     = latency
        self._response    = response_text or f"[{name}] risposta stub"
        self._fail_with   = fail_with
        self._retry_after = rate_limit_retry_after

    async def call(self, payload: Dict[str, Any], timeout: float) -> LLMResponse:
        await asyncio.sleep(self._latency)

        if self._fail_with == "rate_limit":
            raise RateLimitError(
                f"{self.name} simulato 429",
                retry_after=self._retry_after,
            )
        if self._fail_with == "timeout":
            await asyncio.sleep(timeout + 1)  # supera il timeout del router
        if self._fail_with == "error":
            raise RuntimeError(f"{self.name} errore simulato")

        prompt_snippet = str(payload.get("prompt", ""))[:60]
        return LLMResponse(
            content=f"{self._response} | prompt='{prompt_snippet}...'",
            provider=self.name,
            model=self.model,
        )
