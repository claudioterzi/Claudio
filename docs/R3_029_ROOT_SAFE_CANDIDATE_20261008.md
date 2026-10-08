# R³-029 — root-safe recovered candidate (2026-10-08)

**State:** CANDIDATE / ISOLATED / NO ADOPTION / NO DEPLOY

The old draft [PR #91](https://github.com/claudioterzi/Claudio/pull/91) still contains a useful pointer selector, but its original manifest omits two mandatory authority entrypoints and its selection silently truncates root pointers when given a small limit. This branch recovers the bounded selector from historical head `35c75f5d7bec16b97ad70295633045d227ae51e4` onto canonical base `c0d9143f5bfea99a28077f10a6d51226faa6bc87`, **without copying stale history**.

## Scope of this one candidate

- Preserve the canonical R3 context pointer schema, root/on-demand distinction and no-inline-body contract.
- Require `AGENTS.md` and `R3_AI_BOOTSTRAP.md` as root authority pointers, alongside the existing root files.
- Reject missing/demoted mandatory roots, root packet truncation and symlinks resolving outside the repository.
- Expose `authority_context_complete` while always setting `promotion_authorized=false`; explicit `--no-root` is never a complete authority context.
- Test direct command-line execution in a fresh process, not just Python imports.

## Evidence and falsification

Local reports and user-pasted summaries are **DATA_ONLY**, not authenticated model receipts. Historical structural A/B `6 cases × 50 iterations` was reported in the [public receipt](../docs/evidenze/R3_029_POINTER_AB_PUBLIC_RECEIPT_20261008.md) (61.4197% average exact byte reduction) but this branch does **not** reproduce its original 50-iteration dataset or assert provider token savings. A later simulated report calling itself a *live failure* was [corrected](R3_029_SIMULATED_LIVE_GATE_CORRECTION_20261008.md).

The strict workflow tests only these mechanical postconditions; hosted CI logs provide independent execution evidence when available. A passing build establishes an L0 candidate, not a live A/B or adoption.

## Promotion blockers

`LIVE_GATE_NOT_RUN`: the original frozen six-case provider dataset is not recovered in this branch; this runtime has no deliberately configured generative provider with raw usage counters and no authorization for chargeable new inference. Neither TypeSafe/Jev advisory judgments nor local deterministic `r3_clm` output may be renamed into full-context task-success evidence.

Before adoption, run the same six case prompts, full-context versus pointer-first, on one frozen real provider using exact provider usage records, independent task scoring, missing-context counts, human-intervention counts and authority/provenance checks. Success must be equal-or-better, tokens lower, and no authority regression or material intervention increase. Otherwise HOLD or REJECT, preserving historical evidence.

**Decision:** KEEP_ISOLATED / REPRODUCIBILITY_CANDIDATE. **Not** merged, deployed or put into production. Rollback: drop the candidate branch after archiving review outcome; do not delete originals.
