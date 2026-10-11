"""
SDQ1 Orchestratore Gerarchico
Motore 4: Affinità di Modello — blocca la pipeline sul provider vincente
per evitare frammentazione cognitiva tra nodi.

Pipeline features:
  - Esecuzione parallela dei nodi senza dipendenze
  - Esecuzione sequenziale dei nodi con depends_on
  - Affinità di modello propagata tra nodi
  - Context building automatico da risultati precedenti
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sdq1.llm.router import LLMRouter, LLMResponse, NodeType

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# CONFIGURAZIONE NODO
# ─────────────────────────────────────────────────────────────

@dataclass
class NodeConfig:
    """
    Configurazione di un nodo della pipeline.

    prompt_template: stringa con {variabili} da sostituire.
      Variabili disponibili: tutto ciò che sta in initial_payload
      più i risultati dei nodi predecessori (chiave = nome nodo).

    Esempio:
        NodeConfig(
            name="sintesi",
            node_type=NodeType.WAVE_FAST,
            cascade=["claude", "gpt4", "deepseek"],
            prompt_template="Sintetizza questo: {documento}. Analisi precedente: {analisi}",
            depends_on=["analisi"],
            use_hedging=True,
        )
    """
    name: str
    node_type: NodeType
    cascade: List[str]
    prompt_template: str
    use_hedging: bool = False
    depends_on: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# 4. AFFINITÀ DI MODELLO — PIPELINE STATE
# ─────────────────────────────────────────────────────────────

@dataclass
class PipelineState:
    """
    Stato condiviso della pipeline gerarchica.

    locked_provider: una volta che un provider vince il primo nodo,
    viene messo in testa alla cascata di tutti i nodi successivi.
    Questo evita che la pipeline cambi "cervello" a metà esecuzione.
    """
    locked_provider: Optional[str] = None
    results: Dict[str, LLMResponse] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def lock_to(self, provider: str):
        """Blocca l'affinità sul primo provider che vince un nodo reale."""
        if not self.locked_provider and provider not in ("stub", ""):
            self.locked_provider = provider
            logger.info(f"[AFFINITY] Pipeline bloccata su provider: '{provider}'")

    def prioritize_cascade(self, cascade: List[str]) -> List[str]:
        """
        Rimette il provider bloccato in testa alla cascata,
        mantenendo il resto come fallback.
        """
        if not self.locked_provider or self.locked_provider not in cascade:
            return cascade
        return [self.locked_provider] + [p for p in cascade if p != self.locked_provider]

    @property
    def context(self) -> Dict[str, str]:
        """Dict {nome_nodo: contenuto_risposta} per il template dei prompt."""
        return {name: resp.content for name, resp in self.results.items()}


# ─────────────────────────────────────────────────────────────
# ORCHESTRATORE GERARCHICO
# ─────────────────────────────────────────────────────────────

class GerarchicOrchestrator:
    """
    Esegue una pipeline di nodi LLM con:
      - Parallelismo automatico per nodi senza dipendenze
      - Sequenzialità per nodi con depends_on
      - Affinità di modello cross-nodo (motore 4)
      - Propagazione del context tra nodi

    Uso:
        orch = GerarchicOrchestrator(router)
        state = await orch.run_pipeline(nodes, initial_payload)
        final_answer = state.results["sintesi_finale"].content
    """

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run_pipeline(
        self,
        nodes: List[NodeConfig],
        initial_payload: Dict[str, Any],
    ) -> PipelineState:
        """
        Esegui la pipeline gerarchica.
        I nodi pronti (dipendenze soddisfatte) vengono eseguiti in parallelo.
        """
        state = PipelineState()
        pending = list(nodes)
        node_map = {n.name: n for n in nodes}

        # Validazione dipendenze
        known_names = {n.name for n in nodes}
        for node in nodes:
            for dep in node.depends_on:
                if dep not in known_names:
                    raise ValueError(
                        f"[ORCH] Nodo '{node.name}' dipende da '{dep}' che non esiste nella pipeline"
                    )

        logger.info(f"[ORCH] Avvio pipeline — {len(nodes)} nodi")

        while pending:
            ready = [
                n for n in pending
                if all(dep in state.results for dep in n.depends_on)
            ]
            if not ready:
                missing = {n.name: n.depends_on for n in pending}
                raise RuntimeError(
                    f"[ORCH] Stallo: dipendenze non soddisfatte o ciclo. Pending: {missing}"
                )

            logger.info(f"[ORCH] Batch pronto: {[n.name for n in ready]}")

            batch_results = await asyncio.gather(
                *[self._execute_node(node, state, initial_payload) for node in ready],
                return_exceptions=True,
            )

            for node, result in zip(ready, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"[ORCH] Nodo '{node.name}' fallito: {result}")
                    raise result
                state.results[node.name] = result
                pending.remove(node)

        logger.info(f"[ORCH] Pipeline completata. Provider finale: {state.locked_provider}")
        return state

    async def _execute_node(
        self,
        node: NodeConfig,
        state: PipelineState,
        initial_payload: Dict[str, Any],
    ) -> LLMResponse:
        # Affinità: il provider bloccato va in testa alla cascata
        cascade = state.prioritize_cascade(node.cascade)

        # Costruisce il payload: payload iniziale + risultati nodi precedenti
        template_vars = {**initial_payload, **state.context}
        try:
            prompt = node.prompt_template.format(**template_vars)
        except KeyError as e:
            raise ValueError(
                f"[ORCH] Nodo '{node.name}': variabile mancante nel template: {e}"
            ) from e

        payload = {**initial_payload, "prompt": prompt}

        logger.info(
            f"[ORCH] Esecuzione '{node.name}' | tipo={node.node_type.value} "
            f"| hedge={node.use_hedging} | cascata={cascade}"
        )

        response, winning_provider = await self.router.route_request(
            payload=payload,
            node_type=node.node_type,
            cascade=cascade,
            use_hedging=node.use_hedging,
        )

        # Blocca l'affinità sul primo provider che risponde con successo
        state.lock_to(winning_provider)

        logger.info(
            f"[ORCH] '{node.name}' completato — provider={winning_provider} "
            f"latenza={response.latency_ms:.0f}ms"
        )
        return response
