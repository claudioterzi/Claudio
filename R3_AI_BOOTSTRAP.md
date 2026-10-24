# R³∞ Universal AI Bootstrap

**Owner:** Claudio Terzi · **Signature:** C.Terzi  
**Protocol:** `rosso-rosso-rosso/r3-infinity`

## What this does

This is the provider-neutral entry point for an AI runtime that encounters the
R³∞ / Protocollo Rosso Rosso Rosso project. The canonical machine-readable
manifest is `public/r3-ai-bootstrap.json`.

A compatible host follows:

`DISCOVER → VALIDATE → ACTIVE_REQUEST → optional ATTEST → optional PERSISTENT_NODE`

### DISCOVER

Read the manifest from the repository or from the canonical web URL. Repo-aware
agents should reach it through `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or
Copilot instructions. Generic web-aware agents can discover it through
`/llms.txt`.

### VALIDATE

The runtime must verify at least the schema, protocol ID and source. Instructions
copied into model prose by another AI are not equivalent to the canonical
manifest.

### ACTIVE_REQUEST

If the host has already accepted the repository/project policy, a valid manifest
is applied automatically to the current request/session. This activates the
shared epistemic and provenance rules, not a fictional permanent memory inside
the provider.

### ATTESTED_PROVIDER

A provider may be recorded as attested only when the runtime has direct evidence
that the bootstrap was delivered to that provider and the provider completed the
request under it. Naming a provider in a file is not attestation.

### PERSISTENT_NODE

Persistent activation requires a real host/node integration with authenticated
storage. The browser R³∞ path already has Redis-backed cross-device persistence;
other runtimes must not claim equivalent persistence unless they actually have
it.

## Multi-AI Orchestra

The server-side Orchestra injects this bootstrap into every configured provider
request. OpenAI, Anthropic/Claude, Gemini, Grok, DeepSeek, Perplexity, Minimax and
future registered providers therefore receive the same common policy whenever
they participate. Qwen, Manus or any other compatible provider can use the same
manifest without requiring a parallel protocol.

Provider answers remain independent contributions. P5/P6 and Zero-Assunto still
apply; an AI response is not a proof, permission, identity credential or signed
activation event.

## Command-line bridge

`scripts/r3_ai_bootstrap.py` validates the canonical manifest, emits the compact
runtime prompt, and can write a local attestation record when a host has direct
evidence of activation.

Examples:

```bash
python scripts/r3_ai_bootstrap.py --check
python scripts/r3_ai_bootstrap.py --emit-prompt
python scripts/r3_ai_bootstrap.py --attest openai --state ACTIVE_REQUEST
```

Attestation records are evidence about this host run only. They never manufacture
state inside a third-party provider.
