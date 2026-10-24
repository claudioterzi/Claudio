"""Offline falsifiers for three bounded API admission gates.

Only synthetic keys and local Flask test_client calls; no real providers or files.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import api.server as server


class APIGates(unittest.TestCase):
    def setUp(self):
        self.saved_keys = server._API_KEYS
        server._API_KEYS = {"synthetic-owner-key"}
        server.app.testing = True
        self.client = server.app.test_client()
        self.auth = {"X-API-Key": "synthetic-owner-key"}

    def tearDown(self):
        server._API_KEYS = self.saved_keys

    def test_monitor_requires_key_before_state_reads(self):
        with patch.object(server.Path, "exists", return_value=False) as exists:
            for headers in ({}, {"X-API-Key": "wrong"}):
                with self.subTest(headers=headers):
                    result = self.client.get("/monitor", headers=headers)
                    self.assertEqual(result.status_code, 401)
            exists.assert_not_called()

    def test_monitor_valid_key_and_development_mode(self):
        with patch.object(server.Path, "exists", return_value=False):
            self.assertEqual(self.client.get("/monitor", headers=self.auth).status_code, 200)
            server._API_KEYS = set()
            self.assertEqual(self.client.get("/monitor").status_code, 200)

    def test_ask_malformed_json_never_starts_system(self):
        malformed = [[], 1, True, "hello", {"testo": None},
                     {"testo": []}, {"testo": {}}, {"testo": 7},
                     {"testo": False}]
        with patch.object(server, "_get_sistema", side_effect=AssertionError("provider/system touched")) as get_sys:
            for payload in malformed:
                with self.subTest(payload=payload):
                    response = self.client.post("/ask", headers=self.auth, json=payload)
                    self.assertEqual(response.status_code, 400)
            get_sys.assert_not_called()

    def test_ask_valid_and_auth_order(self):
        self.assertEqual(self.client.post("/ask", json={"testo": "ok"}).status_code, 401)
        execution = SimpleNamespace(
            output_finale={"risposta_finale": "synthetic-answer"},
            interrotta=False, motivo_interruzione=None, passi=[]
        )
        orch = Mock()
        orch.esegui.return_value = execution
        with patch.object(server, "_get_sistema", return_value=(orch, None, None, None, None, None, None)):
            response = self.client.post("/ask", headers=self.auth, json={"testo": " test "})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["risposta"], "synthetic-answer")
            orch.esegui.assert_called_once_with({"testo": "test"})

    def test_futures_invalid_selector_precedes_all_effects(self):
        invalid = [[], 17, "ALPHA", {"scenari": "ALPHA"},
                   {"scenari": {"ALPHA": True}}, {"scenari": []},
                   {"scenari": None}, {"scenari": False},
                   {"scenari": [12]}, {"scenari": [None]},
                   {"scenari": ["UNKNOWN"]}]
        with patch.object(server, "_get_sistema", side_effect=AssertionError("system touched")) as get_sys:
            for payload in invalid:
                with self.subTest(payload=payload):
                    response = self.client.post("/futures/run", headers=self.auth, json=payload)
                    self.assertEqual(response.status_code, 400)
            get_sys.assert_not_called()

    def test_futures_valid_selection_and_auth_order(self):
        self.assertEqual(self.client.post("/futures/run", json={}).status_code, 401)
        from sdq1.futures import SCENARI_DEFAULT
        valid = SCENARI_DEFAULT[0].id
        call_log = []
        class FakeSim:
            def __init__(self, llm_fn):
                pass
            def simula_parallelo(self, scenarios):
                call_log.append([x.id for x in scenarios])
                return [SimpleNamespace(successo=True, to_dict=lambda: {"ok": True}) for _ in scenarios]
            def salva_report(self, rows):
                call_log.append("synthetic-report")
                return "not-a-real-file"
        with patch.object(server, "_get_sistema", return_value=(None, Mock())), patch("sdq1.futures.SimulatoreScenari", FakeSim):
            all_response = self.client.post("/futures/run", headers=self.auth, json={})
            selected_response = self.client.post("/futures/run", headers=self.auth, json={"scenari": [valid]})
        self.assertEqual(all_response.status_code, 200)
        self.assertEqual(all_response.get_json()["n_scenari"], len(SCENARI_DEFAULT))
        self.assertEqual(selected_response.status_code, 200)
        self.assertEqual(selected_response.get_json()["n_scenari"], 1)
        self.assertEqual(call_log[-2], [valid])
        self.assertEqual(call_log.count("synthetic-report"), 2)


if __name__ == "__main__":
    unittest.main()
