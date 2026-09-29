"""RedFrag benchmark: same frozen fixture for every System One provider.

The model sees only the case `cluster` (never expected labels, rationale or
falsifiers). Two views:
  flags  - production state: cluster + deterministic evidence flags (what RedFrag sends today)
  blind  - the gate flags and derived evidence are removed from the model's view; the model
           must infer class/action from names, excerpts, hashes and provenance. The final
           decision still uses the full deterministic gate.

Usage:
  python scripts/r3_clm_redfrag_benchmark.py --provider r3_clm --view blind
  CLM_BASE_URL=http://host:8700 python scripts/r3_clm_redfrag_benchmark.py --provider clm
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typesafe_sister import client as system_one_client  # noqa: E402
from typesafe_sister.redfrag import assess_redfrag_cluster  # noqa: E402

GATE_FLAGS = ("same_topic", "semantic_divergence", "divergence_evidence", "canonical_invariant",
              "evidence_role", "superseded", "active_relevance")
DEFAULT_FIXTURE = ROOT / "tests" / "redfrag_benchmark_v1.json"


def _pct(values, p):
    values = sorted(values)
    if not values:
        return None
    idx = min(len(values) - 1, max(0, int(round((p / 100) * (len(values) - 1)))))
    return round(values[idx], 3)


def load_cases(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = raw["cases"] if isinstance(raw, dict) else raw
    out = []
    for c in cases:
        if "cluster" in c:
            out.append((c["cluster"], c["expected_class"], c["expected_action"], c.get("hard_case", [])))
        else:  # legacy 28/09 fixture: strip gold labels before the model sees the case
            cluster = {k: v for k, v in c.items() if k not in ("expected_class", "expected_action")}
            out.append((cluster, c["expected_class"], c["expected_action"], []))
    return out


def make_caller(provider: str, view: str):
    def caller(state, questions):
        model_state = state
        if view == "blind":
            model_state = copy.deepcopy(state)
            model_state.pop("deterministic_evidence", None)
            for k in GATE_FLAGS:
                model_state["cluster"].pop(k, None)
        return system_one_client.system_one(model_state, questions, provider=provider, timeout=30)
    return caller


def run(path: Path, repeats: int = 20, provider: str = "r3_clm", view: str = "flags"):
    cases = load_cases(path)
    caller = make_caller(provider, view)
    rows, timings = [], []
    n = len(cases)
    final_ok = cls_ok = act_ok = dissent = failures = 0
    for cluster, exp_cls, exp_act, hard in cases:
        case_times, result, error = [], None, None
        for _ in range(repeats):
            start = time.perf_counter_ns()
            try:
                result = assess_redfrag_cluster(cluster, caller=caller)
            except Exception as exc:  # recorded, never hidden
                error = type(exc).__name__
                result = None
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            timings.append(elapsed)
            case_times.append(elapsed)
            if error:
                break
        status = (result or {}).get("status", "error")
        if status != "evaluated":
            failures += 1
            rows.append({"id": cluster["id"], "status": status, "error": error, "hard_case": hard})
            continue
        advice = result["model_advice"]
        ok = result["semantic_class"] == exp_cls and result["action"] == exp_act
        c_ok = advice["semantic_class"] == exp_cls
        a_ok = advice["proposed_action"] == exp_act
        final_ok += ok
        cls_ok += c_ok
        act_ok += a_ok
        dissent += bool(advice["dissent"])
        rows.append({"id": cluster["id"], "status": status, "expected": [exp_cls, exp_act],
                     "final": [result["semantic_class"], result["action"]],
                     "model": [advice["semantic_class"], advice["proposed_action"]],
                     "final_ok": ok, "model_class_ok": c_ok, "model_action_ok": a_ok,
                     "dissent": advice["dissent"], "hard_case": hard,
                     "p50_ms": round(statistics.median(case_times), 3)})

    by_class = {}
    for (cluster, exp_cls, _, _), row in zip(cases, rows):
        b = by_class.setdefault(exp_cls, {"n": 0, "model_class_ok": 0, "model_action_ok": 0})
        b["n"] += 1
        b["model_class_ok"] += int(row.get("model_class_ok", False))
        b["model_action_ok"] += int(row.get("model_action_ok", False))
    fixture_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": "R3-REDFRAG-BENCH/1.0", "provider": provider, "view": view,
        "backend": system_one_client.backend_info(provider=provider),
        "fixture": path.name, "fixture_sha256": fixture_sha, "cases": n, "repeats_per_case": repeats,
        "final_decision_accuracy": round(final_ok / n, 4),
        "model_only_class_accuracy": round(cls_ok / n, 4),
        "model_only_action_accuracy": round(act_ok / n, 4),
        "dissent_rate": round(dissent / n, 4),
        "failures_or_abstentions": failures,
        "latency_ms": {"p50": _pct(timings, 50), "p95": _pct(timings, 95), "p99": _pct(timings, 99),
                       "max": round(max(timings), 3) if timings else None},
        "by_expected_class": by_class,
        "physical_deletions": 0,
        "rows": rows,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="RedFrag benchmark on one System One provider")
    ap.add_argument("--provider", default=os.getenv("R3_REDFRAG_PROVIDER", "r3_clm"),
                    choices=["r3_clm", "clm", "typesafe"])
    ap.add_argument("--view", default="flags", choices=["flags", "blind"])
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    args = ap.parse_args()
    report = run(Path(args.fixture), repeats=args.repeats, provider=args.provider, view=args.view)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["failures_or_abstentions"] == 0 else 1)
