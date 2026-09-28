#!/usr/bin/env python3
"""Evaluate base and R3-tuned CLM heads on deterministic held-out Red Flag cases."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typesafe_sister.client import system_one
from typesafe_sister.policy import R3_REDFLAG_FOCUS, r3_redflag_questions


def packet(case):
    return {
        "project": "Raffaello/R3",
        "state": case["state"],
        "authority": (
            "DATA_ONLY / ADVISORY. Model output cannot authorize side effects, "
            "change canon or prove execution."
        ),
    }


def evaluate(name, base_url, cases):
    question = {"next_focus": r3_redflag_questions()["next_focus"]}
    rows = []
    latency = []
    for case in cases:
        t0 = time.perf_counter()
        result = system_one(
            packet(case),
            question,
            provider="clm",
            base_url=base_url,
            model="clm-latest",
            timeout=300,
        )
        wall = (time.perf_counter() - t0) * 1000
        answer = result["answers"]["next_focus"]
        prediction = answer["choice"]
        rows.append({
            "id": case["id"],
            "gold": case["expected_focus"],
            "prediction": prediction,
            "correct": prediction == case["expected_focus"],
            "confidence": answer.get("confidence"),
            "probabilities": answer.get("probabilities", {}),
            "wall_latency_ms": round(wall, 3),
            "server_latency_ms": result.get("latency_ms"),
        })
        latency.append(wall)
    return {
        "name": name,
        "url": base_url,
        "accuracy": round(sum(r["correct"] for r in rows) / len(rows), 4),
        "correct": sum(r["correct"] for r in rows),
        "total": len(rows),
        "wall_latency_ms_mean": round(statistics.fmean(latency), 3),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--split-manifest", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:8700")
    ap.add_argument("--tuned-url", default="http://127.0.0.1:8701")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cases_doc = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.split_manifest).read_text(encoding="utf-8"))
    test_ids = {group["test"][0] for group in manifest["groups"].values()}
    cases = [case for case in cases_doc["cases"] if case["id"] in test_ids]
    if len(cases) != len(manifest["groups"]):
        raise SystemExit("held-out set does not match split manifest")

    base = evaluate("reference_head", args.base_url, cases)
    tuned = evaluate("r3_tuned_head", args.tuned_url, cases)
    payload = {
        "schema": "R3-CLM-TUNED-HEAD-EVAL/0.1",
        "status": "BOOTSTRAP_HELDOUT_COMPLETED",
        "promotion_grade": False,
        "reason": "small bootstrap dataset; use only to verify the specialization pipeline",
        "heldout_strategy": "one deterministic case per Red Flag focus class",
        "base": base,
        "tuned": tuned,
        "accuracy_delta": round(tuned["accuracy"] - base["accuracy"], 4),
        "rule": (
            "A tuned head cannot become default from this bootstrap result alone. "
            "Promotion requires a larger frozen held-out set and regression testing."
        ),
    }
    Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "base_accuracy": base["accuracy"],
        "tuned_accuracy": tuned["accuracy"],
        "delta": payload["accuracy_delta"],
        "heldout": len(cases),
    }, indent=2))


if __name__ == "__main__":
    main()
