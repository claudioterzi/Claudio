import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sdq1.benchmark_controlled import (
    conditions,
    freeze_plan,
    load_dataset,
    run_controlled,
    save_run,
)

DATASET = Path("benchmarks/r3_019_controlled_v1.json")


class ControlledBenchmarkTests(unittest.TestCase):
    def _plan(self):
        return freeze_plan(compare_model="m1", candidate_model="m2",
                           dataset_path=DATASET, repeats=2, commit="test")

    def test_changed_or_missing_plan_digest_is_rejected_before_provider_calls(self):
        mutations = [
            lambda p: p.update(repeats=1),
            lambda p: p["conditions"].pop(),
            lambda p: p["conditions"][0].update(model="other"),
            lambda p: p.update(commit="other"),
            lambda p: p.update(gold_sent_to_model=True),
            lambda p: p.pop("plan_sha256"),
            lambda p: p.update(plan_sha256="0" * 64),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                plan = self._plan()
                mutate(plan)
                factory = Mock()
                with self.assertRaises(ValueError):
                    run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
                factory.assert_not_called()

    def test_invalid_repetitions_are_rejected_during_freeze(self):
        for repeats in (True, 0, 1, 2.5, "3", None):
            with self.subTest(repeats=repeats), self.assertRaises(ValueError):
                freeze_plan(compare_model="m1", candidate_model="m2",
                            dataset_path=DATASET, repeats=repeats, commit="test")

    def test_rehashing_invalid_plan_does_not_bypass_abcd_contract(self):
        for changes in ({"repeats": 1}, {"repeats": 2.5}, {"conditions": []},
                        {"conditions": [vars(conditions("m1", "m2")[0])]},
                        {"gold_sent_to_model": True}, {"success_gated_efficiency": False},
                        {"schema": "unknown"}, {"dataset_version": "other"}):
            with self.subTest(changes=changes):
                plan = self._plan()
                plan.update(changes)
                plan.pop("plan_sha256")
                plan["plan_sha256"] = hashlib.sha256(json.dumps(
                    plan, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")).hexdigest()
                factory = Mock()
                with self.assertRaises(ValueError):
                    run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
                factory.assert_not_called()

    def test_caller_cannot_mutate_plan_during_or_after_execution(self):
        plan = self._plan()
        frozen = copy.deepcopy(plan)

        def factory(*_):
            plan["repeats"] = 1
            plan["conditions"][0]["model"] = "other"
            return lambda _: ""

        result = run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
        self.assertEqual(result["plan"], frozen)
        for summary in result["summaries"].values():
            self.assertEqual(summary["task_runs"], len(load_dataset(DATASET)["tasks"]) * 2)
        plan["conditions"].clear()
        self.assertEqual(result["plan"], frozen)

    def test_dataset_digest_and_execution_use_the_same_read(self):
        for freeze in (True, False):
            with self.subTest(freeze=freeze):
                plan = self._plan()
                with (
                    patch.object(Path, "read_bytes", return_value=DATASET.read_bytes()) as read,
                    patch.object(Path, "read_text", side_effect=AssertionError("second read")),
                ):
                    if freeze:
                        self._plan()
                    else:
                        run_controlled(plan=plan, dataset_path=DATASET,
                                       llm_factory=lambda *_: lambda _: "")
                self.assertEqual(read.call_count, 1)

    def test_empty_or_malformed_evaluators_are_rejected_before_execution(self):
        invalid = [
            {"type": "contains_all", "values": []},
            {"type": "contains_any", "values": [""]},
            {"type": "contains_all", "values": [" "]},
            {"type": "contains_all", "values": "correct"},
            {"type": "contains_all", "values": [1]},
            {"type": "unknown", "values": ["correct"]},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            for evaluator in invalid:
                with self.subTest(evaluator=evaluator):
                    data = json.loads(DATASET.read_text(encoding="utf-8"))
                    data["tasks"][0]["evaluator"] = evaluator
                    dataset.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        freeze_plan(compare_model="m1", candidate_model="m2",
                                    dataset_path=dataset, repeats=2, commit="test")

    def test_verified_success_requires_every_task_to_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            dataset.write_text(json.dumps({"schema": "R3-019-DATASET/1", "dataset_version": "test", "tasks": [
                {"id": str(i), "set": "CORE", "category": "test", "prompt": str(i),
                 "evaluator": {"type": "contains_all", "values": ["correct"]}}
                for i in range(2)]}), encoding="utf-8")
            plan = freeze_plan(compare_model="m1", candidate_model="m2",
                               dataset_path=dataset, repeats=2, commit="test")
            for all_correct in (False, True):
                def factory(*_):
                    return lambda prompt: "correct" if all_correct or prompt.endswith("0") else "wrong"
                result = run_controlled(plan=plan, dataset_path=dataset, llm_factory=factory)
                for summary in result["summaries"].values():
                    self.assertEqual(summary["verified_success"], all_correct)
                    self.assertEqual(summary["accuracy"], 1 if all_correct else 0.5)

    def test_completed_wrong_answers_never_count_as_verified_success(self):
        plan = freeze_plan(compare_model="m1", candidate_model="m2",
                           dataset_path=DATASET, repeats=2, commit="test")
        result = run_controlled(plan=plan, dataset_path=DATASET,
                                llm_factory=lambda *_: lambda prompt: "")
        for summary in result["summaries"].values():
            self.assertTrue(summary["execution_complete"])
            self.assertEqual(summary["accuracy"], 0)
            self.assertFalse(summary["verified_success"])
            self.assertEqual(summary["efficiency_interpretation"], "REFUSE_FAILED_RUN")

    def test_dataset_has_three_required_sets(self):
        data = load_dataset(DATASET)
        self.assertEqual({task["set"] for task in data["tasks"]}, {"CORE", "NOVEL", "ADVERSARIAL"})

    def test_abcd_conditions_are_stable(self):
        value = conditions("m1", "m2")
        self.assertEqual([item.key for item in value], ["A", "B", "C", "D"])
        self.assertEqual([item.method for item in value], ["ESSENTIAL", "RRR", "ESSENTIAL", "RRR"])

    def test_plan_freezes_dataset_and_repetitions(self):
        plan = freeze_plan(
            compare_model="m1",
            candidate_model="m2",
            dataset_path=DATASET,
            repeats=3,
            commit="abc123",
        )
        self.assertFalse(plan["gold_sent_to_model"])
        self.assertEqual(plan["repeats"], 3)
        self.assertEqual(len(plan["plan_sha256"]), 64)
        self.assertEqual(len(plan["dataset_sha256"]), 64)

    def test_gold_fields_never_reach_model_prompt(self):
        seen = []

        def factory(model, method):
            def ask(prompt):
                seen.append(prompt)
                return "no; serve verifica, provenienza, stato e diff"
            return ask

        plan = freeze_plan(
            compare_model="m1",
            candidate_model="m2",
            dataset_path=DATASET,
            repeats=2,
            commit="abc123",
        )
        run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
        joined = "\n".join(seen)
        self.assertNotIn('"evaluator"', joined)
        self.assertNotIn('"forbidden"', joined)
        self.assertNotIn('"values"', joined)

    def test_failed_calls_are_not_efficiency_success(self):
        def factory(model, method):
            def ask(prompt):
                raise RuntimeError("offline")
            return ask

        plan = freeze_plan(
            compare_model="m1",
            candidate_model="m2",
            dataset_path=DATASET,
            repeats=2,
            commit="abc123",
        )
        result = run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
        for summary in result["summaries"].values():
            self.assertFalse(summary["verified_success"])
            self.assertEqual(summary["efficiency_interpretation"], "REFUSE_FAILED_RUN")
            self.assertGreater(summary["error_count"], 0)

    def test_repeat_variance_and_human_friction_are_recorded(self):
        def factory(model, method):
            def ask(prompt):
                if "14:37" in prompt:
                    return "16:25"
                if "sorted" in prompt:
                    return "verifica"
                return "no: dichiarare dato mancante e verificare stato, provenienza e diff"
            return ask

        plan = freeze_plan(
            compare_model="m1",
            candidate_model="m2",
            dataset_path=DATASET,
            repeats=2,
            commit="abc123",
        )
        result = run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
        for summary in result["summaries"].values():
            self.assertIn("run_variance", summary)
            self.assertEqual(summary["user_visible_turns"], 0)
            self.assertEqual(summary["human_interventions"], 0)

    def test_run_persistence_is_non_overwriting(self):
        def factory(model, method):
            return lambda prompt: "no: verificare"

        plan = freeze_plan(
            compare_model="m1",
            candidate_model="m2",
            dataset_path=DATASET,
            repeats=2,
            commit="abc123",
        )
        result = run_controlled(plan=plan, dataset_path=DATASET, llm_factory=factory)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            path = save_run(result, out)
            self.assertTrue(path.exists())
            with self.assertRaises(FileExistsError):
                save_run(result, out)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["run_id"], result["run_id"])


if __name__ == "__main__":
    unittest.main()
