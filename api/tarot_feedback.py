"""Alpha 74 private TEST feedback collector. Claudio Terzi · C.Terzi.

TEST branch only. Attempts delivery to the existing Raffaello bot bridge; if the
bot does not expose a feedback route yet, emits one structured Vercel log entry
so feedback can still be recovered during the test period.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024


def _clean(value, limit):
    return str(value or "").strip()[:limit]


def _score(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 5 else None


def _payload(body):
    ratings = body.get("ratings") if isinstance(body.get("ratings"), dict) else {}
    cleaned = {
        "source": "alpha74-private-test",
        "friend": _clean(body.get("friend"), 80) or None,
        "nickname": _clean(body.get("nickname"), 80) or None,
        "language": _clean(body.get("language"), 8).lower() or "it",
        "reading_number": max(1, min(3, int(body.get("reading_number") or 1))),
        "ratings": {
            "visual": _score(ratings.get("visual")),
            "clarity": _score(ratings.get("clarity")),
            "reading": _score(ratings.get("reading")),
            "coherence": _score(ratings.get("coherence")),
            "return": _score(ratings.get("return")),
        },
        "comment": _clean(body.get("comment"), 1800) or None,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    if any(v is None for v in cleaned["ratings"].values()):
        raise ValueError("Completa i cinque voti da 1 a 5.")
    return cleaned


def _send_bridge(payload):
    base = _clean(os.getenv("RAFFAELLO_BOT_URL"), 500).rstrip("/")
    secret = _clean(os.getenv("RAFFAELLO_BRIDGE_SECRET"), 500)
    parsed = urlparse(base)
    if len(secret) < 32 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        return False
    req = Request(
        base + "/raffaello/v1/feedback",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"X-Raffaello-Secret": secret, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=12) as response:
            return 200 <= int(response.status) < 300
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


@app.after_request
def headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.route("/api/tarocchi/alpha-feedback", methods=["POST"])
@app.route("/", methods=["POST"])
def feedback():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(errore="Serve un oggetto JSON."), 400
    try:
        payload = _payload(body)
    except (ValueError, TypeError):
        return jsonify(errore="Completa i cinque voti da 1 a 5."), 400

    delivered = _send_bridge(payload)
    if not delivered:
        # Structured temporary TEST fallback. No secrets, IP address or user agent.
        print("alpha74_test_feedback=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return jsonify(ok=True, delivered="telegram" if delivered else "test-log")
