#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  if [ -f /tmp/omniroute.pid ]; then kill "$(cat /tmp/omniroute.pid)" 2>/dev/null || true; fi
  if [ -f /tmp/r3-mock.pid ]; then kill "$(cat /tmp/r3-mock.pid)" 2>/dev/null || true; fi
  rm -rf /tmp/omniroute-data
}
trap cleanup EXIT

rm -rf /tmp/omniroute /tmp/omniroute-data
git clone --depth 1 --branch release/v3.8.51 https://github.com/diegosouzapw/OmniRoute.git /tmp/omniroute
cd /tmp/omniroute
SOURCE_VERSION=$(node -p "require('./package.json').version")
SOURCE_SHA=$(git rev-parse HEAD)
test "$SOURCE_VERSION" = "3.8.51"
test -f open-sse/services/autoCombo/modelExposureFilter.ts
test -f open-sse/services/autoCombo/modelLockoutFilter.ts
grep -q 'filterModelExposureCandidates' open-sse/services/autoCombo/virtualFactory.ts
grep -q 'modelVisibilityDenylist' src/shared/validation/settingsSchemas.ts

NPM_CONFIG_LEGACY_PEER_DEPS=true npm ci --no-audit --no-fund --legacy-peer-deps

cat > /tmp/r3_mock.py <<'PY'
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS = [
    "r3-good-model",
    "anthropic/claude-opus-5",
    "big-pickle",
    "felo-chat",
    "felo-search",
]

