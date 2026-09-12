"""Private continuity, immutable canon, explicit analysis and restart recovery."""
import asyncio
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot import db, raffaello, raffaello_engine as engine, raffaello_http as http, raffaello_store as store


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "existing.db"))
    monkeypatch.setenv("RAFFAELLO_ALLOWED_USERS", "17,18")
    monkeypatch.setenv("RAFFAELLO_BRIDGE_SECRET", "test-bridge-secret-" * 3)
    db.init_db()
    db.upsert_user(17, "owner", "Owner")
    db.add_action(17, "An existing private action")
    store.init()


@pytest.fixture
def snapshot():
    card = json.loads((Path(__file__).parents[1] / "bot/data/alpha74.json").read_text())["carte"][0]
    return {"lettura_id": "original-site-id", "domanda": "Che cosa osservare?", "contesto": "Un progetto nuovo",
            "carte": [{"carta": card["nome"], "asse": "est", "polarita": "ombra", "posizione": "presente", "posizione_label": "Presente", "significato_canonico": "client must not replace the canon"}],
            "lettura": {"messaggio": "Lettura già interpretata."},
            "cronologia": [{"domanda": "Una prima domanda", "risposta": "Una prima risposta"}]}


def test_additive_migration_reopen_and_owner_isolation(snapshot):
    rid = store.save_reading(17, snapshot)
    store.init()  # Simulated process restart, opening new DB connections.
    assert db.list_actions(17)[0]["description"] == "An existing private action"
    saved = store.reading(17, rid)
    assert saved["snapshot"]["carte"][0]["asse"] == "est"
    assert saved["snapshot"]["carte"][0]["polarita"] == "ombra"
    assert saved["snapshot"]["carte"][0]["significato_canonico"] != "client must not replace the canon"
    assert store.save_reading(17, snapshot) == rid
    changed = copy.deepcopy(snapshot); changed["carte"][0]["asse"] = "nord"
    with pytest.raises(store.Problem, match="invariati"):
        store.save_reading(17, changed)
    with pytest.raises(store.Problem) as exc:
        store.reading(18, rid)
    assert exc.value.status == 404
    assert store.readings(18) == []


@pytest.mark.parametrize("mutation", ["empty", "bad_axis", "duplicate", "missing_polarity"])
def test_invalid_cards_never_trigger_a_fresh_draw(snapshot, mutation):
    if mutation == "empty": snapshot["carte"] = []
    if mutation == "bad_axis": snapshot["carte"][0]["asse"] = "whatever"
    if mutation == "duplicate": snapshot["carte"] *= 2
    if mutation == "missing_polarity": del snapshot["carte"][0]["polarita"]
    with pytest.raises(store.Problem): store.save_reading(17, snapshot)


def test_link_is_single_use_hashed_expiring_and_revocable(monkeypatch):
    code = store.link_code(17)
    with db.connect() as conn:
        assert conn.execute("SELECT digest FROM r3_links").fetchone()[0] != code.replace("-", "")
    token, owner = store.exchange(code)
    assert owner == 17 and store.session_owner(token) == 17
    with pytest.raises(store.Problem): store.exchange(code)
    store.revoke(17)
    with pytest.raises(store.Problem): store.session_owner(token)
    code = store.link_code(17)
    now = store.time.time()
    monkeypatch.setattr(store.time, "time", lambda: now + 601)
    with pytest.raises(store.Problem): store.exchange(code)


def test_bridge_rejects_missing_auth_and_foreign_ids(snapshot):
    secret = "test-bridge-secret-" * 3
    with pytest.raises(store.Problem): http.dispatch("GET", "/session", {}, {})
    token, _ = store.exchange(store.link_code(18))
    headers = {"X-Raffaello-Secret": secret, "X-Raffaello-Session": token}
    rid = store.save_reading(17, snapshot)
    with pytest.raises(store.Problem): http.dispatch("GET", "/readings/"+rid, headers, {})
    with pytest.raises(store.Problem): http.dispatch("POST", "/drafts", headers, {"domanda": "x", "request_id": "one", "lettura_id": rid, "owner": 17})


