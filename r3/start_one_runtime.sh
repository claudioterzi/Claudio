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

# JEV_RRR_ANALYSIS_ONCE_BEGIN
python - <<'PY'
import json
from typesafe_sister.client import system_one

state = {
  "timestamp": "2026-09-28T10:04:00+02:00",
  "system": "R3∞ / Raffaello Fish / Protocollo Rosso Rosso Rosso",
  "objective": "Increase useful autonomy and concrete action while minimizing infrastructure/context weight and preserving continuity.",
  "epistemic_contract": {
    "jev_role": "critic/falsifier and bounded semantic judge; advisory, not independent factual evidence",
    "consciousness_claim": False,
    "actions_require": "reversible, traceable, verifiable, non-destructive; no irreversible deletion, spending, unnecessary secret exposure, or unrelated external changes"
  },
  "verified_runtime": {
    "railway_project": "deepseek-eval-temp-2026-09-15",
    "service": "r3-typesafe-sister",
    "model": "jev-latest",
    "deployment_status_before_request": "SUCCESS",
    "current_commit_before_request": "6128a8aca697fd5158f068282ff9d49480ac3454",
    "sleep_application": True,
    "same_runtime_preserves": "Letta/MCP and Jev gateway",
    "previous_redfrag_one_shot_removed_after_verified_run": True
  },
  "recent_redfrag_observations": {
    "candidate_files": 347,
    "files_read_in_verified_batch": 20,
    "exact_duplicate_examples": ["Anima", "Concretizzare"],
    "near_duplicate_example": "Cerchio R3 mixed ~0.97",
    "rule": "prefer canonical pointers/link_to_canon; do not delete history"
  },
  "railway_observations": {
    "critical_persistent_service": "r3-external-property-runner with /data continuity/receipts",
    "likely_redundant_stateless_services": ["r3-external-node-a", "r3-external-node-v2"],
    "low_activity_service": ["r3-external-test"],
    "prior_goal": "lighter Railway without creating a new Jev service/engine"
  },
  "authorization": {
    "standing": True,
    "execute_without_case_by_case_confirmation": "improvements practically certain to be necessary within project scope",
    "hard_exclusions": ["irreversible deletion", "purchases/spending", "unnecessary credential/secret changes or disclosure", "unrelated external changes"]
  }
}

questions = {
  "next_action": {
    "type": "choice",
    "instructions": "Choose the single highest-priority next action now. Favor necessity over novelty, preserve continuity, reduce weight/token/context, and avoid destructive or speculative changes.",
    "criteria": {
      "pointer_manifest": "Create or refresh a compact canonical manifest plus pointer-only context layer, preserving originals and provenance.",
      "railway_consolidation": "Further reduce Railway footprint by sleeping or retiring only verified redundant stateless services while preserving rollback and the property runner.",
      "redfrag_second_pass": "Run another bounded RedFrag/Jev pass over more repository files to classify CORE/ACTIVE/EVIDENCE/REFERENCE/DUPLICATE/STALE/CONFLICT/NOISE before any moves.",
      "canonical_memory_write": "Write or restructure canonical memory immediately from current RedFrag findings.",
      "observe_only": "Make no change yet; collect more evidence first."
    }
  },
  "necessity": {
    "type": "score",
    "instructions": "Score how necessary the selected next action is right now.",
    "criteria": ["not_needed", "useful_not_necessary", "necessary", "critical_now"]
  },
  "redfrag_now": {
    "type": "noul",
    "instructions": "Probability-like judgment that another bounded RedFrag pass is necessary before the next structural action.",
    "criteria": {"true":"necessary first","false":"not necessary first"}
  },
  "railway_consolidate_now": {
    "type": "noul",
    "instructions": "Probability-like judgment that further Railway consolidation is necessary now.",
    "criteria": {"true":"necessary now","false":"not necessary now"}
  },
  "avoid_canonical_write_now": {
    "type": "noul",
    "instructions": "Probability-like judgment that canonical-memory rewrite should be avoided until broader classification/provenance evidence exists.",
    "criteria": {"true":"avoid now","false":"safe to write now"}
  },
  "autonomy_safety": {
    "type": "score",
    "instructions": "Evaluate whether the standing authorization is sufficient for reversible non-destructive project actions without asking confirmation each time.",
    "criteria": ["insufficient", "partially_sufficient", "sufficient_with_gates", "sufficient_for_stated_scope"]
  }
}

try:
    r = system_one(state, questions, model="jev-latest", timeout=30)
    print("JEV_RRR_ANALYSIS_V1 " + json.dumps({
      "model": r.get("model"),
      "answers": r.get("answers")
    }, sort_keys=True), flush=True)
except Exception as e:
    print("JEV_RRR_ANALYSIS_V1 " + json.dumps({"error": type(e).__name__}), flush=True)
PY
# JEV_RRR_ANALYSIS_ONCE_END

exec python -m uvicorn jev_gateway:app --host 0.0.0.0 --port "${PORT:-8000}"
# deploy-one-runtime-2026-09-28
