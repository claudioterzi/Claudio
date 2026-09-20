"""TypeSafe "sister" service for bounded semantic judgments in R3∞."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from typing import Any, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typesafe_sister.client import system_one

R3_API_TOKEN = os.getenv("R3_API_TOKEN", "")
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")
TYPESAFE_TIMEOUT_SECONDS = float(os.getenv("TYPESAFE_TIMEOUT_SECONDS", "30"))

log = logging.getLogger("r3.typesafe_sister")
app = FastAPI(title="R3∞ TypeSafe Sister", version="0.1.0")

QuestionKind = Literal["choice", "noul", "score"]


class QuestionSpec(BaseModel):
    type: QuestionKind
    instructions: Any | None = None
    criteria: Any | None = None


class JudgeRequest(BaseModel):
    state: Any
    questions: dict[str, QuestionSpec] = Field(min_length=1)
    model: str | None = None


def _check_token(authorization: Optional[str]) -> None:
    if not R3_API_TOKEN or R3_API_TOKEN == 'changeme':
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


def _system_one(state: Any, questions: dict[str, dict[str, Any]], model: str | None) -> dict[str, Any]:
    if not TYPESAFE_API_KEY:
        raise HTTPException(status_code=503, detail="TypeSafe API non configurata: secret TYPESAFE_API_KEY assente")

    try:
        return system_one(state, questions,
            api_key=TYPESAFE_API_KEY,
            base_url=TYPESAFE_BASE_URL,
            model=model or TYPESAFE_MODEL,
            timeout=TYPESAFE_TIMEOUT_SECONDS,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("TypeSafe request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"TypeSafe upstream error: {type(exc).__name__}") from exc


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "r3-typesafe-sister",
        "provider": "typesafe",
        "configured": bool(TYPESAFE_API_KEY),
        "model": TYPESAFE_MODEL,
        "base_url": TYPESAFE_BASE_URL,
        "role": "bounded_semantic_judgment",
    }


@app.post("/judge")
def judge(request: JudgeRequest, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    _check_token(authorization)
    wire_questions = _wire_questions(request.questions)
    state_hash = _canonical_hash(request.state)
    question_hash = _canonical_hash(wire_questions)
    result = _system_one(request.state, wire_questions, request.model)
    log.info(
        "TypeSafe judgment completed state_sha256=%s questions_sha256=%s model=%s",
        state_hash,
        question_hash,
        result.get("model"),
    )
    return {
        "provider": "typesafe",
        "state_sha256": state_hash,
        "questions_sha256": question_hash,
        "result": result,
        "epistemic_note": "typed_model_judgment_not_independent_factual_evidence",
    }
