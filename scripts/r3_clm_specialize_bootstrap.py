#!/usr/bin/env python3
"""Bootstrap an internal R3 CLM projection head on deterministic Red Flag labels.

This is deliberately small and promotion-blocked. CLM ranks/mines difficult
alternatives, while deterministic R3 policy owns the gold label. The script
uses the already-running Qwen embedding server and base CLM instance.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, *, env=None):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, env=env)


def wait_health(url: str, seconds: int = 240):
    deadline = time.time() + seconds
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("ok"):
                return payload
            last = payload
        except Exception as exc:
            last = type(exc).__name__
        time.sleep(2)
    raise RuntimeError(f"health timeout for {url}: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--live", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--upstream-dir", default="/tmp/CLM")
    ap.add_argument("--embed-url", default="http://127.0.0.1:8090/v1/embeddings")
    ap.add_argument("--base-url", default="http://127.0.0.1:8700")
    ap.add_argument("--tuned-port", type=int, default=8701)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hard = out / "r3-clm-hard-negatives.json"
    dataset = out / "choice-data"
    head = out / "r3-clm-tuned-head"
    split_copy = out / "r3-clm-split-manifest.json"
    eval_out = out / "r3-clm-tuned-eval.json"

    run([
        sys.executable, str(ROOT / "scripts" / "r3_clm_hard_negative_builder.py"),
        "--cases", args.cases, "--live", args.live, "--out", str(hard),
    ])
    run([
        sys.executable, str(ROOT / "scripts" / "r3_clm_prepare_choice_dataset.py"),
        "--cases", args.cases, "--out-dir", str(dataset),
    ])
    split = dataset / "split_manifest.json"
    split_copy.write_bytes(split.read_bytes())

    ckpt = subprocess.check_output(["clm-download"], text=True).strip().splitlines()[-1]
    trainer = Path(args.upstream_dir) / "train" / "finetune.py"
    env = dict(os.environ)
    run([
        sys.executable, str(trainer),
        "--task", "choice",
        "--data", str(dataset),
        "--workflow", "all",
        "--out-dir", str(head),
        "--init-ckpt", ckpt,
        "--embed-url", args.embed_url,
        "--served-model-name", "qwen3-8b",
        "--embed-model", "Qwen/Qwen3-8B",
        "--max-len", "1024",
        "--epochs", "12",
        "--batch", "8",
        "--val-frac", "0.20",
        "--patience", "4",
        "--targets", "hard",
        "--loss", "softce",
    ], env=env)

    tuned_url = f"http://127.0.0.1:{args.tuned_port}"
    log = open(out / "r3-clm-tuned-server.log", "w", encoding="utf-8")
    server_env = dict(os.environ)
    server_env["CLM_ACTION_CACHE"] = "0"
    proc = subprocess.Popen([
        "clm-serve",
        "--ckpt", str(head / "best_head.pt"),
        "--port", str(args.tuned_port),
        "--max-tokens", "1024",
        "--no-ui",
    ], stdout=log, stderr=subprocess.STDOUT, env=server_env)
    try:
        tuned_health = wait_health(tuned_url + "/health")
        (out / "r3-clm-tuned-health.json").write_text(
            json.dumps(tuned_health, indent=2) + "\n", encoding="utf-8"
        )
        run([
            sys.executable, str(ROOT / "scripts" / "r3_clm_eval_tuned_head.py"),
            "--cases", args.cases,
            "--split-manifest", str(split),
            "--base-url", args.base_url,
            "--tuned-url", tuned_url,
            "--out", str(eval_out),
        ])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()

    evaluation = json.loads(eval_out.read_text(encoding="utf-8"))
    summary = {
        "schema": "R3-CLM-INTERNAL-HEAD/0.1",
        "status": "BOOTSTRAP_SPECIALIZATION_EXECUTED",
        "promotion_grade": False,
        "training_cases": json.loads(split.read_text(encoding="utf-8"))["train_count"],
        "heldout_cases": json.loads(split.read_text(encoding="utf-8"))["test_count"],
        "base_accuracy": evaluation["base"]["accuracy"],
        "tuned_accuracy": evaluation["tuned"]["accuracy"],
        "accuracy_delta": evaluation["accuracy_delta"],
        "hard_negative_count": json.loads(hard.read_text(encoding="utf-8"))["count"],
        "rule": (
            "This checkpoint proves the R3-specific CLM specialization path. "
            "It remains candidate-only until a substantially larger frozen holdout "
            "and regression suite satisfy the promotion gate."
        ),
    }
    (out / "r3-clm-internal-head-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
