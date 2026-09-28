#!/bin/sh
set -eu

python /app/letta_blind_probe_once.py || true
python -m pip install --no-cache-dir 'mcp==1.30.0'

python - <<'PY'
import base64
import gzip
import hashlib
import os

chunks = ''.join(os.environ[f'R3_LETTA_V2_CODE_{i}'] for i in range(1, 3))
raw = gzip.decompress(base64.b64decode(chunks))
digest = hashlib.sha256(raw).hexdigest()
assert digest == os.environ['R3_LETTA_V2_WRAPPER_SHA256']
open('/app/letta_bridge_v2.py', 'wb').write(raw)

receipt_chunks = ''.join(os.environ[f'R3_LETTA_RECEIPT_CODE_{i}'] for i in range(1, 3))
receipt_raw = gzip.decompress(base64.b64decode(receipt_chunks))
receipt_digest = hashlib.sha256(receipt_raw).hexdigest()
assert receipt_digest == os.environ['R3_LETTA_RECEIPT_SHA256']
open('/app/r3_letta_receipt_spine.py', 'wb').write(receipt_raw)
PY

# OMEE_JEV_ATOMIC_ONESHOT_BEGIN
python - <<'PY'
import json
import os
from typesafe_sister.client import system_one

raw = os.getenv("R3_OMEE_JEV_ONESHOT_JSON", "").strip()
if raw:
    try:
        payload = json.loads(raw)
        for batch in payload.get("batches", []):
            bid = str(batch.get("batch_id", "UNKNOWN"))
            try:
                result = system_one(
                    batch.get("state", {}),
                    batch.get("questions", {}),
                    model="jev-latest",
                    timeout=20,
                )
                print("OMEE_JEV_ATOMIC " + json.dumps({
                    "batch_id": bid,
                    "model": result.get("model"),
                    "answers": result.get("answers"),
                }, ensure_ascii=False, sort_keys=True), flush=True)
            except Exception as exc:
                print("OMEE_JEV_ATOMIC " + json.dumps({
                    "batch_id": bid,
                    "error": type(exc).__name__,
                }, sort_keys=True), flush=True)
    except Exception as exc:
        print("OMEE_JEV_ATOMIC_INIT " + json.dumps({
            "error": type(exc).__name__,
        }, sort_keys=True), flush=True)
PY
# OMEE_JEV_ATOMIC_ONESHOT_END

exec python -m uvicorn jev_gateway:app --host 0.0.0.0 --port "${PORT:-8000}"
# deploy-one-runtime-2026-09-28
