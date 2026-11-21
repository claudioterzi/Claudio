"""Adversarial and restart tests for signed R3 peer receipts (no provider APIs)."""
import hashlib
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

try:
    from nacl.signing import SigningKey
    class TestKey:
        def __init__(self):
            self.key = SigningKey.generate()
        def public_hex(self):
            return self.key.verify_key.encode().hex()
        def sign(self, data):
            return self.key.sign(data).signature
except ImportError:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    class TestKey:
        def __init__(self):
            self.key = Ed25519PrivateKey.generate()
        def public_hex(self):
            return self.key.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
        def sign(self, data):
            return self.key.sign(data)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r3.peer_receipts import PeerReceiptJournal, ReceiptError, PROTOCOL, canonical


class PeerReceiptsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "r3.db"
        self.keys = {x: TestKey() for x in ("node-a", "node-b", "revoked")}
        self.trusted = {
            name: {"verify_key": key.public_hex(),
                "scopes": ["HEARTBEAT", "CHECKPOINT", "PROVIDER_RUN"],
                "active": name != "revoked"}
            for name, key in self.keys.items()
        }
        self.j = PeerReceiptJournal(self.path, self.trusted)
        self.now = int(time.time())

    def sign(self, node="node-a", kind="HEARTBEAT", payload=None, now=None):
        now = self.now if now is None else now
        challenge = self.j.issue_challenge(node, kind, now=now)
        body = {"protocol": PROTOCOL, "node_id": node, "kind": kind,
                "challenge": challenge["challenge"], "issued_at": now,
                "payload": payload if payload is not None else {"runtime_id": "runtime-1", "boot_id": "boot-1"}}
        return {**body, "signature": self.keys[node].sign(canonical(body)).hex()}

    def checkpoint(self, *, text="Knowledge checked", classification="PUBLIC", readers=None):
        data = {"classification": classification,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "ref": None if classification == "PUBLIC" else "vault://reference-42",
                "text": text if classification == "PUBLIC" else None,
                "readers": readers or []}
        return self.sign(kind="CHECKPOINT", payload=data)

    def test_signed_heartbeat_and_repeated_submission_rejected(self):
        receipt = self.sign()
        proof = self.j.accept(receipt, now=self.now)
        self.assertEqual(proof["state"], "SIGNED_NODE_RECEIPT")
        self.assertEqual(proof["provider_state"], "UNVERIFIED")
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)
        self.assertEqual(self.j.audit()["count"], 1)

    def test_tamper_signed_payload(self):
        receipt = self.sign()
        receipt["payload"]["boot_id"] = "forged"
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)
        self.assertEqual(self.j.audit()["count"], 0)

    def test_wrong_signer_identity(self):
        receipt = self.sign()
        body = {k:v for k,v in receipt.items() if k != "signature"}
        receipt["signature"] = self.keys["node-b"].sign(canonical(body)).hex()
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)

    def test_revoked_node_fails_closed(self):
        with self.assertRaises(ReceiptError):
            self.j.issue_challenge("revoked", "HEARTBEAT")

    def test_unlisted_scope_fails_closed(self):
        self.trusted["node-a"]["scopes"] = ["HEARTBEAT"]
        with self.assertRaises(ReceiptError):
            self.j.issue_challenge("node-a", "CHECKPOINT")

    def test_expired_challenge_and_future_time(self):
        old = self.sign()
        with self.assertRaises(ReceiptError):
            self.j.accept(old, now=self.now + 121)
        future = self.sign(now=self.now + 200)
        with self.assertRaises(ReceiptError):
            self.j.accept(future, now=self.now)

    def test_cross_kind_challenge_substitution(self):
        receipt = self.sign(kind="HEARTBEAT")
        receipt["kind"] = "PROVIDER_RUN"
        receipt["payload"] = {"provider": "gemini", "model": "x", "runtime_id": "runtime-1",
                              "request_sha256": "a"*64, "response_sha256": "b"*64}
        body = {k:v for k,v in receipt.items() if k != "signature"}
        receipt["signature"] = self.keys["node-a"].sign(canonical(body)).hex()
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)

    def test_private_pointer_never_stores_cleartext(self):
        receipt = self.checkpoint(text="SECRET CONTENT", classification="PRIVATE", readers=["node-b"])
        self.j.accept(receipt, now=self.now)
        self.assertNotIn("SECRET CONTENT", self.path.read_bytes().decode("utf-8", "ignore"))
        self.assertEqual(len(self.j.view("node-b", authenticated=True)), 1)
        with self.assertRaises(ReceiptError):
            self.j.view("revoked", authenticated=True)
        self.assertIsNone(self.j.view("node-b", authenticated=True)[0]["checkpoint"]["text"])

    def test_private_text_injection_rejected(self):
        receipt = self.checkpoint(classification="PRIVATE")
        receipt["payload"]["text"] = "password=do-not-write"
        body = {k:v for k,v in receipt.items() if k != "signature"}
        receipt["signature"] = self.keys["node-a"].sign(canonical(body)).hex()
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)

    def test_public_digest_mismatch_rejected(self):
        receipt = self.checkpoint()
        receipt["payload"]["sha256"] = "0" * 64
        body = {k:v for k,v in receipt.items() if k != "signature"}
        receipt["signature"] = self.keys["node-a"].sign(canonical(body)).hex()
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)

    def test_private_access_control(self):
        self.j.accept(self.checkpoint(classification="SEALED", readers=["node-b"]), now=self.now)
        self.assertEqual(len(self.j.view("node-b", authenticated=True)), 1)
        self.assertEqual(len(self.j.view("OWNER", authenticated=True)), 1)
        with self.assertRaises(ReceiptError):
            self.j.view("node-b", authenticated=False)
        with self.assertRaises(ReceiptError):
            self.j.view("untrusted", authenticated=True)

    def test_two_nodes_and_reopen_db(self):
        self.j.accept(self.sign(node="node-a"), now=self.now)
        self.j.accept(self.sign(node="node-b"), now=self.now)
        reopened = PeerReceiptJournal(self.path, self.trusted)
        self.assertTrue(reopened.audit()["ok"])
        self.assertEqual(reopened.audit()["count"], 2)
        self.assertEqual(reopened.status(now=self.now)["nodes"]["node-a"]["state"], "SIGNED_RECENT")
        self.assertEqual(reopened.status(now=self.now + 150)["nodes"]["node-a"]["state"], "STALE")
        self.assertEqual(reopened.status(now=self.now)["nodes"]["revoked"]["state"], "UNVERIFIED")

    def test_ledger_tampering_detected(self):
        self.j.accept(self.sign(), now=self.now)
        db = sqlite3.connect(self.path)
        try:
            db.execute("UPDATE peer_receipts SET body=? WHERE seq=1", ('{"fake":true}',))
            db.commit()
        finally:
            db.close()
        self.assertFalse(self.j.audit()["ok"])
        self.assertEqual(self.j.status()["state"], "WATCH_BLOCKED")
        with self.assertRaises(ReceiptError):
            self.j.view("OWNER", authenticated=True)

    def test_provider_receipt_never_elevates_provider_state(self):
        p = {"provider": "gemini", "model": "gemini-test", "runtime_id": "host-1",
             "request_sha256": "a"*64, "response_sha256": "b"*64}
        self.j.accept(self.sign(kind="PROVIDER_RUN", payload=p), now=self.now)
        self.assertEqual(self.j.status(now=self.now)["nodes"]["node-a"]["provider_execution"], "UNVERIFIED")

    def test_bad_envelope_fields_fail(self):
        receipt = self.sign()
        receipt["role"] = "OWNER"
        with self.assertRaises(ReceiptError):
            self.j.accept(receipt, now=self.now)


if __name__ == "__main__":
    unittest.main()