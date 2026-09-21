# Google Drive Rapid Analyzer — R³∞ Skill

## Purpose
Analyze Google Drive folders/files/versions quickly while preserving provenance, privacy and GitHub↔Drive continuity.

## Canonical flow
1. Read Drive facts first:
   - file/folder metadata;
   - parent/canonical location;
   - sharing/permissions;
   - revision history and last modifier;
   - bounded relevant content;
   - comments only when useful;
   - matching GitHub artifact/version when applicable.
2. Build the bounded state with `sdq1/drive_rapid_analyzer.py`.
3. Call canonical TypeSafe/Jev with `drive_rapid_questions()`.
4. Jev prioritizes one review focus:
   - canonical location;
   - version divergence;
   - duplicate cleanup;
   - privacy/IP boundary;
   - content verification;
   - GitHub↔Drive alignment.
5. Inspect only the minimum additional Drive evidence needed.
6. Before any state change, verify destination/version/permissions and applicable authorization.
7. After a verified change, re-read Drive metadata/content/revision as authoritative postcondition.
8. Propagate only the verified delta through the Capillary layer.

## Jev rule
Jev is advisory. It cannot establish:
- who owns a file;
- current sharing state;
- revision identity;
- file completeness;
- canonical location;
- successful synchronization;
- whether an overwrite/move/delete actually happened.

Those facts must come from Google Drive evidence.

## Revision rule
When version history matters:
`list_file_revisions → previousRevisionId → fetch_file_revision → compare current/previous`

Do not infer absence from a partial folder listing or a text preview.

## Privacy/IP rule
Classify artifacts as PUBLIC | PRIVATE | SEALED before propagation.
Private R³∞ MAX material never moves into public folders merely for synchronization.
SEALED handoffs may carry only safe metadata, reference and hash.

## GitHub↔Drive rule
Drive is the owner-visible document home; GitHub is the technical source for code.
A mismatch is a divergence to resolve, not permission to overwrite either side blindly.

## Capillary rule
This skill is inherited by every R³∞ project. Projects add local file/folder rules but do not create another global Drive analysis engine.

## Acceleration rule
Start with:
`metadata → revision/folder delta → Jev focus → targeted read → postcondition`

Avoid exhaustive Drive scans when a bounded file/folder/version check is sufficient.

Signature: C.Terzi
