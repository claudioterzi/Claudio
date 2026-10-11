"""
SDQ1 Adapters — interfaccia base e adapter HTTP generico.

Per aggiungere un provider reale (Claude, OpenAI, DeepSeek, Gemini):
  1. Sottoclass ProviderAdapter
  2. Implementa call() che chiama l'API e ritorna LLMResponse
  3. Solleva RateLimitError su 429, lascia propagare i timeout
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from sdq1.llm.router import LLMResponse, RateLimitError


class ProviderAdapter(ABC):
    """Interfaccia base per ogni provider LLM."""

    name: str = "base"
    model: str = "unknown"

    @abstractmethod
    async def call(self, payload: Dict[str, Any], timeout: float) -> LLMResponse:
        """
        Chiama il provider e ritorna LLMResponse.

        Contratto:
          - Solleva RateLimitError se il provider risponde 429
          - Lascia propagare asyncio.TimeoutError (il router la gestisce)
          - Non catturare Exception generica — il router la registra nel CB
        """
        ...


class HttpAdapter(ProviderAdapter):
    """
    Adapter generico per API REST che accettano JSON con campo "prompt".
    Adattare endpoint, headers e parsing della risposta per ogni provider.

    Esempio per provider custom:
        class MyAdapter(HttpAdapter):
            name = "myprovider"
            model = "my-model-v1"

            def __init__(self):
                super().__init__(
                    endpoint="https://api.myprovider.com/v1/complete",
                    headers={"Authorization": "Bearer MY_KEY"},
                )

            def _parse_response(self, data: dict) -> str:
                return data["choices"][0]["text"]
    """

    def __init__(
        self,
        endpoint: str,
        headers: Dict[str, str],
        name: str = "http",
        model: str = "generic",
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx richiesto per HttpAdapter: pip install httpx")
        self.name  = name
        self.model = model
        self._endpoint = endpoint
        self._headers  = headers

    async def call(self, payload: Dict[str, Any], timeout: float) -> LLMResponse:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._endpoint,
                json=payload,
                headers=self._headers,
                timeout=timeout,
            )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"{self.name} 429 rate-limit",
                retry_after=retry_after,
            )

        resp.raise_for_status()
        data = resp.json()
        content = self._parse_response(data)

        return LLMResponse(
            content=content,
            provider=self.name,
            model=self.model,
        )

    def _parse_response(self, data: dict) -> str:
        """Override per adattare il parsing al formato del provider."""
        return str(data)
