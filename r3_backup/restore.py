"""Restore and verify an R3 UNIVERSAL BACKUP/1 snapshot without GitHub."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from r3_backup import PROTOCOL


class RestoreError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode:
        raise RestoreError(f"command failed: {' '.join(args)}\n{proc.stderr[-2000:]}")
    return proc


def verify_snapshot(snapshot_dir: Path) -> dict[str, Any]:
    manifest_path = snapshot_dir / "MANIFEST.json"
    if not manifest_path.exists():
        raise RestoreError("MANIFEST.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("protocol") != PROTOCOL:
        raise RestoreError("unsupported backup protocol")
    problems: list[str] = []
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise RestoreError("invalid manifest files list")
    for item in files:
        if not isinstance(item, dict):
            problems.append("invalid-manifest-entry")
            continue
        rel = str(item.get("path") or "")
        expected = str(item.get("sha256") or "")
        path = snapshot_dir / rel
        if not path.is_file():
            problems.append(f"missing:{rel}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            problems.append(f"hash:{rel}")
    return {
        "status": "VERIFIED" if not problems else "FAILED",
        "problems": problems,
        "files_checked": len(files),
    }


def list_repositories(snapshot_dir: Path) -> list[str]:
    run_path = snapshot_dir / "RUN.json"
    if not run_path.exists():
        return []
    run = json.loads(run_path.read_text(encoding="utf-8"))
    return [
        str(item.get("repository"))
        for item in run.get("repositories", [])
        if isinstance(item, dict) and item.get("status") == "VERIFIED"
    ]


def restore_repository(snapshot_dir: Path, repository: str, destination: Path) -> dict[str, Any]:
    verification = verify_snapshot(snapshot_dir)
    if verification["status"] != "VERIFIED":
        raise RestoreError("snapshot hash verification failed")

    safe = repository.replace("/", "--")
    repo_dir = snapshot_dir / "repositories" / safe
    bundle = repo_dir / f"{safe}.bundle"
    if not bundle.is_file():
        raise RestoreError(f"bundle not found for {repository}")

    _run(["git", "bundle", "verify", str(bundle)])
    if destination.exists():
        raise RestoreError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "clone", str(bundle), str(destination)])
    _run(["git", "fsck", "--full"], cwd=destination)

    lfs_archive = repo_dir / f"{safe}.lfs.tar.gz"
    lfs_status = "none"
    if lfs_archive.is_file():
        import tarfile
        git_dir = destination / ".git"
        if not git_dir.is_dir():
            raise RestoreError("restored working clone has no .git directory")
        with tarfile.open(lfs_archive, "r:gz") as tar:
            tar.extractall(git_dir)
        lfs_status = "restored-object-store"

    return {
        "protocol": PROTOCOL,
        "status": "RESTORED_AND_FSCK_VERIFIED",
        "repository": repository,
        "destination": str(destination),
        "lfs": lfs_status,
        "source_snapshot": str(snapshot_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or restore an R3 NAS snapshot")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--repository")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()

    if args.verify_only:
        print(json.dumps(verify_snapshot(args.snapshot), indent=2, ensure_ascii=False))
        return 0

    if not args.repository or args.destination is None:
        parser.error("--repository and --destination are required unless --verify-only is used")
    result = restore_repository(args.snapshot, args.repository, args.destination)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
