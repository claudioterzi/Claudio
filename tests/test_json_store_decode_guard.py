"""Supplement frozen after independent review found parser-capacity bypasses."""

from __future__ import annotations

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
        original = sys.getrecursionlimit()
        self.addCleanup(sys.setrecursionlimit, original)
        sys.setrecursionlimit(1000)
        payload = b'{"SYNTHETIC_PRIVATE_PAYLOAD":{"v":' + b"[" * 5000 + b"0" + b"]" * 5000 + b"}}"
        self._assert_direct_and_factory_reject(payload)


if __name__ == "__main__":
    unittest.main()
