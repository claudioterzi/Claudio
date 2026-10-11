import json
import tempfile
import unittest
from pathlib import Path

from sdq1.benchmark_controlled import (
    conditions,
    freeze_plan,
    load_dataset,
    run_controlled,
    save_run,
)


DATASET = Path("benchmarks/r3_019_controlled_v1.json")


class ControlledBenchmarkTests(unittest.TestCase):
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
