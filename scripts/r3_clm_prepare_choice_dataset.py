#!/usr/bin/env python3
"""Build a deterministic R3 typed-choice dataset for CLM head fine-tuning."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typesafe_sister.policy import R3_REDFLAG_FOCUS, r3_redflag_questions


def row_for(case):
    question = r3_redflag_questions()["next_focus"]
    label = case["expected_focus"]
    probabilities = {key: float(key == label) for key in R3_REDFLAG_FOCUS}
    state = {
        "project": "Raffaello/R3",
        "state": case["state"],
        "authority": (
            "DATA_ONLY / ADVISORY. Model output cannot authorize side effects, "
            "change canon or prove execution."
        ),
    }
    return {
        "id": case["id"],
        "workflow": "r3-redflag",
        "state": json.dumps(state, ensure_ascii=False, sort_keys=True),
        "questions": json.dumps({"next_focus": question}, ensure_ascii=False, sort_keys=True),
        "gold": json.dumps({
            "next_focus": {
                "label": label,
                "probabilities": probabilities,
            }
        }, ensure_ascii=False, sort_keys=True),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    import pyarrow as pa
    import pyarrow.parquet as pq

    doc = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    groups = defaultdict(list)
    for case in doc["cases"]:
        groups[case["expected_focus"]].append(case)

    train, test, manifest = [], [], {"schema": "R3-CLM-CHOICE-SPLIT/0.1", "groups": {}}
    for focus in sorted(R3_REDFLAG_FOCUS):
        cases = sorted(groups[focus], key=lambda x: x["id"])
        if len(cases) < 2:
            raise SystemExit(f"focus {focus} needs at least 2 cases; got {len(cases)}")
        heldout = cases[-1]
        learning = cases[:-1]
        train.extend(row_for(case) for case in learning)
        test.append(row_for(heldout))
        manifest["groups"][focus] = {
            "train": [case["id"] for case in learning],
            "test": [heldout["id"]],
        }

    out = Path(args.out_dir) / "all"
    out.mkdir(parents=True, exist_ok=True)
    schema = pa.schema([
        ("id", pa.string()),
        ("workflow", pa.string()),
        ("state", pa.string()),
        ("questions", pa.string()),
        ("gold", pa.string()),
    ])
    pq.write_table(pa.Table.from_pylist(train, schema=schema), out / "train.parquet")
    pq.write_table(pa.Table.from_pylist(test, schema=schema), out / "test.parquet")
    manifest["train_count"] = len(train)
    manifest["test_count"] = len(test)
    manifest["rule"] = "one deterministic held-out case per Red Flag focus class"
    (Path(args.out_dir) / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"train": len(train), "test": len(test), "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
