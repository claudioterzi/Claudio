#!/usr/bin/env python3
"""
RRREMERGEN API Server — FastAPI backend for web app auto-composition.

Endpoints:
  POST /api/rrremergen/compose - Stream app composition pipeline
  GET  /health                  - Health check
  GET  /models                  - Available LLM models and providers
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from typing import Literal

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

from rrremergen.api.orchestrator import RRRemeRgenOrchestrator
from rrremergen.api.router import LLMRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RRREMERGEN API",
    description="Multi-agent web app composer with LLM routing",
    version="1.0.0"
)

# CORS configuration for frontend access
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize router and orchestrator
router = LLMRouter()


class ComposeOptions(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mode: Literal['local', 'demo', 'cloud'] = 'local'


class ComposeRequest(BaseModel):
    """Request for app composition."""
    prompt: str = Field(min_length=10, max_length=4000)
    user_id: str = "anonymous"
    advanced_options: ComposeOptions = Field(default_factory=ComposeOptions)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    providers: dict
    models_available: int
    availability_verified: bool = False
    local_runner_configured: bool


class ModelsResponse(BaseModel):
    """Available models and providers."""
    providers: list[str]
    model_assignments: dict
    default_mode: str = 'local'
    local_model: str = 'ollama-local/raffaello-r3:3b'
    availability_verified: bool = False


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and provider availability."""
    providers = {}
    total_models = 0

    for provider, config in router.providers.items():
        is_healthy = router._is_provider_healthy(provider)
        providers[provider] = {
            "configured": is_healthy,
            "reachable_verified": False,
            "models": config["models"],
            "priority": config["priority"]
        }
        if is_healthy:
            total_models += len(config["models"])

    return HealthResponse(
        status="ok",
        providers=providers,
        models_available=total_models,
        local_runner_configured=router.local_runner.is_file()
    )


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available LLM models and task assignments."""
    providers = list(router.providers.keys())
    assignments = router._get_task_assignments()

    return ModelsResponse(
        providers=['local', 'demo'] + providers,
        model_assignments=assignments
    )


async def compose_event_stream(
    prompt: str,
    user_id: str,
    advanced_options: dict
) -> AsyncGenerator[str, None]:
    """Stream composition events from orchestrator."""
    try:
        request_router = LLMRouter(mode=advanced_options.get('mode', 'local'))
        orchestrator = RRRemeRgenOrchestrator(request_router)
        async for event in orchestrator.compose_app(prompt, advanced_options):
            # Convert event to JSON and send as SSE
            yield f"data: {json.dumps(event)}\n\n"

            # Small delay to allow streaming
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error("Composition error: %s", type(e).__name__)
        error_event = {
            "type": "error",
            "stage": "orchestration",
            "message": "Composizione interrotta prima del completamento.",
            "timestamp": __import__('time').time()
        }
        yield f"data: {json.dumps(error_event)}\n\n"


@app.post("/api/rrremergen/compose")
async def compose_app(request: ComposeRequest):
    """
    Compose a web application from natural language description.

    Returns: Server-Sent Events stream of composition progress
    """
    if not request.prompt or len(request.prompt.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 10 characters"
        )

    return StreamingResponse(
        compose_event_stream(
            request.prompt,
            request.user_id,
            request.advanced_options.model_dump()
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for real-time streaming
        }
    )


@app.post("/api/rrremergen/validate")
async def validate_generated_app(app_code: dict):
    """
    Validate generated application code.

    Request body:
      {
        "frontend": "...React code...",
        "backend": "...FastAPI code...",
        "database": "...MongoDB schema..."
      }
    """
    from rrremergen.agents.pm import PM

    pm = PM(router)

    # Create a minimal blueprint for validation
    class MinimalBlueprint:
        ui_components = []
        api_routes = []
        requirements = []

    results = await pm.validate_and_debug(
        MinimalBlueprint(),
        app_code,
        {},
        "Code validation"
    )

    return {
        "valid": results['is_valid'],
        "verification_mode": results['verification_mode'],
        "runtime_verified": False,
        "score": results.get("score", 0),
        "issues": results.get("issues", []),
        "warnings": results.get("warnings", []),
        "timestamp": __import__('time').time()
    }


@app.post("/api/rrremergen/deploy")
async def deploy_app(deployment_config: dict):
    """
    Deploy generated application.

    Request body:
      {
        "app_name": "my-app",
        "repository_url": "github.com/...",
        "vercel_project": "my-project"
      }
    """
    raise HTTPException(status_code=501, detail="Deployment non implementato: nessun lavoro accodato.")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "RRREMERGEN API",
        "version": "1.0.0",
        "endpoints": {
            "compose": "POST /api/rrremergen/compose",
            "health": "GET /health",
            "models": "GET /models",
            "validate": "POST /api/rrremergen/validate",
            "deploy": "POST /api/rrremergen/deploy"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("RRREMERGEN_PORT", "8000"))
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info"
    )
