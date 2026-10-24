# R3-007 State-Grounded Verification — R³∞ Skill

## Rule
A successful action trajectory is not proof of the requested state.

## Canonical flow
1. Execute the authorized state-changing action.
2. Record the trajectory signal separately: HTTP status, tool success, deployment READY, UI confirmation, etc.
3. Define the expected postcondition.
4. Read the resulting state from the most authoritative technically available source.
5. Record:
   - postcondition_source
   - expected_state
   - observed_state
   - state_match
   - verification_time
   - verification mode: AUTHORITATIVE | PROXY | UNAVAILABLE
6. Classify the evidence with `sdq1/verification_harness.py`.
7. Never promote a proxy or missing read as authoritative success.

## Decisions
- `VERIFIED_POSTCONDITION`: authoritative read matches expected state.
- `STATE_MISMATCH`: action signaled success but state is wrong.
- `PROXY_MATCH_NOT_AUTHORITATIVE`: proxy agrees but cannot prove state.
- `UNVERIFIED_POSTCONDITION`: no authoritative read.
- `VERIFICATION_ERROR`: verifier failed.
- `TRAJECTORY_FAILED`: action itself failed.

## Authority
This harness classifies evidence. It never grants permission to send, spend, publish, delete, deploy, merge or otherwise change external state.

## Capillary
Every R³∞ project inherits this rule. Domain projects provide their own authoritative observer/comparator but reuse the common harness rather than inventing a second verifier.

Signature: C.Terzi
