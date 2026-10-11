#!/usr/bin/env python3
"""Build a small public status snapshot from repository evidence only.

No network access. No claims about external nodes unless an explicit evidence file exists.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "r3-status.json"


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def latest_daily():
    pattern = re.compile(r"daily_(\d{4}-\d{2}-\d{2})\.txt$")
    found = []
    for p in (ROOT / "output").glob("daily_*.txt"):
        m = pattern.match(p.name)
        if m:
            found.append((m.group(1), p))
    if not found:
        return None, None
    found.sort()
    stamp, path = found[-1]
    return stamp, path


def contact_stats():
    path = ROOT / "output" / "contatti.jsonl"
    total = 0
    verified_human = 0
    last = None
    if not path.exists():
        return total, verified_human, last
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except Exception:
            continue
        total += 1
        if row.get("umano") is True and str(row.get("verifica", "")).strip():
            verified_human += 1
        d = row.get("data")
        if d and (last is None or d > last):
            last = d
    return total, verified_human, last


def hypothesis_stats():
    data = read_json(ROOT / "registro_ipotesi.json", {})
    counts = {"APERTA": 0, "CONFERMATA": 0, "FALSIFICATA": 0, "SOSPESA": 0}
    for row in data.values() if isinstance(data, dict) else []:
        state = str(row.get("stato", "UNKNOWN")).upper()
        counts[state] = counts.get(state, 0) + 1
    return counts, len(data) if isinstance(data, dict) else 0


def benchmark_stats():
    folder = ROOT / "output" / "benchmark"
    files = sorted([p for p in folder.glob("*") if p.is_file()]) if folder.exists() else []
    return len(files), files[-1].name if files else None


def verified_node_stats():
    """Only explicit evidence counts. Absence means zero verified nodes, not zero code."""
    p = ROOT / "output" / "r3_verified_nodes.json"
    data = read_json(p, {})
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    valid = [n for n in nodes if isinstance(n, dict) and n.get("verified") is True and n.get("evidence")]
    return len(valid), valid


def main():
    daily_date, daily_path = latest_daily()
    today = datetime.now(timezone.utc).date()
    gap_days = None
    if daily_date:
        gap_days = (today - date.fromisoformat(daily_date)).days

    hyp_counts, hyp_total = hypothesis_stats()
    contacts_total, contacts_verified_human, last_contact = contact_stats()
    benchmark_count, benchmark_last = benchmark_stats()
    verified_nodes, node_rows = verified_node_stats()

    h2_risk = "UNKNOWN"
    if daily_date:
        h2_risk = "AT_RISK" if gap_days is not None and gap_days > 1 else "CURRENT"

    payload = {
        "schema": "r3-public-status-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "repository-derived",
        "commit": os.getenv("GITHUB_SHA") or None,
        "heartbeat": {
            "last_daily": daily_date,
            "gap_days": gap_days,
            "source_file": str(daily_path.relative_to(ROOT)) if daily_path else None,
        },
        "hypotheses": {
            "total": hyp_total,
            "open": hyp_counts.get("APERTA", 0),
            "confirmed": hyp_counts.get("CONFERMATA", 0),
            "falsified": hyp_counts.get("FALSIFICATA", 0),
            "suspended": hyp_counts.get("SOSPESA", 0),
        },
        "contacts": {
            "records": contacts_total,
            "verified_human": contacts_verified_human,
            "last_date": last_contact,
        },
        "benchmarks": {
            "files": benchmark_count,
            "last_file": benchmark_last,
        },
        "r3": {
            "verified_external_nodes": verified_nodes,
            "nodes": node_rows,
            "claim_policy": "No external node is counted without explicit evidence.",
        },
        "h2": {
            "status": "OPEN",
            "risk": h2_risk,
            "deadline": "2026-12-11",
            "note": "Missing regular daily output is treated as adverse evidence, not hidden.",
        },
        "next_test": "Restore a consecutive heartbeat, then document a two-node sync/failover with hashes and logs.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