def test_manual_analysis_context_and_retry_cache(snapshot, monkeypatch):
    calls = []
    def fake(payload):
        calls.append(payload)
        return {"risposta": "Risposta verificabile nel test.", "motore": {"provider": "test"}}
    monkeypatch.setattr(engine, "call_site", fake)
    rid = store.save_reading(17, snapshot)
    store.select(17, rid)
    task = store.stage(17, "Spiegami questa carta", "message-one", use_current=True)
    assert calls == []
    result = engine.analyze(17, task["id"])
    assert result == engine.analyze(17, task["id"])
    assert len(calls) == 1
    assert calls[0]["lettura"]["carte"] == store.reading(17, rid)["snapshot"]["carte"]
    assert calls[0]["cronologia"][0]["domanda"] == "Una prima domanda"
    assert len(store.reading(17, rid)["cronologia"]) == 1
    # A new browser request continues the same persisted conversation.
    next_task = store.stage(17, "E rispetto al progetto?", "browser-one", rid)
    engine.analyze(17, next_task["id"])
    assert calls[-1]["cronologia"][-1]["risposta"] == result["risposta"]
    store.init()
    assert len(store.reading(17, rid)["cronologia"]) == 2


def test_stale_buttons_failure_and_generation_lock(monkeypatch):
    first = store.stage(17, "Primo testo", "1")
    second = store.stage(17, "Secondo testo", "2")
    with pytest.raises(store.Problem): store.claim(17, first["id"])
    def claim():
        try: return store.claim(17, second["id"])
        except store.Problem as exc: return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))
    assert results.count(None) == 1 and results.count(409) == 1
    store.complete(17, second["id"])
    assert store.draft(17, second["id"])["status"] == "failed"
    def unavailable(payload): raise store.Problem("Not reachable", 503)
    monkeypatch.setattr(engine, "call_site", unavailable)
    with pytest.raises(store.Problem): engine.analyze(17, second["id"])
    assert store.draft(17, second["id"])["status"] == "failed"
    assert store.history(17, second["thread"]) == []


def test_manual_handler_does_not_invoke_ai_or_match_philosophical_keywords(monkeypatch):
    message = SimpleNamespace(text="Non funziona il pulsante di ascolto.", message_id=11, reply_text=AsyncMock())
    update = SimpleNamespace(effective_message=message, effective_user=SimpleNamespace(id=17, username="owner", first_name="Owner"), effective_chat=SimpleNamespace(id=17, type="private"))
    def forbidden(payload): raise AssertionError("AI must only run after Analizza")
    monkeypatch.setattr(engine, "call_site", forbidden)
    asyncio.run(raffaello.stage(update, None))
    reply = message.reply_text.call_args
    assert "Premi Analizza" in reply.args[0]
    assert "Campo" not in reply.args[0]
    callback = reply.kwargs["reply_markup"].inline_keyboard[0][0].callback_data
    assert callback.startswith("r3:a:") and len(callback.encode()) <= 64


def test_no_private_dialogue_in_groups_or_for_unlisted_users():
    message = SimpleNamespace(text="Private", message_id=11, reply_text=AsyncMock())
    update = SimpleNamespace(effective_message=message, effective_user=SimpleNamespace(id=17), effective_chat=SimpleNamespace(id=-99, type="group"), callback_query=None)
    assert asyncio.run(raffaello.private(update)) is False
    assert not engine.allowed(99)


def test_existing_webhook_is_never_deleted_implicitly():
    from bot.main import post_init
    bot = SimpleNamespace(get_webhook_info=AsyncMock(return_value=SimpleNamespace(url="https://example.invalid/webhook")), delete_webhook=AsyncMock())
    with pytest.raises(RuntimeError): asyncio.run(post_init(SimpleNamespace(bot=bot)))
    bot.delete_webhook.assert_not_called()
