# R3-HISTORY/1 — Preservation of the project story

Origin: **Claudio Terzi [CT-LGAI-001]**

## Purpose

R3-HISTORY preserves not only the current files but the sequence that explains how R³ evolved.

The historical archive is append-only. A new interpretation may supersede an old one, but never silently erases it.

## Historical classes

1. **CODE_HISTORY** — Git commits, refs, tags, branches and release artifacts.
2. **DECISION_HISTORY** — decisions, rejected alternatives, hypotheses, falsifiers and adoption gates.
3. **CONVERSATION_HISTORY** — exported ChatGPT/Claude/Grok conversations or other transcripts explicitly supplied to R³.
4. **MEMORY_HISTORY** — canonical memory/state snapshots, rehydration packets and provenance.
5. **EVIDENCE_HISTORY** — receipts, hashes, deployment proofs, test reports and incident records.
6. **DOCUMENT_HISTORY** — specifications, books, PDFs, notes, designs and project documents.
7. **IDENTITY_HISTORY** — versioned protocol/identity documents. Never inferred from a model's hidden state.

## Rules

- No single file is "the history".
- No later summary may destroy the underlying source.
- Summaries and memories are indexes, not substitutes for original records.
- Every historical object gets SHA-256, timestamp, source/provenance and archive path.
- If an item has no recoverable source, it is marked MISSING_SOURCE rather than reconstructed from imagination.
- Nine agents reading the same historical object are one evidence source.
- Secrets are not included in the history archive in plaintext.
- Deletion from a live workspace does not automatically delete its historical archive.
- Any requested permanent deletion must be explicit and applied to every relevant archive under the user's control.

## Conversation preservation

R³ cannot assume that a chat platform will remain available forever. Conversation history must therefore enter the NAS as exported files.

Accepted sources include:

- official account exports;
- Markdown/JSON transcripts intentionally saved by the user;
- project conversation extracts created for archival purposes.

The backup system stores those source files unchanged and may additionally create searchable indexes. An index never replaces the original export.

Default inbox:

```
R3_HISTORY_INBOX/
  conversations/
  documents/
  evidence/
  memory/
```

Anything placed there is copied into the immutable snapshot under `history/` with a manifest.

## Recovery objective

A successful disaster recovery should answer:

1. What code existed?
2. What did we believe at that time?
3. Which claims were facts, hypotheses or simulations?
4. Why was a decision made?
5. What evidence supported it?
6. What changed later?
7. Can the original source still be opened?

If those questions cannot be answered, the backup is data-preserving but not history-preserving.
