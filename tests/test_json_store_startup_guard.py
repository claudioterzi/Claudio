"""New startup-corruption regression suite; synthetic temporary files only."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sdq1.persistence import store


PRIVATE_SENTINEL = "SYNTHETIC_PRIVATE_PAYLOAD"
MALFORMED_FILES = {
    "truncated": b'{"SYNTHETIC_PRIVATE_PAYLOAD": {"v":',
    "invalid_utf8": b'{"SYNTHETIC_PRIVATE_PAYLOAD": {"v": "\xff"}}',
    "non_object": b'["SYNTHETIC_PRIVATE_PAYLOAD"]',
    "non_object_record": b'{"SYNTHETIC_PRIVATE_PAYLOAD": []}',
    "missing_value": b'{"SYNTHETIC_PRIVATE_PAYLOAD": {"scade": null}}',
    "mixed": b'{"live": {"v": 42}, "SYNTHETIC_PRIVATE_PAYLOAD": {}}',
}


class JsonStoreStartupGuardTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.path = Path(self._temporary.name) / "state.json"

    def _assert_corruption_preserved(self, payload: bytes, create):
        self.path.write_bytes(payload)
        caught = None
        try:
            returned = create()
        except ValueError as exc:
            caught = exc
        else:
            # Expose the original loss of data, rather than merely a missing raise.
            returned.set("fresh", "synthetic new state")

        self.assertEqual(self.path.read_bytes(), payload, "corrupt source was overwritten")
        self.assertIsNotNone(caught, "corruption must not become an empty usable store")
        corruption_type = getattr(store, "JsonFileCorruptionError", None)
        self.assertIsNotNone(corruption_type, "use a distinguishable corruption ValueError")
        self.assertIsInstance(caught, corruption_type)
        self.assertIn(str(self.path), str(caught))
        self.assertNotIn(PRIVATE_SENTINEL, str(caught))

    def test_truncated_json_is_preserved_and_rejected(self):
        self._assert_corruption_preserved(MALFORMED_FILES["truncated"], lambda: store.JsonFileStore(path=self.path))

    def test_invalid_utf8_is_preserved_and_rejected(self):
        self._assert_corruption_preserved(MALFORMED_FILES["invalid_utf8"], lambda: store.JsonFileStore(path=self.path))

    def test_non_object_top_levels_are_preserved_and_rejected(self):
        for value in ([], None, PRIVATE_SENTINEL, 7, True):
            with self.subTest(value=value):
                self._assert_corruption_preserved(json.dumps(value).encode(), lambda: store.JsonFileStore(path=self.path))

    def test_non_object_records_are_preserved_and_rejected(self):
        for value in ([], None, PRIVATE_SENTINEL, 7, True):
            with self.subTest(value=value):
                payload = json.dumps({PRIVATE_SENTINEL: value}).encode()
                self._assert_corruption_preserved(payload, lambda: store.JsonFileStore(path=self.path))

    def test_record_missing_value_is_preserved_and_rejected(self):
        self._assert_corruption_preserved(MALFORMED_FILES["missing_value"], lambda: store.JsonFileStore(path=self.path))

    def test_mixed_valid_invalid_records_are_preserved_and_rejected(self):
        self._assert_corruption_preserved(MALFORMED_FILES["mixed"], lambda: store.JsonFileStore(path=self.path))

    def test_invalid_expirations_are_preserved_and_rejected(self):
        for expiry in ("tomorrow", [], {}, True, float("nan"), float("inf"), -float("inf")):
            with self.subTest(expiry=expiry):
                payload = json.dumps({PRIVATE_SENTINEL: {"v": 42, "scade": expiry}}).encode()
                self._assert_corruption_preserved(payload, lambda: store.JsonFileStore(path=self.path))

    def test_factory_propagates_corruption_when_redis_is_unavailable(self):
        with patch.object(store, "_REDIS_SDK_OK", True), patch.object(store, "RedisStore", side_effect=ConnectionError("synthetic unavailable")), patch.object(store.JsonFileStore, "_FILE", self.path):
            for name, payload in MALFORMED_FILES.items():
                with self.subTest(name=name):
                    self._assert_corruption_preserved(payload, lambda: store.crea_store({"host": "offline.invalid", "porta": 6379}))

    def test_factory_propagates_corruption_without_redis_sdk(self):
        with patch.object(store, "_REDIS_SDK_OK", False), patch.object(store.JsonFileStore, "_FILE", self.path):
            self._assert_corruption_preserved(MALFORMED_FILES["truncated"], lambda: store.crea_store({}))

    def test_missing_file_is_initializable(self):
        nested_path = self.path.parent / "new" / "state.json"
        instance = store.JsonFileStore(path=nested_path)
        self.assertIsNone(instance.get("absent"))
        self.assertFalse(nested_path.exists())
        instance.set("fresh", 42)
        self.assertEqual(store.JsonFileStore(path=nested_path).get("fresh"), 42)

    def test_json_values_prefix_and_reopen_roundtrip(self):
        values = {"null": None, "bool": True, "int": 42, "float": 1.5, "str": "città", "list": [1, None, {"x": False}], "object": {"nested": [1, 2]}}
        instance = store.JsonFileStore(prefisso="test:", path=self.path)
        for name, value in values.items():
            instance.set(name, value)
        reopened = store.JsonFileStore(prefisso="test:", path=self.path)
        for name, value in values.items():
            self.assertEqual(reopened.get(name), value)
        self.assertEqual(set(json.loads(self.path.read_text(encoding="utf-8"))), {"test:" + name for name in values})
        self.assertIsNone(store.JsonFileStore(prefisso="other:", path=self.path).get("int"))

    def test_legacy_record_without_expiry_is_supported(self):
        self.path.write_text(json.dumps({"test:k": {"v": {"x": 1}}}), encoding="utf-8")
        instance = store.JsonFileStore(prefisso="test:", path=self.path)
        self.assertEqual(instance.get("k"), {"x": 1})
        instance.set("second", 2)
        self.assertEqual(store.JsonFileStore(prefisso="test:", path=self.path).get("k"), {"x": 1})

    def test_valid_numeric_and_null_expirations_are_supported(self):
        data = {"none": {"v": 1, "scade": None}, "int": {"v": 2, "scade": 3000}, "float": {"v": 3, "scade": 3000.5}, "large_int": {"v": 4, "scade": 10 ** 500}}
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with patch.object(store.time, "time", return_value=2000):
            instance = store.JsonFileStore(path=self.path)
            for name, record in data.items():
                self.assertEqual(instance.get(name), record["v"])
            instance.set("fresh", 5)
        reopened = json.loads(self.path.read_text(encoding="utf-8"))
        for name, record in data.items():
            self.assertEqual(reopened[name], record)

    def test_expired_cleanup_preserves_live_records_and_reopens(self):
        data = {"old": {"v": "expired", "scade": 1000}, "live": {"v": {"kept": True}, "scade": 3000}}
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with patch.object(store.time, "time", return_value=2000):
            instance = store.JsonFileStore(path=self.path)
            self.assertIsNone(instance.get("old"))
            self.assertEqual(instance.get("live"), {"kept": True})
            reopened = store.JsonFileStore(path=self.path)
            self.assertIsNone(reopened.get("old"))
            self.assertEqual(reopened.get("live"), {"kept": True})
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"live": data["live"]})

    def test_factory_uses_healthy_json_without_redis_sdk(self):
        self.path.write_text(json.dumps({"p:kept": {"v": 42}}), encoding="utf-8")
        with patch.object(store, "_REDIS_SDK_OK", False), patch.object(store.JsonFileStore, "_FILE", self.path):
            instance = store.crea_store({"prefisso_chiavi": "p:"})
        self.assertIsInstance(instance, store.JsonFileStore)
        self.assertEqual(instance.get("kept"), 42)

    def test_factory_uses_healthy_json_when_redis_is_unavailable(self):
        self.path.write_text(json.dumps({"kept": {"v": 42}}), encoding="utf-8")
        with patch.object(store, "_REDIS_SDK_OK", True), patch.object(store, "RedisStore", side_effect=ConnectionError("synthetic unavailable")), patch.object(store.JsonFileStore, "_FILE", self.path):
            instance = store.crea_store({"host": "offline.invalid", "porta": 6379})
        self.assertIsInstance(instance, store.JsonFileStore)
        self.assertEqual(instance.get("kept"), 42)

    def test_factory_prefers_healthy_redis(self):
        redis_instance = Mock(spec=store.StatoStore)
        with patch.object(store, "_REDIS_SDK_OK", True), patch.object(store, "RedisStore", return_value=redis_instance), patch.object(store, "JsonFileStore") as json_constructor:
            self.assertIs(store.crea_store({"host": "offline.invalid", "porta": 6379}), redis_instance)
        json_constructor.assert_not_called()

    def test_factory_keeps_fallback_for_non_corruption_io_error(self):
        with patch.object(store, "_REDIS_SDK_OK", False), patch.object(store, "JsonFileStore", side_effect=PermissionError("synthetic denied")):
            instance = store.crea_store({"prefisso_chiavi": "p:"})
        self.assertIsInstance(instance, store.InMemoryStore)
        self.assertEqual(instance.prefisso, "p:")
        instance.set("fresh", 42)
        self.assertEqual(instance.get("fresh"), 42)

    def test_delete_preserves_other_records_across_reopen(self):
        instance = store.JsonFileStore(path=self.path)
        instance.set("remove", 1)
        instance.set("keep", 2)
        self.assertTrue(instance.delete("remove"))
        self.assertFalse(instance.delete("remove"))
        reopened = store.JsonFileStore(path=self.path)
        self.assertIsNone(reopened.get("remove"))
        self.assertEqual(reopened.get("keep"), 2)


if __name__ == "__main__":
    unittest.main()