class H(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def out(self, code, body):
        raw=json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        if self.path in ("/models","/v1/models"):
            return self.out(200,{"object":"list","data":[
                {"id":m,"object":"model","owned_by":"r3-mock"} for m in MODELS
            ]})
        return self.out(404,{"error":"not_found"})
    def do_POST(self):
        n=int(self.headers.get("content-length","0") or 0)
        body=json.loads(self.rfile.read(n) or b"{}")
        if self.path not in ("/chat/completions","/v1/chat/completions"):
            return self.out(404,{"error":"not_found"})
        m=str(body.get("model") or "")
        if m.endswith("anthropic/claude-opus-5"):
            return self.out(401,{"error":{"message":"sign-in required"}})
        if m.endswith("big-pickle"):
            return self.out(403,{"error":{"message":"free tier external use forbidden"}})
        if m.endswith("felo-chat") or m.endswith("felo-search"):
            return self.out(400,{"error":{"message":"model unavailable"}})
        return self.out(200,{
            "id":"chatcmpl-r3-a",
            "object":"chat.completion",
            "model":m or "r3-good-model",
            "choices":[{"index":0,"message":{"role":"assistant","content":"OMNIROUTE_R3_OK"},"finish_reason":"stop"}],
            "usage":{"prompt_tokens":3,"completion_tokens":2,"total_tokens":5}
        })

ThreadingHTTPServer(("127.0.0.1",18080),H).serve_forever()
PY

nohup python /tmp/r3_mock.py >/tmp/r3-mock.log 2>&1 &
echo $! >/tmp/r3-mock.pid
for i in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:18080/v1/models >/tmp/mock-models.json 2>/dev/null; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:18080/v1/models >/dev/null

export JWT_SECRET="$(openssl rand -base64 48 | tr -d '\n')"
export API_KEY_SECRET="$(openssl rand -hex 32)"
export STORAGE_ENCRYPTION_KEY="$(openssl rand -hex 32)"
export INITIAL_PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
export DATA_DIR=/tmp/omniroute-data
export PORT=20128
export HOSTNAME=127.0.0.1
export OMNIROUTE_SERVER_HOST=127.0.0.1
export REQUIRE_API_KEY=true
export AUTH_COOKIE_SECURE=false
export APP_LOG_TO_FILE=false
export OMNIROUTE_DISABLE_BACKGROUND_SERVICES=true
echo "::add-mask::$INITIAL_PASSWORD"

nohup npm run dev >/tmp/omniroute-3851.log 2>&1 &
echo $! >/tmp/omniroute.pid
for i in $(seq 1 180); do
  if curl -fsS http://127.0.0.1:20128/api/health >/tmp/health.json 2>/dev/null; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:20128/api/health >/dev/null

jq -n --arg password "$INITIAL_PASSWORD" '{password:$password}' >/tmp/login.json
code=$(curl -sS -o /tmp/login-response.json -w '%{http_code}' -c /tmp/omni-cookie.txt   -H 'Content-Type: application/json' -d @/tmp/login.json http://127.0.0.1:20128/api/auth/login)
test "$code" -ge 200 && test "$code" -lt 300
CSRF_TOKEN=$(curl -fsS -b /tmp/omni-cookie.txt http://127.0.0.1:20128/api/auth/csrf | jq -r '.token // empty')
test -n "$CSRF_TOKEN"
echo "::add-mask::$CSRF_TOKEN"

cat >/tmp/node.json <<'JSON'
{"type":"openai-compatible","name":"R3 Candidate A Mock","prefix":"r3mock","apiType":"chat","baseUrl":"http://127.0.0.1:18080/v1","modelsPath":"/models"}
JSON
code=$(curl -sS -o /tmp/node-response.json -w '%{http_code}' -X POST   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d @/tmp/node.json http://127.0.0.1:20128/api/provider-nodes)
if [ "$code" -lt 200 ] || [ "$code" -ge 300 ]; then
  echo "NODE_CREATE_FAILED HTTP=$code"; cat /tmp/node-response.json; exit 10
fi
NODE_ID=$(jq -r '.node.id // empty' /tmp/node-response.json)
test -n "$NODE_ID"

jq -n --arg provider "$NODE_ID" '{provider:$provider,name:"R3 Candidate A Connection",priority:1,testStatus:"unknown"}' >/tmp/connection.json
code=$(curl -sS -o /tmp/connection-response.json -w '%{http_code}' -X POST   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d @/tmp/connection.json http://127.0.0.1:20128/api/providers)
if [ "$code" -lt 200 ] || [ "$code" -ge 300 ]; then
  echo "CONNECTION_CREATE_FAILED HTTP=$code"; cat /tmp/connection-response.json; exit 11
fi
CONNECTION_ID=$(jq -r '.connection.id // empty' /tmp/connection-response.json)
test -n "$CONNECTION_ID"

code=$(curl -sS -o /tmp/test-response.json -w '%{http_code}' -X POST   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:20128/api/providers/$CONNECTION_ID/test")
cat /tmp/test-response.json | jq .
test "$code" -ge 200 && test "$code" -lt 300
test "$(jq -r '.valid // .success // false' /tmp/test-response.json)" = "true"

code=$(curl -sS -o /tmp/sync-response.json -w '%{http_code}' -X POST   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:20128/api/providers/$CONNECTION_ID/sync-models?mode=import")
cat /tmp/sync-response.json | jq .
test "$code" -ge 200 && test "$code" -lt 300

code=$(curl -sS -o /tmp/key-response.json -w '%{http_code}' -X POST   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d '{"name":"r3-candidate-a","scopes":["chat"]}'   http://127.0.0.1:20128/api/keys)
test "$code" -ge 200 && test "$code" -lt 300
INFERENCE_KEY=$(jq -r '.key // .apiKey // .token // .rawKey // .secret // empty' /tmp/key-response.json)
test -n "$INFERENCE_KEY"
echo "::add-mask::$INFERENCE_KEY"

curl -fsS -H "Authorization: Bearer $INFERENCE_KEY" http://127.0.0.1:20128/v1/models >/tmp/pre-models.json
curl -fsS -H "Authorization: Bearer $INFERENCE_KEY" http://127.0.0.1:20128/api/v1/auto-combo/auto/candidates >/tmp/pre-candidates.json
PRE_BAD=$(jq '[.candidates[]?.model | select(test("opus-5|big-pickle|felo-chat|felo-search";"i"))] | length' /tmp/pre-candidates.json)
PRE_GOOD=$(jq '[.candidates[]?.model | select(test("r3-good-model";"i"))] | length' /tmp/pre-candidates.json)

pre_start=$(date +%s%3N)
PRE_CODE=$(curl -sS -o /tmp/pre-auto.json -w '%{http_code}'   -H "Authorization: Bearer $INFERENCE_KEY" -H 'Content-Type: application/json'   -d '{"model":"auto","messages":[{"role":"user","content":"Reply only with OMNIROUTE_R3_OK"}],"temperature":0,"max_tokens":24}'   http://127.0.0.1:20128/v1/chat/completions || true)
pre_end=$(date +%s%3N)
PRE_LATENCY=$((pre_end-pre_start))

curl -fsS -b /tmp/omni-cookie.txt http://127.0.0.1:20128/api/settings >/tmp/settings-before.json
REV=$(jq -r '.settingsRevision // empty' /tmp/settings-before.json)
jq -n --arg rev "$REV" '{
  modelVisibilityDenylist:[
    "anthropic/claude-opus-5",
    "big-pickle",
    "felo-chat",
    "felo-search"
  ]
} + (if $rev=="" then {} else {expectedRevision:$rev} end)' >/tmp/settings-patch.json
code=$(curl -sS -o /tmp/settings-after.json -w '%{http_code}' -X PATCH   -b /tmp/omni-cookie.txt -H "x-omniroute-csrf: $CSRF_TOKEN"   -H 'Content-Type: application/json' -d @/tmp/settings-patch.json http://127.0.0.1:20128/api/settings)
if [ "$code" -lt 200 ] || [ "$code" -ge 300 ]; then
  echo "SETTINGS_PATCH_FAILED HTTP=$code"; cat /tmp/settings-after.json; exit 12
fi

curl -fsS -H "Authorization: Bearer $INFERENCE_KEY" http://127.0.0.1:20128/v1/models >/tmp/post-models.json
curl -fsS -H "Authorization: Bearer $INFERENCE_KEY" http://127.0.0.1:20128/api/v1/auto-combo/auto/candidates >/tmp/post-candidates.json

BAD_CATALOG=$(jq '[.data[]?.id | select(test("opus-5|big-pickle|felo-chat|felo-search";"i"))] | length' /tmp/post-models.json)
BAD_POOL=$(jq '[.candidates[]?.model | select(test("opus-5|big-pickle|felo-chat|felo-search";"i"))] | length' /tmp/post-candidates.json)
GOOD_CATALOG=$(jq '[.data[]?.id | select(test("r3-good-model";"i"))] | length' /tmp/post-models.json)
GOOD_POOL=$(jq '[.candidates[]?.model | select(test("r3-good-model";"i"))] | length' /tmp/post-candidates.json)
P1=false
if [ "$BAD_CATALOG" -eq 0 ] && [ "$BAD_POOL" -eq 0 ] && [ "$GOOD_CATALOG" -gt 0 ] && [ "$GOOD_POOL" -gt 0 ]; then P1=true; fi
jq -n --argjson bc "$BAD_CATALOG" --argjson bp "$BAD_POOL" --argjson gc "$GOOD_CATALOG" --argjson gp "$GOOD_POOL" --argjson pass "$P1"   '{blocked_catalog:$bc,blocked_pool:$bp,good_catalog:$gc,good_pool:$gp,pass:$pass}' >/tmp/p1.json

post_start=$(date +%s%3N)
POST_CODE=$(curl -sS -o /tmp/post-auto.json -w '%{http_code}'   -H "Authorization: Bearer $INFERENCE_KEY" -H 'Content-Type: application/json'   -d '{"model":"auto","messages":[{"role":"user","content":"Reply only with OMNIROUTE_R3_OK"}],"temperature":0,"max_tokens":24}'   http://127.0.0.1:20128/v1/chat/completions || true)
post_end=$(date +%s%3N)
POST_LATENCY=$((post_end-post_start))
CONTENT=$(jq -r '.choices[0].message.content // empty' /tmp/post-auto.json 2>/dev/null || true)
MODEL=$(jq -r '.model // empty' /tmp/post-auto.json 2>/dev/null || true)
ERROR=$(jq -r '.error.message // empty' /tmp/post-auto.json 2>/dev/null | cut -c1-700 || true)
P2=false
if [ "$POST_CODE" -ge 200 ] && [ "$POST_CODE" -lt 300 ] && [ -n "$CONTENT" ]; then P2=true; fi
jq -n --argjson status "$POST_CODE" --argjson latency "$POST_LATENCY" --arg content "$CONTENT" --arg model "$MODEL" --arg error "$ERROR" --argjson pass "$P2"   '{http_status:$status,latency_ms:$latency,nonempty_response:($content|length>0),resolved_model:$model,error_summary:$error,pass:$pass}' >/tmp/p2.json

if [ "$P1" = true ] && [ "$P2" = true ]; then
  VERDICT="ADOPT_A"
elif [ "$P1" != true ]; then
  VERDICT="REJECT_A_EXPOSURE"
else
  VERDICT="REJECT_A_DISPATCH_OR_EXHAUSTION"
fi

jq -n   --arg source_version "$SOURCE_VERSION"   --arg source_sha "$SOURCE_SHA"   --argjson pre_status "$PRE_CODE"   --argjson pre_latency "$PRE_LATENCY"   --argjson pre_bad "$PRE_BAD"   --argjson pre_good "$PRE_GOOD"   --argjson p1 "$(cat /tmp/p1.json)"   --argjson p2 "$(cat /tmp/p2.json)"   --arg verdict "$VERDICT"   '{
    schema:"R3-OMNIROUTE-CANDIDATE-A/2",
    source_version:$source_version,
    source_sha:$source_sha,
    test_provider:"deterministic-local-openai-compatible",
    before_denylist:{http_status:$pre_status,latency_ms:$pre_latency,bad_candidates:$pre_bad,good_candidates:$pre_good},
    p1:$p1,
    p2:$p2,
    verdict:$verdict,
    production_modified:false,
    secrets_persisted:false
  }' >/tmp/r3-candidate-a.json

cat /tmp/r3-candidate-a.json
test "$VERDICT" = "ADOPT_A"
