# Skill discovery and executed checks — 7 October 2026

Host research, DATA_ONLY. No Jev browsing or live opinion is claimed. Source
availability, local installation, connected tools and executed verification are
separate observations.

| Skill | Observed availability | Concrete use and evidence |
| --- | --- | --- |
| Google Drive file lifecycle | Connected session skill; used | Existing owner-only R3 Backup folder, approved private upload, metadata/privacy readback and authenticated raw downloads. |
| Full-story verification | Session skill read and applied to the backup flow | Verify archive → upload → actual downloaded bytes → hash → isolated restore. [Pinned official reference](https://github.com/openai/plugins/blob/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f/plugins/vercel/skills/verification/SKILL.md). |
| TypeSafe AI | Official source inspected, not installed | Typed questions and workflow owned by code. It revealed that question IDs are not sent to the model: each skill-fit instruction now names its validated ASCII catalog ID. [Pinned source](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/skills/typesafe-ai/SKILL.md), v0.5.7. |
| R3-007 state-grounded-verification | Source on PR76 readable; absent from current checkout | Reuse existing verification harness for authoritative postconditions; source availability does not merge or activate the skill. [Pinned source](https://github.com/claudioterzi/Claudio/blob/29f9523e2f3322286650e1d9e11db62da00bd380/skills/state-grounded-verification/SKILL.md). PR76 was observed open, non-draft and unmerged. |
| Cloud environment runtime | Session skill available and used | Current readiness observation revision66 and caller preflight both show missing R3_API_TOKEN. Network policy is unrestricted; that does not establish authentication. |
| propose-security-hardening | Official source inspected; plugin not installed | Conditional reference for concrete credential/trust-boundary issues, not a token-injection capability. [Pinned source](https://github.com/openai/plugins/blob/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f/plugins/codex-security/skills/propose-security-hardening/SKILL.md). |

The two repository-installed skills are GitHub Rapid Analyzer and Google Drive
Rapid Analyzer. Both reuse the shared System One layer and deterministic fallback;
no parallel client is introduced. Current official Codex examples are in
[`openai/plugins`](https://github.com/openai/plugins/blob/5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f/README.md).
The previous `openai/skills` README now redirects there; its older installer is
not treated as a current automatic adoption path.

Plugin search for SSH/Tailscale/Runpod/backup returned a DigitalOcean provisioner.
It was not suggested or installed: provisioning a new paid workspace does not
resolve the current existing-resource mandate. TypeSafe/Jev/1Password search
returned no plugin, with no exhaustive-directory claim. Browser profile metadata
contained no recorded signed-in sites; profile names alone do not prove access.

## Correction and actual execution

The original request and BLOCKED receipt remain preserved. The v2 packet contains
eight catalog entries and ten questions, bounded to 18,390 bytes at freeze. The
host supplies the catalog; Jev may only recommend from available IDs plus NO_MATCH.
Retrieved metadata remains DATA_ONLY and cannot install tools or authorize effects.

Fix: `fit_<id>` dictionary keys are invisible to the model, so an instruction that
refers only to its own key cannot identify the target. Each instruction now includes
the already validated ASCII ID, with no interpolation of external descriptions.
The new negative-control test removes host question IDs and checks that instructions
remain distinct and anchored to the correct entry. The expanded local suite has
51 passing methods, no provider calls. A real v2 attempt stopped before HTTP at
2026-10-07T03:36:42Z with BLOCKED_MISSING_TOKEN.

Request: `docs/evidenze/R3_JEV_SKILL_REQUEST_20261007_V2.json`.
Attempt: `docs/evidenze/R3_JEV_SKILL_ATTEMPT_20261007_V2.json`.
No skill can create an unavailable credential binding or certify the universal
3-2-1-1-0 target merely by being loaded.
