import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from r3.reflex.decider import Decision, ReflexDecider
from r3.reflex.executor import ExecutionResult
from r3.reflex.runtime import ReflexRuntime
from r3.reflex.voice import SpeechEvent, VoiceReflexController, parse_speech_event


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "r3_reflex.json").read_text(encoding="utf-8"))


class StubDecider:
    backend = "stub"

    def __init__(self, decision):
        self.decision = decision

    def decide(self, _text):
        return self.decision


class ReflexThresholdTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(CONFIG)
        self.config["backend"] = "demo"
        self.config["dry_run"] = True
        self.decider = ReflexDecider(self.config)

    def test_partial_spanish_waits_then_fires(self):
        first = self.decider.decide("abre el")
        middle = self.decider.decide("abre el bloc")
        final = self.decider.decide("abre el bloc de notas")

        self.assertLess(first.complete, 0.55)
        self.assertGreaterEqual(middle.complete, 0.55)
        self.assertLess(middle.complete, 0.80)
        self.assertGreaterEqual(final.complete, 0.80)
        self.assertEqual(final.action, "open_app")
        self.assertEqual(final.target, "bloc de notas")

    def test_unknown_target_never_becomes_closed_catalog_target(self):
        decision = self.decider.decide("apri photoshop quantum")
        self.assertEqual(decision.target, "none")
        runtime = ReflexRuntime(self.config, decider=self.decider)
        outcome = runtime.evaluate("apri photoshop quantum")
        self.assertFalse(outcome.executed)
        self.assertNotEqual(outcome.stance, "SCATTO")


class ReflexRuntimeGateTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(CONFIG)
        self.config["dry_run"] = True

    def test_dry_run_never_calls_executor(self):
        executor = Mock(return_value=ExecutionResult(True, "open_app", "should not happen"))
        runtime = ReflexRuntime(self.config, executor=executor)
        outcome = runtime.evaluate("apri il blocco note", execute_actions=True)
        self.assertEqual(outcome.stance, "SCATTO")
        self.assertFalse(outcome.executed)
        self.assertEqual(outcome.detail, "dry-run")
        executor.assert_not_called()

    def test_static_risk_blocks_close_even_if_model_says_safe(self):
        decision = Decision(
            complete=0.99,
            action="close_app",
            target="blocco note",
            destructive=0.0,
            provider="stub",
        )
        executor = Mock(return_value=ExecutionResult(True, "close_app", "closed"))
        runtime = ReflexRuntime(
            {**self.config, "dry_run": False},
            decider=StubDecider(decision),
            executor=executor,
        )
        outcome = runtime.evaluate("chiudi blocco note", execute_actions=True)
        self.assertEqual(outcome.stance, "BLOCCO")
        self.assertFalse(outcome.executed)
        executor.assert_not_called()

    def test_explicit_destructive_override_is_still_separate_from_execute(self):
        decision = Decision(
            complete=0.99,
            action="close_app",
            target="blocco note",
            destructive=0.0,
            provider="stub",
        )
        executor = Mock(return_value=ExecutionResult(True, "close_app", "closed"))
        runtime = ReflexRuntime(
            {**self.config, "dry_run": False},
            decider=StubDecider(decision),
            executor=executor,
        )
        outcome = runtime.evaluate(
            "chiudi blocco note",
            execute_actions=True,
            allow_destructive=True,
        )
        self.assertTrue(outcome.executed)
        executor.assert_called_once()

    def test_duplicate_within_cooldown_does_not_fire_twice(self):
        executor = Mock(return_value=ExecutionResult(True, "open_app", "opened"))
        times = iter([10.0, 10.1])
        runtime = ReflexRuntime(
            {**self.config, "dry_run": False},
            executor=executor,
            clock=lambda: next(times),
        )
        first = runtime.evaluate("apri il blocco note", execute_actions=True)
        second = runtime.evaluate("apri il blocco note", execute_actions=True)
        self.assertTrue(first.executed)
        self.assertFalse(second.executed)
        self.assertIn("duplicate", second.detail)
        self.assertEqual(executor.call_count, 1)


class ReflexTypeSafeTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(CONFIG)
        self.config["backend"] = "typesafe"

    @patch("r3.reflex.decider.system_one")
    def test_uses_shared_typesafe_transport_and_parses_typed_answer(self, system_one):
        system_one.return_value = {
            "model": "jev-test",
            "answers": {
                "complete": {"type": "noul", "noul": 0.93},
                "action": {
                    "type": "choice",
                    "choice": "open_app",
                    "confidence": 0.9,
                    "probabilities": {"open_app": 0.9, "none": 0.1},
                },
                "target": {
                    "type": "choice",
                    "choice": "blocco note",
                    "confidence": 0.9,
                    "probabilities": {"blocco note": 0.9, "none": 0.1},
                },
                "destructive": {"type": "noul", "noul": 0.05},
            },
        }
        decision = ReflexDecider(self.config).decide("apri il blocco note")
        self.assertEqual(decision.provider, "typesafe")
        self.assertEqual(decision.model, "jev-test")
        self.assertEqual(decision.action, "open_app")
        self.assertEqual(decision.target, "blocco note")
        system_one.assert_called_once()

    @patch("r3.reflex.decider.system_one")
    def test_typesafe_failure_fails_closed_without_fake_demo(self, system_one):
        system_one.side_effect = RuntimeError("provider down")
        decision = ReflexDecider(self.config).decide("apri il blocco note")
        self.assertEqual(decision.provider, "typesafe_unavailable")
        self.assertEqual(decision.action, "none")
        self.assertEqual(decision.complete, 0.0)
        self.assertEqual(decision.raw["error_class"], "RuntimeError")

    @patch("r3.reflex.decider.system_one")
    def test_out_of_catalog_typed_target_is_rejected(self, system_one):
        system_one.return_value = {
            "model": "jev-test",
            "answers": {
                "complete": {"type": "noul", "noul": 0.99},
                "action": {
                    "type": "choice",
                    "choice": "open_app",
                    "probabilities": {"open_app": 1.0},
                },
                "target": {
                    "type": "choice",
                    "choice": "photoshop quantum",
                    "probabilities": {"photoshop quantum": 1.0},
                },
                "destructive": {"type": "noul", "noul": 0.0},
            },
        }
        decision = ReflexDecider(self.config).decide("apri photoshop quantum")
        self.assertEqual(decision.provider, "typesafe_unavailable")
        self.assertEqual(decision.action, "none")


class ReflexVoiceTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(CONFIG)
        self.config["dry_run"] = False
        self.decision = Decision(
            complete=0.99,
            action="open_app",
            target="blocco note",
            destructive=0.0,
            provider="stub",
        )

    def test_parses_windows_json_event(self):
        event = parse_speech_event(
            '{"type":"recognized","text":"apri il blocco note","confidence":0.91,"final":true}'
        )
        self.assertIsNotNone(event)
        self.assertTrue(event.final)
        self.assertEqual(event.text, "apri il blocco note")
        self.assertAlmostEqual(event.confidence, 0.91)

    def test_status_line_is_not_a_speech_event(self):
        self.assertIsNone(
            parse_speech_event('{"type":"status","status":"ready","active_culture":"it-IT"}')
        )

    def test_two_stable_partial_hypotheses_required_before_execution(self):
        executor = Mock(return_value=ExecutionResult(True, "open_app", "opened"))
        runtime = ReflexRuntime(
            self.config,
            decider=StubDecider(self.decision),
            executor=executor,
        )
        controller = VoiceReflexController(
            runtime,
            stability_hits=2,
            min_confidence=0.20,
            execute_actions=True,
        )
        event = SpeechEvent("apri il blocco note", 0.80, False, "hypothesis")
        first = controller.on_event(event)
        second = controller.on_event(event)
        self.assertEqual(first.stance, "ATTESA")
        self.assertFalse(first.executed)
        self.assertTrue(second.executed)
        self.assertEqual(executor.call_count, 1)

    def test_final_recognition_can_execute_without_second_partial(self):
        executor = Mock(return_value=ExecutionResult(True, "open_app", "opened"))
        runtime = ReflexRuntime(
            self.config,
            decider=StubDecider(self.decision),
            executor=executor,
        )
        controller = VoiceReflexController(
            runtime,
            stability_hits=3,
            execute_actions=True,
        )
        outcome = controller.on_event(
            SpeechEvent("apri il blocco note", 0.85, True, "recognized")
        )
        self.assertTrue(outcome.executed)
        executor.assert_called_once()

    def test_low_confidence_partial_is_held(self):
        executor = Mock(return_value=ExecutionResult(True, "open_app", "opened"))
        runtime = ReflexRuntime(
            self.config,
            decider=StubDecider(self.decision),
            executor=executor,
        )
        controller = VoiceReflexController(
            runtime,
            stability_hits=2,
            min_confidence=0.50,
            execute_actions=True,
        )
        outcome = controller.on_event(
            SpeechEvent("apri il blocco note", 0.20, False, "hypothesis")
        )
        self.assertEqual(outcome.stance, "FERMO")
        executor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
