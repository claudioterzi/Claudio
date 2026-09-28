#!/usr/bin/env python3
"""Run real CLM Red Flag inference against the held-out R3 bootstrap cases.

The script expects a reachable CLM TypeSafe-compatible endpoint in CLM_BASE_URL.
It records full advisory outputs, distributions, wall/server latency, input
tokens, cache health and deterministic label metrics. No action is executed.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from typesafe_sister.redflag import assess_redflag_state

ROOT = Path(__file__).resolve().parents[1]


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def _run_case(case: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    result = assess_redflag_state(
        "Raffaello/R3",
        case["state"],
        provider="clm",
        timeout=timeout,
    )
    wall_ms = (time.perf_counter() - started) * 1000.0

    detected = []
    if result.get("status") == "evaluated":
        detected = [
            flag
            for flag in case.get("must_detect_flags", [])
            if float(result.get("flags", {}).get(flag, 0.0)) >= 0.55
        ]
    return {
        "id": case["id"],
        "expected_focus": case["expected_focus"],
        "expected_lane": case["expected_lane"],
        "must_detect_flags": case.get("must_detect_flags", []),
        "detected_required_flags": detected,
        "wall_latency_ms": round(wall_ms, 3),
        "result": result,
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [row for row in rows if row["result"].get("status") == "evaluated"]
    wall = [float(row["wall_latency_ms"]) for row in evaluated]
    server = [
        float(row["result"]["server_latency_ms"])
        for row in evaluated
        if isinstance(row["result"].get("server_latency_ms"), (int, float))
    ]
    input_tokens = [
        int(row["result"].get("usage", {}).get("input_tokens", 0) or 0)
        for row in evaluated
    ]
    lane_correct = sum(
        row["result"].get("review_gate", {}).get("lane") == row["expected_lane"]
        for row in evaluated
    )
    focus_correct = sum(
        row["result"].get("focus", {}).get("value") == row["expected_focus"]
        for row in evaluated
    )
    required_total = sum(len(row["must_detect_flags"]) for row in evaluated)
    required_hit = sum(len(row["detected_required_flags"]) for row in evaluated)
    return {
        "case_count": len(rows),
        "evaluated_count": len(evaluated),
        "lane_accuracy": round(lane_correct / len(evaluated), 4) if evaluated else None,
        "focus_accuracy": round(focus_correct / len(evaluated), 4) if evaluated else None,
        "required_flag_recall": round(required_hit / required_total, 4) if required_total else None,
        "required_flag_hits": required_hit,
        "required_flag_total": required_total,
        "wall_latency_ms": {
            "p50": round(_percentile(wall, 0.50), 3) if wall else None,
            "p95": round(_percentile(wall, 0.95), 3) if wall else None,
            "mean": round(statistics.fmean(wall), 3) if wall else None,
        },
        "server_latency_ms": {
            "p50": round(_percentile(server, 0.50), 3) if server else None,
            "p95": round(_percentile(server, 0.95), 3) if server else None,
            "mean": round(statistics.fmean(server), 3) if server else None,
        },
        "input_tokens_total": sum(input_tokens),
        "input_tokens_mean": round(statistics.fmean(input_tokens), 2) if input_tokens else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        default=str(ROOT / "benchmarks" / "r3_clm_redflag_cases.json"),
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "r3-clm-redflag-live.json"),
    )
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    base_url = os.getenv("CLM_BASE_URL", "http://127.0.0.1:8700").rstrip("/")
    case_doc = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = case_doc["cases"]

    before_health = _get_json(base_url + "/health")
    models = _get_json(base_url + "/v1/models")

    cold = [_run_case(case, args.timeout) for case in cases]
    mid_health = _get_json(base_url + "/health")
    warm = [_run_case(case, args.timeout) for case in cases]
    after_health = _get_json(base_url + "/health")

    cold_metrics = _metrics(cold)
    warm_metrics = _metrics(warm)
    cold_p50 = cold_metrics["wall_latency_ms"]["p50"]
    warm_p50 = warm_metrics["wall_latency_ms"]["p50"]
    speedup = None
    if cold_p50 and warm_p50:
        speedup = round(cold_p50 / warm_p50, 3)

    payload = {
        "schema": "R3-CLM-REDFLAG-LIVE/0.1",
        "status": "LIVE_CLM_INFERENCE_COMPLETED",
        "authority": "ADVISORY_ONLY",
        "promotion_grade": False,
        "promotion_note": (
            "This run verifies real CLM inference and measures a bootstrap held-out set. "
            "It does not by itself promote CLM to the canonical/default provider."
        ),
        "runtime": {
            "clm_base_url": base_url,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "model_variant": os.getenv("R3_CLM_ENCODER_VARIANT", "unknown"),
            "clm_upstream_commit": os.getenv("R3_CLM_UPSTREAM_COMMIT", "unknown"),
            "llama_cpp_commit": os.getenv("R3_LLAMA_CPP_COMMIT", "unknown"),
        },
        "models": models,
        "health": {
            "before": before_health,
            "after_cold": mid_health,
            "after_warm": after_health,
        },
        "cold": {
            "metrics": cold_metrics,
            "cases": cold,
        },
        "warm": {
            "metrics": warm_metrics,
            "cases": warm,
        },
        "cache_wall_p50_speedup": speedup,
        "dataset": {
            "schema": case_doc.get("schema"),
            "case_count": len(cases),
            "labels": "deterministic R3 policy expectations",
        },
        "safety": {
            "executed_external_actions": 0,
            "merged_to_main": False,
            "spent_money": False,
            "secrets_recorded": False,
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "cold_metrics": cold_metrics,
        "warm_metrics": warm_metrics,
        "cache_wall_p50_speedup": speedup,
        "output": str(out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
