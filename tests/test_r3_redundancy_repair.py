"""Falsifiers for R3 redundant-node corruption repair."""
from __future__ import annotations

import asyncio
import hashlib
import importlib
import io
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nacl.signing
from fastapi import HTTPException, UploadFile


class NodeRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "R3_DATA_DIR": self.tmp.name,
                "R3_API_TOKEN": "TEST_TOKEN",
                "R3_NODE_ID": "repair-test",
                "R3_SIGNING_KEY_HEX": nacl.signing.SigningKey.generate().encode().hex(),
                "R3_CONTROL_VERIFY_KEY_HEX": nacl.signing.SigningKey.generate().verify_key.encode().hex(),
                "R3_REQUIRE_RRR_ACTIVE": "false",
                "R3_REQUIRE_DURABLE_STATE": "false",
            },
            clear=False,
        )
        self.env.start()
        import r3.node as node

        self.node = importlib.reload(node)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def _receive(self, data: bytes):
        upload = UploadFile(filename="replica.bin", file=io.BytesIO(data))
        return asyncio.run(
            self.node.sync_receive(upload, authorization="Bearer TEST_TOKEN")
        )

    def test_existing_corrupt_replica_is_repaired_atomically(self):
        good = b"canonical replica bytes"
        doc_id = hashlib.sha256(good).hexdigest()
        self.assertEqual(self._receive(good)["status"], "stored")

        path = self.node._doc_path(doc_id)
        path.write_bytes(b"corrupted")
        result = self._receive(good)

        self.assertEqual(result["status"], "repaired")
        self.assertEqual(path.read_bytes(), good)
        with self.node._conn() as db:
            repaired = db.execute(
                "SELECT COUNT(*) FROM audit_log WHERE event = 'sync_repair'"
            ).fetchone()[0]
        self.assertEqual(repaired, 1)

    def test_corrupt_replica_is_not_served_to_peers(self):
        good = b"canonical replica bytes"
        doc_id = hashlib.sha256(good).hexdigest()
        self._receive(good)
        self.node._doc_path(doc_id).write_bytes(b"corrupted")

        with self.assertRaises(HTTPException) as ctx:
            self.node.download(doc_id, authorization="Bearer TEST_TOKEN")
        self.assertEqual(ctx.exception.status_code, 409)


class SyncRepairTests(unittest.TestCase):
    def _seed_corrupt_db(self, root: Path, good: bytes) -> str:
        doc_id = hashlib.sha256(good).hexdigest()
        docs = root / "docs"
        docs.mkdir(parents=True)
        (docs / doc_id).write_bytes(b"broken-local-copy")

        db = sqlite3.connect(str(root / "r3.db"))
        db.execute(
            """CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                signature TEXT NOT NULL,
                size INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                deleted INTEGER DEFAULT 0
            )"""
        )
        db.execute(
            """INSERT INTO documents
               (id, filename, sha256, signature, size, uploaded_at, deleted)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (doc_id, "x", doc_id, "sig", len(good), "now"),
        )
        db.commit()
        db.close()
        return doc_id

    def test_integrity_check_skips_bad_peer_and_repairs_from_healthy_peer(self):
        import r3.sync as sync

        good = b"healthy-peer-copy"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_id = self._seed_corrupt_db(root, good)

            def pull(peer, requested):
                self.assertEqual(requested, doc_id)
                if peer == "peer-bad":
                    return b"also-corrupt"
                return good

            def push(local_url, requested, data, filename):
                self.assertEqual(requested, doc_id)
                self.assertEqual(data, good)
                (root / "docs" / requested).write_bytes(data)

            with (
                patch.object(sync, "DATA_DIR", root),
                patch.object(sync, "PEER_URLS", ["peer-bad", "peer-good"]),
                patch.object(sync, "LOCAL_URL", "local"),
                patch.object(sync, "_pull_doc", side_effect=pull),
                patch.object(sync, "_push_doc", side_effect=push),
            ):
                remaining = sync.integrity_check()

            self.assertEqual(remaining, [])
            self.assertEqual((root / "docs" / doc_id).read_bytes(), good)

    def test_integrity_check_keeps_failure_visible_when_no_peer_proves_hash(self):
        import r3.sync as sync

        good = b"healthy-peer-copy"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_id = self._seed_corrupt_db(root, good)

            with (
                patch.object(sync, "DATA_DIR", root),
                patch.object(sync, "PEER_URLS", ["peer-bad"]),
                patch.object(sync, "_pull_doc", return_value=b"wrong"),
                patch.object(sync, "_push_doc") as push,
            ):
                remaining = sync.integrity_check()

            self.assertEqual(remaining, [doc_id])
            push.assert_not_called()


if __name__ == "__main__":
    unittest.main()
