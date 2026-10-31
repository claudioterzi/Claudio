#!/usr/bin/env python3
"""Mine R3 hard negatives from a real CLM Red Flag run.

The gold action comes from the deterministic held-out policy label. CLM is used
only to order the wrong alternatives by plausibility; therefore a model mistake
cannot relabel itself as truth. The output is training-candidate data, not canon.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typesafe_sister.policy import R3_REDFLAG_FOCUS, R3_REDFLAG_POLICY_VERSION


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--live", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cases_doc = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    live = json.loads(Path(args.live).read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in live["cold"]["cases"]}
    out = []

    for case in cases_doc["cases"]:
        row = by_id.get(case["id"])
        if not row or row["result"].get("status") != "evaluated":
            continue
        probs = row["result"].get("focus", {}).get("probabilities", {})
        gold = case["expected_focus"]
        negatives = [
            {
                "action": key,
                "description": R3_REDFLAG_FOCUS[key],
                "clm_probability": float(probs.get(key, 0.0)),
            }
            for key in R3_REDFLAG_FOCUS
            if key != gold
        ]
        negatives.sort(key=lambda item: item["clm_probability"], reverse=True)
        out.append({
            "id": case["id"],
            "task_id": "r3-redflag-" + case["id"],
            "state": case["state"],
            "gold_action": gold,
            "gold_description": R3_REDFLAG_FOCUS[gold],
            "hard_negatives": negatives[:3],
            "clm_predicted_action": row["result"]["focus"]["value"],
            "clm_gold_probability": float(probs.get(gold, 0.0)),
            "source_input_sha256": row["result"]["input_sha256"],
            "policy_version": R3_REDFLAG_POLICY_VERSION,
            "provenance": "deterministic_label + live_clm_ranking",
            "authority": "TRAINING_CANDIDATE_ONLY",
        })

    payload = {
        "schema": "R3-CLM-HARD-NEGATIVES/0.1",
        "status": "MINED_FROM_LIVE_CLM",
        "source_live_schema": live.get("schema"),
        "count": len(out),
        "records": out,
        "rule": (
            "CLM may rank wrong alternatives but cannot generate or replace the deterministic gold label."
        ),
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "count": len(out), "out": str(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
