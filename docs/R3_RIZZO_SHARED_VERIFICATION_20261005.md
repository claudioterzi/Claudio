# Rizzo Flow in R3's existing verification workflow

Status: CANDIDATE / ADAPTER_CONTRACT_TESTED / LIVE_INFERENCE_NOT_RUN.

Rizzo Flow upstream advertises a TypeSafe-compatible POST /v1/systemone API.
R3 already implements that path in typesafe_sister.client and centrally stores
questions in typesafe_sister.policy. Reuse this transport and the universal
review; no second client, semantic engine or production service is introduced.

For an intentionally configured loopback instance:
```
R3_SYSTEMONE_PROVIDER=clm
R3_SYSTEMONE_BASE_URL=http://127.0.0.1:8017
R3_SYSTEMONE_MODEL=rizzo-latest
```
Then call typesafe_sister.universal.assess_project_state with bounded service
metadata and explicitly sourced observations. universal_questions already covers
contradictions, missing critical input, unsupported claims, freshness, readiness,
risk and external effects. Its validated output is advisory only.

The CLM label here identifies the shared compatible adapter, not a claim that
Rizzo implements another provider's proprietary architecture. An external
endpoint must be deliberately configured and protected; loopback is unsuitable
for Railway access to a Dell. No secret or private archive belongs in the input.

Four added fixtures verify explicit Rizzo model/endpoint selection, no-key
local transport with no redirects, rejection of incomplete universal answers,
and provider failure without approval. Existing shared transport/universal tests
are run alongside them. Mocked replies establish plumbing and failure behavior,
not Rizzo model quality, latency, calibration or deployed availability.

## Verification responsibilities
- Model: classify ambiguity, identify apparent contradictions, suggest what
  evidence to inspect next. No factual or authorization promotion from a score.
- Deterministic existing node mechanisms: document hashes, signed control event
  validation, authenticated fingerprints, replication receipts and readback.
- Restore gate: prove a separate backup can recreate persisted state; a semantic
  model cannot substitute for restoration evidence.

## Required live benchmark
Freeze model/runtime SHA and quantization, question policy and held-out service
fixtures; compare Rizzo with the existing Jev/shared baseline on contradictory,
incomplete, stale and adversarial service states. Measure false approvals,
false alarms, abstentions, latency and resource use. Preregister this future
benchmark before executing it. Do not label these fixture tests as that benchmark.

Use existing authorized compute where available; no paid cloud resource or model
weights were provisioned in this candidate. Prefer advisory shadow evaluation
before changing any current default. Do not claim the historical reported Rizzo
21/21 audit was independently reverified by this work.

Upstream inspected: https://github.com/Rizzo-AI-Academy/rizzo-flow
Important upstream caveat: probabilities uncalibrated without local calibration;
no quality equivalence to Jev claimed. Advertised GPU timings are hardware- and
workload-specific, not a prediction for Claudio's Dell or Railway.
