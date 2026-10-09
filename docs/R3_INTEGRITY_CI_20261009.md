# R³ integrity and CI candidate — 2026-10-09

State: **CANDIDATE, not adopted**. Direct owner request: fix demonstrated defects
and apply measurable improvements. Retroactive classification: PATCH + RETEST.
Base: PR #120 at `a4a06d0aef51708c61f4fc5d0f863b1eba832165`;
main observed unchanged at `e01b98a0d9a3a1d135b172088949dd1a5bd79dff`.
This is a separate branch on the existing Evidence Graph candidate. It does not
overwrite that branch, the supervisor candidate #113, or historical receipts.

## Changes and evidence

- **CI:** remove suppressed dependency/test errors, install the declared R3 and
  bot requirements, resolve the bot import path, and run pytest once under
  coverage. Coverage and artifacts survive a failed run. Lint/type/security scans
  in this workflow remain explicitly advisory; the separate Security Scan is
  unchanged. PR triggers include stacked candidates; push checks target main to
  avoid a second copy of the same branch/PR run. Test Runner now explicitly runs
  Evidence Graph, benchmark integrity, backup, RedFrag and CI falsifiers.
- **R3-019:** separate execution completion from evaluated success. All-wrong
  and partly-wrong runs cannot receive success-gated efficiency credit. The
  evaluator is still lexical; this is not a live capability baseline.
- **RedFrag:** hash the entire source, reject a mismatching supplied digest,
  preserve the full digest through clustering, and quarantine oversized active
  sources instead of silently activating a prefix. Normalize each source once.
- **Backup:** report SAR-only restore with zero restored memory/VSS entries and
  separate snapshot counts. Complete-restore requests fail before writes.
  Removing integrity from a modern snapshot cannot downgrade it to legacy.
  Additional falsifier found and fixed: restore used to read a path twice and
  could verify different bytes from those written. It now verifies the exact
  in-memory snapshot it consumes.
- **RRR startup and authentication:** create the sync log directory before its
  first FileHandler. Refuse network event/ask access when NETWORK_SECRET is
  absent and authenticate node-list reads. Existing authorized flows still pass;
  callers of the node-list endpoint must provide the configured secret. Public
  health remains available. Orchestra's health test now checks its existing
  additive bootstrap contract and explicitly refuses a persistence claim.

The three integrity patches were recovered from candidate
`4bf1600891613906ba176376ab50f77617fe5a9a`, preserved on Drive on 2 October,
then compared to current source. Their eight regression cases fail against
the current base (23 tests: 5 failures, 3 errors). The new same-snapshot restore
falsifier also fails against the recovered patch and passes after this revision.

## Validation

Machine-readable receipt: `docs/evidenze/R3_INTEGRITY_CI_20261009.json`.

- Targeted integrity suite: **62 passed, 10 subtests passed**.
- Full local suite after dependency and code fixes: **397 passed, 2 failed,
  1 skipped; 675 subtests passed**. Python 3.12.14 locally; hosted workflows
  declare Python 3.11. Hosted results for this candidate are not claimed here.
- The two remaining failures are Atelier restore/UI assertions about the
  image-generation control. Both also fail on the exact unmodified base.
  They are not waived or rewritten: this R³ candidate does not change the
  separate Atelier flow. Proposal for that domain: reconcile the restored-page
  control with the server-issued image-token contract, preserving refusal of
  forged uploaded permissions. They now correctly keep the full CI red.
- One historical RedFrag fixture check skips because its pinned commit is
  unavailable in this checkout. This is explicitly missing coverage.
- Actual old/new CI shell commands tested in isolated temporary directories:
  pass, failed assertion, collection error, and no-tests cases. Old masked
  command returns 0 in all four; new command succeeds only for the passing case.
- Initial full-run failures caused by missing local SOCKS support are kept in
  the receipt, separate from code defects. Installing the local client dependency
  resolves the loopback tests; no cloud runtime was inspected or changed.

Reproduce the targeted suite:

```sh
python -m pytest -q tests/test_evidence_graph.py tests/test_benchmark_controlled.py tests/test_benchmark_integrity.py tests/test_backup_recoverability.py tests/test_redfrag_pipeline.py tests/test_ci_failure_propagation.py
```

Full suite, after installing the requirements named in the workflow:

```sh
PYTHONPATH=.:integrations/raffaello-bot python -m coverage run -m pytest -q
```

## Measured efficiency and research transfer

For 64 synthetic sources, RedFrag fingerprint calls fall from **128 to 64**.
The complete output is identical on the bounded fixture. Descriptive local
timing: median **1.9182 → 1.6504 ms** per plan, about 14% lower. This uses an
identical deterministic classifier stub, 3 warmups, 20 alternating AB/BA pairs,
and 5 calls per arm; raw samples and fixture hash are in the receipt. There is
no provider call, learned capability claim, or end-to-end speedup claim.

Fixture reconstruction: for each `i in range(64)`, use id/logical_id `str(i)`,
content `('source-%03d-' % i) * 400`, provenance `'fixture:' + str(i)`, and
`active_relevance=True`. Stub assessment returns cluster_id and KEEP_ACTIVE.
Load the baseline module from the pinned base above and compare plan outputs,
fingerprint call counts, and `time.perf_counter_ns()` across counterbalanced arms.

Primary source: Xu et al., [MemTrace, 4 October 2026, sections 3.1–3.3](https://arxiv.org/html/2610.04838v1).
Its useful principle is to bind retained evidence to source conditions, validate
it before reuse, and defer oversized evidence instead of truncating it. The
application here is a bounded engineering interpretation within existing R³
components. No second memory engine or independent distributed-continuity proof
is introduced. Pytest [exit-code documentation](https://docs.pytest.org/en/stable/reference/exit-codes.html)
supports preserving nonzero outcomes, including empty collection.

## Adoption boundary and next action

R3-020 remains candidate-only. Independent complete restore, authenticated
provenance, and provider/model continuity are not proved by these patches.
SAR writes remain atomic per file, not a transaction across all components.

The one-line sync startup fix must be reconciled with #113 rather than replacing
its supervisor work. A merge touching `r3/**` can redeploy watched Railway
services; no merge or deployment is performed. Preserve the candidate and its
Drive mirror, resolve the two known domain failures, and review hosted checks
at the exact resulting revision before adoption. Rollback is a revert of this
isolated candidate; historical receipts stay immutable.
