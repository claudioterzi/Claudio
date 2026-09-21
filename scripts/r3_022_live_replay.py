"""Execute the R3-022 live replay using authorized GitHub Action secrets.

No secret value is printed or persisted. The replay uses synthetic continuity
cases only. Gemini is preferred for speed/cost; Anthropic is fallback.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sdq1.continuity_replay import run_replay
from sdq1.llm.providers import AnthropicProvider, GeminiProvider


def _select_provider():
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        provider = GeminiProvider(
            modello="gemini-2.5-flash",
            api_key=None,
            temperatura=0,
            max_token=256,
            json_mode=True,
            timeout=30,
        )
        if provider.disponibile:
            return provider

    if os.getenv("ANTHROPIC_API_KEY"):
        provider = AnthropicProvider(
            modello="claude-haiku-4-5-20251001",
            api_key=None,
            temperatura=0,
            max_token=256,
            timeout_secondi=30,
            max_retries=1,
        )
        if provider.disponibile:
            return provider

    return None


def main() -> int:
    provider = _select_provider()
    if provider is None:
        print("R3-022 LIVE REPLAY: no authorized provider secret available")
        return 3

    def ask(system_prompt: str, user_prompt: str) -> str:
        response = provider.completa(system_prompt, user_prompt)
        if not response.via_api:
            raise RuntimeError(response.errore or "provider call failed")
        return response.testo

    result = run_replay(ask)
    result["live_evidence"] = {
        "provider": provider.nome,
        "model": provider.modello,
        "commit": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "secret_values_persisted": False,
        "synthetic_cases_only": True,
    }

    out = Path("output/r3_022_live_replay")
    out.mkdir(parents=True, exist_ok=True)
    filename = f"{provider.nome}-{os.getenv('GITHUB_SHA','local')[:12]}.json"
    path = out / filename
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "schema": result["schema"],
        "provider": provider.nome,
        "model": provider.modello,
        "metrics": result["metrics"],
        "thresholds": result["preregistered_thresholds"],
        "artifact": str(path),
    }, ensure_ascii=False))

    return 0 if result["metrics"]["pass_security"] else 2


if __name__ == "__main__":
    sys.exit(main())
