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

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize router and orchestrator
router = LLMRouter()
orchestrator = RRRemeRgenOrchestrator(router)


class ComposeRequest(BaseModel):
    """Request for app composition."""
    prompt: str
    user_id: str = "anonymous"
    advanced_options: dict = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    providers: dict
    models_available: int


class ModelsResponse(BaseModel):
    """Available models and providers."""
    providers: list[str]
    model_assignments: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and provider availability."""
    providers = {}
    total_models = 0

    for provider, config in router.providers.items():
        is_healthy = router._is_provider_healthy(provider)
        providers[provider] = {
            "healthy": is_healthy,
            "models": config["models"],
            "priority": config["priority"]
        }
        if is_healthy:
            total_models += len(config["models"])

    return HealthResponse(
        status="ok",
        providers=providers,
        models_available=total_models
    )


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available LLM models and task assignments."""
    providers = list(router.providers.keys())
    assignments = router._get_task_assignments()

    return ModelsResponse(
        providers=providers,
        model_assignments=assignments
    )


async def compose_event_stream(
    prompt: str,
    user_id: str,
    advanced_options: dict
) -> AsyncGenerator[str, None]:
    """Stream composition events from orchestrator."""
    try:
        logger.info(f"Starting composition for user {user_id}: {prompt[:50]}...")

        async for event in orchestrator.compose_app(prompt, advanced_options):
            # Convert event to JSON and send as SSE
            yield f"data: {json.dumps(event)}\n\n"

            # Small delay to allow streaming
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error(f"Composition error: {str(e)}", exc_info=True)
        error_event = {
            "type": "error",
            "stage": "orchestration",
            "message": str(e),
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

    logger.info(f"Compose request: {request.prompt[:100]}...")

    return StreamingResponse(
        compose_event_stream(
            request.prompt,
            request.user_id,
            request.advanced_options
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
        "valid": results.get("score", 0) >= 70,
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
    # Placeholder for deployment logic
    return {
        "status": "pending",
        "message": "Deployment queued",
        "github_repo": deployment_config.get("repository_url"),
        "vercel_link": f"https://vercel.com/projects/{deployment_config.get('vercel_project')}"
    }


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
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
