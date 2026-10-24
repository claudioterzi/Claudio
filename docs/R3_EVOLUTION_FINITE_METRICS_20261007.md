# R3-020: finite numerical evidence candidate — 7 October 2026

NaN and Infinity could bypass promotion comparisons in the existing Evolution
Kernel; integers beyond float range and malformed critical thresholds could raise
instead of returning a decision. The bounded patch rejects non-finite input
metrics, non-negative threshold violations, malformed critical rules and
non-finite gains derived from otherwise finite operands. It reuses the existing
kernel, preregistration, ledger and protected core-code gate.

The main source pin is `b3e82b84bde170e50c7ffbd5bbb09de0f8b6d546`.
The isolated local worktree starts at `7749b9c`; all six modified preexisting
source/record blobs were fetched from current main and matched byte-for-byte.
Remote publication must build on the current main tree, retaining heartbeat files.

## Observed experiment

Candidate `R3C-FINITE-METRICS-20261007` was preregistered before modification.
A separate agent froze 56 mechanical cases without inspecting the candidate
source, then ran that identical suite against pinned baseline and candidate.

| Observation | Baseline | Candidate |
|---|---:|---:|
| Conformant cases | 17/56 | 56/56 |
| Expected REJECT decisions obtained | 7/46 | 46/46 |
| Invalid admissions | 23 | 0 |
| Unhandled exceptions | 11 | 0 |
| Eligible/HOLD controls preserved | 10/10 | 10/10 |

The 46 expected rejections include 44 invalid input/configuration cases and
2 intentional rejection controls. The other ten controls yield eight eligible
and two HOLD decisions. This is numerical integrity evidence, not model-quality,
independent-provider or live production evidence.

Seventeen kernel unit-test methods and twenty adjacent benchmark methods pass;
the existing self-test, compilation and diff checks pass. A disposable copy of
the pinned baseline was restored, hash-checked, imported and removed. The
existing kernel records this protected core-code candidate as **STAGED**, never
auto-applied. Its two-record experiment hash chain verifies.

## Online proposals and Jev

Official Python documentation was read using Codex web tools:
[finite numbers](https://docs.python.org/3/library/math.html#math.isfinite),
[JSON non-standard numbers](https://docs.python.org/3/library/json.html#infinite-and-nan-number-values),
and [boolean integers](https://docs.python.org/3/library/stdtypes.html#boolean-type-bool).

- A: validate numerical inputs, thresholds and derived gains in the existing
  gate. Implemented and tested here.
- B: reject non-standard values only at JSON ingress. Insufficient for direct
  Python callers or arithmetic overflow after parsing.
- C: combine A with strict JSON at identified interfaces. A separate candidate
  must establish compatibility before changing historical ledger serialization.

The saved bounded Jev request uses the existing shared System One client and
universal policy, explicit TypeSafe provider and `jev-latest`. The actual call
raised `SystemOneNotConfigured` before HTTP: **no Jev opinion, inference or web
browsing occurred**. Resume through an existing authenticated execution channel;
do not retrieve plaintext from a redacted-only connector or create another client.

## Reproduction and provenance

Run from the candidate repository:

```bash
python -m unittest tests.test_evolution_kernel tests.test_benchmark_integrity tests.test_benchmark_controlled -v
python -m sdq1.evolution_kernel --self-test
python docs/evidenze/R3_EVOLUTION_FINITE_20261007/heldout_probe.py --source sdq1/evolution_kernel.py --out /tmp/r3-finite-trial-unique.json
```

The probe writes create-only output. Inspect the aggregate and per-case results;
its process exit code alone does not assert fixture success. To reproduce the
baseline, obtain `sdq1/evolution_kernel.py` at the main source pin, verify its
SHA-256 `42a6a97e62b0ab160521c589d23d7dc1e6ec03d54476252196e218953dde065c`,
and pass that source file to the same unchanged probe with another output path.

[Evidence manifest](evidenze/R3_EVOLUTION_FINITE_20261007.json) pins exact bytes
of original raw receipts, the frozen probe, preregistration, hash chain, unit-test
log and the blocked Jev request. Executor-local paths inside original receipts
are provenance, not universal access links.

Next: review the draft and hosted gates before a separate core-code adoption
decision. No production change, automatic cross-chat memory or background loop
is implied. PR #113 retains its separate real-state recovery and Railway sleep
requirements.
