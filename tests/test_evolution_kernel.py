import json
import tempfile
import unittest
from pathlib import Path

from sdq1.evolution_kernel import (
    EvolutionCandidate,
    EvidenceContext,
    TRAJECTORY_FIELDS,
    append_ledger_record,
    evaluate_candidate,
    save_run_snapshot,
    verify_ledger,
)


def evidence(**overrides):
    data = dict(
        out_of_sample=True,
        provenance_complete=True,
        rollback_verified=True,
        independent_evaluator=True,
        trajectory_audit={name: True for name in TRAJECTORY_FIELDS},
    )
    data.update(overrides)
    return EvidenceContext(**data)


def candidate(**overrides):
    data = dict(
        title="retrieval candidate",
        subsystem="retrieval",
        claim="improves recall without increasing errors",
        primary_metric="recall",
        direction="higher",
        min_gain=0.05,
        source_refs=["paper:test"],
        falsifiers=["recall gain below 0.05"],
        critical_metrics={"error_rate": {"direction": "lower", "max_regression": 0.0}},
        scope="retrieval_weight",
        risk_level="low",
        rollback_ref="git:parent",
    )
    data.update(overrides)
    return EvolutionCandidate(**data)


class EvolutionKernelTests(unittest.TestCase):
    def test_low_risk_reversible_change_can_be_auto_apply_eligible(self):
        decision = evaluate_candidate(
            candidate(),
            {"recall": 0.70, "error_rate": 0.10},
            {"recall": 0.80, "error_rate": 0.08},
            evidence(),
        )
        self.assertEqual(decision.status, "AUTO_APPLY_ELIGIBLE")
        self.assertTrue(decision.auto_apply_eligible)

    def test_critical_regression_is_rejected(self):
        decision = evaluate_candidate(
            candidate(),
            {"recall": 0.70, "error_rate": 0.10},
            {"recall": 0.90, "error_rate": 0.20},
            evidence(),
        )
        self.assertEqual(decision.status, "REJECT")

    def test_protected_core_is_staged_not_auto_applied(self):
        decision = evaluate_candidate(
            candidate(scope="core_code", risk_level="medium"),
            {"recall": 0.70, "error_rate": 0.10},
            {"recall": 0.80, "error_rate": 0.08},
            evidence(),
        )
        self.assertEqual(decision.status, "STAGED")
        self.assertFalse(decision.auto_apply_eligible)

    def test_missing_out_of_sample_evidence_holds_candidate(self):
        decision = evaluate_candidate(
            candidate(),
            {"recall": 0.70, "error_rate": 0.10},
            {"recall": 0.80, "error_rate": 0.08},
            evidence(out_of_sample=False),
        )
        self.assertEqual(decision.status, "HOLD")

    def test_external_side_effects_are_rejected(self):
        decision = evaluate_candidate(
            candidate(scope="external_side_effects", external_side_effects=True, risk_level="high"),
            {"recall": 0.70, "error_rate": 0.10},
            {"recall": 0.90, "error_rate": 0.05},
            evidence(),
        )
        self.assertEqual(decision.status, "REJECT")

    def test_hash_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            append_ledger_record("a", {"x": 1}, ledger)
            append_ledger_record("b", {"x": 2}, ledger)
            self.assertTrue(verify_ledger(ledger)["valid"])
            lines = ledger.read_text(encoding="utf-8").splitlines()
            first = json.loads(lines[0])
            first["payload"]["x"] = 999
            lines[0] = json.dumps(first, sort_keys=True)
            ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertFalse(verify_ledger(ledger)["valid"])

    def test_snapshots_never_overwrite_same_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = save_run_snapshot({"score": 1}, "same", root)
            two = save_run_snapshot({"score": 1}, "same", root)
            self.assertNotEqual(one, two)
            self.assertTrue(one.exists())
            self.assertTrue(two.exists())


if __name__ == "__main__":
    unittest.main()
