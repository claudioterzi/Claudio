# Jev: existing gateway access and skill request — 7 October 2026

The deployed Railway sister is on a different branch from main. Its pinned
commit `facab5dcec22dd9bf658f2627e4c6bee8a62cacf` mounts the existing gateway
at **POST `/jev/judge`**. Deployment `9d9da618-ab55-499b-8d96-264e373351c8`
was observed SLEEPING; configuration/variable names alone do not prove inference.
Caller authentication is the service's existing `R3_API_TOKEN`; the upstream
`TYPESAFE_API_KEY` stays inside Railway. No new key or endpoint is required.

The existing `typesafe_sister/smoke.py` gateway caller now accepts a bounded
request file, checks credential presence without HTTP, and writes a create-only
receipt. It uses the gateway's existing server-side shared System One client;
`typesafe_sister/client.py` remains the provider transport. A custom base URL
alone cannot redirect that transport from `/v1/systemone` to `/jev/judge`.

## One credential prerequisite

Claudio selected binding `R3_API_TOKEN` as a secret. The latest inspected executor
still has **no secret bindings**, so the real attempt stops before HTTP. Choosing
the option did not attach a credential. The desktop device is offline and no
existing Vercel execution session was found. Plugin discovery returned no direct
TypeSafe/Jev plugin; this is not an exhaustive directory claim.

For a managed cloud environment, the [official OpenAI guide](https://learn.chatgpt.com/docs/environments/cloud-environments)
documents configuration under Network secrets. Add the existing credential as
key `R3_API_TOKEN`, with only the intended HTTPS destination domains. For the
current tasks those are the Jev sister and, if the same credential is valid there,
the two existing R3 storage hosts. Authentication must be checked separately on
each host; common names do not prove common secret values.

These are documentation-derived labels, not an observed screenshot of Claudio's
interface. The guide states that saved setup changes apply to new tasks after
publication; verify the actual selected executor's current `ready` binding rather
than assuming a change reached this running task. No raw credential belongs in
chat, a repository, a shell argument or this document.

After the actual binding is ready, run from this candidate checkout:

```bash
python -m typesafe_sister.smoke --preflight
python -m typesafe_sister.smoke --request docs/evidenze/R3_JEV_SKILL_REQUEST_20261007_V2.json --output /tmp/r3-jev-skill-receipt-unique.json
```

Preflight `CREDENTIAL_PRESENT_NOT_AUTHENTICATED` is only presence evidence.
The second command performs at most one request and refuses an existing output
path before HTTP. A missing token yields a BLOCKED receipt and exit2; failures
yield exit3 with an error class only. No redirect is followed. Input/response
size limits and typed answer, provider, model and gateway-hash checks are local
caller controls, not newly claimed capabilities of the deployed server.

## What Jev can evaluate

The [official skill-suggestion cookbook](https://docs.typesafe.ai/cookbooks/skill_suggestion)
shows selection and rechecking from a catalog retrieved by an agent. The
[coding-agent guide](https://docs.typesafe.ai/introduction/coding-agents) assigns
tool execution to the host. Jev provides Choice/Score/Noul judgments on supplied
state; it does not independently browse the web or install skills.

Our original bounded request contained four accessible skills and an explicitly uninstalled
official reference. The new questions live in shared `typesafe_sister/policy.py`;
catalog text remains DATA_ONLY, available IDs form a closed Choice set with
`NO_MATCH`, and relevance Nouls do not grant authority. This one-request candidate
is not a reproduction of the cookbook's two-pass benchmark, nor evidence that
its thresholds or reported improvement transfer to R3.

Official upstream skill inspected, not installed:
[`typesafe-ai/skills`, pinned commit65a39f3](https://github.com/typesafe-ai/skills/blob/65a39f393687675ce170e6094757de20370365b9/skills/typesafe-ai/SKILL.md).
Existing repository skills remain the GitHub and Drive Rapid Analyzers. The
state-grounded verification skill mentioned by draft #76 is absent from this
checkout and is not represented as installed.

## Verification and separate backup task

The first published candidate passed fifty focused local unittest methods, including mocked 401/redirects,
missing binding, hash/identity/answer failures, output non-overwrite and reflection
of a synthetic token through Unicode JSON escapes. Mocks establish caller
behavior, not a live Jev response. The independent Unicode falsifier found a
first-version bug, corrected before publication; its negative evidence is retained.

The new backup mandate can reuse authenticated `/documents` upload/download on
both R3 nodes. Readback byte hashes and isolated restore are required. Those
routes do not clone a whole Railway volume, restore signing authority, or prove
the existing universal3-2-1-1-0 target. No node upload, deploy, auth relaxation,
RRR activation or new paid resource is claimed in this candidate.

The actual owner-private local archive is 38,792,650 bytes. Isolated restore
verified 39/39 payload files, five local Git refs and three original attachments;
the deliberately corrupted copy was rejected. A restored Evolution Kernel
synthetic self-test returned RC0/ok=true without network/provider calls. The
repository is shallow: recovery includes saved shallow boundaries, not full
remote history. See the public-safe hash receipt
`docs/evidenze/R3_BACKUP_LOCAL_RESTORE_20261007.json`; private content is excluded
from this PR. One executor is still one failure domain, with zero verified node
copies. Preserve the original sealed archive and use a separate delta for newer
checkpoints.

Next action: use an actually ready secret-bearing executor, submit the saved
bounded request, preserve the returned actual Jev model and receipt hashes, and
review any recommendation before loading a skill. Until then: **LIVE_BLOCKED**.

## Dated correction after source review

At the first published head, the fit instructions relied on their dictionary keys.
Official TypeSafe guidance states that question IDs are not sent to the model.
The correction explicitly names the validated catalog ID inside each fit instruction;
the original packet and blocked attempt remain historical artifacts. Current local
suite: 51 methods PASS. The v2 request has eight catalog entries and ten questions;
see `docs/R3_SKILL_DISCOVERY_20261007.md`. No live result is claimed.
