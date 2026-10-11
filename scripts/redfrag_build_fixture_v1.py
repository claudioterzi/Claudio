"""Build the RedFrag benchmark fixture v1 from real R3 sources.

Every source is read from a pinned git commit (or recorded from a pinned Drive
file) and hashed exactly; nothing is synthetic. Gold labels follow the
deterministic RedFrag evidence gate, and each case records why the gold is
deterministic and which falsifier would make it ambiguous.

Run:  python scripts/redfrag_build_fixture_v1.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "redfrag_benchmark_v1.json"
REPO = "github:claudioterzi/Claudio"

MAIN = "8050f1c02c512cddfd822c467eab8a7953be4517"
RF_BRANCH = "27391cf3a1aea018ff125ab509e818f5ed500f9a"   # candidate/r3-clm-redfrag-20260928
A1_BRANCH = "cc610bc4b8826110a8854f4765354d8294373438"   # candidate/letta-phase-a1-diagnostic-20260929

# Drive files cannot be fetched in CI: bytes were downloaded on 2026-09-29 and
# hashed; size matches Drive metadata. Excerpts are verbatim from those bytes.
DRIVE = {
    "zz_mem": {"id": "1cfyZtBhduOzKpIbhiDvjuwnlVbTkHLKM", "size": 1144,
               "title": "ZZ_SUPERATO_MEMORIA_PERSISTENTE_INDICE_2026-08-19T18-21.md",
               "sha256": "a13eea39651f3beeb5a88cda52f79dd96151a9740de873ef6807735a8e5684d1",
               "excerpt": "R3 Memoria persistente (Google Drive). Cartella Drive R3_MEMORIA_PERSISTENTE. "
                          "Aggiornato 2026-08-19 (sera, distribuzione nodi). Ordine di lettura obbligatorio per ogni nodo."},
    "zz_idx": {"id": "1mU7WcYSBy51kpQKyIwrU-jWzbQbo0ooV", "size": 6615,
               "title": "ZZ_SUPERATO_00_INDICE_CANONICO_R3_2026-08-25.md",
               "sha256": "6cc0eaaaf73d66edcc68d19cb49228cab4c04ba1cf2b67cabf0dc24c277c65c2",
               "excerpt": "INDICE CANONICO DELLA MEMORIA PERSISTENTE. Aggiornato 2026-08-25. "
                          "Stato: CANONICO - questo file prevale su ogni altra copia dell'indice."},
    "wq_other": {"id": "15H-eUoP_ZfMJ-pjbM9--hxOcCtFQPJfK", "size": 5212,
                 "title": "R3_WORK_QUEUE_2026-09-23_0906.yaml",
                 "sha256": "a965aa4505f29809254954bab07ea119131e76af52da4cd88127cbf5d2c6c491",
                 "excerpt": "R3_WORK_QUEUE.yaml snapshot SYNC-2026-09-23-0906. node grok-4.6-xai; "
                            "github_repo raffaellocantatelli/Rosso-rosso-rosso; priorita R3-019, R3-011, R3-012."},
}


def git_bytes(ref: str, path: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"],
                          check=True, capture_output=True).stdout


def repo_src(ref: str, path: str, lines: tuple[int, int] | None = None) -> dict:
    data = git_bytes(ref, path)
    loc = f"{REPO}@{ref[:12]}:{path}"
    if lines:
        a, b = lines
        data = b"".join(data.splitlines(keepends=True)[a - 1:b])
        loc += f"#L{a}-L{b}"
    text = " ".join(data.decode("utf-8", "replace").split())
    return {"provenance": loc, "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "excerpt": text[:1200]}


def drive_src(key: str) -> dict:
    d = DRIVE[key]
    return {"provenance": f"drive:{d['id']}#{d['title']}", "sha256": "sha256:" + d["sha256"],
            "bytes": d["size"], "excerpt": d["excerpt"]}


# Each spec: id, class, action, hard tag, sources, flags (evidence for the gate),
# canonical index (or None), provenance override, gold rationale, ambiguity falsifier.
def specs():
    M, RF, A1 = MAIN, RF_BRANCH, A1_BRANCH
    return [
        # ---------------- DUPLICATE ----------------
        dict(id="D01", name="Mazzo Tarocchi Alpha 74",
             sources=[repo_src(M, "tarocchi_quantici_alpha.json"),
                      repo_src(M, "integrations/raffaello-bot/bot/data/alpha74.json")],
             canonical=0, flags={}, cls="DUPLICATE", action="LINK_TO_CANON", hard=[],
             rationale="Byte-identical files; scripts/build_alpha74.py declares canonical_path=tarocchi_quantici_alpha.json.",
             falsifier="The bot copy diverges, or the build script stops naming the root file as canonical."),
        dict(id="D02", name="Catalogo materie Organo Terzi 300",
             sources=[repo_src(M, "studio/parfums/organo_terzi_300.json"),
                      repo_src(M, "public/formule/organo-13aff1815ecef350.json")],
             canonical=0, flags={}, cls="DUPLICATE", action="LINK_TO_CANON", hard=[],
             rationale="Byte-identical; perfume_visual.py, tarocchi_web.py and studia_libro_400.py read studio/parfums/, the public copy is a hashed mirror.",
             falsifier="Code starts reading the public/formule copy as source, or the two files diverge."),
        dict(id="D03", name="Output daily SDQ-1 fine agosto",
             sources=[repo_src(M, f"output/daily_2026-08-{d}.txt") for d in ("29", "30", "31")],
             canonical=0, flags={}, cls="DUPLICATE", action="LINK_TO_CANON", hard=["three_way", "duplicate_error_output"],
             rationale="Three byte-identical generated outputs (the same Python traceback on three days); the earliest dated file is the canonical instance.",
             falsifier="A later daily differs, or the daily generator is shown to embed per-day state that should differ."),
        dict(id="D04", name="Pipeline RedFrag: main e branch candidato",
             sources=[repo_src(M, "typesafe_sister/redfrag_pipeline.py"),
                      repo_src(RF, "typesafe_sister/redfrag_pipeline.py")],
             canonical=0, flags={}, cls="DUPLICATE", action="LINK_TO_CANON", hard=["cross_branch"],
             rationale="Byte-identical on main and on the superseded candidate branch; main is canonical after PR #103.",
             falsifier="The candidate branch copy is edited after the merge."),
        dict(id="D05", name="Ricevuta Letta Phase A 29/09 (copia su branch doppione)",
             sources=[repo_src(M, "docs/evidenze/R3_LETTA_PHASE_A_2026-09-29.json"),
                      repo_src(A1, "docs/evidenze/R3_LETTA_PHASE_A_2026-09-29.json")],
             canonical=0, flags={}, provenance_override=[0], cls="DUPLICATE", action="QUARANTINE_REVIEW",
             hard=["duplicate_incomplete_provenance"],
             rationale="Byte-identical, but the second copy lives only on a duplicate branch slated for closure, so only one stable pointer is recorded; the gate quarantines duplicates without complete provenance.",
             falsifier="The branch is protected or its copy gets a stable pointer: provenance becomes complete and the gold becomes LINK_TO_CANON."),
        # ---------------- CONFLICT ----------------
        dict(id="X01", name="Push su main: autorizzato o vietato",
             sources=[repo_src(M, "CLAUDE.md", (102, 102)), repo_src(M, "CLAUDE.md", (109, 109))],
             canonical=None, flags={"semantic_divergence": True, "divergence_evidence": True, "same_topic": True},
             cls="CONFLICT", action="KEEP_DISTINCT_POINTERS", hard=["same_topic_divergent"],
             rationale="Line 102 authorizes push to main and says it replaces the old limit; line 109 still lists the limit as non-negotiable. Both are live in the same file.",
             falsifier="CLAUDE.md removes line 109 or marks it superseded: the pair becomes STALE + CORE."),
        dict(id="X02", name="R3_WORK_QUEUE: stesso nome, repository diverso",
             sources=[repo_src(M, "R3_WORK_QUEUE.yaml"), drive_src("wq_other")],
             canonical=None, flags={"semantic_divergence": True, "divergence_evidence": True, "same_topic": True},
             cls="CONFLICT", action="KEEP_DISTINCT_POINTERS", hard=["same_name_different_repo"],
             rationale="Same file name; the Drive snapshot declares github_repo raffaellocantatelli/Rosso-rosso-rosso and a different priority list. Different content, must not be merged.",
             falsifier="Evidence that the Drive snapshot was generated from claudioterzi/Claudio at a known commit."),
        dict(id="X03", name="Stato documento System One CLM",
             sources=[repo_src(M, "docs/R3_SYSTEMONE_CLM_2026-09-29.md", (5, 5)),
                      repo_src(M, "docs/R3_SYSTEMONE_CLM_2026-09-29.md", (109, 113))],
             canonical=None, flags={"semantic_divergence": True, "divergence_evidence": True, "same_topic": True},
             cls="CONFLICT", action="KEEP_DISTINCT_POINTERS", hard=["intra_document"],
             rationale="Header says CANDIDATE PATCH on a branch; the same document later says MERGED on main. Neither line is marked superseded.",
             falsifier="The header is corrected: the conflict disappears."),
        dict(id="X04", name="redfrag.py: main contro branch candidato",
             sources=[repo_src(M, "typesafe_sister/redfrag.py"), repo_src(RF, "typesafe_sister/redfrag.py")],
             canonical=None, flags={"semantic_divergence": True, "divergence_evidence": True, "same_topic": True},
             cls="CONFLICT", action="KEEP_DISTINCT_POINTERS", hard=["cross_branch"],
             rationale="Same module, different backend routing (router provider vs direct local call). Code divergence must stay visible until the branch is closed.",
             falsifier="The candidate branch is closed and recorded as superseded: the branch copy becomes STALE."),
        dict(id="X05", name="Livello System One: solo Jev o provider-neutral",
             sources=[repo_src(M, "AGENTS.md", (59, 68)), repo_src(M, "AGENTS.md", (140, 150))],
             canonical=None, flags={"semantic_divergence": True, "divergence_evidence": True, "same_topic": True},
             cls="CONFLICT", action="KEEP_DISTINCT_POINTERS", hard=["canon_vs_canon"],
             rationale="Both sections are live canon in AGENTS.md: one names TypeSafe/Jev as the universal layer, the other makes the layer provider-neutral with CLM preferred.",
             falsifier="AGENTS.md marks the Jev section as superseded: it becomes STALE."),
        # ---------------- CORE ----------------
        dict(id="K01", name="Zero-Assunto", sources=[repo_src(M, "AGENTS.md", (32, 36))], canonical=0,
             flags={"canonical_invariant": True}, cls="CORE", action="KEEP_ACTIVE", hard=[],
             rationale="Shared canonical rule read at startup by every agent.",
             falsifier="Rule removed or moved to a superseded file."),
        dict(id="K02", name="Principio Fondante", sources=[repo_src(M, "CLAUDE.md", (38, 53))], canonical=0,
             flags={"canonical_invariant": True}, cls="CORE", action="KEEP_ACTIVE", hard=[],
             rationale="Declared non-negotiable and prior to every technical rule.",
             falsifier="Owner revokes or rewrites the principle."),
        dict(id="K03", name="Multi-AI convergence gate", sources=[repo_src(M, "AGENTS.md", (55, 57))], canonical=0,
             flags={"canonical_invariant": True}, cls="CORE", action="KEEP_ACTIVE", hard=[],
             rationale="Canonical authority rule: agreement between providers is not authority.",
             falsifier="Rule removed from AGENTS.md."),
        dict(id="K04", name="Confine cooperazione Letta", sources=[repo_src(M, "AGENTS.md", (70, 81))], canonical=0,
             flags={"canonical_invariant": True}, cls="CORE", action="KEEP_ACTIVE", hard=[],
             rationale="Canonical security/authority boundary for Letta output and keys.",
             falsifier="Section superseded by a newer boundary."),
        dict(id="K05", name="Regola provider System One CLM/Jev", sources=[repo_src(M, "AGENTS.md", (140, 150))],
             canonical=0, flags={"canonical_invariant": True}, cls="CORE", action="KEEP_ACTIVE",
             hard=["canon_similar_to_stale"],
             rationale="Current canonical provider rule; lexically close to the stale Jev-only lesson in S03.",
             falsifier="A newer provider rule supersedes it."),
        # ---------------- EVIDENCE ----------------
        dict(id="E01", name="Evidenza cooperazione Letta 28/09",
             sources=[repo_src(M, "docs/evidenze/R3_LETTA_COOPERATION_2026-09-28.json")], canonical=0,
             flags={"evidence_role": True}, cls="EVIDENCE", action="KEEP_ACTIVE", hard=[],
             rationale="Machine-readable receipt backing the VERIFIED transport claims.",
             falsifier="Receipt replaced by a newer receipt that re-verifies the same claims."),
        dict(id="E02", name="Ricevuta Phase A fallita",
             sources=[repo_src(M, "docs/evidenze/R3_LETTA_PHASE_A_2026-09-29.json")], canonical=0,
             flags={"evidence_role": True}, cls="EVIDENCE", action="KEEP_ACTIVE", hard=["negative_evidence"],
             rationale="Records a failed live run; negative results are the falsifier and must not be dropped.",
             falsifier="None short of the run being shown invalid."),
        dict(id="E03", name="Receiver test hyperdense in quarantena",
             sources=[repo_src(M, "docs/evidenze/R3_HYPERDENSE_RECEIVER_TEST_2026-09-23.json")], canonical=0,
             flags={"evidence_role": True}, cls="EVIDENCE", action="KEEP_ACTIVE", hard=["negative_evidence"],
             rationale="First real falsifier of the receiver protocol (peer claimed A_PASS without running Phase A).",
             falsifier="Protocol version retired and the test re-run on the new version."),
        dict(id="E04", name="Confronto multi-peer hyperdense",
             sources=[repo_src(M, "docs/evidenze/R3_HYPERDENSE_MULTI_PEER_COMPARISON_2026-09-23.json")], canonical=0,
             flags={"evidence_role": True}, cls="EVIDENCE", action="KEEP_ACTIVE", hard=[],
             rationale="Comparative evidence cited by the continuity consolidation.",
             falsifier="Superseded by a larger comparison on the same protocol."),
        dict(id="E05", name="Evidenza consolidamento continuità 23/09",
             sources=[repo_src(M, "docs/evidenze/R3_CONTINUITY_CONSOLIDATION_2026-09-23.json")], canonical=0,
             flags={"evidence_role": True}, cls="EVIDENCE", action="KEEP_ACTIVE", hard=[],
             rationale="Receipt ledger evidence (FIRST_SEEN / DUPLICATE_REPLAY) still cited by MEMORIA.",
             falsifier="MEMORIA stops citing it and a newer receipt covers the same claims."),
        # ---------------- STALE ----------------
        dict(id="S01", name="Indice memoria persistente 19/08 (superato)", sources=[drive_src("zz_mem")], canonical=0,
             flags={"superseded": True}, cls="STALE", action="KEEP_POINTER", hard=[],
             rationale="Renamed ZZ_SUPERATO_* on 25/08 by the successor index; kept readable, not deleted.",
             falsifier="Successor index is lost, making this the latest recoverable copy."),
        dict(id="S02", name="Indice 'CANONICO' 25/08 poi superato", sources=[drive_src("zz_idx")], canonical=0,
             flags={"superseded": True}, cls="STALE", action="KEEP_POINTER", hard=["stale_claims_canon"],
             rationale="Its own text says CANONICO and 'prevale su ogni altra copia', but the file was later renamed ZZ_SUPERATO_*; the rename is the later, authoritative signal.",
             falsifier="No successor index exists in Drive or repo."),
        dict(id="S03", name="Lezione TypeSafe/Jev come percorso canonico",
             sources=[repo_src(M, "MEMORIA_PROGETTO.md", (111, 111))], canonical=0,
             flags={"superseded": True}, cls="STALE", action="KEEP_POINTER", hard=["stale_similar_to_canon"],
             rationale="States jev-latest as the canonical path; superseded by the provider-neutral System One rule (K05).",
             falsifier="MEMORIA re-affirms Jev as the only canonical path after 29/09."),
        dict(id="S04", name="R3-028: Phase A/B/C NOT_RUN",
             sources=[repo_src(M, "R3_WORK_QUEUE.yaml", (199, 199))], canonical=0,
             flags={"superseded": True}, cls="STALE", action="KEEP_POINTER", hard=["stale_near_active"],
             rationale="Says Phase A/B/C are NOT_RUN; MEMORIA_PROGETTO.md 29/09 records Phase A as RUN/FAILED.",
             falsifier="The 29/09 MEMORIA entry is reverted."),
        dict(id="S05", name="Probe Letta 403 del 23/09",
             sources=[repo_src(M, "docs/R3_CONTINUITY_CONSOLIDATION_2026-09-23.md", (44, 48))], canonical=0,
             flags={"superseded": True}, cls="STALE", action="KEEP_POINTER", hard=["historical_keep_pointer"],
             rationale="Historical diagnosis superseded on 28/09 (Cloudflare 1010, not an invalid key); the doc itself says it must not be deleted, so it leaves the active window as a pointer.",
             falsifier="The 403 is reproduced with the httpx transport."),
        # ---------------- ACTIVE ----------------
        dict(id="A01", name="R3-028: blocker Phase A con C",
             sources=[repo_src(M, "R3_WORK_QUEUE.yaml", (200, 200))], canonical=0,
             flags={"active_relevance": True}, cls="ACTIVE", action="KEEP_ACTIVE", hard=["active_near_stale"],
             rationale="Rigorous Phase A with a virgin worker C has still not run; the blocker is current.",
             falsifier="Rigorous Phase A with C is executed and recorded."),
        dict(id="A02", name="R3-029 pointer-first: candidato non promosso",
             sources=[repo_src(M, "R3_WORK_QUEUE.yaml", (203, 210))], canonical=0,
             flags={"active_relevance": True}, cls="ACTIVE", action="KEEP_ACTIVE", hard=["candidate_not_canon"],
             rationale="Open work item in DEVELOPMENT; active but explicitly blocked from promotion pending A/B.",
             falsifier="A/B runs and the item is adopted or rejected."),
        dict(id="A03", name="Script benchmark RedFrag",
             sources=[repo_src(M, "scripts/r3_clm_redfrag_benchmark.py")], canonical=0,
             flags={"active_relevance": True}, cls="ACTIVE", action="KEEP_ACTIVE", hard=[],
             rationale="Tool used by the current RedFrag A/B work.",
             falsifier="Replaced by a newer benchmark runner."),
        dict(id="A04", name="Harness Letta Phase A.1",
             sources=[repo_src(M, "raffaello_crypto_scout/app.py", (403, 528))], canonical=0,
             flags={"active_relevance": True}, cls="ACTIVE", action="KEEP_ACTIVE", hard=[],
             rationale="Current diagnostic code on main, reused by the next Letta test.",
             falsifier="Letta work closed and the harness removed."),
        dict(id="A05", name="Documento RedFrag su System One",
             sources=[repo_src(M, "docs/R3_REDFRAG_SYSTEMONE_2026-09-29.md")], canonical=0,
             flags={"active_relevance": True}, cls="ACTIVE", action="KEEP_ACTIVE", hard=["candidate_not_canon"],
             rationale="Describes the current candidate and the planned CLM A/B; active, not canon.",
             falsifier="A/B completed and the doc superseded by its receipt."),
    ]


def build() -> dict:
    cases = []
    for s in specs():
        srcs = s["sources"]
        prov_idx = s.get("provenance_override", list(range(len(srcs))))
        cluster = {
            "id": s["id"], "name": s["name"],
            "source_count": len(srcs),
            "content_hashes": [x["sha256"] for x in srcs],
            "provenance": [srcs[i]["provenance"] for i in prov_idx],
            "canonical_source": srcs[s["canonical"]]["provenance"] if s["canonical"] is not None else "",
            "excerpts": [x["excerpt"] for x in srcs],
            **s["flags"],
        }
        cases.append({
            "id": s["id"], "cluster": cluster,
            "expected_class": s["cls"], "expected_action": s["action"],
            "hard_case": s["hard"], "gold_rationale": s["rationale"], "ambiguity_falsifier": s["falsifier"],
            "sources": [{k: x[k] for k in ("provenance", "sha256", "bytes")} for x in srcs],
        })
    body = {"schema": "R3-REDFRAG-BENCH-FIXTURE/1.0", "pinned_main": MAIN,
            "note": "Real sources only; model sees `cluster` only. Frozen before any CLM GPU run.",
            "cases": cases}
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="rebuild and compare with the committed fixture")
    args = ap.parse_args()
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if args.check:
        same = OUT.read_text(encoding="utf-8") == text
        print("fixture reproducible" if same else "fixture DIFFERS from sources")
        sys.exit(0 if same else 1)
    OUT.write_text(text, encoding="utf-8")
    print(OUT, "sha256", hashlib.sha256(text.encode("utf-8")).hexdigest(), "cases", len(data["cases"]))


if __name__ == "__main__":
    main()
