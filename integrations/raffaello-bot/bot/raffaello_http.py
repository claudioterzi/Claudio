"""Private HTTP bridge. Never accepts an owner ID supplied by a browser."""
from __future__ import annotations

import re

from bot import raffaello_engine as engine
from bot import raffaello_store as store


def dispatch(method, path, headers, body):
    if not engine.authorized(headers.get("X-Raffaello-Secret")):
        raise store.Problem("Accesso non autorizzato.", 401)
    if method == "POST" and path == "/link":
        token, owner = store.exchange(body.get("code"))
        if not engine.allowed(owner):
            store.revoke(owner)
            raise store.Problem("Account non abilitato.", 403)
        return {"token": token}
    owner = store.session_owner(headers.get("X-Raffaello-Session"))
    if not engine.allowed(owner):
        raise store.Problem("Account non abilitato.", 403)
    if path == "/session" and method == "GET":
        state = store.current(owner)
        return {"linked": True, "active_reading": state["active_reading"], "cronologia": store.history(owner, state["thread"], 30)}
    if path == "/session" and method == "DELETE":
        store.revoke(owner)
        return {"linked": False}
    if path == "/readings" and method == "GET":
        return {"letture": store.readings(owner)}
    if path == "/readings" and method == "POST":
        return {"id": store.save_reading(owner, body)}
    match = re.fullmatch(r"/readings/([a-f0-9]{32})", path)
    if match and method == "GET":
        return store.reading(owner, match[1])
    if path == "/drafts" and method == "POST":
        task = store.stage(owner, body.get("domanda"), body.get("request_id"), body.get("lettura_id"))
        return {"id": task["id"], "status": task["status"]}
    match = re.fullmatch(r"/drafts/([a-f0-9]{32})(/analyze)?", path)
    if match and method == "GET" and not match[2]:
        task = store.draft(owner, match[1])
        return {key: task[key] for key in ("id", "reading_id", "question", "answer", "status")}
    if match and method == "POST" and match[2]:
        return engine.analyze(owner, match[1])
    raise store.Problem("Percorso non disponibile.", 404)
