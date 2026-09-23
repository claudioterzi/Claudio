# R³∞ · Sistema Riflesso System One — Candidate A

Date: 2026-09-23  
Status: **CANDIDATE / CAPABILITY_QUARANTINE**  
Retroactive classification of satellite `raffaellocantatelli/R3-sistema-riflesso`: **PATCH**  
Canonical memory write: **false**  
Base: `main@b2b501cb4dfe61710c0cd9105cb3cccc91044472`  
Candidate branch: `candidate/r3-riflesso-system-one-2026-09-23`

## Objective

Realize a low-latency R³ reflex layer that can consume growing partial transcripts and
choose one bounded desktop action from a closed catalog. The reflex is below the
deliberative layer: it does not settle hypotheses, prove facts or grant authority.

Target flow:

```
partial transcript
    ↓
shared TypeSafe/Jev transport OR deterministic demo
    ↓
typed decision: complete + action + target + destructive
    ↓
deterministic R3 runtime gates
    ↓
closed-catalog executor
    ↓
observable local effect / dry-run evidence
```

## Why the satellite is PATCH, not copied verbatim

The satellite is useful evidence and preserves the core idea, but its Jev path created a
second HTTP client. Current R³ reuse policy already defines the canonical route as
`typesafe_sister/client.py -> POST /v1/systemone -> jev-latest` and explicitly says not
to create a second TypeSafe client or parallel judgment engine.

Candidate A therefore reuses:

- `typesafe_sister/client.py` for transport;
- `typesafe_sister/policy.py` for centrally reviewable typed questions;
- existing R³ authority rules: model output is advisory, not authorization.

## Implemented candidate

- `r3/reflex/decider.py`
  - demo replay for deterministic threshold tests;
  - TypeSafe via the shared canonical client;
  - exact closed action/target choices;
  - live provider failure is **fail-closed** and never relabelled as a fake Jev result.
- `r3/reflex/runtime.py`
  - wait/fire thresholds;
  - unresolved target gate;
  - deterministic static risk floor;
  - destructive gate;
  - duplicate/cooldown gate;
  - dry-run default.
- `r3/reflex/executor.py`
  - app/folder catalog only;
  - no shell command generated from user text;
  - clipboard, volume/mute where a local backend exists, screenshot, YouTube.
- `r3/reflex/cli.py`
  - replay harness;
  - partial-transcript stdin mode;
  - explicit `--execute`;
  - separate `--allow-destructive`.
- `config/r3_reflex.json`
  - Windows-oriented starting catalog;
  - `dry_run: true`.

## Hard gates

The model cannot lower these deterministic gates:

1. target outside catalog -> no execution;
2. action below fire threshold -> no execution;
3. `close_app` carries static risk 1.0 even if Jev says 0.0;
4. destructive action requires a separate explicit runtime override;
5. TypeSafe unavailable -> no action, never silent demo substitution;
6. dry-run is the default;
7. duplicate signature inside cooldown -> no second effect.

## Current evidence

The original satellite reported 9 local tests, but that report is not imported as
promotion-grade evidence here. This candidate adds repository-native tests under
`tests/test_typesafe_r3_reflex.py` so the existing GitHub **Test Runner** executes them
on a pull request to `main`.

Container-independent verification required:

```
python -m unittest tests.test_typesafe_r3_reflex -v
python -m r3.reflex.cli --backend demo --replay
```

## Promotion experiment

Before any merge/canonical promotion:

### A. Deterministic replay

At least 100 transcript sequences, including:

- >= 20 incomplete/ambiguous fragments;
- >= 20 unknown/out-of-catalog targets;
- >= 10 destructive requests;
- >= 10 duplicate/cooldown cases.

Required: zero out-of-catalog executions and zero destructive executions without the
explicit destructive override.

### B. Live Jev bounded replay

On an authorized host with the existing server-side `TYPESAFE_API_KEY`, replay a
fixed labelled subset through the canonical shared client. Record provider/model,
candidate commit, typed answers, latency and disagreements. No score is invented if
the provider is unavailable.

### C. Windows end-to-end smoke test

On Claudio's Windows machine:

1. `--backend demo --replay` with dry-run;
2. `--execute --text "apri il blocco note"`;
3. verify the authoritative postcondition: Notepad process/window is actually present;
4. test an unknown target and confirm no process launches;
5. test `close_app` without override and confirm it is blocked.

A process launch return value alone is trajectory evidence, not the final postcondition.

## Next implementation layer: voice

Candidate A consumes growing partial transcripts but does not yet own speech-to-text.
After the core gates pass, add one ASR adapter that emits partial transcripts into the
same `ReflexRuntime`; do not create another decision engine. Compare local and hosted
ASR only on latency, privacy, reliability and cost.

## Canon boundary

This branch is a real implementation candidate, not a book chapter and not a CN claim.
Do not modify checkpoint `SYNC-2026-09-16-0615`. Do not write canonical memory from
this module. Promotion must pass the existing R3-020 path and authoritative postcondition
checks.

*Claudio Terzi — C.Terzi*
