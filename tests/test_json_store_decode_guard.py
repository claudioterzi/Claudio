"""Supplement frozen after independent review found parser-capacity bypasses."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sdq1.persistence import store


class JsonStoreDecodeGuardTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.path = Path(self._temporary.name) / "state.json"

    def _assert_direct_and_factory_reject(self, payload):
        for route in ("direct", "factory"):
            with self.subTest(route=route):
                self.path.write_bytes(payload)
                caught = None
                try:
                    with patch.object(store, "_REDIS_SDK_OK", False), patch.object(store.JsonFileStore, "_FILE", self.path):
                        returned = store.JsonFileStore(path=self.path) if route == "direct" else store.crea_store({})
                except Exception as exc:
                    caught = exc
                else:
                    returned.set("fresh", "synthetic new state")
                self.assertEqual(self.path.read_bytes(), payload)
                self.assertIsInstance(caught, store.JsonFileCorruptionError, "parser rejection must not become a usable memory fallback")
                self.assertIn(str(self.path), str(caught))
                self.assertNotIn("SYNTHETIC_PRIVATE_PAYLOAD", str(caught))

    def test_integer_digit_limit_error_rejects_direct_and_factory_startup(self):
        original = sys.get_int_max_str_digits()
        self.addCleanup(sys.set_int_max_str_digits, original)
        sys.set_int_max_str_digits(4300)
        payload = b'{"SYNTHETIC_PRIVATE_PAYLOAD":{"v":' + b"9" * 4301 + b"}}"
        self._assert_direct_and_factory_reject(payload)

    def test_recursion_limit_error_rejects_direct_and_factory_startup(self):
        # Decoder capacity differs across CPython versions. Always exercise the
        # error boundary deterministically without relying on native stack depth.
        with patch.object(store.json, "loads", side_effect=RecursionError("SYNTHETIC_PRIVATE_PAYLOAD")):
            self._assert_direct_and_factory_reject(b'{"SYNTHETIC_PRIVATE_PAYLOAD":{"v":0}}')

        original = sys.getrecursionlimit()
        self.addCleanup(sys.setrecursionlimit, original)
        sys.setrecursionlimit(1000)
        payload = b'{"SYNTHETIC_PRIVATE_PAYLOAD":{"v":' + b"[" * 5000 + b"0" + b"]" * 5000 + b"}}"
        # Keep the bounded real-input control (about 10 KiB). Python 3.11 rejects
        # this depth; newer native decoders can accept and round-trip it. A valid
        # accepted value is not corruption and reading it must not alter bytes.
        try:
            json.loads(payload)
        except RecursionError:
            self._assert_direct_and_factory_reject(payload)
        else:
            for route in ("direct", "factory"):
                with self.subTest(route=route, decoder="accepts_real_input"):
                    self.path.write_bytes(payload)
                    with patch.object(store, "_REDIS_SDK_OK", False), patch.object(store.JsonFileStore, "_FILE", self.path):
                        loaded = store.JsonFileStore(path=self.path) if route == "direct" else store.crea_store({})
                    value = loaded.get("SYNTHETIC_PRIVATE_PAYLOAD")
                    for _ in range(5000):
                        self.assertIsInstance(value, list)
                        self.assertEqual(len(value), 1)
                        value = value[0]
                    self.assertEqual(value, 0)
                    self.assertEqual(self.path.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
