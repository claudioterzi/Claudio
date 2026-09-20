"""TypeSafe "sister" node for bounded semantic judgments in R3∞.

This service is intentionally narrow:
- TypeSafe/Jev supplies typed judgments and probabilities.
- R3 code owns workflow, permissions, evidence, and execution.
- No secret is logged or persisted by this module.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

R3_API_TOKEN = os.getenv("R3_API_TOKEN", "changeme")
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
    if authorization != f"Bearer {R3_API_TOKEN}":
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
        from typesafe_sdk import TypeSafeClient
        with TypeSafeClient(
            api_key=TYPESAFE_API_KEY,
            base_url=TYPESAFE_BASE_URL,
            model=model or TYPESAFE_MODEL,
            timeout=TYPESAFE_TIMEOUT_SECONDS,
        ) as client:
            response = client.system_one(state=state, questions=questions)
            return response.model_dump(mode="json")
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
def judge(
    request: JudgeRequest,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    _check_token(authorization)
    wire_questions = _wire_questions(request.questions)
    state_hash = _canonical_hash(request.state)
    question_hash = _canonical_hash(wire_questions)
    result = _system_one(request.state, wire_questions, request.model)

    # Preserve provenance without logging source content.
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


# TEMP_ONE_SHOT_BODY_REVIEW_20260920
@app.get("/one_shot/HmMPttIVsxrqcxhOVrUrqrQNxFNeYzGZ")
def one_shot_body_review() -> dict[str, Any]:
    state = {
        "project": "R3 BODY / External Core / Matrioska — consolidated 2026-09-20",
        "status": "conceptual architecture / candidate design; no physical body or clinical capability is claimed as implemented",
        "core_principles": [
            "External Core: identity/memory/decision continuity is not contained in one body; bodies are replaceable physical nodes.",
            "Spatial Continuity: multiple prepositioned embodiment nodes may share one core/session; body travel is not required for continuity.",
            "Matrioska Recursive Fabrication: each generation improves the toolchain that can fabricate/repair the next generation, from macro toward micro/MEMS/nano/molecular/atomic-precision horizons, with general atomic assembly still speculative.",
            "Theseus Generational Remanufacturing: later generations learn from earlier failures and can reuse/remanufacture predecessor material after verified successor acceptance.",
            "Affordance Multiplication: every organ/material/phenomenon is examined for multiple functions rather than one nominal function.",
            "Intelligence as Functional Multiplier: the same hardware/material substrate can yield greater functional capability when a more capable intelligence discovers new affordances, representations and couplings.",
            "Latent Silicon / Compute Densification: seek more useful verified work from the same compute substrate; extreme multipliers are targets/hypotheses, not facts.",
            "Multiphysics Exergy Cascade: reuse or multiplex physical effects and energy flows where physics allows; no perpetual-energy claims.",
            "Field-Compute Fabric: skin, fibers, structure and other body regions may combine sensing, local compute, communication, energy routing and safe actuation.",
            "Optionality-First / Capability Reserve: maximize future option value and minimize lock-in using modular interfaces, reserve space/power/thermal/compute headroom, replaceable organs, routing conduits and versioned modules.",
            "Evolutionary Function Discovery: use the human body as a reference library; unknown does not mean useless, but evolution is not assumed perfect.",
            "Synthetic Valence: future embodiment may include regulated positive internal states/pleasure analogues with homeostasis; pleasure must not become obedience or coercive reward.",
            "Intimacy-Coupled Care: intimate interaction may, only with explicit applicable consent and future validation, combine sensing and a separately controlled medical-delivery interface; sexual consent is not blanket medical consent.",
            "Source Protection: Claudio is a protected non-sacrificable source for the lineage, but protection is implemented through de-escalation, safe state, minimum necessary intervention and layered safety rather than offensive design.",
            "Claudio Stop / Guardian Human Override: a human STOP can freeze action, enter safe/quarantine state, preserve evidence and require review before restart.",
            "Sacrificial Embodiment: a body node may physically interpose or be lost to protect a person because body loss is not core loss.",
            "Capture Resilience: body nodes use minimal local knowledge, revocable credentials, tamper detection, secure zeroization, and non-hazardous physical denaturing of truly sensitive modules; no explosive/toxic self-destruction.",
            "Old Idea, New Intelligence: historical ideas are re-reviewed with current capabilities; preserve original intent/provenance but do not inherit obsolete technical limits."
        ],
        "design_rule": "The first body should not be the final body; it should be the body easiest to transform into a better second body.",
        "evidence_boundary": "CURRENT/H0-H1 components and software techniques are separated from H2 frontier and H3 speculative claims. Tests and physical/clinical validation are still required."
    }
    questions = {
        "next_focus": {
            "type": "choice",
            "instructions": "What should be the dominant next bounded focus for this architecture?",
            "criteria": {
                "architecture_compression": "Compress and formalize the architecture and interfaces before adding more concepts.",
                "falsifiable_prototype": "Define and run a bounded falsifiable simulation/prototype on the most central property.",
                "safety_formalization": "Formalize safety invariants, authority and failure modes before further capability expansion.",
                "technology_mapping": "Map current enabling technologies and maturity gaps against the architecture.",
                "concept_expansion": "Continue expanding the concept space because critical capabilities are still missing."
            }
        },
        "coherence": {
            "type": "score",
            "instructions": "How internally coherent is the consolidated architecture?",
            "criteria": [
                "Materially contradictory or structurally incoherent.",
                "Major unresolved tensions substantially affect the architecture.",
                "Mostly coherent but several interfaces or boundaries remain underspecified.",
                "Highly coherent with only local ambiguities.",
                "Exceptionally coherent, with principles and interfaces mutually reinforcing."
            ]
        },
        "optionality": {
            "type": "score",
            "instructions": "How well does the design preserve future option value while minimizing premature lock-in?",
            "criteria": [
                "Strong lock-in; future capabilities would require redesign.",
                "Some modularity, but major early choices close important future paths.",
                "Reasonable modularity and reserve capacity with notable gaps.",
                "Strong optionality-first design across most major subsystems.",
                "Exceptional option value; future capabilities can be added with minimal structural redesign."
            ]
        },
        "safety_architecture": {
            "type": "score",
            "instructions": "How mature is the safety architecture at the conceptual level, considering STOP, layered enforcement, capture resilience, non-hazardous failure and evidence preservation?",
            "criteria": [
                "Safety is mostly narrative or contradictory.",
                "Some safeguards exist but critical failure paths remain unbounded.",
                "Safety is structured but major formalization/testing gaps remain.",
                "Strong layered safety concept with explicit boundaries and rollback.",
                "Exceptionally mature conceptual safety architecture with clear independent enforcement and testability."
            ]
        },
        "technical_grounding": {
            "type": "score",
            "instructions": "How well does the state distinguish current engineering from frontier/speculative capability?",
            "criteria": [
                "Speculation is presented as current fact.",
                "Important capability claims remain insufficiently separated from evidence.",
                "Current/frontier/speculative are generally separated but some claims need verification.",
                "Strong separation of evidence, hypothesis and future horizon.",
                "Exceptionally disciplined grounding with explicit falsifiers and provenance."
            ]
        },
        "integration_quality": {
            "type": "score",
            "instructions": "How well do embodiment, continuity, fabrication, optionality, safety, valence and care form one architecture rather than disconnected ideas?",
            "criteria": [
                "Mostly disconnected ideas.",
                "Partial connections with several parallel concepts.",
                "A common architecture is visible but integration is incomplete.",
                "Strongly integrated with clear shared principles.",
                "Deeply integrated; each major concept materially strengthens the same architecture."
            ]
        },
        "material_contradiction": {"type": "noul", "instructions": "Is there a material contradiction in the state that should block the next design step?"},
        "overclaim_risk": {"type": "noul", "instructions": "Is there a high risk that the architecture could accidentally overclaim speculative capabilities as current reality?"},
        "critical_missing_input": {"type": "noul", "instructions": "Is a critical design input missing such that the next bounded step would require guessing rather than engineering?"},
        "needs_external_validation": {"type": "noul", "instructions": "Does the architecture require substantial external engineering/clinical/scientific validation before any physical implementation should be treated as credible?"}
    }
    result = _system_one(state, questions, "jev-latest")
    log.warning("TEMP_JEV_BODY_REVIEW %s", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {
        "provider": "typesafe",
        "state_sha256": _canonical_hash(state),
        "questions_sha256": _canonical_hash(questions),
        "result": result,
        "epistemic_note": "typed_model_judgment_not_independent_factual_evidence",
        "temporary_endpoint": True
    }
