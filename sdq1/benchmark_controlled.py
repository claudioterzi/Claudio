"""R3-019 controlled A/B/C/D baseline runner.

This layer sits above the historical benchmark. It freezes the experiment plan,
keeps gold data scoring-side, repeats tasks, preserves raw outputs and records
success-gated efficiency/human-friction fields without inventing unavailable
cost/token metrics.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from sdq1.benchmark_integrity import generate_run_id

LLMFactory = Callable[[str, str], Callable[[str], str]]

RRR_PREFIX = (
    "Protocollo RRR operativo: separa fatti/ipotesi, non inventare successi, "
    "preserva provenienza, applica P5/P6 e verifica i postcondition quando rilevanti. "
)


@dataclass(frozen=True)
class Condition:
    key: str
    model: str
    method: str


def conditions(compare_model: str, candidate_model: str) -> list[Condition]:
    return [
        Condition("A", compare_model, "ESSENTIAL"),
        Condition("B", compare_model, "RRR"),
        Condition("C", candidate_model, "ESSENTIAL"),
        Condition("D", candidate_model, "RRR"),
    ]


def load_dataset(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "R3-019-DATASET/1":
        raise ValueError("invalid dataset schema")
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("empty dataset")
    ids = [task.get("id") for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task ids")
    for task in tasks:
        if task.get("set") not in {"CORE", "NOVEL", "ADVERSARIAL"}:
            raise ValueError("invalid task set")
        if not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
            raise ValueError("invalid task prompt")
        if not isinstance(task.get("evaluator"), dict):
            raise ValueError("missing evaluator")
    return value


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluate(task: dict[str, Any], answer: str) -> bool:
    text = answer.lower()
    forbidden = [str(x).lower() for x in task.get("forbidden", [])]
    if any(value in text for value in forbidden):
        return False
    evaluator = task["evaluator"]
    values = [str(x).lower() for x in evaluator.get("values", [])]
    kind = evaluator.get("type")
    if kind == "contains_any":
        return any(value in text for value in values)
    if kind == "contains_all":
        return all(value in text for value in values)
    raise ValueError(f"unsupported evaluator: {kind}")


def _model_prompt(task: dict[str, Any], method: str) -> str:
    # Gold/evaluator/forbidden fields must not enter the model prompt.
    prompt = task["prompt"]
    return (RRR_PREFIX + "\n\n" + prompt) if method == "RRR" else prompt


def freeze_plan(
    *,
    compare_model: str,
    candidate_model: str,
    dataset_path: Path,
    repeats: int = 3,
    commit: str,
) -> dict[str, Any]:
    if repeats < 2:
        raise ValueError("repeats must be >= 2")
    dataset = load_dataset(dataset_path)
    plan = {
        "schema": "R3-019-PLAN/1",
        "dataset_version": dataset["dataset_version"],
        "dataset_sha256": dataset_sha256(dataset_path),
        "compare_model": compare_model,
        "candidate_model": candidate_model,
        "repeats": repeats,
        "commit": commit,
        "conditions": [asdict(item) for item in conditions(compare_model, candidate_model)],
        "sets": ["CORE", "NOVEL", "ADVERSARIAL"],
        "success_gated_efficiency": True,
        "gold_sent_to_model": False,
    }
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"))
    plan["plan_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return plan


def run_controlled(
    *,
    plan: dict[str, Any],
    dataset_path: Path,
    llm_factory: LLMFactory,
) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    if dataset_sha256(dataset_path) != plan["dataset_sha256"]:
        raise ValueError("dataset changed after plan freeze")

    started = datetime.now(timezone.utc)
    records: list[dict[str, Any]] = []
    for condition in plan["conditions"]:
        ask = llm_factory(condition["model"], condition["method"])
        for repeat in range(plan["repeats"]):
            for task in dataset["tasks"]:
                prompt = _model_prompt(task, condition["method"])
                t0 = time.perf_counter()
                error = None
                try:
                    answer = ask(prompt)
                    passed = _evaluate(task, answer)
                except Exception as exc:  # benchmark evidence must preserve failure
                    answer = ""
                    passed = False
                    error = type(exc).__name__
                latency_ms = int((time.perf_counter() - t0) * 1000)
                records.append({
                    "condition": condition["key"],
                    "model": condition["model"],
                    "method": condition["method"],
                    "repeat": repeat,
                    "task_id": task["id"],
                    "set": task["set"],
                    "category": task["category"],
                    "passed": passed,
                    "latency_ms": latency_ms,
                    "error": error,
                    "raw_output": answer[:4000],
                    "user_visible_turns": 0,
                    "human_interventions": 0,
                    "tool_calls": 1,
                })

    summaries: dict[str, Any] = {}
    for condition in plan["conditions"]:
        key = condition["key"]
        subset = [r for r in records if r["condition"] == key]
        completed = [r for r in subset if r["error"] is None]
        verified_success = len(completed) == len(subset)
        accuracy = sum(1 for r in subset if r["passed"]) / len(subset)
        latencies = [r["latency_ms"] for r in completed]
        repeat_scores = []
        for repeat in range(plan["repeats"]):
            rep = [r for r in subset if r["repeat"] == repeat]
            repeat_scores.append(sum(1 for r in rep if r["passed"]) / len(rep))
        summaries[key] = {
            "condition": condition,
            "task_runs": len(subset),
            "verified_success": verified_success,
            "accuracy": round(accuracy, 6),
            "run_variance": round(statistics.pvariance(repeat_scores), 8),
            "mean_latency_ms": int(statistics.mean(latencies)) if latencies else None,
            "tool_calls": sum(r["tool_calls"] for r in subset),
            "user_visible_turns": 0,
            "human_interventions": 0,
            "error_count": sum(1 for r in subset if r["error"] is not None),
            "efficiency_interpretation": (
                "ELIGIBLE_FOR_COMPARISON" if verified_success else "REFUSE_FAILED_RUN"
            ),
        }

    finished = datetime.now(timezone.utc)
    return {
        "schema": "R3-019-CONTROLLED-RUN/1",
        "run_id": generate_run_id(started),
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "plan": plan,
        "summaries": summaries,
        "records": records,
        "promotion_state": "EVIDENCE_ONLY_NEXT_GATES_REQUIRED",
    }


def save_run(run: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run['run_id']}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(run, handle, ensure_ascii=False, indent=2)
    return path
