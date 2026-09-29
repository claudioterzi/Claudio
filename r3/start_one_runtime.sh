#!/bin/sh
set -eu

python /app/letta_blind_probe_once.py || true

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

if [ "${R3_JEV_BENCH_V1:-0}" = "1" ]; then
  (cd /app/bench_runtime && PYTHONPATH=/app/bench_runtime python run_jev_bench.py) &
fi

exec python -m uvicorn jev_gateway:app --host 0.0.0.0 --port "${PORT:-8000}"
# deploy-one-runtime-2026-09-28
