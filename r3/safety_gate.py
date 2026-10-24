#!/usr/bin/env python3
"""
R3-020: Self-Improvement Safety Gate

Struttura di controllo per modifiche autonome al sistema.
Pattern: candidate → test → benchmark → review → merge

Ogni modifica proposta passa attraverso:
1. Sandbox test (nessun side effect)
2. Regression check (non perde capacità esistenti)
3. Performance benchmark (migliore o neutrale)
4. Evidence review (perché è sicura questa modifica?)
5. Human checkpoint (approval per merge)
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class GateStatus(Enum):
    """Stato di una modifica attraverso il gate."""
    PROPOSED = "proposed"
    SANDBOX_PASS = "sandbox_pass"
    REGRESSION_FAIL = "regression_fail"
    PERF_ACCEPTABLE = "perf_acceptable"
    EVIDENCE_REVIEW = "evidence_review"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    MERGED = "merged"
    ROLLED_BACK = "rolled_back"


@dataclass
class TestResult:
    """Risultato di un test."""
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class BenchmarkResult:
    """Risultato di un benchmark comparativo."""
    metric_name: str
    baseline: float
    candidate: float
    improvement_percent: float
    acceptable: bool  # True se >= baseline o migliore

    def to_dict(self):
        return asdict(self)


@dataclass
class SafetyGateProposal:
    """Una modifica candidata per il safety gate."""
    id: str
    title: str
    description: str
    files_modified: List[str]
    rationale: str  # Perché questa modifica è sicura?
    test_plan: str  # Come testiamo che funziona?
    rollback_plan: str  # Come annulliamo se necessario?

    created_at: str
    status: GateStatus = GateStatus.PROPOSED

    # Risultati progressivi
    test_results: List[TestResult] = None
    benchmark_results: List[BenchmarkResult] = None
    regression_check: Optional[bool] = None
    evidence_notes: str = ""
    human_approval: Optional[bool] = None
    approval_notes: str = ""

    merged_at: Optional[str] = None
    merged_commit: Optional[str] = None

    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.benchmark_results is None:
            self.benchmark_results = []

    def compute_hash(self) -> str:
        """Hash della proposta per audit trail."""
        content = f"{self.id}:{self.title}:{self.files_modified}:{self.rationale}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def can_proceed_to_merge(self) -> bool:
        """Verifica se la proposta può essere mergiata."""
        checks = [
            self.status == GateStatus.HUMAN_APPROVED,
            len(self.test_results) > 0,
            all(tr.passed for tr in self.test_results),
            self.regression_check is True,
            len(self.benchmark_results) > 0,
            all(br.acceptable for br in self.benchmark_results),
        ]
        return all(checks)

    def to_dict(self):
        d = asdict(self)
        d['status'] = self.status.value
        d['test_results'] = [tr.to_dict() for tr in self.test_results]
        d['benchmark_results'] = [br.to_dict() for br in self.benchmark_results]
        return d


class SafetyGate:
    """Gestisce il flusso di modiche attraverso il safety gate."""

    def __init__(self, log_file: str = "r3/logs/safety_gate_audit.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.proposals: Dict[str, SafetyGateProposal] = {}

    def propose_change(
        self,
        title: str,
        description: str,
        files_modified: List[str],
        rationale: str,
        test_plan: str,
        rollback_plan: str,
    ) -> SafetyGateProposal:
        """Registra una modifica proposta."""
        proposal_id = f"SGP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        proposal = SafetyGateProposal(
            id=proposal_id,
            title=title,
            description=description,
            files_modified=files_modified,
            rationale=rationale,
            test_plan=test_plan,
            rollback_plan=rollback_plan,
            created_at=datetime.now().isoformat(),
        )

        self.proposals[proposal_id] = proposal
        self._log(proposal, "PROPOSED")
        print(f"✅ Proposal {proposal_id} registered: {title}")
        return proposal

    def record_test_result(
        self,
        proposal_id: str,
        test_name: str,
        passed: bool,
        duration_ms: float,
        error: Optional[str] = None,
    ) -> bool:
        """Registra il risultato di un test."""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]
        result = TestResult(
            name=test_name,
            passed=passed,
            duration_ms=duration_ms,
            error=error
        )
        proposal.test_results.append(result)

        status_str = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status_str} Test '{test_name}' for {proposal_id} ({duration_ms:.1f}ms)")

        self._log(proposal, f"TEST_{test_name}_{'PASS' if passed else 'FAIL'}")
        return True

    def record_benchmark(
        self,
        proposal_id: str,
        metric_name: str,
        baseline: float,
        candidate: float,
    ) -> bool:
        """Registra un benchmark comparativo."""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]
        improvement = ((candidate - baseline) / baseline * 100) if baseline != 0 else 0
        acceptable = candidate >= baseline or improvement > -5  # Tollero -5%

        result = BenchmarkResult(
            metric_name=metric_name,
            baseline=baseline,
            candidate=candidate,
            improvement_percent=improvement,
            acceptable=acceptable,
        )
        proposal.benchmark_results.append(result)

        status = "✅ ACCEPTABLE" if acceptable else "⚠️  BELOW_BASELINE"
        print(f"{status} {metric_name}: {baseline:.2f} → {candidate:.2f} ({improvement:+.1f}%)")

        self._log(proposal, f"BENCHMARK_{metric_name}")
        return True

    def approve_by_human(
        self,
        proposal_id: str,
        approved: bool,
        notes: str = ""
    ) -> bool:
        """Approva o rifiuta una proposta (richiede umano)."""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]

        if not approved and not proposal.can_proceed_to_merge():
            print(f"❌ Cannot approve: tests/benchmarks not complete")
            return False

        proposal.human_approval = approved
        proposal.approval_notes = notes
        proposal.status = GateStatus.HUMAN_APPROVED if approved else GateStatus.HUMAN_REJECTED

        action = "APPROVED" if approved else "REJECTED"
        print(f"🔒 Proposal {proposal_id} {action} by human")
        self._log(proposal, f"HUMAN_{action}")
        return True

    def merge(
        self,
        proposal_id: str,
        commit_hash: str,
    ) -> bool:
        """Mergia la modifica al ramo principale."""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]

        if not proposal.can_proceed_to_merge():
            print(f"❌ Cannot merge: safety gate checks failed")
            return False

        proposal.status = GateStatus.MERGED
        proposal.merged_at = datetime.now().isoformat()
        proposal.merged_commit = commit_hash

        print(f"✅ Proposal {proposal_id} MERGED → commit {commit_hash}")
        self._log(proposal, f"MERGED_{commit_hash}")
        return True

    def rollback(
        self,
        proposal_id: str,
        reason: str,
    ) -> bool:
        """Annulla una modifica mergiata."""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]
        proposal.status = GateStatus.ROLLED_BACK

        print(f"⚠️  Proposal {proposal_id} ROLLED_BACK: {reason}")
        self._log(proposal, f"ROLLED_BACK: {reason}")
        return True

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict]:
        """Ritorna lo stato attuale di una proposta."""
        if proposal_id not in self.proposals:
            return None
        return self.proposals[proposal_id].to_dict()

    def _log(self, proposal: SafetyGateProposal, event: str):
        """Log event per audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "proposal_id": proposal.id,
            "event": event,
            "proposal_hash": proposal.compute_hash(),
            "status": proposal.status.value,
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


