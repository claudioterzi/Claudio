"""R3-019 Phase-0 integrity layer for the historical SDQ-1 benchmark.

This module deliberately wraps ``sdq1.benchmark`` instead of rewriting the
legacy suite. It adds the measurement-integrity properties required by the
R3-019 canon before a run can be treated as longitudinal promotion evidence:

- unique run identifiers;
- non-overwriting persistence;
- explicit COMPLETE / INCOMPLETE / INVALID status;
- explicit denominators and error counts;
- refusal to treat incomplete/invalid or legacy-unwrapped comparisons as
  promotion-grade evidence.

It does *not* make the legacy benchmark scientifically complete by itself.
Held-out tasks, repetitions, variance, frozen configs and the rest of the
canonical R3-019 protocol still apply.
"""

from __future__ import annotations

import copy
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sdq1 import benchmark as legacy

INTEGRITY_SCHEMA_VERSION = "r3-019-phase0-v1"
VALID_STATUSES = {"COMPLETE", "INCOMPLETE", "INVALID"}


class AmbiguousSnapshotError(ValueError):
    """Raised when a date selector resolves to more than one benchmark run."""


def generate_run_id(now: datetime | None = None) -> str:
    """Return a sortable, collision-resistant run id without external state."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    return f"{now.strftime('%Y%m%dT%H%M%S.%fZ')}-{uuid.uuid4().hex}"


def _safe_component(value: str) -> str:
    value = value.replace("/", "-").replace(".", "_")
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "unknown"


def prepare_snapshot(snapshot: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    """Return a copy of ``snapshot`` annotated with Phase-0 integrity metadata.

    Status semantics:
    - INVALID: required structural fields are absent or results are not a list;
    - INCOMPLETE: structure exists but one or more tests errored, or the observed
      denominator disagrees with the runner's declared total;
    - COMPLETE: all observed tests completed without runner errors and the
      denominator is internally consistent.

    This function validates structure; it does not retroactively prove the
    provenance of a historical snapshot. Promotion-grade comparison therefore
    separately requires both inputs to have already carried this integrity
    schema when presented to the comparator.
    """
    prepared = copy.deepcopy(snapshot)
    meta = prepared.setdefault("meta", {})
    summary = prepared.setdefault("sommario", {})
    results = prepared.get("risultati")

    meta["integrity_schema_version"] = INTEGRITY_SCHEMA_VERSION
    meta["run_id"] = run_id or meta.get("run_id") or generate_run_id()

    required_meta = ("modello", "data", "timestamp_inizio", "timestamp_fine")
    structurally_valid = all(meta.get(key) for key in required_meta) and isinstance(results, list)

    if not structurally_valid:
        observed_total = len(results) if isinstance(results, list) else 0
        error_count = observed_total
        completed_count = 0
        expected_total = summary.get("totale")
        status = "INVALID"
    else:
        observed_total = len(results)
        expected_total = summary.get("totale", observed_total)
        error_count = sum(1 for item in results if item.get("errore") not in (None, ""))
        completed_count = observed_total - error_count
        denominator_mismatch = not isinstance(expected_total, int) or expected_total != observed_total
        status = "INCOMPLETE" if error_count or denominator_mismatch else "COMPLETE"

    meta["run_status"] = status
    summary["expected_total"] = expected_total
    summary["observed_total"] = observed_total
    summary["completed_count"] = completed_count
    summary["error_count"] = error_count
    summary["promotion_grade_eligible"] = status == "COMPLETE"
    return prepared


def run_suite_integrity(
    modello: str = "gemini-2.5-flash",
    suite: list[dict] | None = None,
) -> dict[str, Any]:
    """Run the legacy fixed suite, then attach integrity semantics."""
    raw = legacy.esegui_suite(modello=modello, suite=suite)
    return prepare_snapshot(raw)


def save_snapshot(
    snapshot: dict[str, Any],
    output_dir: Path | None = None,
) -> Path:
    """Persist one run exactly once.

    Uses exclusive creation (``x`` mode): a collision or an attempted replay
    with the same run id fails loudly instead of overwriting evidence.
    """
    prepared = snapshot
    if prepared.get("meta", {}).get("integrity_schema_version") != INTEGRITY_SCHEMA_VERSION:
        prepared = prepare_snapshot(prepared)

    output_dir = output_dir or legacy.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    meta = prepared["meta"]
    data = _safe_component(str(meta.get("data", "unknown-date")))
    model = _safe_component(str(meta.get("modello", "unknown-model")))
    run_id = _safe_component(str(meta["run_id"]))
    path = output_dir / f"{data}_{model}_{run_id}.json"

    with path.open("x", encoding="utf-8") as handle:
        json.dump(prepared, handle, indent=2, ensure_ascii=False)
    return path


def _read_snapshot(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def find_snapshots(
    modello: str,
    selector: str,
    output_dir: Path | None = None,
) -> list[tuple[Path, dict[str, Any]]]:
    """Find runs by exact run_id first, otherwise by exact YYYY-MM-DD date."""
    output_dir = output_dir or legacy.OUTPUT_DIR
    if not output_dir.exists():
        return []

    by_run_id: list[tuple[Path, dict[str, Any]]] = []
    by_date: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(output_dir.glob("*.json")):
        snap = _read_snapshot(path)
        if not snap:
            continue
        meta = snap.get("meta", {})
        if meta.get("modello") != modello:
            continue
        if meta.get("run_id") == selector:
            by_run_id.append((path, snap))
        if meta.get("data") == selector:
            by_date.append((path, snap))
    return by_run_id or by_date


def load_snapshot(
    modello: str,
    selector: str,
    output_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Load one run without silently guessing among same-day snapshots."""
    matches = find_snapshots(modello, selector, output_dir=output_dir)
    if not matches:
        return None
    if len(matches) > 1:
        run_ids = [m[1].get("meta", {}).get("run_id", m[0].name) for m in matches]
        raise AmbiguousSnapshotError(
            f"Selector {selector!r} resolves to {len(matches)} runs; use a run_id: {run_ids}"
        )
    return matches[0][1]


