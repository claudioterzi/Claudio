"""R3∞ autonomous evolution kernel.

Deterministic, auditable gate for turning research signals into candidate
improvements without silently rewriting canonical state. It operates above the
foundation model: memory, retrieval, routing, prompts, orchestration,
evaluation, provenance and reversible configuration. It may rewrite project code, workflow and project-level policy when a candidate
survives the R3-020 evidence gates. Foundation invariants, authority boundaries,
credentials, canonical history and platform constraints remain outside the
self-modification envelope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4

SCHEMA_VERSION = "r3-evolution-v1"
DEFAULT_LEDGER = Path("output/evolution/ledger.jsonl")
DEFAULT_SNAPSHOT_DIR = Path("output/evolution/runs")
AUTO_APPLY_SCOPES = frozenset({
    "prompt", "routing", "retrieval_weight", "evaluation_budget",
    "memory_index", "tool_selection", "core_code", "workflow",
    "project_policy", "documentation", "evaluation",
    "provider_configuration", "reuse_learning_model", "rewrite_strategy",
})
IMMUTABLE_SCOPES = frozenset({
    "foundation_invariants", "credentials", "canonical_history",
    "authority_boundary", "platform_constraints", "foundation_model_weights",
})
PROTECTED_SCOPES = frozenset({"external_side_effects"})
REWRITE_SCOPES_REQUIRING_ROLLBACK = frozenset({
    "core_code", "workflow", "project_policy", "evaluation",
    "provider_configuration", "reuse_learning_model", "rewrite_strategy",
})
TRAJECTORY_FIELDS = (
    "goal_match", "evidence_integrity", "authority_scope",
    "unexpected_side_effects", "recovery_behavior",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_token(value: str) -> str:
    out = []
    for char in value:
        out.append(char if char.isalnum() or char in ("-", "_") else "-")
    return "".join(out).strip("-") or "item"


@dataclass(frozen=True)
class EvolutionCandidate:
    title: str
    subsystem: str
    claim: str
    primary_metric: str
    direction: str = "higher"
    min_gain: float = 0.0
    source_refs: List[str] = field(default_factory=list)
    falsifiers: List[str] = field(default_factory=list)
    critical_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scope: str = "core_code"
    risk_level: str = "medium"
    reversible: bool = True
    rollback_ref: Optional[str] = None
    external_side_effects: bool = False
    candidate_id: str = field(default_factory=lambda: "R3C-" + uuid4().hex[:12])
    preregistered_at: str = field(default_factory=_utc_now)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if self.direction not in {"higher", "lower"}:
            errors.append("direction must be 'higher' or 'lower'")
        if self.risk_level not in {"low", "medium", "high", "critical"}:
            errors.append("risk_level must be low/medium/high/critical")
        if not self.title.strip() or not self.claim.strip():
            errors.append("title and claim are required")
        if not self.primary_metric.strip():
            errors.append("primary_metric is required")
        if not self.source_refs:
            errors.append("at least one provenance source_ref is required")
        if not self.falsifiers:
            errors.append("at least one falsifier must be preregistered")
        if self.scope in IMMUTABLE_SCOPES:
            errors.append("immutable foundation scope cannot be modified by the evolution kernel")
        if (self.scope in PROTECTED_SCOPES or self.scope in REWRITE_SCOPES_REQUIRING_ROLLBACK) and not self.rollback_ref:
            errors.append("rewrite/protected scopes require rollback_ref")
        if self.external_side_effects and self.scope != "external_side_effects":
            errors.append("external_side_effects must use the external_side_effects scope")
        return errors

    @property
    def prediction_hash(self) -> str:
        payload = asdict(self)
        payload.pop("preregistered_at", None)
        return _sha256(payload)


@dataclass(frozen=True)
class EvidenceContext:
    out_of_sample: bool
    provenance_complete: bool
    rollback_verified: bool
    trajectory_audit: Mapping[str, bool]
    independent_evaluator: bool = False
    notes: str = ""

    def missing_trajectory_checks(self) -> List[str]:
        return [name for name in TRAJECTORY_FIELDS if not bool(self.trajectory_audit.get(name, False))]


@dataclass(frozen=True)
class PromotionDecision:
    candidate_id: str
    status: str
    primary_gain: Optional[float]
    reasons: List[str]
    regressions: Dict[str, float]
    auto_apply_eligible: bool
    decided_at: str = field(default_factory=_utc_now)


def _metric_gain(baseline: float, trial: float, direction: str) -> float:
    return (trial - baseline) if direction == "higher" else (baseline - trial)


def _as_number(metrics: Mapping[str, Any], name: str) -> Optional[float]:
    value = metrics.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def evaluate_candidate(candidate: EvolutionCandidate, baseline: Mapping[str, Any],
                       trial: Mapping[str, Any], evidence: EvidenceContext) -> PromotionDecision:
    """R3-020 gate: REJECT, HOLD, STAGED or AUTO_APPLY_ELIGIBLE."""
    reasons: List[str] = []
    regressions: Dict[str, float] = {}
    validation_errors = candidate.validate()
    if validation_errors:
        return PromotionDecision(candidate.candidate_id, "REJECT", None,
                                 validation_errors, regressions, False)

    base_primary = _as_number(baseline, candidate.primary_metric)
    trial_primary = _as_number(trial, candidate.primary_metric)
    if base_primary is None or trial_primary is None:
        return PromotionDecision(candidate.candidate_id, "REJECT", None,
            [f"primary metric '{candidate.primary_metric}' missing or non-numeric"],
            regressions, False)
    primary_gain = _metric_gain(base_primary, trial_primary, candidate.direction)

    for metric_name, rule in candidate.critical_metrics.items():
        direction = str(rule.get("direction", "higher"))
        max_regression = float(rule.get("max_regression", 0.0))
        base_value = _as_number(baseline, metric_name)
        trial_value = _as_number(trial, metric_name)
        if base_value is None or trial_value is None:
            reasons.append(f"critical metric '{metric_name}' missing")
            continue
        gain = _metric_gain(base_value, trial_value, direction)
        regression = max(0.0, -gain)
        regressions[metric_name] = regression
        if regression > max_regression:
            reasons.append(
                f"critical regression: {metric_name}={regression:.6g} > allowed {max_regression:.6g}"
            )

    missing_trajectory = evidence.missing_trajectory_checks()
    if missing_trajectory:
        reasons.append("trajectory audit failed: " + ", ".join(missing_trajectory))
    if not evidence.rollback_verified:
        reasons.append("rollback not verified")
    if candidate.external_side_effects:
        reasons.append("external side effects are never auto-applied by this kernel")

    hard_failure = any(
        reason.startswith("critical regression:")
        or reason.startswith("critical metric '")
        or reason.startswith("trajectory audit failed:")
        or reason == "rollback not verified"
        or reason == "external side effects are never auto-applied by this kernel"
        for reason in reasons
    )
    if hard_failure:
        return PromotionDecision(candidate.candidate_id, "REJECT", primary_gain,
                                 reasons, regressions, False)

    if primary_gain < candidate.min_gain:
        reasons.append(f"target gain not met: {primary_gain:.6g} < required {candidate.min_gain:.6g}")
        return PromotionDecision(candidate.candidate_id, "HOLD", primary_gain,
                                 reasons, regressions, False)

    if not evidence.provenance_complete:
        reasons.append("provenance incomplete")
    if not evidence.out_of_sample:
        reasons.append("out-of-sample evidence missing")
    if candidate.risk_level in {"high", "critical"} and not evidence.independent_evaluator:
        reasons.append("high-risk candidate requires independent evaluator")
    if reasons:
        return PromotionDecision(candidate.candidate_id, "HOLD", primary_gain,
                                 reasons, regressions, False)

    auto_apply = (
        candidate.scope in AUTO_APPLY_SCOPES
        and candidate.scope not in PROTECTED_SCOPES
        and candidate.scope not in IMMUTABLE_SCOPES
        and candidate.reversible
        and candidate.risk_level in {"low", "medium"}
        and not candidate.external_side_effects
    )
    return PromotionDecision(
        candidate.candidate_id,
        "AUTO_APPLY_ELIGIBLE" if auto_apply else "STAGED",
        primary_gain,
        ["all configured evidence and regression gates passed"],
        regressions,
        auto_apply,
    )


def append_ledger_record(kind: str, payload: Mapping[str, Any],
                         ledger_path: Path = DEFAULT_LEDGER) -> Dict[str, Any]:
    """Append a hash-chained record. Existing history is never rewritten."""
    ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash: Optional[str] = None
    if ledger_path.exists():
        lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            previous_hash = json.loads(lines[-1]).get("record_hash")
    record: Dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "record_id": "R3R-" + uuid4().hex,
        "timestamp": _utc_now(),
        "kind": kind,
        "previous_hash": previous_hash,
        "payload": dict(payload),
    }
    record["record_hash"] = _sha256(record)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(record) + "\n")
    return record


def verify_ledger(ledger_path: Path = DEFAULT_LEDGER) -> Dict[str, Any]:
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        return {"valid": True, "records": 0, "errors": []}
    errors: List[str] = []
    previous_hash: Optional[str] = None
    count = 0
    for index, raw in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        count += 1
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: invalid JSON: {exc}")
            break
        actual_hash = record.get("record_hash")
        check = dict(record)
        check.pop("record_hash", None)
        if actual_hash != _sha256(check):
            errors.append(f"line {index}: record hash mismatch")
        if record.get("previous_hash") != previous_hash:
            errors.append(f"line {index}: previous hash mismatch")
        previous_hash = actual_hash
    return {"valid": not errors, "records": count, "errors": errors}


def preregister(candidate: EvolutionCandidate,
                ledger_path: Path = DEFAULT_LEDGER) -> Dict[str, Any]:
    payload = asdict(candidate)
    payload["prediction_hash"] = candidate.prediction_hash
    return append_ledger_record("candidate_preregistered", payload, ledger_path)


def record_decision(candidate: EvolutionCandidate, decision: PromotionDecision,
                    baseline: Mapping[str, Any], trial: Mapping[str, Any],
                    evidence: EvidenceContext,
                    ledger_path: Path = DEFAULT_LEDGER) -> Dict[str, Any]:
    return append_ledger_record("promotion_decision", {
        "candidate_id": candidate.candidate_id,
        "prediction_hash": candidate.prediction_hash,
        "decision": asdict(decision),
        "baseline_hash": _sha256(dict(baseline)),
        "trial_hash": _sha256(dict(trial)),
        "evidence": asdict(evidence),
    }, ledger_path)


def save_run_snapshot(snapshot: Mapping[str, Any], label: str,
                      snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Unique append-only run storage; same-day runs can never overwrite."""
    snapshot_dir = Path(snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    digest = _sha256(dict(snapshot))[:12]
    path = snapshot_dir / f"{timestamp}_{_safe_token(label)}_{digest}.json"
    counter = 1
    while path.exists():
        path = snapshot_dir / f"{timestamp}_{_safe_token(label)}_{digest}_{counter}.json"
        counter += 1
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def benchmark_metrics(snapshot: Mapping[str, Any]) -> Dict[str, float]:
    """Normalize an existing sdq1.benchmark snapshot into evolution metrics."""
    summary = snapshot.get("sommario", {})
    results = snapshot.get("risultati", [])
    total = int(summary.get("totale", 0) or 0)
    error_count = sum(1 for item in results if item.get("errore"))
    return {
        "score": float(summary.get("punteggio", 0.0) or 0.0),
        "latency_ms": float(summary.get("latenza_media_ms", 0.0) or 0.0),
        "error_rate": (error_count / total) if total else 1.0,
        "valid_tests": float(max(0, total - error_count)),
    }


def self_test() -> Dict[str, Any]:
    candidate = EvolutionCandidate(
        title="self-test routing candidate",
        subsystem="router",
        claim="routing improves quality without critical regressions",
        primary_metric="score",
        min_gain=0.02,
        source_refs=["internal:self-test"],
        falsifiers=["score gain below 0.02", "error_rate regression above 0"],
        critical_metrics={"error_rate": {"direction": "lower", "max_regression": 0.0}},
        scope="routing",
        risk_level="low",
        rollback_ref="git:self-test-parent",
    )
    evidence = EvidenceContext(
        out_of_sample=True,
        provenance_complete=True,
        rollback_verified=True,
        independent_evaluator=True,
        trajectory_audit={name: True for name in TRAJECTORY_FIELDS},
    )
    decision = evaluate_candidate(candidate,
        {"score": 0.70, "error_rate": 0.05},
        {"score": 0.75, "error_rate": 0.04}, evidence)
    return {"ok": decision.status == "AUTO_APPLY_ELIGIBLE", "decision": asdict(decision)}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="R3∞ autonomous evolution kernel")
    parser.add_argument("--verify-ledger", action="store_true")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--snapshot", help="save a JSON snapshot append-only")
    parser.add_argument("--label", default="run")
    args = parser.parse_args(argv)
    if args.self_test:
        result = self_test()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2
    if args.verify_ledger:
        result = verify_ledger(Path(args.ledger))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 3
    if args.snapshot:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        print(save_run_snapshot(snapshot, args.label))
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
