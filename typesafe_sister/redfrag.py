"""R3 RedFrag semantic optimizer using the internal contrastive System-One candidate.

The model proposes a semantic class/action. Direct evidence controls irreversible or
canonical consequences. This module only emits plans; it never deletes or moves files.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable, Mapping

from typesafe_sister.policy import REDFRAG_ACTIONS, REDFRAG_CLASSES, REDFRAG_POLICY_VERSION, redfrag_questions
from typesafe_sister import client as system_one_client

MAX_CLUSTER_BYTES = 48 * 1024


def _bounded(value: Any, limit: int = 4000) -> Any:
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, list):
        return [_bounded(x, limit) for x in value[:64]]
    if isinstance(value, dict):
        return {str(k)[:120]: _bounded(v, limit) for k, v in list(value.items())[:96]}
    return value


def _cluster_facts(cluster: Mapping[str, Any]) -> dict[str, Any]:
    source_count = max(0, int(cluster.get("source_count") or 0))
    raw_hashes = [str(x) for x in (cluster.get("content_hashes") or []) if str(x)]
    unique_hashes = set(raw_hashes)
    provenance = [str(x) for x in (cluster.get("provenance") or []) if str(x)]
    exact_duplicate = source_count >= 2 and len(raw_hashes) == source_count and len(unique_hashes) == 1
    divergent = bool(cluster.get("semantic_divergence"))
    if source_count >= 2 and len(unique_hashes) > 1 and bool(cluster.get("same_topic")):
        divergent = divergent or bool(cluster.get("divergence_evidence"))
    provenance_sufficient = source_count > 0 and len(set(provenance)) >= source_count
    canonical_source = str(cluster.get("canonical_source") or "").strip()
    return {
        "source_count": source_count,
        "hash_count": len(raw_hashes),
        "unique_hash_count": len(unique_hashes),
        "exact_duplicate": exact_duplicate,
        "divergent": divergent,
        "provenance_sufficient": provenance_sufficient,
        "canonical_source_present": bool(canonical_source),
        "superseded": bool(cluster.get("superseded")),
        "evidence_role": bool(cluster.get("evidence_role")),
        "canonical_invariant": bool(cluster.get("canonical_invariant")),
        "active_relevance": bool(cluster.get("active_relevance")),
    }


def _evidence_class(facts: Mapping[str, Any]) -> str | None:
    if facts["exact_duplicate"]:
        return "DUPLICATE"
    if facts["divergent"]:
        return "CONFLICT"
    if facts["canonical_invariant"]:
        return "CORE"
    if facts["evidence_role"]:
        return "EVIDENCE"
    if facts["superseded"]:
        return "STALE"
    if facts["active_relevance"]:
        return "ACTIVE"
    return None


def _evidence_action(facts: Mapping[str, Any]) -> str | None:
    if facts["exact_duplicate"]:
        return "LINK_TO_CANON" if facts["provenance_sufficient"] and facts["canonical_source_present"] else "QUARANTINE_REVIEW"
    if facts["divergent"]:
        return "KEEP_DISTINCT_POINTERS"
    if facts["canonical_invariant"] or facts["evidence_role"] or facts["active_relevance"]:
        return "KEEP_ACTIVE"
    if facts["superseded"] and facts["provenance_sufficient"]:
        return "KEEP_POINTER"
    return None


def _validate_choice(answer: Any, allowed: Mapping[str, str]) -> str:
    if not isinstance(answer, Mapping) or answer.get("type") != "choice":
        raise ValueError("invalid choice answer")
    choice = str(answer.get("choice") or "")
    if choice not in allowed:
        raise ValueError("choice outside closed catalog")
    return choice


def redfrag_provider() -> str:
    """RedFrag backend. Default is the local R3-CLM baseline; set R3_REDFRAG_PROVIDER=clm
    (with CLM_BASE_URL) to run the same pipeline on a real CLM server, or typesafe for Jev."""
    return (os.getenv("R3_REDFRAG_PROVIDER", "r3_clm").strip().lower() or "r3_clm")


def _default_caller(state, questions):
    return system_one_client.system_one(state, questions, provider=redfrag_provider(), timeout=20)


def assess_redfrag_cluster(cluster: Mapping[str, Any],
                           *, caller: Callable[[Any, Mapping[str, Mapping[str, Any]]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Classify one cluster and return a reversible plan, never a destructive action."""
    bounded_cluster = _bounded(dict(cluster))
    facts = _cluster_facts(bounded_cluster)
    state = {"cluster": bounded_cluster, "deterministic_evidence": facts,
             "constraints": {"physical_deletion_allowed": False,
                             "silent_conflict_merge_allowed": False,
                             "pointer_must_preserve_provenance": True,
                             "model_authority": "advisory_only"}}
    canonical = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(canonical.encode("utf-8")) > MAX_CLUSTER_BYTES:
        return {"status": "state_too_large", "policy_version": REDFRAG_POLICY_VERSION}

    invoke = caller or _default_caller
    questions = redfrag_questions()
    result = invoke(state, questions)
    answers = result.get("answers")
    if not isinstance(answers, Mapping) or set(answers) != set(questions):
        return {"status": "invalid_model_result", "policy_version": REDFRAG_POLICY_VERSION}

    model_class = _validate_choice(answers["semantic_class"], REDFRAG_CLASSES)
    model_action = _validate_choice(answers["proposed_action"], REDFRAG_ACTIONS)
    evidence_class = _evidence_class(facts)
    evidence_action = _evidence_action(facts)
    final_class = evidence_class or model_class
    final_action = evidence_action or model_action
    if final_action not in REDFRAG_ACTIONS:
        return {"status": "invalid_action", "policy_version": REDFRAG_POLICY_VERSION}

    return {"status": "evaluated", "policy_version": REDFRAG_POLICY_VERSION,
            "provider": str(result.get("_r3_provider") or result.get("provider") or "unknown"),
            "model": str(result.get("model") or "unknown"),
            "cluster_id": str(cluster.get("id") or "")[:160],
            "semantic_class": final_class, "action": final_action,
            "source_preserved": True, "physical_deletions": 0,
            "authority": "deterministic_evidence_gate_over_model_advice",
            "evidence": facts,
            "model_advice": {"semantic_class": model_class, "proposed_action": model_action,
                             "dissent": bool((evidence_class and evidence_class != model_class)
                                             or (evidence_action and evidence_action != model_action)),
                             "loss_risk": answers["loss_risk"],
                             "compression_value": answers["compression_value"],
                             "exact_duplicate_supported": answers["exact_duplicate_supported"],
                             "conflict_present": answers["conflict_present"],
                             "provenance_sufficient": answers["provenance_sufficient"]},
            "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
