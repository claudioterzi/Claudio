"""Contract tests for signed RRR network activation."""
from __future__ import annotations

import importlib
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import nacl.signing

from r3.rrr_control import (
    POLICY_SHA256,
    PROTOCOL,
    RRRControlError,
    _next_counter,
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
        self.assertEqual(payload["policy_sha256"], POLICY_SHA256)
        self.assertEqual(payload["action"], "activate")
        self.assertEqual(payload["counter"], 100)
        self.assertEqual(public_key_from_signing_key(self.signing_hex), self.verify_hex)

    def test_tamper_and_wrong_key_are_rejected(self):
        tampered = dict(self.event)
        tampered["action"] = "deactivate"
        with self.assertRaises(RRRControlError):
            verify_event(tampered, self.verify_hex)

        wrong_policy = dict(self.event)
        wrong_policy["policy_sha256"] = "0" * 64
        with self.assertRaisesRegex(RRRControlError, "policy hash mismatch"):
            verify_event(wrong_policy, self.verify_hex)

        other = nacl.signing.SigningKey.generate().verify_key.encode().hex()
        with self.assertRaises(RRRControlError):
            verify_event(self.event, other)

    def test_sync_does_not_trust_unsigned_status_ordering_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "R3_DATA_DIR": tmp,
                "R3_CONTROL_VERIFY_KEY_HEX": self.verify_hex,
            }
            with patch.dict(os.environ, env, clear=False):
                import r3.sync as sync
                sync = importlib.reload(sync)

                stored = {
                    key: value
                    for key, value in self.event.items()
                    if key != "schema"
                }
                correct = {
                    "event": stored,
                    "counter": self.event["counter"],
                    "event_id": self.event["event_id"],
                }
                trusted = sync._trusted_rrr_view(correct)
                self.assertEqual(trusted["counter"], 100)
                self.assertEqual(trusted["event_id"], self.event["event_id"])

                forged_counter = dict(correct)
                forged_counter["counter"] = 10**30
                with self.assertRaisesRegex(
                    RRRControlError, "status counter disagrees"
                ):
                    sync._trusted_rrr_view(forged_counter)

                forged_id = dict(correct)
                forged_id["event_id"] = "f" * 64
                with self.assertRaisesRegex(
                    RRRControlError, "status event_id disagrees"
                ):
                    sync._trusted_rrr_view(forged_id)

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

    def test_durable_counter_never_moves_back_when_wall_clock_regresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            counter_db = os.path.join(tmp, "controller-counter.db")
            with patch("r3.rrr_control.time.time_ns", side_effect=[1000, 900, 900]):
                first = _next_counter(counter_db)
                second = _next_counter(counter_db)
                third = _next_counter(counter_db)
        self.assertEqual(first, 1000)
        self.assertEqual(second, 1001)
        self.assertEqual(third, 1002)

    def test_concurrent_writers_serialize_order_and_audit_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "R3_DATA_DIR": tmp,
                "R3_API_TOKEN": "TEST_TOKEN",
                "R3_NODE_ID": "node-concurrent-test",
                "R3_CONTROL_VERIFY_KEY_HEX": self.verify_hex,
                "R3_SIGNING_KEY_HEX": nacl.signing.SigningKey.generate().encode().hex(),
            }
            with patch.dict(os.environ, env, clear=False):
                import r3.node as node
                node = importlib.reload(node)

                lower = sign_event(
                    "activate",
                    self.signing_hex,
                    issuer="Claudio Terzi",
                    counter=500,
                    issued_at="2026-09-20T06:50:00+00:00",
                    nonce="concurrent-lower-0001",
                )
                higher = sign_event(
                    "deactivate",
                    self.signing_hex,
                    issuer="Claudio Terzi",
                    counter=501,
                    issued_at="2026-09-20T06:50:00+00:00",
                    nonce="concurrent-higher-0001",
                )
                barrier = threading.Barrier(2)

                def apply(event):
                    barrier.wait(timeout=5)
                    try:
                        result = node.rrr_event(event, "Bearer TEST_TOKEN", "concurrent-test")
                        return ("ok", result["counter"])
                    except Exception as exc:
                        return ("error", getattr(exc, "status_code", None))

                with ThreadPoolExecutor(max_workers=2) as pool:
                    outcomes = list(pool.map(apply, [lower, higher]))

                latest = node.rrr_status("Bearer TEST_TOKEN")
                self.assertEqual(latest["counter"], 501)
                self.assertEqual(latest["event_id"], higher["event_id"])
                self.assertFalse(latest["active"])
                self.assertIn(("ok", 501), outcomes)
                self.assertTrue(
                    ("ok", 500) in outcomes or ("error", 409) in outcomes,
                    outcomes,
                )

                with node._conn() as db:
                    event_count = db.execute(
                        "SELECT COUNT(*) FROM protocol_events"
                    ).fetchone()[0]
                    audit_count = db.execute(
                        "SELECT COUNT(*) FROM audit_log WHERE event = 'rrr_event'"
                    ).fetchone()[0]
                self.assertEqual(event_count, audit_count)

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

                policy = node.rrr_policy()
                self.assertEqual(policy["protocol"], PROTOCOL)
                self.assertEqual(policy["policy_sha256"], POLICY_SHA256)
                self.assertTrue(policy["required_on_join"])
                self.assertEqual(policy["activation_phrase"], "ROSSO ROSSO ROSSO")

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
