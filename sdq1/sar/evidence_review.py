"""Deterministic review of externally supplied evidence; no model/API calls.

Concept: Claudio Terzi, R3 infinity. This gate validates records, not truth.
Run: python sdq1/sar/evidence_review.py examples/astra_review.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: nonempty text required")
    return value


def _rating(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: numeric rating required")
    if not math.isfinite(value) or not 1 <= value <= 10:
        raise ValueError(f"{name}: finite rating in [1, 10] required")
    return value


def review(record):
    """Rank eligible candidates; missing/failed checks never count as success.

    Ratings are declared judgments. Evidence and check references must be
    inspected by the caller. A 'ready_for_review' result never authorizes merge.
    """
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    for key in ("objective", "revision", "model", "acceptance_criterion"):
        _text(record.get(key), key)
    candidates = record.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("at least one candidate required")
    seen = set()
    results = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be an object")
        cid = _text(candidate.get("id"), "id")
        if cid in seen:
            raise ValueError("duplicate candidate id")
        seen.add(cid)
        _text(candidate.get("proposal"), "proposal")
        _text(candidate.get("falsifier"), "falsifier")
        ratings = [_rating(candidate.get(k), k) for k in ("impact", "speed", "risk")]
        reasons = []
        evidence = candidate.get("evidence", [])
        if not isinstance(evidence, list):
            raise ValueError("evidence must be a list")
        evidence_ids = set()
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError("evidence item must be an object")
            eid = _text(item.get("id"), "evidence.id")
            if eid in evidence_ids:
                raise ValueError("duplicate evidence id")
            evidence_ids.add(eid)
            for key in ("source", "observation"):
                _text(item.get(key), f"evidence.{key}")
            if item.get("kind") not in {"source", "test", "measurement", "simulation"}:
                raise ValueError("invalid evidence kind")
        checks = candidate.get("checks", [])
        if not isinstance(checks, list):
            raise ValueError("checks must be a list")
        check_ids = set()
        roles = set()
        for check in checks:
            if not isinstance(check, dict):
                raise ValueError("check must be an object")
            name = _text(check.get("name"), "check.name")
            if name in check_ids:
                raise ValueError("duplicate check name")
            check_ids.add(name)
            role = check.get("role")
            if role not in {"acceptance", "countercheck", "regression"}:
                raise ValueError("invalid check role")
            roles.add(role)
            status = check.get("status")
            if status not in {"pass", "fail", "unknown"}:
                raise ValueError("invalid check status")
            refs = check.get("evidence_ids", [])
            if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs):
                raise ValueError("evidence_ids must be a list of strings")
            if not refs or not set(refs) <= evidence_ids:
                reasons.append(f"{name}: evidence missing or unresolved")
            elif all(e["kind"] == "simulation" for e in evidence if e["id"] in refs):
                reasons.append(f"{name}: simulation alone is insufficient")
            if status != "pass":
                reasons.append(f"{name}: {status}")
        for role in sorted({"acceptance", "countercheck", "regression"} - roles):
            reasons.append(f"missing {role} check")
        results.append({
            "id": cid,
            "priority": round(ratings[0] * ratings[1] / ratings[2], 6),
            "status": "blocked" if reasons else "ready_for_review",
            "reasons": reasons,
        })
    ranked = sorted(results, key=lambda x: (x["status"] != "ready_for_review", -x["priority"], x["id"]))
    eligible = [r for r in ranked if r["status"] == "ready_for_review"]
    return {
        "schema_version": "1.0.0", "objective": record["objective"],
        "revision": record["revision"], "model": record["model"],
        "selected_for_review": eligible[0]["id"] if eligible else None,
        "candidates": ranked, "automatic_promotion": False,
        "limitation": "Validates supplied records; does not authenticate sources or measure model intelligence.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        result = review(json.loads(args.record.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Invalid review record: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["selected_for_review"] is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
