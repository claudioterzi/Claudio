import unittest

from terzi_flow.core import (
    DistillationPolicy,
    chunk_state,
    decision_signature,
    distill,
)


def relevance_judge(state, questions):
    chunks = {item["id"]: item["text"] for item in state["candidate_evidence"]}
    answers = {}
    for key in questions:
        chunk_id = key.removeprefix("keep_")
        text = chunks[chunk_id].lower()
        keep = 0.99 if ("critical" in text or "contradiction" in text) else 0.01
        answers[key] = {"noul": keep}
    return {"model": "fake-rizzo", "answers": answers}


def audit_judge(state, questions):
    chunks = {item["id"]: item["text"] for item in state["candidate_evidence"]}
    answers = {}
    for key in questions:
        chunk_id = key.removeprefix("keep_")
        text = chunks[chunk_id].lower()
        # Auditor rescues provenance even when primary judge did not.
        keep = 0.95 if "source:" in text else 0.02
        answers[key] = {"noul": keep}
    return {"model": "fake-jev", "answers": answers}


class TerziFlowTests(unittest.TestCase):
    def test_chunking_preserves_text_paragraphs(self):
        chunks = chunk_state("Alpha critical.\n\nBeta noise.")
        self.assertEqual([c.text for c in chunks], ["Alpha critical.", "Beta noise."])
        self.assertNotEqual(chunks[0].sha256, chunks[1].sha256)

    def test_two_judge_distillation_keeps_critical_and_provenance(self):
        state = (
            "Critical evidence changes the decision.\n\n"
            "Routine boilerplate that does not matter.\n\n"
            "Source: primary registry, 2026-09-27."
        )
        questions = {
            "decision": {
                "type": "choice",
                "options": {"a": "A", "b": "B"},
                "instructions": "Which outcome is supported?",
            }
        }
        capsule = distill(
            state,
            questions,
            primary_judge=relevance_judge,
            audit_judge=audit_judge,
            policy=DistillationPolicy(),
        )
        kept = "\n".join(c.text for c in capsule.kept)
        omitted = "\n".join(c.text for c in capsule.omitted)
        self.assertIn("Critical evidence", kept)
        self.assertIn("Source: primary registry", kept)
        self.assertIn("Routine boilerplate", omitted)
        self.assertEqual(capsule.primary_model, "fake-rizzo")
        self.assertEqual(capsule.auditor_model, "fake-jev")
        self.assertGreater(capsule.reduction_ratio, 0)

    def test_exact_duplicates_are_omitted_without_rewriting(self):
        state = "Same paragraph.\n\nSame paragraph.\n\nCritical evidence."
        questions = {"x": {"type": "noul", "instructions": "Is evidence present?"}}
        capsule = distill(
            state,
            questions,
            primary_judge=relevance_judge,
            audit_judge=audit_judge,
        )
        duplicate_actions = [d.action for d in capsule.decisions if d.action == "OMIT_DUPLICATE"]
        self.assertEqual(len(duplicate_actions), 1)
        self.assertEqual(len(capsule.duplicate_of), 1)

    def test_uncertain_is_kept_without_auditor(self):
        def uncertain(state, questions):
            return {
                "model": "uncertain",
                "answers": {key: {"noul": 0.4} for key in questions},
            }

        capsule = distill(
            "One.\n\nTwo.",
            {"x": {"type": "noul", "instructions": "Question?"}},
            primary_judge=uncertain,
        )
        self.assertEqual(len(capsule.omitted), 0)
        self.assertEqual(len(capsule.kept), 2)

    def test_decision_signature_uses_typed_values(self):
        signature = decision_signature(
            {
                "answers": {
                    "a": {"noul": 0.8},
                    "b": {"choice": "x"},
                    "c": {"score": 2},
                }
            }
        )
        self.assertEqual(signature["a"], ("noul", True))
        self.assertEqual(signature["b"], ("choice", "x"))
        self.assertEqual(signature["c"], ("score", 2))


if __name__ == "__main__":
    unittest.main()
