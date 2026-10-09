"""OpenMontage capability record for Raffaello Creative Studio.

This module is intentionally metadata-only for now: it does not claim that
OpenMontage is installed or executable inside this repository. The capability
moves to ADOPTED only after the sandbox/baseline/audit gates pass.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CapabilityRecord:
    name: str
    repository: str
    status: str
    purpose: str
    candidate_pipeline: str
    stages: Tuple[str, ...]
    useful_patterns: Tuple[str, ...]
    adoption_gates: Tuple[str, ...]
    first_use_case: str


OPENMONTAGE_CAPABILITY = CapabilityRecord(
    name="OpenMontage",
    repository="calesthio/OpenMontage",
    status="CANDIDATE",
    purpose=(
        "Agentic audiovisual production for Raffaello Creative Studio: "
        "research, script, scene planning, assets, editing, composition and "
        "a future bridge toward coherent 3D worlds."
    ),
    candidate_pipeline="cinematic",
    stages=(
        "research",
        "proposal",
        "script",
        "scene_plan",
        "assets",
        "edit",
        "compose",
    ),
    useful_patterns=(
        "pipeline manifests instead of ad-hoc orchestration",
        "stage-specific director skills",
        "append-only decision history",
        "human approval gates for consequential creative decisions",
        "provider/tool capability preflight",
        "scene-level provenance and auditable production state",
    ),
    adoption_gates=(
        "DISCOVERED",
        "CANDIDATE",
        "SANDBOX",
        "BASELINE_A_B",
        "FALSIFICATION",
        "AUDIT",
        "ADOPTED_OR_REJECTED",
    ),
    first_use_case="Cubo Vivo 2D — single-scene audiovisual sample",
)
