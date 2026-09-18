"""Cross-repository contract test; set R3_BOT_CHECKOUT to the bot checkout.

Real SQLite + bot HTTP handler + website Flask routes. Only the external AI
provider and the network transport to the deployed hosts are substituted.
No Telegram account, token, private records or paid API calls are used.
"""
import copy
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from api import raffaello as site, tarot_alpha


@unittest.skipUnless(os.getenv("R3_BOT_CHECKOUT"), "Set R3_BOT_CHECKOUT for cross-repository integration")
class RaffaelloRoundtrip(unittest.TestCase):
    def test_site_to_bot_to_same_site_reading(self):
        checkout = Path(os.environ["R3_BOT_CHECKOUT"]).resolve()
        sys.path.insert(0, str(checkout))
        # Reuse the bot's installed dev environment if the caller lacks PTB.
        sys.path.extend(str(p) for p in checkout.glob(".venv/lib/python*/site-packages"))
        from bot import db, main, raffaello_store as store, raffaello_engine as engine
        secret = "integration-test-secret-" * 2
        root = Path(__file__).parents[1]
        self.assertEqual(json.loads((checkout / "bot/data/alpha74.json").read_text()), json.loads((root / "tarocchi_quantici_alpha.json").read_text()))
        with tempfile.TemporaryDirectory() as tmp, patch.object(db, "DATABASE_PATH", str(Path(tmp) / "bot.db")), patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": secret, "RAFFAELLO_ALLOWED_USERS": "17,18", "RAFFAELLO_BOT_URL": "https://bot.example.invalid"}):
            db.init_db(); store.init(); db.upsert_user(17, "test", "Test")
            db.add_action(17, "An existing action to preserve")
            server = ThreadingHTTPServer(("127.0.0.1", 0), main._Health)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            def transport(method, path, body=None, token=None):
                headers = {"Content-Type": "application/json", "X-Raffaello-Secret": secret}
                if token: headers["X-Raffaello-Session"] = token
                req = Request(f"http://127.0.0.1:{server.server_port}/raffaello/v1"+path, method=method, headers=headers,
                              data=json.dumps(body).encode() if body is not None else None)
                try:
                    with urlopen(req, timeout=5) as response: return json.loads(response.read())
                except HTTPError as error:
                    raise site.BridgeError("Access denied in integration test", error.code) from error
            calls = []
            def fake_alpha(cards, question, original, context, previous, history, **options):
                calls.append(copy.deepcopy({"carte": cards, "domanda": question, "cronologia": history}))
                return {"risposta": "Test: " + question, "carte_richiamate": [c["carta"] for c in cards]}, {"provider": "test-only"}
            def invoke_site(payload):
                with site.app.test_client() as client:
                    response = client.post("/api/raffaello/engine", json=payload, headers={"X-Raffaello-Secret": secret})
                    self.assertEqual(response.status_code, 200)
                    return response.get_json()
            try:
                with patch.object(site, "_bridge", side_effect=transport), patch.object(engine, "call_site", side_effect=invoke_site), patch.object(tarot_alpha, "_ai_follow_up", side_effect=fake_alpha):
                    browser, stranger = site.app.test_client(), site.app.test_client()
                    headers = {"X-Raffaello": "1"}
                    code = store.link_code(17)
                    self.assertEqual(browser.post("/api/raffaello/link", json={"code": code}, headers=headers).status_code, 200)
                    card = tarot_alpha._deck()[0]
                    payload = {"lettura_id": "site-original", "domanda": "A sample question", "contesto": "Sample context",
                               "carte": [{"carta": card["nome"], "asse": "est", "polarita": "ombra", "posizione": "presente", "posizione_label": "Presente"}],
                               "lettura": {"messaggio": "Existing interpretation"}}
                    saved = browser.post("/api/raffaello/readings", json=payload, headers=headers)
                    self.assertEqual(saved.status_code, 200)
                    rid = saved.get_json()["id"]
                    store.select(17, rid)
                    task = store.stage(17, "Telegram follow-up", "tg:17:1", use_current=True)
                    self.assertEqual(len(calls), 0)
                    result = engine.analyze(17, task["id"])
                    self.assertEqual(engine.analyze(17, task["id"]), result)
                    self.assertEqual(len(calls), 1)
                    resumed = browser.get("/api/raffaello/readings/"+rid).get_json()
                    self.assertEqual(resumed["cronologia"][0]["risposta"], result["risposta"])
                    frozen = resumed["snapshot"]["carte"]
                    draft = browser.post("/api/raffaello/drafts", json={"domanda": "Website follow-up", "lettura_id": rid, "request_id": "web:1"}, headers=headers).get_json()
                    answer = browser.post("/api/raffaello/drafts/"+draft["id"]+"/analyze", json={}, headers=headers)
                    self.assertEqual(answer.status_code, 200)
                    self.assertEqual(calls[-1]["cronologia"][-1]["risposta"], result["risposta"])
                    store.init()  # Reopen all connections as after a process restart.
                    final = browser.get("/api/raffaello/readings/"+rid).get_json()
                    self.assertEqual(final["snapshot"]["carte"], frozen)
                    self.assertEqual(len(final["cronologia"]), 2)
                    self.assertEqual(len(db.list_actions(17)), 1)
                    self.assertEqual(stranger.get("/api/raffaello/readings/"+rid).status_code, 401)
                    other_code = store.link_code(18)
                    stranger.post("/api/raffaello/link", json={"code": other_code}, headers=headers)
                    self.assertEqual(stranger.get("/api/raffaello/readings/"+rid).status_code, 404)
            finally:
                server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__": unittest.main()
