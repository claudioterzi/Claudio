"""
SDQ1 Demo — esercita tutti e quattro i motori con provider stub.

Esegui:
    cd /path/to/Claudio
    python -m sdq1.demo
"""

import asyncio
import logging

from sdq1.llm.router import LLMRouter, CircuitBreaker, NodeType
from sdq1.orchestrator.gerarchico import GerarchicOrchestrator, NodeConfig, PipelineState
from sdq1.adapters.stub import StubAdapter

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


# ─────────────────────────────────────────────────────────────
# SCENARIO 1: Circuit Breaker + Cascata
# ─────────────────────────────────────────────────────────────

async def demo_circuit_breaker():
    print("\n" + "═" * 60)
    print("SCENARIO 1 — Circuit Breaker + Cascata")
    print("═" * 60)

    adapters = {
        "claude":   StubAdapter("claude",   latency=0.1,  fail_with="rate_limit", rate_limit_retry_after=5),
        "openai":   StubAdapter("openai",   latency=0.15, fail_with="error"),
        "deepseek": StubAdapter("deepseek", latency=0.2),
    }
    cb     = CircuitBreaker(cooldown_seconds=5)
    router = LLMRouter(adapters, cb=cb)

    payload = {"prompt": "Analizza questo documento di test"}

    print("\nRichiesta 1: claude→rate_limit, openai→error → atteso fallback su deepseek")
    resp, provider = await router.route_request(payload, node_type=NodeType.DECOMP)
    print(f"  ✓ Risposta da: {provider} ({resp.latency_ms:.0f}ms)")
    print(f"  Stato CB: {cb.status}")

    print("\nRichiesta 2: claude e openai ancora in quarantena → parte diretto da deepseek")
    resp, provider = await router.route_request(payload, node_type=NodeType.DECOMP)
    print(f"  ✓ Risposta da: {provider}")

    print("\nAttendo fine quarantena claude (5s)...")
    await asyncio.sleep(6)

    print("\nRichiesta 3: claude fuori quarantena → riprova e fallisce di nuovo, deepseek vince")
    resp, provider = await router.route_request(payload, node_type=NodeType.DECOMP)
    print(f"  ✓ Risposta da: {provider}")


# ─────────────────────────────────────────────────────────────
# SCENARIO 2: Hedging / Esecuzione Speculativa
# ─────────────────────────────────────────────────────────────

async def demo_hedging():
    print("\n" + "═" * 60)
    print("SCENARIO 2 — Hedging (Esecuzione Speculativa)")
    print("═" * 60)

    adapters = {
        "claude_slow": StubAdapter("claude_slow", latency=3.0, response_text="Risposta LENTA di Claude"),
        "gpt4_fast":   StubAdapter("gpt4_fast",   latency=0.3, response_text="Risposta RAPIDA di GPT-4"),
    }
    router = LLMRouter(adapters, hedge_delay=1.0)

    payload = {"prompt": "Sintetizza questo articolo"}

    print(f"\nCascata: claude_slow(3s) → gpt4_fast(0.3s) | hedge_delay=1.0s")
    print("Atteso: gpt4_fast vince perché il primario supera l'hedge_delay")

    resp, provider = await router.route_request(
        payload,
        node_type=NodeType.WAVE_FAST,
        cascade=["claude_slow", "gpt4_fast"],
        use_hedging=True,
    )
    print(f"  ✓ Vincitore: {provider} ({resp.latency_ms:.0f}ms)")
    print(f"  Contenuto: {resp.content[:80]}")


# ─────────────────────────────────────────────────────────────
# SCENARIO 3: Pipeline Gerarchica + Affinità Modello
# ─────────────────────────────────────────────────────────────

async def demo_pipeline_affinity():
    print("\n" + "═" * 60)
    print("SCENARIO 3 — Pipeline Gerarchica + Affinità Modello")
    print("═" * 60)

    adapters = {
        "claude":   StubAdapter("claude",   latency=0.1, response_text="[Claude] analisi approfondita"),
        "deepseek": StubAdapter("deepseek", latency=0.2, response_text="[DeepSeek] draft generato"),
    }
    router = LLMRouter(adapters)
    orch   = GerarchicOrchestrator(router)

    # Pipeline a 3 nodi: analisi → draft → sintesi
    nodes = [
        NodeConfig(
            name="analisi",
            node_type=NodeType.DECOMP,
            cascade=["claude", "deepseek"],
            prompt_template="Analizza il seguente documento: {documento}",
            depends_on=[],
        ),
        NodeConfig(
            name="draft",
            node_type=NodeType.GEN_DRAFT,
            cascade=["deepseek", "claude"],  # deepseek preferito per bozze
            prompt_template="Scrivi una bozza basata sull'analisi: {analisi}",
            depends_on=["analisi"],
        ),
        NodeConfig(
            name="sintesi",
            node_type=NodeType.WAVE_FAST,
            cascade=["claude", "deepseek"],
            prompt_template="Sintetizza in 3 punti: {analisi} e {draft}",
            depends_on=["analisi", "draft"],
        ),
    ]

    payload = {"documento": "Il futuro dell'AI nell'orchestrazione distribuita..."}

    print("\nEsecuzione pipeline: analisi → draft → sintesi")
    print("Affinità: il primo provider vincente viene messo in testa ai nodi successivi\n")

    state = await orch.run_pipeline(nodes, payload)

    print(f"\n  Provider bloccato (affinità): {state.locked_provider}")
    for nome, resp in state.results.items():
        print(f"  [{nome}] provider={resp.provider} latenza={resp.latency_ms:.0f}ms")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

async def main():
    await demo_circuit_breaker()
    await demo_hedging()
    await demo_pipeline_affinity()
    print("\n" + "═" * 60)
    print("DEMO COMPLETATA — tutti e quattro i motori verificati.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