# Singleton
_gate = None

def get_safety_gate() -> SafetyGate:
    """Get or create the global safety gate instance."""
    global _gate
    if _gate is None:
        _gate = SafetyGate()
    return _gate


if __name__ == "__main__":
    # Test della safety gate
    gate = SafetyGate()

    # Proponi una modifica
    proposal = gate.propose_change(
        title="Add city expansion to flight hunter",
        description="Support searching from Venezia, Genova, Roma",
        files_modified=["scripts/daily_flight_hunt.py", ".env.example"],
        rationale="More cities = more deal opportunities. No API changes, just config expansion.",
        test_plan="1. Verify Ryanair API responds for new airports\n2. Check alert thresholds work\n3. Regression: old cities still work",
        rollback_plan="Revert commits if new cities break search or alerts",
    )

    # Simula test
    gate.record_test_result(proposal.id, "ryanair_api_venezia", True, 145.3)
    gate.record_test_result(proposal.id, "ryanair_api_genova", True, 162.1)
    gate.record_test_result(proposal.id, "alert_threshold_check", True, 23.5)
    gate.record_test_result(proposal.id, "regression_mxp_bru_fco", True, 89.2)

    # Simula benchmark
    gate.record_benchmark(proposal.id, "search_time_ms", 450.0, 420.0)  # Più veloce ✓
    gate.record_benchmark(proposal.id, "alerts_accuracy", 0.98, 0.98)  # Uguale ✓

    # Human approval
    gate.approve_by_human(proposal.id, True, "Looks good. Coverage increased, no regressions.")

    # Merge
    gate.merge(proposal.id, "abc123def456")

    print("\n📋 Final status:")
    print(json.dumps(gate.get_proposal_status(proposal.id), indent=2))
