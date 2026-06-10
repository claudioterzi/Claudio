"""LLMRouter: seleziona il provider con strategie configurabili."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GeminiProvider,
    OpenAIProvider,
    PerplexityProvider,
    ProviderBase,
    RispostaProvider,
    StubProvider,
)

log = logging.getLogger(__name__)


# Mapping provider_name -> (classe, modello_default)
PROVIDER_REGISTRY: dict[str, tuple[type[ProviderBase], str]] = {
    "anthropic": (AnthropicProvider, "claude-fable-5"),
    "openai": (OpenAIProvider, "gpt-4o-mini"),
    "deepseek": (DeepSeekProvider, "deepseek-chat"),
    "perplexity": (PerplexityProvider, "sonar-pro"),
    "gemini": (GeminiProvider, "gemini-2.5-flash"),
    "stub": (StubProvider, "stub-model"),
}


@dataclass
class RegolaRouter:
    """Definisce come scegliere un provider per un dato 'profilo'."""

    profilo: str            # es. "veloce", "ragionamento", "ricerca", "default"
    cascata: list[str]      # es. ["anthropic", "openai", "stub"]
    modelli: dict[str, str] = field(default_factory=dict)  # override per provider


@dataclass
class EsitoChiamata:
    risposta: RispostaProvider
    provider_usati: list[str]
    profilo: str


class LLMRouter:
    """Costruisce provider dalla config e li seleziona via cascata."""

    def __init__(self, opts_globali: dict[str, Any], regole: list[RegolaRouter]):
        self.opts = opts_globali
        self.regole = {r.profilo: r for r in regole}
        if "default" not in self.regole:
            raise ValueError("Manca la regola 'default' nel router")
        self._cache: dict[tuple[str, str], ProviderBase] = {}

    def _ottieni(self, provider_name: str, modello: str) -> ProviderBase:
        chiave = (provider_name, modello)
        if chiave in self._cache:
            return self._cache[chiave]
        if provider_name not in PROVIDER_REGISTRY:
            raise KeyError(f"Provider sconosciuto: {provider_name}")
        cls, _ = PROVIDER_REGISTRY[provider_name]
        prov = cls(modello=modello, api_key=None, **self.opts)
        self._cache[chiave] = prov
        return prov

    def _modello_per(self, regola: RegolaRouter, provider_name: str) -> str:
        if provider_name in regola.modelli:
            return regola.modelli[provider_name]
        return PROVIDER_REGISTRY[provider_name][1]

    def chiama(self, sistema: str, utente: str, profilo: str = "default") -> EsitoChiamata:
        regola = self.regole.get(profilo) or self.regole["default"]
        tentati: list[str] = []
        ultima: RispostaProvider | None = None
        for provider_name in regola.cascata:
            modello = self._modello_per(regola, provider_name)
            prov = self._ottieni(provider_name, modello)
            tentati.append(provider_name)
            if not prov.disponibile:
                log.debug("Router: %s non disponibile, prossimo", provider_name)
                continue
            risposta = prov.completa(sistema, utente)
            ultima = risposta
            # 'stub' è esplicitamente l'ultima risorsa: si accetta sempre.
            # Per gli altri, si accetta solo se ha prodotto testo via API.
            successo = bool(risposta.testo) and (
                provider_name == "stub" or risposta.via_api
            )
            if successo:
                return EsitoChiamata(
                    risposta=risposta, provider_usati=tentati, profilo=profilo
                )
            log.debug(
                "Router: %s ha risposto vuoto o errore (%s), prossimo",
                provider_name,
                risposta.errore,
            )
        if ultima is None:
            # Nessun provider disponibile: usa stub esplicito
            stub = self._ottieni("stub", "stub-model")
            ultima = stub.completa(sistema, utente)
            tentati.append("stub")
        return EsitoChiamata(risposta=ultima, provider_usati=tentati, profilo=profilo)

    def provider_attivi(self) -> dict[str, bool]:
        """Verifica quali provider sono utilizzabili (cred + SDK)."""
        risultato: dict[str, bool] = {}
        for name, (cls, modello_default) in PROVIDER_REGISTRY.items():
            try:
                prov = self._ottieni(name, modello_default)
                risultato[name] = prov.disponibile
            except Exception:  # noqa: BLE001
                risultato[name] = False
        return risultato


def crea_router_da_config(opts_globali: dict[str, Any], regole_raw: list[dict]) -> LLMRouter:
    regole = [
        RegolaRouter(
            profilo=r["profilo"],
            cascata=r["cascata"],
            modelli=r.get("modelli", {}),
        )
        for r in regole_raw
    ]
    return LLMRouter(opts_globali=opts_globali, regole=regole)
