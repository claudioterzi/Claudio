"""Contract tests for signed RRR network activation."""
from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

import nacl.signing

from r3.rrr_control import (
    PROTOCOL,
    RRRControlError,
    public_key_from_signing_key,
    replication_direction,
    sign_event,
    verify_event,
)


class TestRRRControl(unittest.TestCase):
    def setUp(self):
        key = nacl.signing.SigningKey.generate()
        self.signing_hex = key.encode().hex()
        self.verify_hex = key.verify_key.encode().hex()
        self.event = sign_event(
            "activate",
            self.signing_hex,
            issuer="Claudio Terzi",
            counter=100,
            issued_at="2026-09-20T03:30:00+00:00",
            nonce="n" * 24,
        )

    def test_signed_event_round_trip_and_public_key(self):
        payload = verify_event(self.event, self.verify_hex)
        self.assertEqual(payload["protocol"], PROTOCOL)
        self.assertEqual(payload["action"], "activate")
        self.assertEqual(payload["counter"], 100)
        self.assertEqual(public_key_from_signing_key(self.signing_hex), self.verify_hex)

    def test_tamper_and_wrong_key_are_rejected(self):
        tampered = dict(self.event)
        tampered["action"] = "deactivate"
        with self.assertRaises(RRRControlError):
            verify_event(tampered, self.verify_hex)

        other = nacl.signing.SigningKey.generate().verify_key.encode().hex()
        with self.assertRaises(RRRControlError):
            verify_event(self.event, other)

    def test_replication_direction_never_resolves_equal_counter_conflict(self):
        event_a = {"event_id": "a"}
        event_b = {"event_id": "b"}
        self.assertEqual(
            replication_direction(
                {"event": event_a, "counter": 3, "event_id": "a"},
                {"event": None, "counter": None, "event_id": None},
            ),
            "local_to_peer",
        )
        self.assertEqual(
            replication_direction(
                {"event": event_a, "counter": 3, "event_id": "a"},
                {"event": event_a, "counter": 3, "event_id": "a"},
            ),
            "equal",
        )
        self.assertEqual(
            replication_direction(
                {"event": event_a, "counter": 3, "event_id": "a"},
                {"event": event_b, "counter": 3, "event_id": "b"},
            ),
            "conflict",
        )

    def test_node_applies_signed_event_and_rejects_replay_downgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "R3_DATA_DIR": tmp,
                "R3_API_TOKEN": "TEST_TOKEN",
                "R3_NODE_ID": "node-test",
                "R3_CONTROL_VERIFY_KEY_HEX": self.verify_hex,
                "R3_SIGNING_KEY_HEX": nacl.signing.SigningKey.generate().encode().hex(),
            }
            with patch.dict(os.environ, env, clear=False):
                import r3.node as node
                node = importlib.reload(node)

                empty = node.rrr_status("Bearer TEST_TOKEN")
                self.assertFalse(empty["active"])
                self.assertIsNone(empty["event_id"])

                applied = node.rrr_event(self.event, "Bearer TEST_TOKEN", "controller")
                self.assertEqual(applied["status"], "applied")
                self.assertTrue(applied["active"])

                duplicate = node.rrr_event(self.event, "Bearer TEST_TOKEN", "peer-a")
                self.assertEqual(duplicate["status"], "already_applied")

                stale = sign_event(
                    "deactivate",
                    self.signing_hex,
                    issuer="Claudio Terzi",
                    counter=99,
                    issued_at="2026-09-20T03:31:00+00:00",
                    nonce="s" * 24,
                )
                with self.assertRaises(Exception) as failure:
                    node.rrr_event(stale, "Bearer TEST_TOKEN", "peer-a")
                self.assertEqual(getattr(failure.exception, "status_code", None), 409)

                newer = sign_event(
                    "deactivate",
                    self.signing_hex,
                    issuer="Claudio Terzi",
                    counter=101,
                    issued_at="2026-09-20T03:32:00+00:00",
                    nonce="d" * 24,
                )
                stopped = node.rrr_event(newer, "Bearer TEST_TOKEN", "controller")
                self.assertFalse(stopped["active"])
                self.assertEqual(stopped["counter"], 101)


if __name__ == "__main__":
    unittest.main()
