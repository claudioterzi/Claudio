"""RedFrag manifest pipeline: SOURCE -> FINGERPRINT -> CLUSTER -> PLAN -> CONTEXT MAP.

Read-only by construction. It never mutates, deletes, moves or overwrites source files.
Callers provide content/provenance records; the output is a reversible context manifest.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from typesafe_sister.redfrag import assess_redfrag_cluster

MAX_RECORDS = 2048
MAX_CONTENT_CHARS = 200_000


def _fingerprint(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _record(raw: Mapping[str, Any]) -> dict[str, Any]:
    source_id = str(raw.get("id") or "").strip()
    provenance = str(raw.get("provenance") or "").strip()
    if not source_id or not provenance:
        raise ValueError("every RedFrag source requires id and provenance")
    content = str(raw.get("content") or "")
    fingerprint = _fingerprint(content)
    if raw.get("content_hash") and str(raw["content_hash"]) != fingerprint:
        raise ValueError("RedFrag content_hash does not match full source content")
    return {
        "id": source_id[:240],
        "logical_id": str(raw.get("logical_id") or source_id)[:240],
        "content": content[:MAX_CONTENT_CHARS],
        "content_truncated": len(content) > MAX_CONTENT_CHARS,
        "hash": fingerprint,
        "provenance": provenance[:1000],
        "canonical": bool(raw.get("canonical")),
        "canonical_invariant": bool(raw.get("canonical_invariant")),
        "evidence_role": bool(raw.get("evidence_role")),
        "active_relevance": bool(raw.get("active_relevance")),
        "superseded": bool(raw.get("superseded")),
        "semantic_divergence": bool(raw.get("semantic_divergence")),
    }


def build_clusters(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    items = [_record(x) for x in records]
    return _clusters_from_records(items)


def _clusters_from_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(items) > MAX_RECORDS:
        raise ValueError("too many RedFrag records")
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(item["logical_id"], []).append(item)

    clusters = []
    for logical_id, group in groups.items():
        hashes = [x["hash"] for x in group]
        canonical = next((x for x in group if x["canonical"]), None)
        divergent_evidence = any(x["semantic_divergence"] for x in group)
        clusters.append({
            "id": logical_id,
            "name": logical_id,
            "source_count": len(group),
            "content_hashes": hashes,
            "provenance": [x["provenance"] for x in group],
            "canonical_source": canonical["provenance"] if canonical else "",
            "same_topic": len(group) > 1,
            "semantic_divergence": divergent_evidence,
            "divergence_evidence": divergent_evidence,
            "canonical_invariant": any(x["canonical_invariant"] for x in group),
            "evidence_role": any(x["evidence_role"] for x in group),
            "active_relevance": any(x["active_relevance"] for x in group),
            "superseded": all(x["superseded"] for x in group),
            "source_ids": [x["id"] for x in group],
        })
    return clusters


def plan_context(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    items = [_record(x) for x in records]
    clusters = _clusters_from_records(items)
    plans = [assess_redfrag_cluster(cluster) for cluster in clusters]
    by_logical = {str(p["cluster_id"]): p for p in plans}

    active, pointers, quarantined = [], [], []
    for item in items:
        plan = by_logical[item["logical_id"]]
        action = plan["action"]
        pointer = {"source_id": item["id"], "provenance": item["provenance"], "sha256": item["hash"]}
        if action == "KEEP_ACTIVE" and item["content_truncated"]:
            quarantined.append({**pointer, "logical_id": item["logical_id"],
                                "action": "QUARANTINE_REVIEW", "reason": "content_exceeds_context_limit"})
        elif action == "KEEP_ACTIVE":
            active.append({**pointer, "content": item["content"], "logical_id": item["logical_id"]})
        elif action in {"KEEP_POINTER", "LINK_TO_CANON", "KEEP_DISTINCT_POINTERS"}:
            pointers.append({**pointer, "logical_id": item["logical_id"], "action": action})
        else:
            quarantined.append({**pointer, "logical_id": item["logical_id"], "action": action})

    input_chars = sum(len(x["content"]) for x in items)
    active_chars = sum(len(x["content"]) for x in active)
    reduction = 0.0 if input_chars == 0 else 1.0 - (active_chars / input_chars)
    manifest = {
        "schema": "R3-REDFRAG-CONTEXT/0.1",
        "source_records": len(items),
        "logical_clusters": len(clusters),
        "active_records": active,
        "pointers": pointers,
        "quarantined": quarantined,
        "plans": plans,
        "context_reduction_ratio": round(reduction, 6),
        "physical_deletions": 0,
        "source_mutations": 0,
        "reversible": True,
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return manifest
