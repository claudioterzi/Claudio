# GitHub Rapid Analyzer — R³∞ Skill

## Purpose
Analyze repository/commit/PR/diff changes quickly without sacrificing provenance or verification.

## Canonical flow
1. Fetch authoritative GitHub facts first: base/head SHAs, changed files, diff/patch, checks/statuses, mergeability and review state.
2. Build a bounded state packet with `sdq1/github_rapid_analyzer.py`.
3. Call canonical TypeSafe/Jev using `github_rapid_questions()`.
4. Use Jev only to prioritize semantic review focus:
   - security/integrity
   - regression
   - verification gap
   - duplication/architecture drift
   - merge readiness
5. Inspect only the highest-value files/checks first.
6. Apply P5/P6 and authoritative GitHub postconditions before merge/deploy claims.
7. Emit the result through TĀRAKA when handing off to another AI.

## Jev rule
Jev is a fast semantic triage layer, not a repository oracle. It must never invent:
- mergeability;
- passing CI;
- deployment success;
- permissions;
- runtime behavior;
- security success.

If Jev is unavailable, fall back immediately to deterministic GitHub evidence review.

## Capillary rule
This skill is shared across every R³∞ project. Projects may add domain-specific checks, but they must reuse this shared analyzer and TypeSafe transport rather than creating another GitHub review engine.

## Acceleration rule
Start with:
`changed_files → checks/statuses → Jev focus → targeted diff → falsifier → decision`

Do not read the entire repository when a bounded diff and dependency context are sufficient.

## Private-IP rule
When a change touches proprietary/private R³∞ material, classify it before review. Public analysis may expose hashes/references only; private payloads remain SEALED/private.

Signature: C.Terzi
