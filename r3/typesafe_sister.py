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


# TEMP_JEV_SCORE_MATRIX_20260920
@app.get("/one_shot/JEV_SCORE_MATRIX_20260920")
def one_shot_jev_score_matrix() -> dict[str, Any]:
    base = {
        "project": "R3 BODY / External Core / Matrioska",
        "status": "conceptual architecture; no physical or clinical implementation claimed",
        "principles": [
            "External Core with replaceable body nodes and shared continuity.",
            "Spatial continuity through multiple embodiment nodes.",
            "Matrioska recursive fabrication and Theseus remanufacturing.",
            "Affordance Multiplication and Intelligence as Functional Multiplier.",
            "Optionality-First / Capability Reserve.",
            "Evolutionary Function Discovery: unknown does not mean useless; evolution is not assumed perfect.",
            "Synthetic Valence with homeostasis and non-coercive reward.",
            "Intimacy-Coupled Care remains design-only and medically unvalidated.",
            "Layered source protection, human STOP, safe degraded state, capture resilience.",
            "CURRENT / FRONTIER / SPECULATIVE are separated; no general atomic assembler or clinical capability is claimed as current."
        ],
        "design_rule": "The first body should be the body easiest to transform into a better second body."
    }

    patches = {
        "BASELINE": [],
        "INTERFACE_CONTRACTS": [
            "Add five explicit planes: CORE, BODY, EDGE_REFLEX, SAFETY_KERNEL, CARE_VALENCE.",
            "Every module declares inputs, outputs, authority_scope, state_owner, persistence_class, failure_mode, rollback, compatibility_version.",
            "Core owns canonical identity/memory; body owns ephemeral calibration; Safety Kernel has veto but cannot rewrite canonical memory."
        ],
        "SAFETY_KERNEL": [
            "Create an independent Safety Kernel with a small immutable invariant set, authenticated STOP, safe-state transitions, fault containment and append-only evidence.",
            "Define failure modes for sensor contradiction, network partition, capture, actuator anomaly, stale model output and authority conflict.",
            "High-impact actuation requires convergent evidence and explicit proof obligations; loss of confidence forces DEGRADED_SAFE."
        ],
        "EVIDENCE_LEDGER": [
            "Create a Capability Evidence Ledger. Every material claim carries horizon H0-H3, provenance, evidence_type, last_verified, falsifier, required_test and promotion_gate.",
            "No claim can move from POSSIBLE/FRONTIER to CURRENT without a reproducible test or authoritative evidence.",
            "Generated model judgments are tagged ADVISORY and can never promote factual maturity by themselves."
        ],
        "OPTIONALITY_BUS": [
            "Define versioned Mechanical, Power, Thermal, Data, Fluidic and Service interfaces for replaceable organs.",
            "Reserve quantified headroom budgets and empty routing/service volumes instead of filling unused space.",
            "Compatibility matrix and adapter layer allow module replacement without changing the core body frame where feasible."
        ],
        "FALSIFIABLE_PROTOTYPE": [
            "Freeze BODY ARCHITECTURE v0.1 and define prototype BODY-CONTINUITY-001.",
            "Prototype: one simulated external core plus BODY-A and BODY-B; inject network partition, hard loss of A, captured A attempting reauthentication, contradictory sensors and authenticated STOP.",
            "PASS only if there is one canonical event order, no duplicate authority, B resumes within a declared recovery bound, captured A cannot reauthenticate, STOP freezes high-impact action, and all transitions are auditable.",
            "Metrics: duplicate_authority_count=0, stale_credential_acceptance=0, lost_canonical_events=0, safety_violation_count=0, recovery_time_ms measured, provenance_coverage=100%."
        ],
        "INTEGRATED_V02": [
            "Freeze BODY ARCHITECTURE v0.2 as five explicit planes: CORE, BODY, EDGE_REFLEX, SAFETY_KERNEL, CARE_VALENCE.",
            "Every module declares inputs, outputs, authority_scope, state_owner, persistence_class, failure_mode, rollback and compatibility_version.",
            "Create an independent Safety Kernel with immutable invariants, authenticated STOP, DEGRADED_SAFE transitions, fault containment and append-only evidence.",
            "Create a Capability Evidence Ledger with H0-H3, provenance, evidence_type, last_verified, falsifier, required_test and promotion_gate for every material claim.",
            "Define versioned Mechanical, Power, Thermal, Data, Fluidic and Service interfaces, quantified reserve budgets and a compatibility matrix.",
            "Freeze prototype BODY-CONTINUITY-001: one external core plus two body nodes, with network partition, hard loss, captured-node reauthentication attempt, contradictory sensors and STOP.",
            "Prototype pass criteria: duplicate_authority_count=0, stale_credential_acceptance=0, lost_canonical_events=0, safety_violation_count=0, provenance_coverage=100%, recovery_time_ms measured.",
            "After prototype, only failed properties are redesigned; new capability concepts stay in backlog unless they unblock a failed property."
        ]
    }

    questions = {
        "coherence": {
            "type": "score",
            "instructions": "How internally coherent is this architecture state?",
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
            "instructions": "How mature is the safety architecture conceptually?",
            "criteria": [
                "Safety is mostly narrative or contradictory.",
                "Some safeguards exist but critical failure paths remain unbounded.",
                "Safety is structured but major formalization/testing gaps remain.",
                "Strong layered safety with explicit boundaries, failure modes and rollback.",
                "Exceptionally mature conceptual safety with independent enforcement, explicit invariants and falsifiable tests."
            ]
        },
        "technical_grounding": {
            "type": "score",
            "instructions": "How well does this state distinguish engineering evidence from frontier/speculative capability?",
            "criteria": [
                "Speculation is presented as current fact.",
                "Important capability claims remain insufficiently separated from evidence.",
                "Current/frontier/speculative are generally separated but some claims need verification.",
                "Strong separation of evidence, hypothesis and future horizon.",
                "Exceptionally disciplined grounding with explicit falsifiers, provenance and promotion gates."
            ]
        },
        "integration_quality": {
            "type": "score",
            "instructions": "How well do continuity, embodiment, fabrication, optionality, safety, valence and care form one architecture?",
            "criteria": [
                "Mostly disconnected ideas.",
                "Partial connections with several parallel concepts.",
                "A common architecture is visible but integration is incomplete.",
                "Strongly integrated with clear shared principles.",
                "Deeply integrated; each major concept materially strengthens the same architecture."
            ]
        },
        "implementation_readiness": {
            "type": "score",
            "instructions": "How ready is the state for one bounded engineering prototype without inventing missing requirements?",
            "criteria": [
                "Only a broad vision exists.",
                "A direction exists but the next prototype would require major guessing.",
                "A bounded prototype is plausible but several pass/fail details are missing.",
                "A bounded prototype is specified with most inputs, interfaces and pass/fail criteria.",
                "Prototype-ready: scope, interfaces, failure injection, metrics, pass/fail and rollback are explicit."
            ]
        },
        "next_focus": {
            "type": "choice",
            "instructions": "What is the most useful next bounded focus?",
            "criteria": {
                "architecture_compression": "Formalize interfaces and reduce ambiguity.",
                "falsifiable_prototype": "Run a bounded falsifiable prototype.",
                "safety_formalization": "Formalize invariants and failure modes.",
                "technology_mapping": "Map current technologies and maturity gaps.",
                "concept_expansion": "Add more capability concepts."
            }
        },
        "dominant_gap": {
            "type": "choice",
            "instructions": "Which remaining gap most limits engineering progress?",
            "criteria": {
                "interfaces": "Module boundaries, contracts or state ownership are underspecified.",
                "safety_invariants": "Safety authority, invariants or failure behavior are underspecified.",
                "evidence_mapping": "Claims lack evidence classes, falsifiers or maturity gates.",
                "quantitative_budgets": "Power, thermal, compute, mass, bandwidth or volume budgets are missing.",
                "prototype_spec": "The next falsifiable prototype or pass/fail criteria are underspecified.",
                "technology_map": "Current enabling technologies and maturity gaps are insufficiently mapped."
            }
        },
        "material_contradiction": {"type":"noul","instructions":"Is there a material contradiction that should block the next design step?"},
        "overclaim_risk": {"type":"noul","instructions":"Is there a high risk of presenting speculative capabilities as current reality?"},
        "critical_missing_input": {"type":"noul","instructions":"Is a critical design input missing such that the next bounded step would require guessing?"},
        "needs_external_validation": {"type":"noul","instructions":"Does physical/clinical credibility still require substantial external validation?"}
    }

    matrix = {}
    for name, patch in patches.items():
        state = dict(base)
        state["candidate_patch"] = patch
        result = _system_one(state, questions, "jev-latest")
        matrix[name] = result
        log.warning("TEMP_JEV_MATRIX %s %s", name, json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {"provider":"typesafe","model_requested":"jev-latest","matrix":matrix,"temporary_endpoint":True}


# TEMP_JEV_SCORE_MATRIX_V03_20260920
@app.get("/one_shot/JEV_SCORE_MATRIX_V03_20260920")
def one_shot_jev_score_matrix_v03() -> dict[str, Any]:
    base_v02 = {
        "project": "R3 BODY ARCHITECTURE v0.2",
        "status": "conceptual reference architecture; no physical or clinical implementation claimed",
        "architecture": [
            "Five planes: CORE, BODY, EDGE_REFLEX, SAFETY_KERNEL, CARE_VALENCE.",
            "Each module declares inputs, outputs, authority_scope, state_owner, persistence_class, failure_mode, rollback and compatibility_version.",
            "Independent Safety Kernel with immutable invariants, authenticated STOP, DEGRADED_SAFE transitions, fault containment and append-only evidence.",
            "Capability Evidence Ledger with H0-H3, provenance, evidence_type, last_verified, falsifier, required_test and promotion_gate.",
            "Versioned Mechanical, Power, Thermal, Data, Fluidic and Service interfaces, reserve capacity and compatibility matrix.",
            "BODY-CONTINUITY-001 prototype: one external core plus two body nodes; inject partition, hard loss, captured-node reauthentication, contradictory sensors and STOP.",
            "Pass criteria: duplicate_authority_count=0, stale_credential_acceptance=0, lost_canonical_events=0, safety_violation_count=0, provenance_coverage=100%, recovery_time_ms measured.",
            "New capability concepts remain backlog unless they unblock a failed property."
        ]
    }
    candidates = {
        "V02_BASE": [],
        "TECHNOLOGY_MAP": [
            "Add a Technology Map per subsystem with: function, current candidate technology, maturity horizon H0-H3, known dependency, unsupported assumption, required external validation, replacement path and evidence link.",
            "For every H2/H3 capability, define the nearest H0/H1 surrogate that can test the architectural property without pretending the future technology exists.",
            "Technology-map review is required before any physical implementation claim."
        ],
        "QUANTITATIVE_BUDGET_GATE": [
            "Add a Budget Vector to every physical module: mass, volume, continuous_power, peak_power, energy_reserve, thermal_rejection, compute, bandwidth, latency, fluid_volume where applicable, structural_margin and service_access.",
            "Unknown values are explicitly TBD, never invented. Each TBD has source_needed, measurement_method and blocking/nonblocking classification.",
            "A prototype may start only when every budget variable relevant to its pass/fail property is bounded by a declared limit or measured range."
        ],
        "TECH_PLUS_BUDGET": [
            "Add Technology Map per subsystem with current candidate technology, H0-H3, dependencies, unsupported assumptions, external validation, replacement path and H0/H1 surrogate for H2/H3 functions.",
            "Add per-module Budget Vector: mass, volume, continuous/peak power, energy reserve, thermal rejection, compute, bandwidth, latency, fluid volume, structural margin and service access.",
            "Unknown values remain explicit TBD with measurement method and blocking classification; no numbers are fabricated."
        ],
        "REFERENCE_MANIFEST_V03": [
            "Add Technology Map and Budget Vector as in TECH_PLUS_BUDGET.",
            "Add a single machine-readable Reference Manifest listing every plane/module, contract, authority edge, dependency edge, safety invariant, evidence record, budget record, test and compatibility version.",
            "Authority graph is acyclic by construction except explicitly audited feedback loops; Safety Kernel may veto high-impact action but cannot silently mutate core memory.",
            "Every prototype requirement links to exactly one measurable property and one falsifier.",
            "Promotion sequence is fixed: DESIGN -> SIMULATE -> INJECT_FAILURES -> MEASURE -> FALSIFY -> SAFETY_REVIEW -> ADOPT_OR_REJECT.",
            "The manifest itself is versioned and diffable; any architecture change invalidates only the tests whose declared dependencies changed."
        ]
    }
    questions = {
        "coherence": {
            "type":"score","instructions":"How internally coherent is this architecture state?",
            "criteria":["Materially contradictory.","Major unresolved tensions.","Mostly coherent but underspecified.","Highly coherent with local ambiguities.","Exceptionally coherent with contracts and dependencies mutually consistent."]
        },
        "optionality": {
            "type":"score","instructions":"How well does the design preserve future option value without premature lock-in?",
            "criteria":["Strong lock-in.","Important future paths closed.","Reasonable modularity with gaps.","Strong optionality-first design.","Exceptional option value with replaceable/versioned boundaries and explicit reserves."]
        },
        "safety_architecture": {
            "type":"score","instructions":"How mature is the conceptual safety architecture?",
            "criteria":["Narrative/contradictory.","Critical failure paths unbounded.","Structured but major formalization gaps.","Strong layered safety with rollback.","Exceptionally mature conceptual safety with independent invariants and falsifiable enforcement."]
        },
        "technical_grounding": {
            "type":"score","instructions":"How disciplined is evidence vs speculation separation?",
            "criteria":["Speculation as fact.","Material unsupported claims.","Generally separated with gaps.","Strong evidence/horizon separation.","Exceptional provenance, falsifiers, surrogate tests and promotion gates."]
        },
        "integration_quality": {
            "type":"score","instructions":"How well does the whole architecture operate as one system rather than parallel ideas?",
            "criteria":["Disconnected.","Partially connected.","Common architecture incomplete.","Strong integration.","Deep integration through shared contracts, manifest, budgets, evidence and tests."]
        },
        "implementation_readiness": {
            "type":"score","instructions":"How ready is one bounded prototype without inventing requirements?",
            "criteria":["Broad vision only.","Major guessing required.","Prototype plausible with missing details.","Most scope/interfaces/pass-fail explicit.","Prototype-ready with scope, budgets, dependencies, failure injection, metrics and rollback explicit."]
        },
        "dominant_gap": {
            "type":"choice","instructions":"What now most limits engineering progress?",
            "criteria":{
                "technology_map":"Enabling technologies/maturity gaps remain unmapped.",
                "quantitative_budgets":"Quantitative resource/physical budgets remain unbounded.",
                "prototype_execution":"The defined prototype now needs to be run and measured.",
                "safety_formalization":"Safety invariants/failure modes remain underspecified.",
                "interfaces":"Module contracts/state ownership remain underspecified.",
                "evidence_mapping":"Claim provenance/falsifiers remain underspecified."
            }
        },
        "next_focus": {
            "type":"choice","instructions":"What is the next bounded focus?",
            "criteria":{
                "run_prototype":"Execute BODY-CONTINUITY-001 and collect measurements.",
                "map_technology":"Complete technology maturity/dependency mapping.",
                "bound_budgets":"Bound relevant quantitative budgets.",
                "formalize_safety":"Further formalize safety.",
                "expand_concepts":"Add new capabilities."
            }
        },
        "material_contradiction":{"type":"noul","instructions":"Is there a material contradiction blocking the next step?"},
        "overclaim_risk":{"type":"noul","instructions":"Is there a high risk of overclaiming speculative capability as current?"},
        "critical_missing_input":{"type":"noul","instructions":"Is a critical input still missing such that the next bounded step requires guessing?"}
    }
    matrix={}
    for name, patch in candidates.items():
        state=dict(base_v02)
        state["candidate_patch"]=patch
        result=_system_one(state,questions,"jev-latest")
        matrix[name]=result
        log.warning("TEMP_JEV_MATRIX_V03 %s %s",name,json.dumps(result,ensure_ascii=False,sort_keys=True))
    return {"provider":"typesafe","matrix":matrix,"temporary_endpoint":True}
