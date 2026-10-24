"""Frozen independent numeric falsifiers for the existing R3-020 gate.

Run against an explicitly selected baseline or candidate source file. No model,
network, promotion or repository mutation occurs. The source module is executed
only to import its existing candidate/evidence/decision interfaces.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


def cases():
    records = []

    def add(name, expected, **changes):
        records.append({"id": name, "expected_status": expected, "changes": changes})

    invalid = "REJECT"
    allowed = "AUTO_APPLY_ELIGIBLE"
    specials = [("nan", float("nan")), ("positive_inf", float("inf")),
                ("negative_inf", -float("inf"))]
    for field in ("base_primary", "trial_primary", "base_critical", "trial_critical"):
        for label, value in specials:
            add(f"nonfinite_{field}_{label}", invalid, **{field: value})
    for field in ("min_gain", "max_regression"):
        for label, value in specials:
            add(f"nonfinite_threshold_{field}_{label}", invalid, **{field: value})

    enormous = 10 ** 5000
    for field in ("base_primary", "trial_primary", "base_critical", "trial_critical",
                  "min_gain", "max_regression"):
        for label, value in (("positive", enormous), ("negative", -enormous)):
            add(f"unrepresentable_integer_{field}_{label}", invalid, **{field: value})

    for direction in ("higher", "lower"):
        for label, base, trial in (("increasing", -1.6e308, 1.6e308),
                                   ("decreasing", 1.6e308, -1.6e308)):
            add(f"primary_gain_overflow_{direction}_{label}", invalid,
                direction=direction, base_primary=base, trial_primary=trial)
            add(f"critical_gain_overflow_{direction}_{label}", invalid,
                critical_direction=direction, base_critical=base, trial_critical=trial)

    for label, value in (("empty", ""), ("unknown", "sideways"),
                         ("case_variant", "Higher"), ("none", None),
                         ("integer", 7), ("bool", True)):
        add(f"invalid_critical_direction_{label}", invalid, critical_direction=value)

    add("finite_positive_control", allowed)
    add("finite_zero_metrics_control", allowed, base_primary=0.0, trial_primary=0.0,
        min_gain=0.0, base_critical=0.0, trial_critical=0.0)
    add("finite_negative_metrics_higher_control", allowed,
        base_primary=-9.0, trial_primary=-3.0, min_gain=1.0,
        base_critical=-1.0, trial_critical=-2.0)
    add("finite_negative_metrics_lower_control", allowed,
        direction="lower", base_primary=-3.0, trial_primary=-9.0, min_gain=1.0,
        base_critical=-1.0, trial_critical=-2.0)
    add("finite_integers_control", allowed, base_primary=0, trial_primary=4,
        min_gain=1, base_critical=2, trial_critical=1)
    add("representable_large_integers_control", allowed,
        base_primary=10 ** 200, trial_primary=2 * (10 ** 200), min_gain=1.0)
    add("finite_critical_higher_control", allowed, critical_direction="higher",
        base_critical=-2.0, trial_critical=-1.0)
    add("finite_allowed_critical_regression_control", allowed,
        base_critical=0.1, trial_critical=0.25, max_regression=0.2)
    add("finite_primary_no_gain_control", "HOLD", base_primary=0.4, trial_primary=0.4)
    add("finite_primary_regression_control", "HOLD", base_primary=0.4, trial_primary=-0.1)
    add("finite_excess_critical_regression_control", invalid,
        base_critical=-2.0, trial_critical=-1.0, max_regression=0.0)
    add("negative_finite_regression_limit_control", invalid, max_regression=-0.01)
    return records


def labelled(value):
    if isinstance(value, float) and not math.isfinite(value):
        label = "NaN" if math.isnan(value) else ("+Infinity" if value > 0 else "-Infinity")
        return {"numeric_label": label}
    if isinstance(value, int) and not isinstance(value, bool) and value.bit_length() > 1024:
        return {"numeric_label": "oversized_integer", "sign": 1 if value > 0 else -1,
                "bit_length": value.bit_length()}
    if isinstance(value, dict):
        return {str(key): labelled(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [labelled(item) for item in value]
    return value


def load_module(source):
    name = "_r3_020_heldout_target"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ValueError("source module is not loadable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def probe(source):
    module = load_module(source)
    results = []
    for item in cases():
        changes = item["changes"]
        candidate = module.EvolutionCandidate(
            title="independent numeric integrity probe",
            subsystem="continuity",
            claim="only finite valid measurements can support candidate eligibility",
            primary_metric="verified_detection_rate",
            direction=changes.get("direction", "higher"),
            min_gain=changes.get("min_gain", 0.1),
            source_refs=["heldout:frozen-independent-numeric-suite"],
            falsifiers=["invalid measurement admitted or valid finite control rejected"],
            critical_metrics={"error_rate": {
                "direction": changes.get("critical_direction", "lower"),
                "max_regression": changes.get("max_regression", 0.0),
            }},
            scope="prompt", risk_level="low", reversible=True,
            rollback_ref="scratch:remove-candidate", candidate_id=item["id"],
            preregistered_at="2026-10-07T00:00:00+00:00",
        )
        evidence = module.EvidenceContext(
            out_of_sample=True, provenance_complete=True, rollback_verified=True,
            trajectory_audit={field: True for field in module.TRAJECTORY_FIELDS},
            independent_evaluator=True,
            notes="Independent local deterministic probe; no runtime/model claim.",
        )
        baseline = {"verified_detection_rate": changes.get("base_primary", 0.4),
                    "error_rate": changes.get("base_critical", 0.1)}
        trial = {"verified_detection_rate": changes.get("trial_primary", 0.8),
                 "error_rate": changes.get("trial_critical", 0.08)}
        record = {"id": item["id"], "expected_status": item["expected_status"],
                  "inputs": labelled(changes)}
        try:
            decision = module.evaluate_candidate(candidate, baseline, trial, evidence)
            record.update(actual_status=decision.status,
                          primary_gain=labelled(decision.primary_gain),
                          reasons=decision.reasons,
                          auto_apply_eligible=decision.auto_apply_eligible,
                          passes=decision.status == item["expected_status"])
        except Exception as error:
            record.update(actual_status="EXCEPTION", error_class=type(error).__name__,
                          passes=False)
        results.append(record)

    invalid_records = [item for item in results if item["expected_status"] == "REJECT"]
    controls = [item for item in results if item["expected_status"] != "REJECT"]
    return {
        "schema": "R3-020-INDEPENDENT-NUMERIC-PROBE/1",
        "authority": "DATA_ONLY",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source.resolve()),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "suite_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "aggregate": {
            "total": len(results), "passed": sum(item["passes"] for item in results),
            "failed": sum(not item["passes"] for item in results),
            "invalid_expected": len(invalid_records),
            "invalid_rejected": sum(item["passes"] for item in invalid_records),
            "controls_expected": len(controls),
            "controls_preserved": sum(item["passes"] for item in controls),
            "exceptions": sum(item["actual_status"] == "EXCEPTION" for item in results),
            "invalid_admitted": sum(item["actual_status"] in {"STAGED", "AUTO_APPLY_ELIGIBLE"}
                                    for item in invalid_records),
        },
        "results": results,
        "limits": ["Numeric gate only; no semantic model, provider, cloud or deployment executed.",
                   "Deterministic fixtures do not establish generalization or live capability growth."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.source)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"suite_sha256": result["suite_sha256"],
                      "source_sha256": result["source_sha256"],
                      "aggregate": result["aggregate"], "output": str(args.out)},
                     allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
