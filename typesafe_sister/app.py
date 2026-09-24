"""R3 sister service for bounded typed semantic judgments."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from typing import Any, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typesafe_sister.client import TypeSafeNotConfigured, configured, system_one

R3_API_TOKEN = os.getenv("R3_API_TOKEN", "")
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")
TYPESAFE_TIMEOUT_SECONDS = float(os.getenv("TYPESAFE_TIMEOUT_SECONDS", "30"))
R3_JUDGE_MODE = os.getenv("R3_JUDGE_MODE", "off").strip().lower()
R3_JUDGE_BASE_URL = os.getenv("R3_JUDGE_BASE_URL", "http://127.0.0.1:8017")

log = logging.getLogger("r3.typesafe_sister")
app = FastAPI(title="R3∞ Sister Judge", version="0.2.0")

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


def _system_one(state: Any, questions: dict[str, dict[str, Any]], model: str | None) -> dict[str, Any]:
    try:
        return system_one(
            state,
            questions,
            api_key=TYPESAFE_API_KEY,
            base_url=TYPESAFE_BASE_URL,
            model=model or TYPESAFE_MODEL,
            timeout=TYPESAFE_TIMEOUT_SECONDS,
        )
    except TypeSafeNotConfigured as exc:
        raise HTTPException(status_code=503, detail="Nessun backend typed-judge disponibile/adottato") from exc
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Typed-judge request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"Typed-judge upstream error: {type(exc).__name__}") from exc


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "r3-sister-judge",
        "router": "R3-JUDGE/1",
        "configured": configured(),
        "r3_judge_mode": R3_JUDGE_MODE,
        "r3_judge_base_url": R3_JUDGE_BASE_URL,
        "typesafe_configured": bool(TYPESAFE_API_KEY),
        "typesafe_model": TYPESAFE_MODEL,
        "role": "bounded_semantic_judgment",
        "epistemic_class": "IPOTESI",
    }


@app.post("/judge")
def judge(request: JudgeRequest, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    _check_token(authorization)
    wire_questions = _wire_questions(request.questions)
    state_hash = _canonical_hash(request.state)
    question_hash = _canonical_hash(wire_questions)
    result = _system_one(request.state, wire_questions, request.model)
    meta = result.get("x_r3") if isinstance(result.get("x_r3"), dict) else {}
    log.info(
        "R3 judgment completed state_sha256=%s questions_sha256=%s provider=%s model=%s",
        state_hash,
        question_hash,
        meta.get("provider"),
        result.get("model"),
    )
    return {
        "provider": meta.get("provider") or "unknown_typed_judge",
        "state_sha256": state_hash,
        "questions_sha256": question_hash,
        "result": result,
        "epistemic_class": "IPOTESI",
        "factual_authority": False,
        "falsification": meta.get("falsification") or {},
        "evidence_group_sha256": meta.get("evidence_group_sha256"),
        "independent_confirmation": False,
        "epistemic_note": "typed_model_judgment_not_independent_factual_evidence",
    }
