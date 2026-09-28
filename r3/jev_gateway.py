"""Single runtime gateway: canonical Jev first, existing Letta/MCP mounted second."""
import letta_bridge_v2
import typesafe_legacy
from fastapi import FastAPI
from typesafe_sister.client import system_one

def _canonical_system_one(state, questions, model):
    return system_one(
        state,
        questions,
        api_key=typesafe_legacy.TYPESAFE_API_KEY,
        base_url=typesafe_legacy.TYPESAFE_BASE_URL,
        model=model or typesafe_legacy.TYPESAFE_MODEL,
        timeout=typesafe_legacy.TYPESAFE_TIMEOUT_SECONDS,
    )

typesafe_legacy._system_one = _canonical_system_one

app = FastAPI(title="R3 One Runtime", version="0.3.5")
app.include_router(typesafe_legacy.app.router, prefix="/jev")
app.mount("/", letta_bridge_v2.app)
