# R³∞ BODY — MCK Operational Loop v0.1 · 2026-09-22

**Owner:** Claudio Terzi  
**Project:** IDEA-026 — Raffaello Body / Care / Matrioska  
**Status:** CANDIDATE / SOFTWARE HARNESS / NO PHYSICAL ACTUATION  
**Signature:** C.Terzi

## The leap

The MCK principle — **Matter · reflective continuity · Knowledge** — is no longer only a design sentence.

This candidate implements the first bounded cycle in which a BODY observation can become a physical-action candidate, pass independent verification and a deterministic body gate, produce an observed result, and only then become a knowledge candidate.

```
SENSE
  ↓
PERCEIVE
  ↓
REFLECT
  ↓
IMAGINE POSSIBILITIES
  ↓
VERIFY
  ↓
BODY_ACTION_GATE
  ↓
ACT
  ↓
OBSERVE
  ↓
LEARN
  ↓
EVOLVE_CANDIDATE
```

This is a software harness. It does not command real hardware.

## MCK mapping

### M — Matter

Matter is represented by:
- BODY identity;
- sensor frame;
- sensor integrity;
- observations and provenance;
- actuator candidate;
- physical trajectory signal;
- authoritative postcondition observation.

### C — reflective continuity

For engineering purposes, this layer represents:
- CORE identity continuity;
- BODY identity;
- self-state;
- uncertainty;
- contradictory sensory evidence;
- STOP state;
- authority envelope;
- independent verification of model-origin actions.

It is **not evidence or a declaration of phenomenal consciousness**.

### K — Knowledge

Knowledge is not the action response itself.

An experience is eligible to become a knowledge candidate only when the action's requested postcondition is verified through the carried R3-007 state-grounded verification contract.

```
tool/action success ≠ knowledge
authoritative postcondition match → knowledge candidate
```

Failed, mismatched or unverifiable experience remains in the append-only ledger as evidence but is not promoted.

## Identity invariant

```
CORE CONTINUITY > BODY CONTINUITY
```

The cycle records both:
- `core_identity_id`
- `body_id`

Changing BODY or edge perception model does not change CORE identity.

This makes the architecture capable of testing hot-swappable bodies, limbs, sensors and edge models without relocating Raffaello's identity into any one component.

## Edge perception

The loop accepts a replaceable `perceiver` interface.

A future MiniCPM-class model can be tested here as an edge perception module, but no particular MiniCPM release is made canonical by this harness.

Rule:

> Edge perception may change what Raffaello sees; it does not become what Raffaello is.

## Scacchiera connection

The possibility generator is the execution-level interface to the **Matrice dei Possibili / Scacchiera Quantica**.

It may generate multiple action candidates.

The selector never asks a language model which candidate has authority. Each branch is independently verified and passed through `BODY_ACTION_GATE`; only already-allowed branches enter deterministic selection.

Current selection policy:
1. only allowed candidates;
2. higher declared priority;
3. lower physical risk;
4. stable action id tie-break.

This policy is deliberately simple and falsifiable.

## No direct LLM motor control

Invariant enforced by code:

- a model may propose a `CORE_ACTION`;
- a model-origin action requires independent verification;
- an `EDGE_REFLEX` cannot originate from a model;
- an `EDGE_REFLEX` must be deterministic, preregistered and low risk;
- high/critical physical actions are not autonomously executed by v0.1;
- unresolved sensor/perception contradictions block actuation;
- authenticated STOP blocks actuation;
- missing authority scope blocks actuation.

The executor itself is host-supplied. The language model never receives a direct actuator handle from this module.

## R3-007 reuse

This branch carries the already-falsified R3-007 postcondition harness rather than inventing a BODY-specific verifier.

Consequently:
- `HTTP 200`, `success=true`, motor-driver ACK or UI confirmation are trajectory evidence only;
- authoritative read-after-action state is required for `VERIFIED_POSTCONDITION`;
- proxy/unavailable observations do not become verified success.

## Body Evidence Ledger

Every HOLD or attempted action writes a hash-chained append-only record through the existing R3 evolution ledger primitive.

Two record kinds:
- `body_mck_hold`
- `body_mck_experience`

The record separates:
- Matter;
- reflection;
- knowledge/postcondition state.

A failed experience remains useful negative evidence.

## Falsifiers

The candidate fails if any test shows that:
1. a model-origin physical action executes without independent verification;
2. STOP fails to veto;
3. unresolved sensor contradiction still actuates;
4. a high/critical action auto-executes;
5. an EDGE_REFLEX can be generated directly by a model;
6. an unregistered reflex executes;
7. action success without authoritative postcondition promotes knowledge;
8. wrong observed state promotes knowledge;
9. the first unsafe Scacchiera branch prevents a later safe branch from being selected;
10. swapping edge model or BODY silently changes CORE identity;
11. ledger integrity breaks.

## First target experiment

The current deterministic tests use a simulated cup-reaching task:
- one sensor frame;
- multiple possible actions;
- injected unsafe branch;
- injected contradiction;
- injected postcondition mismatch;
- edge-model hot swap;
- BODY-A → BODY-B swap while CORE remains constant.

No physical capability is inferred from these tests.

## Promotion path

```
DESIGN
→ SOFTWARE FALSIFICATION
→ BODY-CONTINUITY-001 SIMULATION
→ HARDWARE-IN-THE-LOOP
→ LOW-ENERGY BENCH ACTUATION
→ SAFETY REVIEW
→ LIMITED PHYSICAL PILOT
```

At each boundary:
- preserve provenance;
- use authoritative postconditions;
- keep rollback;
- never promote a simulation to embodiment evidence.

## Files

- `sdq1/body_mck_loop.py`
- `tests/test_body_mck_loop.py`
- `sdq1/verification_harness.py` — carried R3-007 dependency
- `docs/R3_BODY_ARCHITECTURE_V0_3.md`

— C.Terzi