def compare_snapshots(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Compare two runs while separating descriptive delta from promotion evidence.

    Legacy snapshots without the Phase-0 schema may still yield descriptive
    deltas, but they cannot become promotion-grade merely by being normalized at
    comparison time. That would launder historical provenance defects.
    """
    first_native = first.get("meta", {}).get("integrity_schema_version") == INTEGRITY_SCHEMA_VERSION
    second_native = second.get("meta", {}).get("integrity_schema_version") == INTEGRITY_SCHEMA_VERSION

    first_prepared = first if first_native else prepare_snapshot(first)
    second_prepared = second if second_native else prepare_snapshot(second)

    s1 = first_prepared.get("sommario", {})
    s2 = second_prepared.get("sommario", {})
    m1 = first_prepared.get("meta", {})
    m2 = second_prepared.get("meta", {})

    score1 = s1.get("punteggio")
    score2 = s2.get("punteggio")
    latency1 = s1.get("latenza_media_ms")
    latency2 = s2.get("latenza_media_ms")

    delta_score = None
    if isinstance(score1, (int, float)) and isinstance(score2, (int, float)):
        delta_score = round(float(score2) - float(score1), 3)

    delta_latency = None
    if isinstance(latency1, (int, float)) and isinstance(latency2, (int, float)):
        delta_latency = int(latency2 - latency1)

    statuses = (m1.get("run_status"), m2.get("run_status"))
    provenance_ok = first_native and second_native
    promotion_grade = provenance_ok and statuses == ("COMPLETE", "COMPLETE")

    if not provenance_ok:
        reason = "At least one run lacks native Phase-0 integrity provenance; descriptive deltas cannot support promotion."
    elif not promotion_grade:
        reason = "At least one run is not COMPLETE; descriptive deltas cannot support promotion."
    else:
        reason = "Both runs carry Phase-0 provenance and are COMPLETE; other R3-019 promotion gates still apply."

    return {
        "run_id_from": m1.get("run_id"),
        "run_id_to": m2.get("run_id"),
        "status_from": statuses[0],
        "status_to": statuses[1],
        "native_integrity_from": first_native,
        "native_integrity_to": second_native,
        "delta_punteggio": delta_score,
        "delta_latenza_ms": delta_latency,
        "promotion_grade": promotion_grade,
        "promotion_decision": "ELIGIBLE_FOR_NEXT_GATES" if promotion_grade else "REFUSE",
        "reason": reason,
    }
