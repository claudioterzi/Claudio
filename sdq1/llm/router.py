"""LLMRouter: seleziona il provider con strategie configurabili.

Ottimizzazioni attive:
  A. Circuit Breaker  – salta provider in rate-limit per Retry-After secondi
  B. Hedging          – per nodi critici lancia 2 provider in parallelo
  C. Dynamic Timeout  – timeout diverso per profilo (governa il hedging)
  D. Model Affinity   – vincola i nodi successivi al provider già usato
  E. Response Cache   – evita chiamate duplicate entro TTL (default 5 min)

Commutazione Creativa (--fase):
  esplora      – esplorazione ampia, provider economici, molte opzioni
  soglia       – transizione, profilo bilanciato standard
  cristallizza – impegno finale, provider migliore, hedging attivo
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import logging
import queue
import re
import time
from dataclasses import dataclass, field
from typing import Any

from .specializzazioni import classifica, nodo_per_problema
from .providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GeminiProvider,
    GrokProvider,
    OllamaProvider,
    OpenAIProvider,
    PerplexityProvider,
    ProviderBase,
    RispostaProvider,
    StubProvider,
)

log = logging.getLogger(__name__)

PROVIDER_REGISTRY: dict[str, tuple[type[ProviderBase], str]] = {
    "anthropic":  (AnthropicProvider,  "claude-fable-5"),
    "openai":     (OpenAIProvider,     "gpt-4o-mini"),
    "deepseek":   (DeepSeekProvider,   "deepseek-chat"),
    "perplexity": (PerplexityProvider, "sonar-pro"),
    "gemini":     (GeminiProvider,     "gemini-2.5-flash"),
    "grok":       (GrokProvider,       "grok-3"),
    "ollama":     (OllamaProvider,     "llama3.2"),
    "stub":       (StubProvider,       "stub-model"),
}

_RETRY_AFTER_RE = re.compile(r"retry.after[^\d]*(\d+)", re.IGNORECASE)
_RATE_PATTERNS = frozenset({
    "429", "rate limit", "quota exceeded", "too many requests", "resource_exhausted",
    "credit balance is too low", "billing", "insufficient_quota",
})


@dataclass
class RegolaRouter:
    profilo: str
    cascata: list[str]
    modelli: dict[str, str] = field(default_factory=dict)
    timeout_s: float | None = None   # C: timeout per questo profilo


@dataclass
class EsitoChiamata:
    risposta: RispostaProvider
    provider_usati: list[str]
    profilo: str
    hedged: bool = False


# Commutazione Creativa: mappa fase → profilo router
FASE_PROFILO: dict[str, str] = {
    "esplora":      "esplora",
    "soglia":       "soglia",
    "cristallizza": "cristallizza",
}


class LLMRouter:
    # C: timeout di default per profilo (secondi)
    _TIMEOUT_DEFAULT: dict[str, float] = {
        "veloce":       15.0,
        "default":      45.0,
        "ragionamento": 90.0,
        "ricerca":      60.0,
        "esplora":      20.0,
        "soglia":       45.0,
        "cristallizza": 90.0,
    }
    # B: attesa prima di lanciare il provider secondario
    HEDGE_WAIT_S: float = 3.0

    # E: TTL cache risposte (secondi)
    CACHE_TTL_S: float = 300.0

    def __init__(self, opts_globali: dict[str, Any], regole: list[RegolaRouter]):
        self.opts = opts_globali
        self.regole = {r.profilo: r for r in regole}
        if "default" not in self.regole:
            raise ValueError("Manca la regola 'default' nel router")
        self._cache: dict[tuple[str, str], ProviderBase] = {}
        self._circuit: dict[str, float] = {}      # A: provider_name -> expiry timestamp
        self._resp_cache: dict[str, tuple[RispostaProvider, float]] = {}  # E: response cache

    # ------------------------------------------------------------------ #
    # E. Response Cache                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _cache_key(sistema: str, utente: str, profilo: str) -> str:
        raw = f"{profilo}|{sistema[:200]}|{utente[:400]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _leggi_cache(self, key: str) -> RispostaProvider | None:
        entry = self._resp_cache.get(key)
        if entry is None:
            return None
        risposta, ts = entry
        if time.time() - ts > self.CACHE_TTL_S:
            del self._resp_cache[key]
            return None
        log.debug("Cache hit: %s", key)
        return risposta

    def _scrivi_cache(self, key: str, risposta: RispostaProvider) -> None:
        if risposta.via_api and risposta.testo:
            self._resp_cache[key] = (risposta, time.time())

    # ------------------------------------------------------------------ #
    # A. Circuit Breaker                                                   #
    # ------------------------------------------------------------------ #

    def _circuit_aperto(self, nome: str) -> bool:
        exp = self._circuit.get(nome)
        if exp is None:
            return False
        if time.time() > exp:
            del self._circuit[nome]
            log.info("Circuit Breaker: %s ripristinato", nome)
            return False
        return True

    def _apri_circuit(self, nome: str, errore: str) -> None:
        m = _RETRY_AFTER_RE.search(errore)
        delay = int(m.group(1)) if m else 60
        delay = max(10, min(delay, 3600))
        self._circuit[nome] = time.time() + delay
        log.warning("Circuit Breaker: %s aperto per %ds", nome, delay)

    @staticmethod
    def _e_rate_limit(errore: str | None) -> bool:
        if not errore:
            return False
        low = errore.lower()
        return any(k in low for k in _RATE_PATTERNS)

    # ------------------------------------------------------------------ #
    # Provider cache                                                       #
    # ------------------------------------------------------------------ #

    def _ottieni(self, nome: str, modello: str) -> ProviderBase:
        key = (nome, modello)
        if key not in self._cache:
            if nome not in PROVIDER_REGISTRY:
                raise KeyError(f"Provider sconosciuto: {nome}")
            cls, _ = PROVIDER_REGISTRY[nome]
            self._cache[key] = cls(modello=modello, api_key=None, **self.opts)
        return self._cache[key]

    def _modello_per(self, regola: RegolaRouter, nome: str) -> str:
        return regola.modelli.get(nome, PROVIDER_REGISTRY[nome][1])

    # ------------------------------------------------------------------ #
    # C. Dynamic timeout                                                   #
    # ------------------------------------------------------------------ #

    def _timeout_s(self, regola: RegolaRouter) -> float:
        if regola.timeout_s is not None:
            return regola.timeout_s
        return self._TIMEOUT_DEFAULT.get(
            regola.profilo, float(self.opts.get("timeout_secondi", 60))
        )

    # ------------------------------------------------------------------ #
    # B. Hedging                                                           #
    # ------------------------------------------------------------------ #

    def _chiama_con_hedging(
        self,
        sistema: str,
        utente: str,
        regola: RegolaRouter,
        cascata_eff: list[str],
    ) -> EsitoChiamata:
        """Lancia primario; dopo HEDGE_WAIT_S avvia secondario; vince il primo."""
        primario = cascata_eff[0]
        secondario = cascata_eff[1] if len(cascata_eff) > 1 else None
        risultati: queue.Queue[tuple[str, RispostaProvider]] = queue.Queue()
        tentati: list[str] = [primario]

        def _esegui(nome: str) -> None:
            modello = self._modello_per(regola, nome)
            try:
                prov = self._ottieni(nome, modello)
                r = prov.completa(sistema, utente)
            except Exception as exc:  # noqa: BLE001
                r = RispostaProvider(
                    testo="", provider=nome, modello=modello,
                    via_api=False, latenza_ms=0, errore=str(exc),
                )
            risultati.put((nome, r))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        try:
            executor.submit(_esegui, primario)

            # Attendi HEDGE_WAIT_S: se il primario risponde bene, usalo subito
            try:
                nome, r = risultati.get(timeout=self.HEDGE_WAIT_S)
                if r.via_api and r.testo:
                    return EsitoChiamata(
                        risposta=r, provider_usati=tentati, profilo=regola.profilo
                    )
                if self._e_rate_limit(r.errore):
                    self._apri_circuit(nome, r.errore or "")
            except queue.Empty:
                log.debug(
                    "Hedging: %s lento (>%.1fs), lancio %s",
                    primario, self.HEDGE_WAIT_S, secondario,
                )

            # Lancia il secondario se disponibile e circuit chiuso
            if secondario and not self._circuit_aperto(secondario):
                tentati.append(secondario)
                executor.submit(_esegui, secondario)

            # Accetta il primo risultato valido entro il timeout del profilo
            scadenza = time.time() + self._timeout_s(regola)
            while time.time() < scadenza:
                rimasto = scadenza - time.time()
                try:
                    nome, r = risultati.get(timeout=min(rimasto, 2.0))
                    if r.via_api and r.testo:
                        return EsitoChiamata(
                            risposta=r, provider_usati=tentati,
                            profilo=regola.profilo, hedged=True,
                        )
                    if self._e_rate_limit(r.errore):
                        self._apri_circuit(nome, r.errore or "")
                except queue.Empty:
                    continue
        finally:
            executor.shutdown(wait=False)

        # Nessun provider ha risposto: fallback stub
        stub = self._ottieni("stub", "stub-model")
        r = stub.completa(sistema, utente)
        tentati.append("stub")
        return EsitoChiamata(risposta=r, provider_usati=tentati, profilo=regola.profilo)

    # ------------------------------------------------------------------ #
    # Main entry point                                                     #
    # ------------------------------------------------------------------ #

    def _risposta_debole(self, testo: str) -> bool:
        """Test-Time Compute: rileva risposte di scarsa qualità che meritano retry."""
        if not testo or len(testo) < 30:
            return True
        stub_markers = ("[stub:", "modalità locale", "provider: stub")
        return any(m in testo.lower() for m in stub_markers)

    def chiama(
        self,
        sistema: str,
        utente: str,
        profilo: str = "default",
        fase: str | None = None,              # Commutazione Creativa (esplora/soglia/cristallizza)
        problema: str | None = None,          # Routing semantico (codice/ragionamento/ricerca/...)
        hedging: bool = False,
        provider_vincolo: str | None = None,  # D: Model Affinity
        budget_tentativi: int = 1,            # Test-Time Compute: retry con prompt arricchito
        cache: bool = True,                   # E: Response Cache
        auto_classifica: bool = False,        # classifica automaticamente il testo se problema=None
    ) -> EsitoChiamata:
        # Routing semantico: classifica automatica se richiesta
        if problema is None and auto_classifica:
            problema = classifica(utente)
            if problema:
                log.debug("Auto-classificazione: '%s'", problema)

        # Routing semantico: problema sovrascrive provider_vincolo di default
        if problema is not None and provider_vincolo is None:
            nodo = nodo_per_problema(problema)
            if nodo:
                provider_vincolo = nodo.provider
                log.debug("Routing semantico: %s → %s", problema, nodo.provider)

        # Commutazione Creativa: fase sovrascrive profilo se specificata
        if fase is not None:
            profilo_fase = FASE_PROFILO.get(fase)
            if profilo_fase:
                profilo = profilo_fase
                if fase == "cristallizza":
                    hedging = True
            else:
                log.warning("Fase sconosciuta '%s', uso profilo '%s'", fase, profilo)
        regola = self.regole.get(profilo) or self.regole["default"]

        # E. Response Cache: restituisce risposta cached se disponibile
        ckey = self._cache_key(sistema, utente, profilo)
        if cache and not provider_vincolo:
            cached = self._leggi_cache(ckey)
            if cached is not None:
                cached.metadata["cached"] = True
                return EsitoChiamata(risposta=cached, provider_usati=["cache"],
                                     profilo=profilo)

        # D. Model Affinity: sposta il provider vincolato in testa alla cascata
        cascata = list(regola.cascata)
        if provider_vincolo and provider_vincolo in cascata and cascata[0] != provider_vincolo:
            cascata.remove(provider_vincolo)
            cascata.insert(0, provider_vincolo)
            log.debug("Affinity: %s → testa cascata per profilo %s", provider_vincolo, profilo)

        # A. Filtra provider con circuit aperto (se tutti aperti, riprova comunque)
        cascata_eff = [p for p in cascata if not self._circuit_aperto(p)] or cascata

        # B. Hedging per agenti critici (almeno 2 provider reali disponibili)
        if hedging:
            disponibili = [
                p for p in cascata_eff
                if p != "stub"
                and self._ottieni(p, self._modello_per(regola, p)).disponibile
            ]
            if len(disponibili) >= 2:
                return self._chiama_con_hedging(sistema, utente, regola, disponibili)

        # Cascata sequenziale standard
        tentati: list[str] = []
        ultima: RispostaProvider | None = None
        for nome in cascata_eff:
            modello = self._modello_per(regola, nome)
            prov = self._ottieni(nome, modello)
            tentati.append(nome)
            if not prov.disponibile:
                log.debug("Router: %s non disponibile", nome)
                continue
            r = prov.completa(sistema, utente)
            ultima = r
            if bool(r.testo) and (nome == "stub" or r.via_api):
                # Test-Time Compute: se risposta debole e budget > 1, retry con prompt arricchito
                if budget_tentativi > 1 and self._risposta_debole(r.testo):
                    utente_arricchito = (
                        f"{utente}\n\n[APPROFONDISCI: la risposta precedente era insufficiente. "
                        "Fornisci più dettaglio e precisione.]"
                    )
                    r2 = prov.completa(sistema, utente_arricchito)
                    if not self._risposta_debole(r2.testo):
                        r2.metadata["test_time_compute"] = True
                        self._scrivi_cache(ckey, r2)
                        return EsitoChiamata(risposta=r2, provider_usati=tentati, profilo=profilo)
                self._scrivi_cache(ckey, r)
                return EsitoChiamata(risposta=r, provider_usati=tentati, profilo=profilo)
            if self._e_rate_limit(r.errore):
                self._apri_circuit(nome, r.errore or "")
            log.debug("Router: %s fallito (%s)", nome, r.errore)

        if ultima is None:
            stub = self._ottieni("stub", "stub-model")
            ultima = stub.completa(sistema, utente)
            tentati.append("stub")
        return EsitoChiamata(risposta=ultima, provider_usati=tentati, profilo=profilo)

    def provider_attivi(self) -> dict[str, bool]:
        risultato: dict[str, bool] = {}
        for name, (_, modello_default) in PROVIDER_REGISTRY.items():
            try:
                prov = self._ottieni(name, modello_default)
                risultato[name] = prov.disponibile
            except Exception:  # noqa: BLE001
                risultato[name] = False
        return risultato

    def stato_circuit_breaker(self) -> dict[str, Any]:
        """A. Stato corrente dei circuit breaker."""
        ora = time.time()
        return {
            n: {"aperto": exp > ora, "ripristino_tra_s": max(0, round(exp - ora, 1))}
            for n, exp in self._circuit.items()
        }


def crea_router_da_config(opts_globali: dict[str, Any], regole_raw: list[dict]) -> LLMRouter:
    regole = [
        RegolaRouter(
            profilo=r["profilo"],
            cascata=r["cascata"],
            modelli=r.get("modelli", {}),
            timeout_s=r.get("timeout_s"),  # C: dynamic timeout
        )
        for r in regole_raw
    ]
    return LLMRouter(opts_globali=opts_globali, regole=regole)
