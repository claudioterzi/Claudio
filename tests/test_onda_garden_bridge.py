import unittest
from datetime import datetime, timezone

from sdq1.onda_garden_bridge import (
    GardenBridgeError, build_garden_event, build_review_response, validate_candidate,
)
from sdq1.onda_protocol import ProtocolError, new_envelope, validate_envelope

NOW = datetime(2026, 10, 30, 12, 15, tzinfo=timezone.utc)


def candidate(**overrides):
    value = {
        "candidate_id": "GROWTH-001",
        "project": "bounded-growth-experiment",
        "hypothesis": "A reversible change can improve verified useful value.",
        "metric": "verified outcome delta",
        "next_reversible_test": "Run one sandbox A/B test with rollback.",
        "stage": "SANDBOX",
        "classification": "PRIVATE",
        "evidence_refs": ["local:giardino/checkpoint-001"],
        "requested_action": "REVIEW_ONLY",
    }
    value.update(overrides)
    return value


class OndaGardenBridgeTests(unittest.TestCase):
    def test_candidate_emits_valid_advisory_event(self):
        event = build_garden_event(candidate(), epoch=7, now=NOW)
        self.assertEqual(event["tipo"], "EVENTO")
        self.assertEqual(event["mittente"], "MEMO-002")
        self.assertEqual(event["destinatario"], "RAFFA-001")
        self.assertEqual(event["payload"]["authority"], "DATA_ONLY_ADVISORY")
        self.assertFalse(event["payload"]["candidate"]["auto_execute"])

    def test_consequential_action_requires_claudio_confirmation(self):
        normalized = validate_candidate(candidate(requested_action="SPEND"))
        self.assertTrue(normalized["consequential"])
        self.assertTrue(normalized["requires_claudio_confirmation"])
        self.assertFalse(normalized["auto_execute"])

    def test_sensitive_fields_are_rejected(self):
        with self.assertRaises(GardenBridgeError):
            validate_candidate(candidate(extra={"api_key": "do-not-accept"}))

    def test_bad_stage_is_rejected(self):
        with self.assertRaises(GardenBridgeError):
            validate_candidate(candidate(stage="AUTO_DEPLOY"))

    def test_review_response_is_correlated_and_non_executing(self):
        event = build_garden_event(candidate(), epoch=7, now=NOW)
        response = build_review_response(
            event, disposition="RETEST", rationale="Need held-out evidence.", epoch=7, now=NOW
        )
        self.assertEqual(response["tipo"], "RISPOSTA")
        self.assertEqual(response["id_correlazione"], event["id_messaggio"])
        self.assertFalse(response["payload"]["auto_execute"])

    def test_garden_cannot_escalate_itself_to_command_authority(self):
        msg = new_envelope(
            sender="MEMO-002", recipient="RAFFA-001", kind="COMANDO", epoch=7,
            payload={"action": "execute"}, correlation_id="00000000-0000-4000-8000-000000000001", now=NOW,
        )
        with self.assertRaises(ProtocolError):
            validate_envelope(msg, 7, now=NOW)


if __name__ == "__main__":
    unittest.main()
