"""10-file admission benchmark for R3-JUDGE/1.

The manifest must contain exactly ten already-labelled files: five ``stub`` and
five ``real``.  This command does not activate the backend; it only emits a gate
record.  ``adopt`` is true only when the stricter R3 threshold is met.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from typesafe_sister.client import system_one

from r3_judge import ORIGIN, PROTOCOL

QUESTION = {
    "is_stub": {
        "type": "noul",
        "instructions": (
            "Is this file effectively an empty output, placeholder, stub, scaffold, "
            "or non-substantive result rather than a real completed output? Judge only "
            "the supplied file content. Boilerplate alone is not a completed output."
        ),
        "criteria": {
            "true": "The file is empty, placeholder-like, stub/scaffold, or lacks substantive output.",
            "false": "The file contains substantive completed output beyond placeholder/scaffold text.",
        },
    }
}


def _read_manifest(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = data.get("fixtures") if isinstance(data, dict) else None
    if not isinstance(fixtures, list) or len(fixtures) != 10:
        raise ValueError("manifest must contain exactly 10 fixtures")
    labels = [str(item.get("label", "")).lower() for item in fixtures if isinstance(item, dict)]
    if labels.count("stub") != 5 or labels.count("real") != 5:
        raise ValueError("manifest must contain exactly 5 stub and 5 real labels")
    clean: list[dict[str, str]] = []
    for index, item in enumerate(fixtures):
        if not isinstance(item, dict):
            raise ValueError(f"fixture {index} is not an object")
        file_path = str(item.get("path") or "").strip()
        fixture_id = str(item.get("id") or file_path or f"fixture-{index + 1}")
        if not file_path:
            raise ValueError(f"fixture {fixture_id!r} has no path")
        clean.append({"id": fixture_id, "path": file_path, "label": str(item["label"]).lower()})
    return clean


def _classify(base_url: str, fixture: dict[str, str], *, model: str, api_key: str, timeout: float) -> dict[str, Any]:
    content = Path(fixture["path"]).read_text(encoding="utf-8", errors="replace")
    state = {
        "content": content[:262144],
        "benchmark_rule": "Classify only the supplied content. No filename, fixture id or label is provided.",
    }
    result = system_one(
        state, QUESTION, provider="clm", base_url=base_url,
        model=model, api_key=api_key, timeout=timeout,
    )
    identity = result.get("model")
    metadata = result.get("x_rizzo")
    if not isinstance(identity, str) or not identity.strip():
        raise ValueError("response model must be a non-empty string")
    if not isinstance(metadata, dict):
        raise ValueError("response x_rizzo must be an object")
    fingerprint = metadata.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        raise ValueError("response fingerprint must be a non-empty string")
    answer = ((result.get("answers") or {}).get("is_stub") or {})
    probability = answer.get("noul")
    if type(probability) not in (int, float) or not 0 <= probability <= 1:
        raise ValueError("invalid is_stub response")
    predicted = "stub" if float(probability) >= 0.5 else "real"
    return {
        "id": fixture["id"],
        "path": fixture["path"],
        "expected": fixture["label"],
        "predicted": predicted,
        "p_stub": float(probability),
        "correct": predicted == fixture["label"],
        "model": identity,
        "backend_fingerprint": fingerprint,
    }


def _validate_rows(rows: list[dict[str, Any]]) -> None:
    """Reject malformed rows instead of coercing them (external review 2026-10-05)."""
    ids, paths = set(), set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {index} is not an object")
        if type(row.get("correct")) is not bool:
            raise ValueError(f"row {index}: correct must be a real boolean")
        for key in ("model", "backend_fingerprint"):
            value = row.get(key)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"row {index}: {key} must be a string")
        case_id, case_path = row.get("id"), row.get("path")
        if not isinstance(case_id, str) or not case_id or not isinstance(case_path, str) or not case_path:
            raise ValueError(f"row {index}: id and path are required")
        if case_id in ids or case_path in paths:
            raise ValueError(f"row {index}: duplicate case id or path")
        ids.add(case_id)
        paths.add(case_path)


def summarize(rows: list[dict[str, Any]], *, min_correct: int = 8,
              expected_model: str | None = None,
              expected_fingerprint: str | None = None) -> dict[str, Any]:
    if len(rows) != 10:
        raise ValueError("exactly 10 benchmark rows are required")
    _validate_rows(rows)
    correct = sum(bool(row.get("correct")) for row in rows)
    stub_rows = [r for r in rows if r.get("expected") == "stub"]
    real_rows = [r for r in rows if r.get("expected") == "real"]
    if len(stub_rows) != 5 or len(real_rows) != 5:
        raise ValueError("benchmark rows must be balanced 5/5")
    stub_recall = sum(bool(r.get("correct")) for r in stub_rows) / 5
    real_recall = sum(bool(r.get("correct")) for r in real_rows) / 5
    accuracy = correct / 10
    balanced_accuracy = (stub_recall + real_recall) / 2
    beats_chance = accuracy > 0.5
    r3_strict_gate = (
        correct >= min_correct
        and stub_recall >= 0.8
        and real_recall >= 0.8
    )
    # Exact identity: no str() coercion and no strip() equating different values.
    models = sorted({r.get("model") or "" for r in rows})
    fingerprints = sorted({r.get("backend_fingerprint") or "" for r in rows})
    stable_backend = (len(models) == 1 and bool(models[0].strip())
                      and len(fingerprints) == 1 and bool(fingerprints[0].strip()))
    pinned = all(isinstance(value, str) and bool(value.strip())
                 for value in (expected_model, expected_fingerprint))
    matches_expected = pinned
    if expected_model is not None and (not stable_backend or models[0] != expected_model):
        matches_expected = False
    if expected_fingerprint is not None and (not stable_backend or fingerprints[0] != expected_fingerprint):
        matches_expected = False
    return {
        "protocol": PROTOCOL,
        "origin": ORIGIN,
        "benchmark": "R3-STUB-SEPARATION/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": 10,
        "correct": correct,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "stub_recall": stub_recall,
        "real_recall": real_recall,
        "beats_chance": beats_chance,
        "required_correct": min_correct,
        "stable_backend": stable_backend,
        "model": models[0] if len(models) == 1 else "",
        "backend_fingerprint": fingerprints[0] if len(fingerprints) == 1 else "",
        "expected_model": expected_model,
        "expected_fingerprint": expected_fingerprint,
        "matches_expected": matches_expected,
        "statistical_note": "10-case smoke gate only: random guessing passes 36/1024 (3.5%); not evidence of >=80% recall.",
        "adopt": bool(beats_chance and r3_strict_gate and stable_backend and matches_expected),
        "epistemic_class": "TEST_RESULT",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the R3-JUDGE 10-file admission benchmark")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-url", default=os.getenv("R3_JUDGE_BASE_URL", "http://127.0.0.1:8017"))
    parser.add_argument("--model", default=os.getenv("R3_JUDGE_MODEL", "rizzo-latest"))
    parser.add_argument("--api-key", default=os.getenv("R3_JUDGE_API_KEY", ""))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--expect-fingerprint", default=os.getenv("R3_JUDGE_EXPECT_FINGERPRINT", ""))
    parser.add_argument("--min-correct", type=int, default=8, choices=range(6, 11), metavar="6..10")
    parser.add_argument("--output", type=Path, default=Path("r3_judge/adoption_gate.json"))
    args = parser.parse_args()
    if not args.model.strip() or not args.expect_fingerprint.strip():
        parser.error("a non-empty --model and --expect-fingerprint are required before inference")

    fixtures = _read_manifest(args.manifest)
    rows = [
        _classify(args.base_url, fixture, model=args.model, api_key=args.api_key, timeout=args.timeout)
        for fixture in fixtures
    ]
    report = summarize(rows, min_correct=args.min_correct,
                       expected_model=args.model, expected_fingerprint=args.expect_fingerprint or None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Create-only: never overwrite an existing gate record (protocol requirement).
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["adopt"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
