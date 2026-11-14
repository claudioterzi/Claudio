"""Bounded caller for the existing authenticated R3∞ Jev gateway.

The server owns the shared System One transport and upstream TypeSafe key.
This caller never installs skills, runs tools selected by a model or creates a
second semantic engine. The original backup smoke fixture remains the default.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx

CANONICAL_GATEWAY_URL = "https://r3-typesafe-sister-production.up.railway.app/jev"
MAX_REQUEST_BYTES = 65536
MAX_RESPONSE_BYTES = 131072
MAX_QUESTIONS = 16


def default_payload() -> dict:
    return {
        "model": "jev-latest",
        "state": {
            "message": "A backup check completed, but no independent restore proof exists yet.",
            "context": "R3 continuity status classification fixture",
        },
        "questions": {
            "route": {
                "type": "choice",
                "instructions": "Which bounded next action best matches the state?",
                "criteria": {
                    "continue_monitoring": "No blocker and no missing proof that requires action.",
                    "request_restore_test": "The state lacks an independent restore proof.",
                    "escalate_security": "There is evidence of a security compromise.",
                },
            },
            "restore_missing": {
                "type": "noul",
                "instructions": "Does the state explicitly lack independent restore proof?",
                "criteria": {
                    "true": "Independent restore proof is absent or pending.",
                    "false": "Independent restore proof is present and verified.",
                },
            },
            "priority": {
                "type": "score",
                "instructions": "How important is it to address the missing verification next?",
                "criteria": [
                    "No action needed.",
                    "Low priority.",
                    "Useful but not urgent.",
                    "Important next validation.",
                    "Critical blocker requiring immediate action.",
                ],
            },
        },
    }

def _digest(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_request(payload: dict) -> dict:
    """Match the deployed gateway's wire normalization, with local bounds."""
    if not isinstance(payload, dict) or set(payload) - {"state", "questions", "model"}:
        raise ValueError("unsupported request fields")
    if "state" not in payload:
        raise ValueError("state required")
    model = payload.get("model", "jev-latest")
    if not isinstance(model, str) or not model.startswith("jev-") or len(model) > 80:
        raise ValueError("explicit Jev model required")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        raise ValueError("bounded nonempty questions required")
    wire = {}
    for name, question in questions.items():
        if not isinstance(name, str) or not name or len(name) > 80 or not isinstance(question, dict):
            raise ValueError("invalid question")
        if set(question) - {"type", "instructions", "criteria"}:
            raise ValueError("unsupported question fields")
        kind = question.get("type")
        if not isinstance(kind, str) or kind not in {"choice", "score", "noul"}:
            raise ValueError("invalid question type")
        body = {"type": kind}
        if question.get("instructions") is not None:
            if not isinstance(question["instructions"], str):
                raise ValueError("instructions must be text")
            body["instructions"] = question["instructions"]
        criteria = question.get("criteria")
        if kind == "choice" and (not isinstance(criteria, dict) or not criteria):
            raise ValueError("choice criteria required")
        if kind == "score" and (not isinstance(criteria, list) or not criteria):
            raise ValueError("score criteria required")
        if kind == "noul" and criteria is not None and not isinstance(criteria, dict):
            raise ValueError("invalid noul criteria")
        if criteria is not None:
            body["criteria"] = criteria
        wire[name] = body
    result = {"state": payload["state"], "questions": wire, "model": model}
    raw = json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("request too large")
    return result


def access_status() -> dict:
    token = os.getenv("R3_API_TOKEN", "")
    present = bool(token.strip()) and token != "changeme"
    url = os.getenv("R3_TYPESAFE_URL", CANONICAL_GATEWAY_URL).rstrip("/")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("gateway must be HTTPS without credentials, query or fragment")
    return {"status": "CREDENTIAL_PRESENT_NOT_AUTHENTICATED" if present else "BLOCKED_MISSING_TOKEN",
            "gateway": url + "/judge", "token_present": present,
            "required_secret": "R3_API_TOKEN", "inference_executed": False}


def _finite_probability(value) -> bool:
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and 0 <= value <= 1
    except OverflowError:
        return False


def _contains_token(value, token: str) -> bool:
    if isinstance(value, str):
        return token in value
    if isinstance(value, dict):
        return any(_contains_token(key, token) or _contains_token(item, token)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_token(item, token) for item in value)
    return False


