"""Bounded Le.Labo transport: reuse the existing OpenAI key in this runtime.

No provider credential can be read through this service. Callers authenticate
with timestamped HMAC; Redis atomically rejects replay and limits paid calls.
"""
import hashlib
import hmac
import json
import os
import re
import time
from urllib.parse import urlparse

import httpx
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4_000_000
BASE = "/api/laboratory-ai/"
TEXT_MODEL = "gpt-6.1-sol"
IMAGE_MODEL = "gpt-image-2.5-flare"

# One atomic operation: replay fencing plus daily/hourly counters, no documents.
LIMIT_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then return -1 end
redis.call('SET', KEYS[1], '1', 'EX', 360)
if tonumber(ARGV[1]) == 0 then return 1 end
if tonumber(redis.call('GET',KEYS[2]) or '0') >= tonumber(ARGV[1]) then return 0 end
if tonumber(redis.call('GET',KEYS[3]) or '0') >= tonumber(ARGV[2]) then return 0 end
redis.call('INCR',KEYS[2]); redis.call('EXPIRE',KEYS[2],90000)
redis.call('INCR',KEYS[3]); redis.call('EXPIRE',KEYS[3],3700)
return 1
"""


def error(code, status):
    return jsonify({"error": {"code": code}}), status


@app.after_request
def private_response(response):
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def authenticated(raw):
    secret = os.environ.get("LE_LABO_BRIDGE_SECRET", "")
    stamp = request.headers.get("X-Labo-Time", "")
    nonce = request.headers.get("X-Labo-Nonce", "")
    signature = request.headers.get("X-Labo-Signature", "")
    if len(secret) < 32 or not re.fullmatch(r"[0-9]{10}", stamp):
        return False
    if abs(int(time.time()) - int(stamp)) > 120:
        return False
    if not re.fullmatch(r"[a-f0-9-]{36}", nonce) or not re.fullmatch(r"[a-f0-9]{64}", signature):
        return False
    message = f"POST\n{request.path}\n{stamp}\n{nonce}\n{hashlib.sha256(raw).hexdigest()}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def reserve(operation):
    endpoint = os.environ.get("KV_REST_API_URL", "")
    token = os.environ.get("KV_REST_API_TOKEN", "")
    parsed = urlparse(endpoint)
    if not token or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("limiter_unavailable")
    now = int(time.time())
    prefix = "le-labo:ai:v1:"
    daily, hourly = (20, 10) if operation == "images" else (120, 30)
    if operation == "health":
        daily = 0
    command = ["EVAL", LIMIT_SCRIPT, 3, prefix + "nonce:" + request.headers["X-Labo-Nonce"],
               prefix + operation + ":day:" + str(now // 86400),
               prefix + operation + ":hour:" + str(now // 3600), daily, hourly]
    response = httpx.post(endpoint, json=command, headers={"Authorization": "Bearer " + token}, timeout=8, follow_redirects=False)
    response.raise_for_status()
    result = response.json()
    if "error" in result or result.get("result") not in (-1, 0, 1):
        raise RuntimeError("limiter_unavailable")
    return result["result"]


def validate(payload, operation):
    if not isinstance(payload, dict):
        return False
    if operation == "health":
        return payload == {}
    if operation == "images":
        allowed = {"model", "prompt", "n", "size", "output_format"}
        return (set(payload) <= allowed and payload.get("model") == IMAGE_MODEL
                and isinstance(payload.get("prompt"), str) and 1 <= len(payload["prompt"]) <= 20000
                and payload.get("n") == 1 and payload.get("size") == "1536x1024"
                and payload.get("output_format") == "jpeg")
    allowed = {"model", "store", "max_output_tokens", "instructions", "input", "text"}
    if set(payload) - allowed or payload.get("model") != TEXT_MODEL or payload.get("store") is not False:
        return False
    tokens = payload.get("max_output_tokens")
    if type(tokens) is not int or not 16 <= tokens <= 14000:
        return False
    if not isinstance(payload.get("instructions"), str) or len(payload["instructions"]) > 16000:
        return False
    fmt = payload.get("text", {}).get("format", {})
    if fmt.get("type") != "json_schema" or fmt.get("strict") is not True or not isinstance(fmt.get("schema"), dict):
        return False
    messages = payload.get("input")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 2:
        return False
    for message in messages:
        if not isinstance(message, dict) or set(message) != {"role", "content"} or message["role"] != "user":
            return False
        content = message["content"]
        if not isinstance(content, list) or not 1 <= len(content) <= 4:
            return False
        for item in content:
            if not isinstance(item, dict):
                return False
            kind = item.get("type")
            if kind == "input_text":
                if set(item) != {"type", "text"} or not isinstance(item["text"], str) or len(item["text"]) > 100000:
                    return False
            elif kind == "input_image":
                if set(item) - {"type", "image_url", "detail"} or not isinstance(item.get("image_url"), str):
                    return False
                if not re.fullmatch(r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+", item["image_url"]):
                    return False
            elif kind == "input_file":
                if set(item) != {"type", "filename", "file_data"} or not isinstance(item["file_data"], str):
                    return False
                if not re.fullmatch(r"data:application/pdf;base64,[A-Za-z0-9+/=]+", item["file_data"]):
                    return False
            else:
                return False
    return True


@app.route(BASE + "<operation>", methods=["POST"])
def relay(operation):
    if operation not in {"responses", "images", "health"}:
        return error("not_found", 404)
    raw = request.get_data(cache=True)
    if not authenticated(raw):
        return error("unauthorized", 401)
    try:
        payload = json.loads(raw)
        if not validate(payload, operation):
            return error("invalid_request", 400)
    except (ValueError, TypeError, AttributeError):
        return error("invalid_request", 400)
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return error("provider_unconfigured", 503)
    try:
        reservation = reserve(operation)
    except Exception:
        return error("limiter_unavailable", 503)
    if reservation == -1:
        return error("replayed_request", 409)
    if reservation == 0:
        return error("rate_limited", 429)
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    try:
        if operation == "health":
            checks = {}
            for label, model in (("recipes", TEXT_MODEL), ("images", IMAGE_MODEL)):
                response = httpx.get("https://api.openai.com/v1/models/" + model, headers=headers, timeout=12, follow_redirects=False)
                checks[label] = response.status_code == 200
            return jsonify({"configured": True, "modelsAccessible": checks, "rateLimiter": True})
        suffix = "responses" if operation == "responses" else "images/generations"
        if operation == "images":
            payload = {**payload, "output_compression": 75, "quality": "medium"}
        response = httpx.post("https://api.openai.com/v1/" + suffix, json=payload, headers=headers, timeout=155, follow_redirects=False)
        if not response.is_success:
            # Upstream error messages can contain key fragments: never forward them.
            status = 429 if response.status_code == 429 else 502
            code = "provider_credentials" if response.status_code == 401 else "provider_request_failed"
            return error(code, status)
        if len(response.content) > 4_000_000:
            return error("provider_response_too_large", 502)
        return jsonify(response.json())
    except Exception:
        return error("provider_unavailable", 502)


@app.errorhandler(413)
def oversized(_error):
    return error("request_too_large", 413)
