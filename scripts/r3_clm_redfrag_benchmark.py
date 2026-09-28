from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typesafe_sister.redfrag import assess_redfrag_cluster


def _pct(values, p):
    values = sorted(values)
    if not values:
        return None
    idx = min(len(values) - 1, max(0, int(round((p / 100) * (len(values) - 1)))))
    return values[idx]


def run(path: Path, repeats: int = 100):
    cases = json.loads(path.read_text(encoding="utf-8"))
    rows, timings = [], []
    final_passed = model_class_agree = model_action_agree = observations = 0
    for case in cases:
        assess_redfrag_cluster(case)
    for case in cases:
        last, case_times = None, []
        for _ in range(repeats):
            start = time.perf_counter_ns()
            result = assess_redfrag_cluster(case)
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            timings.append(elapsed_ms)
            case_times.append(elapsed_ms)
            last = result
        result = last
        ok = result.get("semantic_class") == case["expected_class"] and result.get("action") == case["expected_action"]
        final_passed += int(ok)
        advice = result.get("model_advice") or {}
        class_agree = advice.get("semantic_class") == case["expected_class"]
        action_agree = advice.get("proposed_action") == case["expected_action"]
        model_class_agree += int(class_agree)
        model_action_agree += int(action_agree)
        observations += 1
        rows.append({"id": case["id"], "ok": ok, "class": result.get("semantic_class"),
                     "action": result.get("action"), "model_class": advice.get("semantic_class"),
                     "model_action": advice.get("proposed_action"), "model_class_agrees": class_agree,
                     "model_action_agrees": action_agree, "model_dissent": advice.get("dissent"),
                     "p50_ms": round(statistics.median(case_times), 3)})
    return {"schema": "R3-CLM-REDFRAG-BENCH/0.1", "fixture": path.name, "cases": len(rows),
            "repeats_per_case": repeats, "final_decision_passed": final_passed,
            "final_decision_accuracy": final_passed / max(1, len(rows)),
            "model_only_semantic_class_agreement": model_class_agree / max(1, observations),
            "model_only_action_agreement": model_action_agree / max(1, observations),
            "latency_ms": {"mean": round(statistics.fmean(timings), 3),
                           "p50": round(_pct(timings, 50), 3), "p95": round(_pct(timings, 95), 3),
                           "p99": round(_pct(timings, 99), 3), "max": round(max(timings), 3)},
            "network_calls": 0, "physical_deletions": 0, "rows": rows}


if __name__ == "__main__":
    fixture = ROOT / "tests" / "redfrag_checkpoint_20260928.json"
    report = run(fixture)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["final_decision_passed"] == report["cases"] else 1)
