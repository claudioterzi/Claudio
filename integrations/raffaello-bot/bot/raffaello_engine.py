"""Authenticated reuse of the site's AI engine; no invented offline AI answers."""
from __future__ import annotations

import json
import os
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from bot import raffaello_store as store


def allowed(owner):
    ids = {part.strip() for part in os.getenv("RAFFAELLO_ALLOWED_USERS", "").split(",")}
    return str(owner) in ids


def site_url():
    return os.getenv("RAFFAELLO_SITE_URL", "https://claudio-ebon.vercel.app").rstrip("/")


def authorized(secret):
    expected = os.getenv("RAFFAELLO_BRIDGE_SECRET", "")
    return len(expected) >= 32 and secrets.compare_digest(expected.encode(), (secret or "").encode())


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call_site(payload):
    secret = os.getenv("RAFFAELLO_BRIDGE_SECRET", "")
    base = site_url()
    parsed = urlparse(base)
    if len(secret) < 32 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query:
        raise store.Problem("Il collegamento con Raffaello non è ancora configurato. La domanda è salvata; potrai riprovare con Analizza.", 503)
    headers = {"Content-Type": "application/json", "X-Raffaello-Secret": secret}
    bypass = os.getenv("RAFFAELLO_VERCEL_BYPASS_SECRET", "")
    if bypass:
        headers["x-vercel-protection-bypass"] = bypass
    req = Request(base + "/api/raffaello/engine", data=json.dumps(payload, ensure_ascii=False).encode(), headers=headers, method="POST")
    try:
        with build_opener(NoRedirect).open(req, timeout=70) as response:
            raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("oversize")
            data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        raise store.Problem("Il motore di Raffaello non è raggiungibile in questo momento. La domanda resta salvata: riprova con Analizza.", 503) from exc
    if not isinstance(data, dict) or not isinstance(data.get("risposta"), str) or not data["risposta"].strip() or len(data["risposta"]) > 8000:
        raise store.Problem("La risposta ricevuta non è valida. Puoi riprovare con Analizza.", 502)
    return {"risposta": data["risposta"], "motore": data.get("motore", {}), "riferimenti": data.get("riferimenti", [])}


def analyze(owner, did):
    if not allowed(owner):
        raise store.Problem("Questo account non è abilitato a Raffaello.", 403)
    cached = store.claim(owner, did)
    if cached is not None:
        return cached
    try:
        task = store.draft(owner, did)
        context = store.reading(owner, task["reading_id"])["snapshot"] if task["reading_id"] else None
        previous = store.history(owner, task["thread"])
        if context:
            previous = (context["cronologia"] + previous)[-8:]
        result = call_site({"domanda": task["question"], "lettura": context, "cronologia": previous,
                            "lingua": task.get("language") or (context or {}).get("lingua") or "it"})
        result["lettura_id"] = task["reading_id"]
        result["richiesta_id"] = did
        store.complete(owner, did, result)
        return result
    except Exception:
        store.complete(owner, did)
        raise
