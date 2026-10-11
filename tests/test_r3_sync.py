import hashlib
import json
import os
import unittest
from unittest.mock import patch

from api import r3_sync


class FakePipeline:
    def __init__(self, db):
        self.db = db
        self.ops = []
    def watch(self, key):
        self.key = key
    def get(self, key):
        return self.db.get(key)
    def unwatch(self):
        return None
    def multi(self):
        return None
    def set(self, key, value):
        self.ops.append((key, value))
    def execute(self):
        for key, value in self.ops:
            self.db[key] = value
        return [True for _ in self.ops]
    def reset(self):
        self.ops = []


class FakeRedis:
    def __init__(self):
        self.db = {}
    def get(self, key):
        return self.db.get(key)
    def set(self, key, value, ex=None):
        self.db[key] = value
        return True
    def delete(self, key):
        self.db.pop(key, None)
        return 1
    def eval(self, script, count, *keys):
        return 1
    def pipeline(self):
        return FakePipeline(self.db)


def event(claim="uno", previous=None, suffix="1"):
    data = {
        "id": "R3E-test-" + suffix,
        "ts": "2026-09-20T09:00:00.000Z",
        "state": "FATTO",
        "claim": claim,
        "evidence": "test",
        "falsifier": "fallisce",
        "source": "unit",
        "priority": "R3-019",
        "previous_hash": previous,
    }
    stable = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data["hash"] = hashlib.sha256(stable.encode()).hexdigest()
    return data


class R3SyncTests(unittest.TestCase):
    def setUp(self):
        self.redis = FakeRedis()
        self.env = patch.dict(os.environ, {
            "PERFUME_ARCHIVE_SECRET": "s" * 48,
            "PERFUME_ARCHIVE_PASSWORD": "unit-test-value",
        }, clear=False)
        self.env.start()
        self.redis_patch = patch.object(r3_sync, "_redis", return_value=self.redis)
        self.redis_patch.start()
        self.client = r3_sync.app.test_client()

    def tearDown(self):
        self.redis_patch.stop()
        self.env.stop()

    def enroll(self):
        response = self.client.post("/api/r3-sync/enroll", json={"password": "unit-test-value", "device_name": "test"})
        self.assertEqual(response.status_code, 200)
        return response.get_json()["token"]

    def headers(self, token):
        return {"Authorization": "Bearer " + token}

    def test_health_checks_read_write_and_auth(self):
        response = self.client.get("/api/r3-sync/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["read_write"])
        self.assertTrue(body["auth_configured"])

    def test_enrollment_rejects_wrong_value(self):
        response = self.client.post("/api/r3-sync/enroll", json={"password": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_authenticated_round_trip_and_stale_write_rejected(self):
        token = self.enroll()
        initial = self.client.get("/api/r3-sync", headers=self.headers(token))
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(initial.get_json()["revision"], 0)
        first = event()
        write = self.client.put("/api/r3-sync", headers=self.headers(token), json={
            "base_revision": 0, "base_head": None, "events": [first],
        })
        self.assertEqual(write.status_code, 200)
        self.assertEqual(write.get_json()["revision"], 1)
        fetched = self.client.get("/api/r3-sync", headers=self.headers(token)).get_json()
        self.assertEqual(fetched["events"][0]["hash"], first["hash"])
        stale = self.client.put("/api/r3-sync", headers=self.headers(token), json={
            "base_revision": 0, "base_head": None, "events": [first],
        })
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.get_json()["error"], "revision_conflict")

    def test_server_rejects_history_rewrite(self):
        token = self.enroll()
        first = event("radice", suffix="a")
        self.client.put("/api/r3-sync", headers=self.headers(token), json={
            "base_revision": 0, "base_head": None, "events": [first],
        })
        other = event("radice diversa", suffix="b")
        rewrite = self.client.put("/api/r3-sync", headers=self.headers(token), json={
            "base_revision": 1, "base_head": first["hash"], "events": [other],
        })
        self.assertEqual(rewrite.status_code, 409)
        self.assertEqual(rewrite.get_json()["error"], "non_append_only")

    def test_invalid_hash_chain_rejected(self):
        token = self.enroll()
        first = event()
        first["claim"] = "tampered"
        response = self.client.put("/api/r3-sync", headers=self.headers(token), json={
            "base_revision": 0, "base_head": None, "events": [first],
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_ledger")


if __name__ == "__main__":
    unittest.main()