def validate_response(result: dict, request: dict) -> None:
    if not isinstance(result, dict) or result.get("provider") != "typesafe":
        raise ValueError("unexpected gateway provider")
    if (result.get("state_sha256") != _digest(request["state"])
            or result.get("questions_sha256") != _digest(request["questions"])):
        raise ValueError("gateway input hash mismatch")
    response = result.get("result")
    if not isinstance(response, dict) or response.get("_r3_provider") != "typesafe":
        raise ValueError("unexpected upstream provider")
    model = response.get("model")
    if not isinstance(model, str) or not model.startswith("jev-") or len(model) > 80:
        raise ValueError("missing or unexpected actual Jev model")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(request["questions"]):
        raise ValueError("incomplete or unexpected answers")
    for name, question in request["questions"].items():
        answer = answers[name]
        if not isinstance(answer, dict):
            raise ValueError("invalid typed answer")
        kind = question["type"]
        if kind == "choice":
            choice = answer.get("choice")
            if not isinstance(choice, str) or choice not in question["criteria"]:
                raise ValueError("choice outside supplied catalog")
        elif kind == "noul":
            if not _finite_probability(answer.get("noul")):
                raise ValueError("invalid noul probability")
        else:
            score = answer.get("score")
            if (not isinstance(score, (int, float)) or isinstance(score, bool)
                    or not math.isfinite(score) or not 0 <= score <= len(question["criteria"]) - 1):
                raise ValueError("invalid score")
        if "confidence" in answer and not _finite_probability(answer["confidence"]):
            raise ValueError("invalid confidence")


def judge_request(payload: dict, *, timeout: float = 45) -> dict:
    request = normalize_request(payload)
    status = access_status()
    if not status["token_present"]:
        raise RuntimeError("R3_API_TOKEN not bound to this executor")
    if not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError("invalid bounded timeout")
    token = os.environ["R3_API_TOKEN"]
    # Reject redirect destinations, preserve proxy/CA trust, and make exactly one call.
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        with client.stream("POST", status["gateway"],
                           headers={"Authorization": "Bearer " + token}, json=request) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > MAX_RESPONSE_BYTES:
                    raise ValueError("gateway response too large")
    if token.encode("utf-8") in data:
        raise ValueError("credential reflected in response")
    result = json.loads(data)
    if _contains_token(result, token):
        raise ValueError("credential reflected in decoded response")
    _digest(result)  # Reject non-standard NaN/Infinity anywhere before saving a receipt.
    validate_response(result, request)
    return {"schema": "R3_JEV_GATEWAY_RECEIPT/1.0", "authority": "DATA_ONLY_ADVISORY",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "TYPED_RESPONSE_VALIDATED", "gateway": status["gateway"],
            "request_sha256": _digest(request), "state_sha256": result["state_sha256"],
            "questions_sha256": result["questions_sha256"], "response": result,
            "automatic_actions": False, "web_search_by_jev": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="presence-only, no HTTP")
    parser.add_argument("--request", type=Path, help="bounded state/questions/model JSON file")
    parser.add_argument("--output", type=Path, help="create-only receipt; existing files refused before HTTP")
    args = parser.parse_args(argv)
    output = None
    try:
        if args.output:
            output = args.output.open("x", encoding="utf-8")
        if args.preflight:
            receipt = access_status()
            code = 0 if receipt["token_present"] else 2
        else:
            payload = default_payload()
            if args.request:
                with args.request.open("rb") as handle:
                    raw = handle.read(MAX_REQUEST_BYTES + 1)
                if len(raw) > MAX_REQUEST_BYTES:
                    raise ValueError("request file too large")
                payload = json.loads(raw)
            request = normalize_request(payload)
            status = access_status()
            if not status["token_present"]:
                receipt = {**status, "request_sha256": _digest(request),
                           "observed_at_utc": datetime.now(timezone.utc).isoformat()}
                code = 2
            else:
                receipt = judge_request(request)
                code = 0
    except Exception as exc:
        # Do not include exception messages, response bodies or credentials in errors.
        receipt = {"status": "FAILED", "error_class": type(exc).__name__,
                   "inference_success": False, "automatic_actions": False}
        code = 3
    if output is not None:
        with output:
            json.dump(receipt, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
