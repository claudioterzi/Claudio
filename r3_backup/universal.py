"""R3 UNIVERSAL BACKUP/1 — GitHub-independent archive to Synology.

A model or a sync client never gets to self-certify persistence. Repository data
is first verified locally (git fsck + git bundle verify + SHA-256). When the
destination is a direct mounted NAS share, that same verification is NAS-resident.
When the destination is a Synology Drive synchronized folder, the run remains
LOCAL_VERIFIED_PENDING_NAS until the NAS-side verifier writes a NAS receipt.

GitHub secret values are not exportable by GitHub and are never claimed as saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from r3_backup import ORIGIN, PROTOCOL

DEFAULT_CONFIG = "r3_backup/config.json"
DEFAULT_CACHE = Path.home() / ".r3-backup-cache"
DESTINATION_KINDS = {"direct_nas", "synology_drive_sync"}


class BackupError(RuntimeError):
    pass


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args: list[str], *, cwd: Path | None = None, check: bool = True) -> CommandResult:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode:
        raise BackupError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr[-2000:]}"
        )
    return CommandResult(proc.stdout, proc.stderr, proc.returncode)


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _safe_repo_name(full_name: str) -> str:
    return full_name.replace("/", "--")


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BackupError("config must be a JSON object")
    return data


def discover_repositories(config: dict[str, Any]) -> list[str]:
    repos = {str(x).strip() for x in config.get("repositories", []) if str(x).strip()}
    if not config.get("discover_owner_repositories", True) or not _command_exists("gh"):
        return sorted(repos)

    for owner in config.get("owners", []):
        owner = str(owner).strip()
        if not owner:
            continue
        result = _run(
            ["gh", "repo", "list", owner, "--limit", "1000", "--json", "nameWithOwner"],
            check=False,
        )
        if result.returncode:
            continue
        try:
            for item in json.loads(result.stdout):
                full = str(item.get("nameWithOwner") or "").strip()
                if full:
                    repos.add(full)
        except (ValueError, TypeError):
            continue
    return sorted(repos)


def _repo_url(full_name: str) -> str:
    return f"https://github.com/{full_name}.git"


def update_mirror(full_name: str, mirror_dir: Path) -> None:
    mirror_dir.parent.mkdir(parents=True, exist_ok=True)
    if not mirror_dir.exists():
        _run(["git", "clone", "--mirror", _repo_url(full_name), str(mirror_dir)])
    else:
        _run(["git", "--git-dir", str(mirror_dir), "remote", "set-url", "origin", _repo_url(full_name)])
        _run(["git", "--git-dir", str(mirror_dir), "remote", "update", "--prune"])
    _run(["git", "--git-dir", str(mirror_dir), "fsck", "--full"])


def fetch_lfs(mirror_dir: Path) -> bool:
    probe = _run(["git", "lfs", "version"], check=False)
    if probe.returncode:
        return False
    result = _run(
        ["git", "--git-dir", str(mirror_dir), "lfs", "fetch", "--all", "origin"],
        check=False,
    )
    return result.returncode == 0


def create_bundle(mirror_dir: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "--git-dir", str(mirror_dir), "bundle", "create", str(destination), "--all"])
    _run(["git", "bundle", "verify", str(destination)])


def archive_lfs(mirror_dir: Path, destination: Path) -> bool:
    lfs_root = mirror_dir / "lfs"
    if not lfs_root.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(destination, "w:gz") as tar:
        tar.add(lfs_root, arcname="lfs")
    return True


def mirror_wiki(full_name: str, wiki_dir: Path) -> bool:
    url = f"https://github.com/{full_name}.wiki.git"
    if wiki_dir.exists():
        result = _run(["git", "--git-dir", str(wiki_dir), "remote", "update", "--prune"], check=False)
    else:
        wiki_dir.parent.mkdir(parents=True, exist_ok=True)
        result = _run(["git", "clone", "--mirror", url, str(wiki_dir)], check=False)
    if result.returncode:
        if wiki_dir.exists() and not (wiki_dir / "HEAD").exists():
            shutil.rmtree(wiki_dir, ignore_errors=True)
        return False
    return _run(["git", "--git-dir", str(wiki_dir), "fsck", "--full"], check=False).returncode == 0


METADATA_ENDPOINTS = {
    "repo": "",
    "issues": "/issues?state=all&per_page=100",
    "issue_comments": "/issues/comments?per_page=100",
    "pulls": "/pulls?state=all&per_page=100",
    "pull_comments": "/pulls/comments?per_page=100",
    "releases": "/releases?per_page=100",
    "milestones": "/milestones?state=all&per_page=100",
    "labels": "/labels?per_page=100",
    "workflows": "/actions/workflows?per_page=100",
    "workflow_runs": "/actions/runs?per_page=100",
}


def export_github_metadata(full_name: str, destination: Path) -> dict[str, str]:
    status: dict[str, str] = {}
    if not _command_exists("gh"):
        return {"status": "gh_cli_unavailable"}
    destination.mkdir(parents=True, exist_ok=True)
    base = f"repos/{full_name}"

    for name, suffix in METADATA_ENDPOINTS.items():
        target = destination / f"{name}.json"
        args = ["api"]
        if suffix and "per_page=100" in suffix:
            args.extend(["--paginate", "--slurp"])
        args.append(base + suffix)
        result = _run(["gh", *args], check=False)
        if result.returncode:
            status[name] = f"unavailable:{result.returncode}"
            continue
        target.write_text(result.stdout or "null\n", encoding="utf-8")
        status[name] = "saved"

    for kind, cmd in {
        "secret_names.txt": ["gh", "secret", "list", "--repo", full_name],
        "variable_names.txt": ["gh", "variable", "list", "--repo", full_name],
    }.items():
        result = _run(cmd, check=False)
        if result.returncode == 0:
            (destination / kind).write_text(result.stdout, encoding="utf-8")
            status[kind] = "names_only"
        else:
            status[kind] = "unavailable"
    return status


def _write_json_verified(data: Any, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = destination.with_suffix(destination.suffix + ".partial")
    temp.write_text(payload, encoding="utf-8")
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    actual = sha256_file(temp)
    if actual != expected:
        temp.unlink(missing_ok=True)
        raise BackupError(f"write verification failed: {destination}")
    os.replace(temp, destination)
    return actual


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def _snapshot_manifest(snapshot_dir: Path) -> dict[str, Any]:
    files = []
    excluded = {"MANIFEST.json", "SHA256SUMS", "NAS_RECEIPT.json"}
    for path in _iter_files(snapshot_dir):
        if path.name in excluded:
            continue
        files.append({
            "path": path.relative_to(snapshot_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "protocol": PROTOCOL,
        "origin": ORIGIN,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "integrity_status": "LOCAL_VERIFIED",
        "verification": [
            "git fsck --full passed for every saved repository mirror",
            "git bundle verify passed for every repository bundle",
            "SHA-256 recorded for every archived snapshot file",
        ],
        "files": files,
    }


def _write_sha256sums(snapshot_dir: Path) -> str:
    excluded = {"SHA256SUMS", "NAS_RECEIPT.json"}
    lines: list[str] = []
    for path in _iter_files(snapshot_dir):
        if path.name in excluded:
            continue
        rel = path.relative_to(snapshot_dir).as_posix()
        lines.append(f"{sha256_file(path)}  {rel}")
    payload = "\n".join(lines) + "\n"
    target = snapshot_dir / "SHA256SUMS"
    target.write_text(payload, encoding="utf-8", newline="\n")
    return sha256_file(target)


def backup_repo(
    full_name: str,
    *,
    cache_root: Path,
    snapshot_dir: Path,
    include_lfs: bool,
    include_wikis: bool,
    metadata: bool,
) -> dict[str, Any]:
    safe = _safe_repo_name(full_name)
    mirror = cache_root / "mirrors" / f"{safe}.git"
    result: dict[str, Any] = {"repository": full_name, "status": "STARTED"}

    update_mirror(full_name, mirror)
    result["git_fsck"] = "passed"

    lfs_ok = fetch_lfs(mirror) if include_lfs else False
    result["lfs_fetch"] = "passed" if lfs_ok else "not_present_or_unavailable"

    repo_dir = snapshot_dir / "repositories" / safe
    repo_dir.mkdir(parents=True, exist_ok=True)
    bundle = repo_dir / f"{safe}.bundle"
    create_bundle(mirror, bundle)
    result["bundle"] = "verified"

    if include_lfs:
        lfs_archive = repo_dir / f"{safe}.lfs.tar.gz"
        result["lfs_archive"] = "saved" if archive_lfs(mirror, lfs_archive) else "none"

    if include_wikis:
        wiki_mirror = cache_root / "wikis" / f"{safe}.wiki.git"
        if mirror_wiki(full_name, wiki_mirror):
            wiki_bundle = repo_dir / f"{safe}.wiki.bundle"
            create_bundle(wiki_mirror, wiki_bundle)
            result["wiki"] = "saved"
        else:
            result["wiki"] = "none_or_unavailable"

    if metadata:
        result["metadata"] = export_github_metadata(full_name, repo_dir / "github_metadata")

    result["status"] = "VERIFIED"
    return result


def backup_all(
    config_path: Path,
    nas_root: Path,
    cache_root: Path = DEFAULT_CACHE,
    *,
    destination_kind: str = "synology_drive_sync",
) -> dict[str, Any]:
    if not _command_exists("git"):
        raise BackupError("git is required")
    if destination_kind not in DESTINATION_KINDS:
        raise BackupError(f"invalid destination kind: {destination_kind}")

    config = load_config(config_path)
    repos = discover_repositories(config)
    if not repos:
        raise BackupError("no repositories configured or discovered")

    root = nas_root.expanduser().resolve() / "R3_UNIVERSAL_BACKUP"
    stamp = utc_stamp()
    snapshot_dir = root / "snapshots" / stamp
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    cache_root.mkdir(parents=True, exist_ok=True)

    run: dict[str, Any] = {
        "protocol": PROTOCOL,
        "origin": ORIGIN,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": stamp,
        "destination_kind": destination_kind,
        "archive_root": str(root),
        "repositories_requested": repos,
        "repositories": [],
        "status": "RUNNING",
        "limitations": [
            "GitHub secret values cannot be exported; only names can be inventoried.",
            "External issue attachments and external package/container registries are not guaranteed by v1.",
        ],
    }

    try:
        for full_name in repos:
            try:
                item = backup_repo(
                    full_name,
                    cache_root=cache_root,
                    snapshot_dir=snapshot_dir,
                    include_lfs=bool(config.get("include_lfs", True)),
                    include_wikis=bool(config.get("include_wikis", True)),
                    metadata=bool(config.get("export_github_metadata", True)),
                )
            except Exception as exc:
                item = {
                    "repository": full_name,
                    "status": "FAILED",
                    "error_class": type(exc).__name__,
                    "detail": str(exc)[-2000:],
                }
            run["repositories"].append(item)

        failed = [x for x in run["repositories"] if x.get("status") != "VERIFIED"]
        if failed:
            run["status"] = "PARTIAL"
        elif destination_kind == "direct_nas":
            run["status"] = "NAS_VERIFIED"
        else:
            run["status"] = "LOCAL_VERIFIED_PENDING_NAS"
        run["finished_at"] = datetime.now(timezone.utc).isoformat()
        _write_json_verified(run, snapshot_dir / "RUN.json")

        manifest = _snapshot_manifest(snapshot_dir)
        manifest_hash = _write_json_verified(manifest, snapshot_dir / "MANIFEST.json")
        sha256sums_hash = _write_sha256sums(snapshot_dir)

        receipt = {
            "protocol": PROTOCOL,
            "snapshot": stamp,
            "status": run["status"],
            "destination_kind": destination_kind,
            "manifest_sha256": manifest_hash,
            "sha256sums_sha256": sha256sums_hash,
            "snapshot_path": str(snapshot_dir),
            "repository_count": len(run["repositories"]),
            "verified_repositories": sum(x.get("status") == "VERIFIED" for x in run["repositories"]),
            "failed_repositories": [x.get("repository") for x in failed],
            "nas_confirmation_required": destination_kind == "synology_drive_sync" and not failed,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_json_verified(receipt, root / "LATEST.json")
        _write_json_verified(receipt, root / "receipts" / f"{stamp}.json")
        return receipt
    except Exception:
        run["status"] = "FAILED"
        run["finished_at"] = datetime.now(timezone.utc).isoformat()
        try:
            _write_json_verified(run, snapshot_dir / "RUN.json")
        except Exception:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up R3 GitHub repositories to Synology")
    parser.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG))
    parser.add_argument("--nas-root", type=Path, default=None)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--destination-kind",
        choices=sorted(DESTINATION_KINDS),
        default=os.getenv("R3_BACKUP_DESTINATION_KIND", "synology_drive_sync"),
    )
    args = parser.parse_args()

    raw_nas = str(args.nas_root) if args.nas_root else os.getenv("R3_NAS_ROOT", "").strip()
    if not raw_nas:
        print(json.dumps({
            "status": "NOT_CONFIGURED",
            "required": "Set R3_NAS_ROOT to a mounted NAS share or Synology Drive sync folder.",
        }), file=sys.stderr)
        return 2

    try:
        receipt = backup_all(
            args.config,
            Path(raw_nas),
            args.cache_root,
            destination_kind=args.destination_kind,
        )
    except Exception as exc:
        print(json.dumps({
            "protocol": PROTOCOL,
            "status": "FAILED",
            "error_class": type(exc).__name__,
            "detail": str(exc),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 3 if receipt["status"] == "PARTIAL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
