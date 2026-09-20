# !/usr/bin/env python3
"""Convert Graphify graph.json into a Cubo Quantico browser overlay.

Usage:
  python scripts/graphify_to_cubo.py \
      graphify-out/graph.json public/cubo-graphify-data.js \
      --max-nodes 900

The converter is intentionally dependency-free. It accepts Graphify's NetworkX
node-link output with either `edges` or `links`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def _stable_unit(seed: str, salt: str) -> float:
    digest = hashlib.sha256(f"{salt}:{seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def _position(node_id: str) -> tuple[float, float, float]:
    # Keep imported graph nodes inside the existing Cubo envelope.
    x = -165.0 + _stable_unit(node_id, "x") * 330.0
    y = -110.0 + _stable_unit(node_id, "y") * 220.0
    z = -130.0 + _stable_unit(node_id, "z") * 260.0
    return round(x, 2), round(y, 2), round(z, 2)


def _safe_id(raw: Any) -> str:
    text = str(raw)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"gfy-{digest}"


def _node_score(degree: int) -> int:
    if degree <= 0:
        return 2
    return max(2, min(10, int(round(2 + 2.2 * math.log2(1 + degree)))))


def convert(payload: dict[str, Any], max_nodes: int = 900) -> dict[str, Any]:
    raw_nodes = payload.get("nodes") or []
    raw_edges = payload.get("edges") or payload.get("links") or []

    degree: dict[str, int] = {}
    for edge in raw_edges:
        s, t = str(edge.get("source")), str(edge.get("target"))
        degree[s] = degree.get(s, 0) + 1
        degree[t] = degree.get(t, 0) + 1

    ranked = sorted(
        raw_nodes,
        key=lambda n: (
            degree.get(str(n.get("id")), 0),
            str(n.get("label") or n.get("id") or ""),
        ),
        reverse=True,
    )
    if max_nodes > 0:
        ranked = ranked[:max_nodes]

    kept_raw_ids = {str(n.get("id")) for n in ranked}
    id_map = {raw_id: _safe_id(raw_id) for raw_id in kept_raw_ids}

    nodes: list[dict[str, Any]] = []
    for node in ranked:
        raw_id = str(node.get("id"))
        label = str(node.get("label") or raw_id)
        file_type = str(node.get("file_type") or "unknown")
        source_file = node.get("source_file")
        d = degree.get(raw_id, 0)
        score = _node_score(d)
        fx, fy, fz = _position(raw_id)
        nodes.append(
            {
                "id": id_map[raw_id],
                "title": label,
                "category": f"Graphify · {file_type}",
                "year": 2026,
                "importance": score,
                "density": score,
                "kind": "graph",
                "sourceSystem": "Graphify",
                "sourceFile": source_file,
                "sourceLocation": node.get("source_location"),
                "sourceUrl": node.get("source_url"),
                "graphifyId": raw_id,
                "color": "#8aa4b8",
                "fx": fx,
                "fy": fy,
                "fz": fz,
            }
        )

    links: list[dict[str, Any]] = []
    for edge in raw_edges:
        raw_s, raw_t = str(edge.get("source")), str(edge.get("target"))
        if raw_s not in kept_raw_ids or raw_t not in kept_raw_ids:
            continue
        confidence = str(edge.get("confidence") or "AMBIGUOUS").upper()
        score = edge.get("confidence_score")
        if confidence == "EXTRACTED":
            score = 1.0
        links.append(
            {
                "source": id_map[raw_s],
                "target": id_map[raw_t],
                "type": str(edge.get("relation") or "related"),
                "confidence": confidence,
                "confidenceScore": score,
                "evidence": confidence,
                "sourceSystem": "Graphify",
                "sourceFile": edge.get("source_file"),
                "sourceLocation": edge.get("source_location"),
                "weight": edge.get("weight", 1.0),
                "state": "OBSERVED",
            }
        )

    return {
        "meta": {
            "source": "Graphify",
            "schema": "CUBO_GRAPHIFY_DATA/1.0",
            "nodes": len(nodes),
            "links": len(links),
            "inputNodes": len(raw_nodes),
            "inputLinks": len(raw_edges),
            "maxNodes": max_nodes,
            "policy": {
                "EXTRACTED": "direct evidence; may be displayed as observed",
                "INFERRED": "inference; never auto-promote to fact",
                "AMBIGUOUS": "manual review required",
            },
        },
        "nodes": nodes,
        "links": links,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_json", type=Path)
    parser.add_argument("output_js", type=Path)
    parser.add_argument("--max-nodes", type=int, default=900)
    args = parser.parse_args()

    payload = json.loads(args.graph_json.read_text(encoding="utf-8"))
    out = convert(payload, max_nodes=args.max_nodes)
    args.output_js.parent.mkdir(parents=True, exist_ok=True)
    js = (
        "/* Generated by scripts/graphify_to_cubo.py. Do not hand-edit. */\n"
        "window.CUBO_GRAPHIFY_DATA = "
        + json.dumps(out, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    args.output_js.write_text(js, encoding="utf-8")
    print(
        f"Cubo Graphify overlay: {out['meta']['nodes']} nodes, "
        f"{out['meta']['links']} links -> {args.output_js}"
    )


if __name__ == "__main__":
    main()
