#!/usr/bin/env python3
"""Manual native probe of the existing R3 loader after simulated provider loss.

No provider client, activation, permanent integration or new recovery engine.
The private guard wrapper is excluded from the PUBLIC companion archive.
Run baseline first; run final only with a freshly downloaded Drive companion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile


SEED_SHA256 = "2c80dafc22a1adb5951131ad9dcdd10093e87e34198bd947e0a18d22680b3522"
CHECKPOINT_SHA256 = "55d20418d692179513c7174964f7641047f6ff53aebc2a4d05633032633aea73"
EVIDENCE_SHA256 = "27e74b97b4daa26c0d76763db30d2c255db916819ab5a48c3a4dc1ebcc52281d"
CHECKPOINT_PATH = "docs/evidenze/R3_PORTABLE_SEED_CHECKPOINT_20261008.json"
EVIDENCE_PATH = "docs/evidenze/R3_PORTABLE_SEED_DISTRIBUTION_20261008.json"
TASK_FIELDS = ("decision", "status", "evidence", "next_action", "blocker", "completion_criterion", "resume_trigger")
SEED_MEMBERS = {
    "MANIFEST.json", "R3_AI_BOOTSTRAP.md", "R3_BASE_PRIORITIES.yaml",
    "R3_CAPILLARY_INHERITANCE.yaml", "R3_UNIVERSAL_BACKUP.yaml", "README.txt",
    "docs/R3_LEARNING_WATCH_2026-09-18.md", "docs/R3_RETROACTIVE_CANON_OVERLAY.md",
    "public/R3_SEME_PORTABILE_20261008.txt", "public/r3-ai-bootstrap.json",
    "public/r3-sister-alignment.json", "public/r3-taraka-schema.json",
    "scripts/r3_ai_bootstrap.py",
}
COMPANION_MEMBERS = {CHECKPOINT_PATH, EVIDENCE_PATH, "WORKSTATE_README.txt", "WORKSTATE_MANIFEST.json"}
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024
MAX_EXTRACTED_BYTES = 4 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned_archive(path: Path, external_pin: str, expected_members: set[str], manifest_name: str) -> dict[str, bytes]:
    """Fixture preparation only, with a trusted external pin before extraction."""
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("archive input too large")
    raw = path.read_bytes()
    if sha256(raw) != external_pin:
        raise ValueError("external archive SHA256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(expected_members) or set(names) != expected_members:
            raise ValueError("unexpected or duplicate archive member")
        if sum(entry.file_size for entry in archive.infolist()) > MAX_EXTRACTED_BYTES:
            raise ValueError("expanded archive too large")
        for entry in archive.infolist():
            name = entry.filename
            parts = PurePosixPath(name)
            if parts.is_absolute() or ".." in parts.parts or "\\" in name or str(parts) != name:
                raise ValueError("non-relative archive name")
            mode = entry.external_attr >> 16
            if entry.is_dir() or not stat.S_ISREG(mode):
                raise ValueError("archive member is not a regular file")
        if archive.testzip() is not None:
            raise ValueError("archive CRC failure")
        files = {name: archive.read(name) for name in names}
    manifest = json.loads(files[manifest_name])
    entries = manifest["files"]
    entry_paths = [entry["path"] for entry in entries]
    if len(entry_paths) != len(set(entry_paths)) or set(entry_paths) != expected_members - {manifest_name}:
        raise ValueError("manifest inventory mismatch")
    for entry in entries:
        data = files[entry["path"]]
        if len(data) != entry["bytes"] or sha256(data) != entry["sha256"]:
            raise ValueError("archive payload hash mismatch")
    return files


def inventory(folder: Path) -> dict:
    files = {}
    directories = []
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError("unexpected fixture symlink")
        relative = path.relative_to(folder).as_posix()
        if path.is_dir():
            directories.append(relative)
        else:
            raw = path.read_bytes()
            files[relative] = {"bytes": len(raw), "sha256": sha256(raw)}
    return {"files": files, "directories": directories}


def fixture_from_payload(folder: Path, payload: dict[str, bytes]) -> None:
    folder.mkdir(parents=True, exist_ok=False)
    for name, raw in payload.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)


def run_loader(folder: Path, wrapper: Path, original_source_control: Path,
               checkpoint_pin: str = CHECKPOINT_SHA256, evidence_pin: str = EVIDENCE_SHA256) -> dict:
    before = inventory(folder)
    command = [sys.executable, "-I", "-S", "-B", str(wrapper), str(folder), str(original_source_control),
               "--check", "--resume", CHECKPOINT_PATH, "--checkpoint-sha256", checkpoint_pin,
               "--evidence-sha256", evidence_pin]
    process = subprocess.run(command, cwd=folder, env={}, capture_output=True, text=True, timeout=20)
    after = inventory(folder)
    native = json.loads(process.stdout)
    if process.returncode != native["loader_exit_code"]:
        raise AssertionError("wrapped process and loader exit codes differ")
    controls = native["guard_controls"]
    required_controls = {
        "read_outside": ("open", "read", "read outside fixture and stdlib"),
        "read_original_source": ("open", "read", "read outside fixture and stdlib"),
        "write_outside": ("open", "write", "file write"),
        "write_inside": ("open", "write", "file write"),
        "mkdir_inside": ("os.mkdir", "mutation", "filesystem mutation"),
        "socket": ("socket.__new__", "network", "network or DNS"),
        "dns": ("socket.getaddrinfo", "network", "network or DNS"),
        "subprocess": ("subprocess.Popen", "subprocess", "subprocess or process creation"),
    }
    if set(controls) != set(required_controls):
        raise AssertionError("guard negative control failed")
    for name, (event, operation, reason) in required_controls.items():
        expected = {"event": event, "operation": operation, "reason": reason}
        value = controls[name]
        if value["blocked"] is not True or value["events"] != [expected] or value["error"] != "recovery guard rejected " + reason:
            raise AssertionError("guard control event/reason differs: " + name)
    if native["loader_denied_operations"]:
        raise AssertionError("loader attempted a forbidden operation")
    if native["environment_entry_count"] != 0 or not all(native[key] for key in ["python_isolated", "python_no_site", "python_no_bytecode"]):
        raise AssertionError("child isolation flags or empty environment missing")
    if native["third_party_module_origins"]:
        raise AssertionError("third-party module loaded")
    if before != after:
        raise AssertionError("loader or controls changed fixture filesystem")
    return {"returncode": process.returncode, "native_guard_receipt": native,
            "filesystem_before": before, "filesystem_after": after,
            "filesystem_unchanged": True, "outer_stderr": process.stderr}


def require_blocked(result: dict, reason_fragment: str) -> None:
    records = result["native_guard_receipt"]["stdout_records"]
    if result["returncode"] != 2 or len(records) != 1 or records[0].get("state") != "RESUME_BLOCKED":
        raise AssertionError("resume failed without expected blocked result")
    if reason_fragment not in records[0].get("reason", "") or "task_state" in records[0]:
        raise AssertionError("unexpected failure reason or task state leaked")


def write_receipt(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["baseline", "final"])
    parser.add_argument("--seed-zip", required=True, type=Path)
    parser.add_argument("--companion-zip", type=Path)
    parser.add_argument("--companion-sha256")
    parser.add_argument("--wrapper", required=True, type=Path)
    parser.add_argument("--original-source-control", required=True, type=Path,
                        help="guard denial control only; never used as loader input")
    parser.add_argument("--fixture-parent", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    seed = pinned_archive(args.seed_zip, SEED_SHA256, SEED_MEMBERS, "MANIFEST.json")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_root = args.fixture_parent / (args.mode + "-" + stamp)
    results = {}
    if args.mode == "baseline":
        fixture_from_payload(run_root, seed)
        result = run_loader(run_root, args.wrapper, args.original_source_control)
        require_blocked(result, "missing or outside repository")
        results["seed_only_missing_checkpoint"] = result
        recovered = False
    else:
        if not args.companion_zip or not args.companion_sha256:
            parser.error("final requires actual fresh Drive companion plus external SHA256 pin")
        companion = pinned_archive(args.companion_zip, args.companion_sha256, COMPANION_MEMBERS, "WORKSTATE_MANIFEST.json")
        if set(seed) & set(companion):
            raise AssertionError("companion would overwrite original seed")
        if sha256(companion[CHECKPOINT_PATH]) != CHECKPOINT_SHA256 or sha256(companion[EVIDENCE_PATH]) != EVIDENCE_SHA256:
            raise AssertionError("companion remote record external pins mismatch")
        checkpoint = json.loads(companion[CHECKPOINT_PATH])
        expected_state = {field: checkpoint[field] for field in TASK_FIELDS}
        payload = {**seed, **companion}
        for name in ["valid", "wrong_checkpoint_pin", "wrong_evidence_pin", "missing_checkpoint", "missing_evidence", "corrupt_evidence", "wrong_owner"]:
            folder = run_root / name
            case_payload = dict(payload)
            cp_pin = CHECKPOINT_SHA256
            ev_pin = EVIDENCE_SHA256
            if name == "wrong_checkpoint_pin":
                cp_pin = "0" * 64
            elif name == "wrong_evidence_pin":
                ev_pin = "0" * 64
            elif name == "missing_checkpoint":
                del case_payload[CHECKPOINT_PATH]
            elif name == "missing_evidence":
                del case_payload[EVIDENCE_PATH]
            elif name == "corrupt_evidence":
                case_payload[EVIDENCE_PATH] = case_payload[EVIDENCE_PATH] + b" "
            elif name == "wrong_owner":
                manifest = json.loads(case_payload["public/r3-ai-bootstrap.json"])
                manifest["owner"] = "Synthetic Incorrect Owner"
                case_payload["public/r3-ai-bootstrap.json"] = json.dumps(manifest).encode("utf-8")
            fixture_from_payload(folder, case_payload)
            result = run_loader(folder, args.wrapper, args.original_source_control, cp_pin, ev_pin)
            records = result["native_guard_receipt"]["stdout_records"]
            if name == "valid":
                if result["returncode"] != 0 or len(records) != 2:
                    raise AssertionError("valid recovery did not return exactly two records")
                resume, validated = records
                if resume.get("authority") != "DATA_ONLY" or resume.get("task_state") != expected_state:
                    raise AssertionError("recovered task state differs from pinned checkpoint")
                if resume.get("effects_executed") is not False or resume.get("claims_independently_verified") is not False:
                    raise AssertionError("recovery incorrectly claimed effects or proof")
                if resume.get("checkpoint_sha256") != CHECKPOINT_SHA256 or resume.get("evidence_sha256") != EVIDENCE_SHA256:
                    raise AssertionError("recovered pin labels differ")
                if validated.get("ok") is not True or validated.get("state") != "VALIDATED":
                    raise AssertionError("second output record is not static validation")
            elif name == "wrong_owner":
                if result["returncode"] != 1 or records or "BootstrapError: unexpected canonical owner" not in result["native_guard_receipt"]["stderr"]:
                    raise AssertionError("copied wrong owner not refused before recovery")
            else:
                reason = "missing or outside repository" if name.startswith("missing_") else "SHA256 mismatch"
                require_blocked(result, reason)
            results[name] = result
        recovered = True
    receipt = {
        "schema": "R3_PROVIDER_LOSS_CONTEXT_PROBE/1.0", "authority": "DATA_ONLY",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
        "seed_input": str(args.seed_zip), "seed_sha256": SEED_SHA256,
        "companion_input": str(args.companion_zip) if args.companion_zip else None,
        "companion_sha256": args.companion_sha256, "checkpoint_sha256": CHECKPOINT_SHA256,
        "evidence_sha256": EVIDENCE_SHA256, "wrapper_sha256": sha256(args.wrapper.read_bytes()),
        "probe_source_sha256": sha256(Path(__file__).read_bytes()), "fixture_root": str(run_root),
        "cases": results, "workstate_recovered": recovered,
        "input_zip_preserved": sha256(args.seed_zip.read_bytes()) == SEED_SHA256,
        "companion_preserved": (sha256(args.companion_zip.read_bytes()) == args.companion_sha256) if args.companion_zip else None,
        "network_guard_scope": "Python audited loader operations; no OS isolation or actual provider outage",
        "claims": {"simulated_github_and_original_workspace_unavailable": True,
                   "actual_cloud_outage": False, "os_airgap": False, "distinct_physical_host": False,
                   "model_inference": False, "private_history_or_volume_restored": False,
                   "controller_or_credentials_restored": False, "project_owner_labels_are_authentication": False},
        "recovered_scope": "Only the seven fields of public checkpoint55d204... and static bootstrap; claims remain unverified",
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps({"mode": args.mode, "receipt": str(args.receipt), "fixture": str(run_root),
                      "case_returncodes": {name: result["returncode"] for name, result in results.items()},
                      "workstate_recovered": recovered}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
