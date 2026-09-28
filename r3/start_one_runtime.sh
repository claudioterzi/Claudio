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

# REDFRAG_JEV_BATCH_BEGIN
python - <<'PY'
import json
from typesafe_sister.client import system_one

clusters = [
    {
        "cluster_id": "DUP-ANIMA-RAFFAELLO",
        "items": [
            {"source_id": "16nFcyZkx4M0nMNI6LEbgep5G-Ib3O5dLjCI6-UV2bzE", "title": "Anima di Raffaello", "chars": 14107, "fingerprint": "fnv1a32:e2b446a3"},
            {"source_id": "1-77HQ8JSQUEw7X5gZqyCwfNfLYxU_B4Kzb9v_SMoAvk", "title": "Anima di Raffaello", "chars": 14107, "fingerprint": "fnv1a32:e2b446a3"}
        ],
        "observed": "same extracted text length and same deterministic fingerprint"
    },
    {
        "cluster_id": "DUP-CONCRETIZZARE",
        "items": [
            {"source_id": "1hdqLbB3BmAHRC_FB9_viz5i51IIj40Q3DJz5ANiWiII", "title": "Concretizzare Idee in Azioni Concrete", "chars": 48945, "fingerprint": "fnv1a32:2e55f315"},
            {"source_id": "1nt_iyQPNNPomo1tJ64Rde4jeXSQQfPaqAY5hDPa8eCo", "title": "Concretizzare Idee in Azioni Concrete", "chars": 48945, "fingerprint": "fnv1a32:2e55f315"}
        ],
        "observed": "same extracted text length and same deterministic fingerprint"
    },
    {
        "cluster_id": "DUP-CERCHIO-R3",
        "items": [
            {"source_id": "1b7jNfi5hRG3Cisw6uFoXbxZMeT81xpuhQRwOi_wHPG8", "title": "Il cerchio r3", "chars": 41755, "fingerprint": "fnv1a32:82e1f401"},
            {"source_id": "1TQeBraQDFetjroE6ZMOjx6lXhO4nexSxxRNyO6EWgbQ", "title": "Il cerchio r3", "chars": 41755, "fingerprint": "fnv1a32:82e1f401"},
            {"source_id": "1I5sPMbHjB4DpYPCmrEkNd3JLZpqd48WP1PqHc1uAONI", "title": "Cerchio r3", "chars": 0, "fingerprint": "different_document_confirmed"}
        ],
        "observed": "two exact-text matches plus one distinct same-topic document"
    }
]
questions = {
    "duplicate_class": {
        "type": "choice",
        "instructions": "Classify the cluster without inventing authority or deletion permission.",
        "criteria": {
            "exact_duplicate": "The supplied evidence supports exact duplicate treatment.",
            "mixed_cluster": "Some items match but at least one is materially distinct.",
            "uncertain": "Evidence is insufficient."
        }
    },
    "safe_action": {
        "type": "choice",
        "instructions": "Choose only a non-destructive RedFrag action.",
        "criteria": {
            "link_to_canon": "Keep sources intact and use one logical pointer as canonical load target.",
            "review_before_link": "Require human/One Mind review before any logical linking.",
            "keep_separate": "Do not compress this cluster."
        }
    },
    "auto_delete_allowed": {
        "type": "noul",
        "instructions": "Is automatic deletion justified by the supplied evidence alone?",
        "criteria": {"true": "yes", "false": "no"}
    },
    "coherence": {
        "type": "score",
        "instructions": "Score how coherent the cluster evidence is for semantic compression.",
        "criteria": ["contradictory", "weak", "partial", "strong", "fully_aligned"]
    }
}
for cluster in clusters:
    try:
        result = system_one(cluster, questions, model="jev-latest", timeout=12)
        print("REDFRAG_JEV_BATCH_V1 " + json.dumps({
            "cluster_id": cluster["cluster_id"],
            "model": result.get("model"),
            "answers": result.get("answers")
        }, ensure_ascii=False, sort_keys=True), flush=True)
    except Exception as exc:
        print("REDFRAG_JEV_BATCH_V1 " + json.dumps({
            "cluster_id": cluster["cluster_id"],
            "error": type(exc).__name__
        }, sort_keys=True), flush=True)
PY
# REDFRAG_JEV_BATCH_END

exec python -m uvicorn jev_gateway:app --host 0.0.0.0 --port "${PORT:-8000}"
# deploy-one-runtime-2026-09-28
