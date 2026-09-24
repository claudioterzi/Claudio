"""Admission gate for R3-JUDGE local model backends.

The gate is deliberately file-based and create-only from a benchmark run.  Active
mode must never infer that a backend is adopted merely because a service responds.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from r3_judge import PROTOCOL

DEFAULT_GATE_PATH = "r3_judge/adoption_gate.json"


def load_gate(path: str | None = None) -> dict[str, Any] | None:
    target = Path(path or os.getenv("R3_JUDGE_GATE", DEFAULT_GATE_PATH))
    try:
        raw = target.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def gate_allows(result: dict[str, Any], path: str | None = None) -> bool:
    """Return True only for an adopted gate matching the responding model.

    A gate generated for another model/fingerprint is not portable.  We match the
    model id and the Rizzo fingerprint.
    """
    gate = load_gate(path)
    if not gate or gate.get("protocol") != PROTOCOL or gate.get("adopt") is not True:
        return False

    gate_model = str(gate.get("model") or "")
    result_model = str(result.get("model") or "")
    if not gate_model or gate_model != result_model:
        return False

    gate_fp = str(gate.get("backend_fingerprint") or "")
    x_rizzo = result.get("x_rizzo") if isinstance(result.get("x_rizzo"), dict) else {}
    result_fp = str(x_rizzo.get("fingerprint") or "")
    if not gate_fp or not result_fp or gate_fp != result_fp:
        return False
    return True
