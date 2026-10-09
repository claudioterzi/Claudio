#!/usr/bin/env python3
"""Deterministic R³∞ context-pointer selector.

This layer reduces repeated context payloads by passing verified repository
pointers first and expanding source documents only when task tags require them.
It never treats a pointer as source authority and never embeds pointed bodies.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "public" / "r3-context-pointer-manifest.json"

SCHEMA = "R3_CONTEXT_POINTER_MANIFEST_V1"
PROTOCOL = "rosso-rosso-rosso/r3-infinity"
LOAD_MODES = {"root", "on_demand"}


class ContextPointerError(ValueError):
    pass


def load_pointer_manifest(path: Path = DEFAULT_MANIFEST, *, root: Path = ROOT) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextPointerError(f"pointer manifest unreadable: {exc}") from exc
    validate_pointer_manifest(value, root=root)
    return value


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextPointerError("pointer path must be a non-empty string")
    path = Path(value.strip())
    if path.is_absolute() or ".." in path.parts:
        raise ContextPointerError("pointer path must stay inside repository root")
    return path.as_posix()


def validate_pointer_manifest(
    value: Any,
    *,
    root: Path = ROOT,
    verify_paths: bool = True,
) -> None:
    if not isinstance(value, dict):
        raise ContextPointerError("pointer manifest must be an object")
    if value.get("schema") != SCHEMA:
        raise ContextPointerError("unexpected pointer schema")
    if value.get("protocol_id") != PROTOCOL:
        raise ContextPointerError("unexpected protocol_id")
    if value.get("strategy") != "pointer_first_bounded_expansion":
        raise ContextPointerError("unexpected pointer strategy")
    if value.get("content_policy") != "retrieve_source_on_demand":
        raise ContextPointerError("unexpected content policy")

    entries = value.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ContextPointerError("entries must be a non-empty list")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    root_count = 0

    for entry in entries:
        if not isinstance(entry, dict):
            raise ContextPointerError("pointer entry must be an object")
        if "content" in entry or "body" in entry:
            raise ContextPointerError("pointer entries must not inline source bodies")

        pointer_id = entry.get("id")
        if not isinstance(pointer_id, str) or not pointer_id.strip():
            raise ContextPointerError("pointer id must be a non-empty string")
        if pointer_id in seen_ids:
            raise ContextPointerError(f"duplicate pointer id: {pointer_id}")
        seen_ids.add(pointer_id)

        path = _safe_relative_path(entry.get("path"))
        if path in seen_paths:
            raise ContextPointerError(f"duplicate pointer path: {path}")
        seen_paths.add(path)

        if verify_paths and not (root / path).is_file():
            raise ContextPointerError(f"pointer target missing: {path}")

        role = entry.get("role")
        if not isinstance(role, str) or not role.strip():
            raise ContextPointerError(f"pointer role missing: {pointer_id}")

        mode = entry.get("load_mode")
        if mode not in LOAD_MODES:
            raise ContextPointerError(f"invalid load_mode for {pointer_id}")
        if mode == "root":
            root_count += 1

        tags = entry.get("tags")
        if (
            not isinstance(tags, list)
            or not tags
            or not all(isinstance(tag, str) and tag.strip() for tag in tags)
        ):
            raise ContextPointerError(f"invalid tags for {pointer_id}")

    if root_count == 0:
        raise ContextPointerError("at least one root pointer is required")


def _normalized_tags(tags: Iterable[str] | None) -> set[str]:
    if tags is None:
        return set()
    return {tag.strip().lower() for tag in tags if isinstance(tag, str) and tag.strip()}


def select_pointers(
    manifest: dict[str, Any],
    *,
    tags: Iterable[str] | None = None,
    include_root: bool = True,
    limit: int = 12,
) -> list[dict[str, Any]]:
    validate_pointer_manifest(manifest)
    if limit < 1:
        raise ContextPointerError("limit must be at least 1")

    wanted = _normalized_tags(tags)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(entry: dict[str, Any]) -> None:
        pointer_id = entry["id"]
        if pointer_id not in seen and len(selected) < limit:
            selected.append(entry)
            seen.add(pointer_id)

    if include_root:
        for entry in manifest["entries"]:
            if entry["load_mode"] == "root":
                add(entry)

    if wanted:
        for entry in manifest["entries"]:
            entry_tags = {tag.lower() for tag in entry["tags"]}
            if wanted.intersection(entry_tags):
                add(entry)

    return selected


def pointer_packet(
    manifest: dict[str, Any],
    *,
    tags: Iterable[str] | None = None,
    include_root: bool = True,
    limit: int = 12,
) -> dict[str, Any]:
    pointers = select_pointers(
        manifest,
        tags=tags,
        include_root=include_root,
        limit=limit,
    )
    return {
        "schema": SCHEMA,
        "protocol_id": PROTOCOL,
        "manifest_version": manifest["version"],
        "strategy": manifest["strategy"],
        "content_policy": manifest["content_policy"],
        "count": len(pointers),
        "pointers": [
            {
                "id": entry["id"],
                "path": entry["path"],
                "role": entry["role"],
                "load_mode": entry["load_mode"],
            }
            for entry in pointers
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="R³∞ bounded context pointer selector")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--no-root", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    manifest = load_pointer_manifest(args.manifest)
    if args.check:
        print(json.dumps({
            "ok": True,
            "schema": manifest["schema"],
            "protocol_id": manifest["protocol_id"],
            "version": manifest["version"],
            "entries": len(manifest["entries"]),
        }, ensure_ascii=False))
        return 0

    print(json.dumps(pointer_packet(
        manifest,
        tags=args.tag,
        include_root=not args.no_root,
        limit=args.limit,
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
