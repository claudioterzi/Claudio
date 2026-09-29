"""R3∞ provider-neutral System One sister for the combined Railway runtime.

Mounted under /jev by the historical gateway to preserve compatibility while
routing to CLM or TypeSafe/Jev through the shared canonical client.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from typing import Any, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from typesafe_sister.client import (
    SystemOneCapabilityUnavailable,
    SystemOneNotConfigured,
    backend_info,
    rank,
    system_one,
)

R3_API_TOKEN = os.getenv("R3_API_TOKEN", "")
SYSTEMONE_TIMEOUT_SECONDS = float(
    os.getenv("R3_SYSTEMONE_TIMEOUT_SECONDS", os.getenv("TYPESAFE_TIMEOUT_SECONDS", "30"))
)

log = logging.getLogger("r3.systemone_sister")
app = FastAPI(title="R3∞ System One Sister", version="0.3.0")

QuestionKind = Literal["choice", "noul", "score"]


class QuestionSpec(BaseModel):
    type: QuestionKind
    instructions: Any | None = None
    criteria: Any | None = None


class JudgeRequest(BaseModel):
    state: Any
    questions: dict[str, QuestionSpec] = Field(min_length=1)
    model: str | None = None


class RankRequest(BaseModel):
    context: Any
    question: str
    answers: list[str] = Field(min_length=1)
    model: str | None = None


def _check_token(authorization: Optional[str]) -> None:
    if not R3_API_TOKEN or R3_API_TOKEN == "changeme":
        raise HTTPException(status_code=503, detail="Token del servizio non configurato")
    if not authorization or not secrets.compare_digest(authorization, f"Bearer {R3_API_TOKEN}"):
        raise HTTPException(status_code=401, detail="Token non valido")


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _wire_questions(questions: dict[str, QuestionSpec]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, q in questions.items():
        body: dict[str, Any] = {"type": q.type}
        if q.instructions is not None:
            body["instructions"] = q.instructions
        if q.type == "choice":
            if not isinstance(q.criteria, dict) or not q.criteria:
                raise HTTPException(status_code=422, detail=f"choice {name!r} requires non-empty object criteria")
            body["criteria"] = q.criteria
        elif q.type == "score":
            if not isinstance(q.criteria, list) or not q.criteria:
                raise HTTPException(status_code=422, detail=f"score {name!r} requires non-empty ordered list criteria")
            body["criteria"] = q.criteria
        elif q.criteria is not None:
            if not isinstance(q.criteria, dict):
                raise HTTPException(status_code=422, detail=f"noul {name!r} criteria must be an object when supplied")
            body["criteria"] = q.criteria
        out[name] = body
    return out


@app.get("/health")
def health() -> dict[str, Any]:
    info = backend_info()
    return {
        "status": "healthy",
        "service": "r3-typesafe-sister",
        "provider": info["provider"],
        "configured": info["configured"],
        "model": info["model"],
        "base_url": info["base_url"],
        "role": "bounded_semantic_judgment",
        "api_contract": "typesafe-compatible-systemone",
        "native_rank": info["provider"] == "clm",
    }


@app.post("/judge")
def judge(request: JudgeRequest, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    _check_token(authorization)
    wire_questions = _wire_questions(request.questions)
    state_hash = _canonical_hash(request.state)
    question_hash = _canonical_hash(wire_questions)
    try:
        result = system_one(
            request.state,
            wire_questions,
            model=request.model,
            timeout=SYSTEMONE_TIMEOUT_SECONDS,
        )
    except SystemOneNotConfigured as exc:
        raise HTTPException(status_code=503, detail="System One backend non configurato") from exc
    except Exception as exc:
        log.warning("System One request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"System One upstream error: {type(exc).__name__}") from exc

    provider = str(result.get("_r3_provider") or "unknown")
    log.info(
        "System One judgment completed state_sha256=%s questions_sha256=%s provider=%s model=%s",
        state_hash,
        question_hash,
        provider,
        result.get("model"),
    )
    return {
        "provider": provider,
        "state_sha256": state_hash,
        "questions_sha256": question_hash,
        "result": result,
        "epistemic_note": "typed_model_judgment_not_independent_factual_evidence",
    }


@app.post("/rank")
def rank_candidates(request: RankRequest, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    _check_token(authorization)
    context_hash = _canonical_hash(request.context)
    question_hash = _canonical_hash(request.question)
    answers_hash = _canonical_hash(request.answers)
    try:
        result = rank(
            request.context,
            request.question,
            request.answers,
            model=request.model,
            timeout=SYSTEMONE_TIMEOUT_SECONDS,
        )
    except SystemOneNotConfigured as exc:
        raise HTTPException(status_code=503, detail="System One backend non configurato") from exc
    except SystemOneCapabilityUnavailable as exc:
        raise HTTPException(status_code=501, detail="Native rank non disponibile sul backend attivo") from exc
    except Exception as exc:
        log.warning("System One rank failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"System One upstream error: {type(exc).__name__}") from exc

    provider = str(result.get("_r3_provider") or "unknown")
    log.info(
        "System One rank completed context_sha256=%s question_sha256=%s answers_sha256=%s provider=%s model=%s",
        context_hash,
        question_hash,
        answers_hash,
        provider,
        result.get("model"),
    )
    return {
        "provider": provider,
        "context_sha256": context_hash,
        "question_sha256": question_hash,
        "answers_sha256": answers_hash,
        "result": result,
        "epistemic_note": "ranked_model_judgment_not_independent_factual_evidence",
    }
