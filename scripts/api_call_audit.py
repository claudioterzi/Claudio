#!/usr/bin/env python3
"""Audit one OpenAI-compatible chat completion call without storing credentials.

Claudio Terzi · C.Terzi

Writes request.json, response.json, body.txt and manifest.json with:
timestamps, latency, SHA-256 hashes, model and token usage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--message", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--base-url", required=True)
    p.add_argument("--out-dir", default="output/api_audit")
    p.add_argument("--max-tokens", type=int, default=1000)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--api-key-env", default="LLM_API_KEY")
    args = p.parse_args()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Manca la variabile ambiente {args.api_key_env}.")
    if not (1 <= args.max_tokens <= 8192):
        raise SystemExit("--max-tokens fuori intervallo.")
    if not (0 <= args.temperature <= 2):
        raise SystemExit("--temperature fuori intervallo.")

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    out = Path(args.out_dir) / run_id
    out.mkdir(parents=True, exist_ok=False)

    request_record = {
        "base_url": args.base_url,
        "model": args.model,
        "messages": [{"role": "user", "content": args.message}],
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    request_bytes = canonical(request_record)
    (out / "request.json").write_text(
        json.dumps(request_record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    started = now_utc()
    t0 = time.perf_counter()
    client = OpenAI(api_key=api_key, base_url=args.base_url)
    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=request_record["messages"],
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except Exception as exc:
        manifest = {
            "status": "error",
            "started_at_utc": started,
            "completed_at_utc": now_utc(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
            "request_sha256": sha256(request_bytes),
            "error_type": type(exc).__name__,
            "error": str(exc)[:2000],
        }
        (out / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"run_dir": str(out), **manifest}, ensure_ascii=False, indent=2))
        return 2

    raw = response.model_dump(mode="json")
    body = response.choices[0].message.content or ""
    response_bytes = canonical(raw)
    body_bytes = body.encode("utf-8")
    (out / "response.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "body.txt").write_bytes(body_bytes)

    usage = raw.get("usage") or {}
    manifest = {
        "status": "ok",
        "started_at_utc": started,
        "completed_at_utc": now_utc(),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
        "base_url": args.base_url,
        "model_requested": args.model,
        "model_returned": raw.get("model"),
        "request_sha256": sha256(request_bytes),
        "response_sha256": sha256(response_bytes),
        "body_sha256": sha256(body_bytes),
        "body_utf8_bytes": len(body_bytes),
        "usage": usage,
        "note": "This proves a recorded request/response exchange with the configured endpoint; nothing more.",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_dir": str(out), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
