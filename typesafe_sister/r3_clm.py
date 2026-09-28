"""R3 internal contrastive System-One candidate.

This is intentionally small, local and provider-neutral. It implements the same
closed typed decision contract used by TypeSafe/Jev (choice/score/noul) without
claiming to reproduce the weights or capabilities of Stanford/NVIDIA CLM-v0.1.

R3 rules:
- advisory only;
- no side effects;
- no permission/canon promotion;
- deterministic, bounded inputs and stable outputs;
- can be run in shadow mode beside Jev for A/B evidence.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
import os
import re
import unicodedata
from typing import Any, Mapping

MODEL_ID = "r3-clm-v0.1-hash-contrastive"
DEFAULT_DIM = 4096
DEFAULT_TEMPERATURE = 0.42
MAX_STATE_BYTES = 64 * 1024
MAX_TEXT_CHARS = 96_000

_WORD = re.compile(r"[a-z0-9_]+")


class R3CLMError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise R3CLMError("state is not JSON serializable") from exc
    if len(text.encode("utf-8")) > MAX_STATE_BYTES:
        raise R3CLMError("state too large")
    return text


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return text.lower()[:MAX_TEXT_CHARS]


def _semantic_state_text(value: Any, prefix: str = "", depth: int = 0) -> str:
    """Flatten JSON-like state while preserving boolean polarity."""
    if depth > 8:
        return ""
    parts: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, child in list(value.items())[:128]:
            key = _normalize(str(raw_key)).replace(" ", "_")[:120]
            full = f"{prefix}_{key}".strip("_")
            if isinstance(child, bool):
                parts.append(full if child else "not_" + full)
            else:
                nested = _semantic_state_text(child, full, depth + 1)
                if nested:
                    parts.append(nested)
    elif isinstance(value, list):
        for child in value[:96]:
            nested = _semantic_state_text(child, prefix, depth + 1)
            if nested:
                parts.append(nested)
    elif value is None:
        if prefix:
            parts.append("none_" + prefix)
    else:
        text = _normalize(str(value))[:2000]
        parts.append((prefix + " " + text) if prefix else text)
    return " ".join(parts)


def _features(text: str) -> Counter[str]:
    text = _normalize(text)
    words = _WORD.findall(text)
    out: Counter[str] = Counter()
    for token in words:
        out["w:" + token] += 1.0
        if len(token) >= 4:
            padded = "^" + token + "$"
            for i in range(len(padded) - 2):
                out["c3:" + padded[i:i + 3]] += 0.22
    for a, b in zip(words, words[1:]):
        out[f"b:{a}_{b}"] += 0.75
    return out


def _bucket(feature: str, dim: int) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value % dim, -1.0 if (value >> 63) else 1.0


def _encode(text: str, dim: int) -> dict[int, float]:
    vec: dict[int, float] = {}
    for feature, weight in _features(text).items():
        idx, sign = _bucket(feature, dim)
        vec[idx] = vec.get(idx, 0.0) + sign * float(weight)
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / norm for k, v in vec.items()}


def _cosine(a: Mapping[int, float], b: Mapping[int, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(key, 0.0) for key, value in a.items())


def _softmax(logits: Mapping[str, float], temperature: float) -> dict[str, float]:
    if not logits:
        raise R3CLMError("empty candidate set")
    t = max(float(temperature), 1e-3)
    peak = max(logits.values())
    exps = {key: math.exp((value - peak) / t) for key, value in logits.items()}
    total = sum(exps.values()) or 1.0
    return {key: value / total for key, value in exps.items()}


def _candidate_key_bonus(state_text: str, key: str) -> float:
    key_tokens = [x for x in _WORD.findall(_normalize(key)) if len(x) > 2]
    if not key_tokens:
        return 0.0
    state_tokens = set(_WORD.findall(_normalize(state_text)))
    matched = sum(token in state_tokens for token in key_tokens)
    return 0.12 * (matched / len(key_tokens))


def _token_overlap(state_text: str, candidate_text: str) -> float:
    a = set(_WORD.findall(_normalize(state_text)))
    b = set(_WORD.findall(_normalize(candidate_text)))
    if not a or not b:
        return 0.0
    useful = {x for x in b if len(x) > 3}
    if not useful:
        return 0.0
    return len(a & useful) / math.sqrt(max(1, len(useful)))


@dataclass(frozen=True)
class RankResult:
    choice: str
    confidence: float
    probabilities: dict[str, float]
    logits: dict[str, float]


class R3ContrastiveModel:
    """Deterministic contrastive scorer over a closed candidate catalog."""

    def __init__(self, *, dim: int = DEFAULT_DIM, temperature: float = DEFAULT_TEMPERATURE,
                 prototypes: Mapping[str, Mapping[str, list[str]]] | None = None) -> None:
        if dim < 256:
            raise R3CLMError("dim too small")
        self.dim = int(dim)
        self.temperature = float(temperature)
        self.prototypes = prototypes or {}

    def rank(self, state: Any, question_id: str, instructions: str,
             candidates: Mapping[str, str]) -> RankResult:
        if not candidates:
            raise R3CLMError("question has no candidates")
        _canonical_json(state)
        state_text = _semantic_state_text(state)
        query_vec = _encode("STATE " + state_text, self.dim)
        instruction_vec = _encode("QUESTION " + instructions, self.dim)
        logits: dict[str, float] = {}
        for key, description in candidates.items():
            key = str(key)
            description = str(description)
            prototype_texts = list((self.prototypes.get(str(question_id)) or {}).get(key) or [])[:32]
            candidate_text = f"CANDIDATE {key} {description}"
            if prototype_texts:
                candidate_text += "\nVERIFIED_PROTOTYPES " + " ".join(str(x)[:1500] for x in prototype_texts)
            candidate_vec = _encode(candidate_text, self.dim)
            score = 4.2 * _cosine(query_vec, candidate_vec)
            score += 0.18 * _cosine(instruction_vec, candidate_vec)
            score += 0.30 * _token_overlap(state_text, candidate_text)
            score += _candidate_key_bonus(state_text, key)
            logits[key] = score
        probabilities = _softmax(logits, self.temperature)
        choice = max(probabilities, key=probabilities.get)
        return RankResult(choice=choice, confidence=float(probabilities[choice]),
                          probabilities={k: float(v) for k, v in probabilities.items()},
                          logits={k: float(v) for k, v in logits.items()})


def _load_prototypes_from_env() -> Mapping[str, Mapping[str, list[str]]]:
    path = os.getenv("R3_CLM_PROTOTYPES", "").strip()
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise R3CLMError("prototype store must be an object")
    return value


def _choice_answer(rank: RankResult) -> dict[str, Any]:
    return {"type": "choice", "choice": rank.choice, "confidence": rank.confidence,
            "probabilities": rank.probabilities}


def _score_answer(rank: RankResult, criteria: list[str]) -> dict[str, Any]:
    keys = [str(i) for i in range(len(criteria))]
    probs = {key: rank.probabilities[key] for key in keys}
    expected = sum(float(i) * probs[str(i)] for i in range(len(criteria)))
    return {"type": "score", "score": expected, "confidence": rank.confidence,
            "probabilities": probs, "legend": {str(i): str(text) for i, text in enumerate(criteria)}}


def _noul_answer(model: R3ContrastiveModel, state: Any, question_id: str,
                 instructions: str, spec: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping) and "true" in criteria and "false" in criteria:
        rank = model.rank(state, question_id, instructions,
                          {"true": str(criteria["true"]), "false": str(criteria["false"])})
        return {"type": "noul", "noul": float(rank.probabilities["true"])}, False
    return {"type": "noul", "noul": 0.5}, True


def system_one_local(state: Any, questions: Mapping[str, Mapping[str, Any]],
                     *, model: R3ContrastiveModel | None = None) -> dict[str, Any]:
    """Evaluate TypeSafe-compatible questions locally, without network calls."""
    if not isinstance(questions, Mapping) or not questions:
        raise R3CLMError("questions must be a non-empty object")
    _canonical_json(state)
    engine = model or R3ContrastiveModel(prototypes=_load_prototypes_from_env())
    answers: dict[str, Any] = {}
    abstained: list[str] = []
    for question_id, raw_spec in questions.items():
        if not isinstance(raw_spec, Mapping):
            raise R3CLMError("invalid question spec")
        spec = dict(raw_spec)
        qtype = str(spec.get("type", ""))
        instructions = str(spec.get("instructions", ""))[:16_000]
        if qtype == "choice":
            criteria = spec.get("criteria")
            if not isinstance(criteria, Mapping) or not criteria:
                raise R3CLMError("choice requires criteria")
            rank = engine.rank(state, str(question_id), instructions,
                               {str(k): str(v) for k, v in criteria.items()})
            answers[str(question_id)] = _choice_answer(rank)
        elif qtype == "score":
            criteria = spec.get("criteria")
            if not isinstance(criteria, list) or len(criteria) < 2:
                raise R3CLMError("score requires at least two levels")
            rank = engine.rank(state, str(question_id), instructions,
                               {str(i): str(text) for i, text in enumerate(criteria)})
            answers[str(question_id)] = _score_answer(rank, [str(x) for x in criteria])
        elif qtype == "noul":
            answer, did_abstain = _noul_answer(engine, state, str(question_id), instructions, spec)
            answers[str(question_id)] = answer
            if did_abstain:
                abstained.append(str(question_id))
        else:
            raise R3CLMError(f"unsupported question type: {qtype}")
    return {"model": MODEL_ID, "provider": "r3_internal", "answers": answers,
            "meta": {"authority": "advisory_only", "network_calls": 0,
                     "abstained_questions": abstained, "encoder": "stable_hash_sparse_v1"}}


def compare_answer_sets(primary: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return bounded A/B agreement metrics without declaring either model correct."""
    p = primary.get("answers") if isinstance(primary, Mapping) else None
    c = candidate.get("answers") if isinstance(candidate, Mapping) else None
    if not isinstance(p, Mapping) or not isinstance(c, Mapping):
        return {"status": "invalid"}
    keys = sorted(set(p) & set(c))
    if not keys:
        return {"status": "no_common_questions", "questions": 0}
    comparable = agreements = 0
    deltas: dict[str, Any] = {}
    for key in keys:
        pa, ca = p[key], c[key]
        if not isinstance(pa, Mapping) or not isinstance(ca, Mapping) or pa.get("type") != ca.get("type"):
            continue
        qtype = pa.get("type")
        comparable += 1
        if qtype == "choice":
            same = pa.get("choice") == ca.get("choice")
            agreements += int(same)
            deltas[key] = {"type": qtype, "same_choice": same}
        elif qtype == "score":
            try:
                diff = abs(float(pa.get("score")) - float(ca.get("score")))
            except (TypeError, ValueError):
                diff = None
            same = diff is not None and diff <= 0.5
            agreements += int(same)
            deltas[key] = {"type": qtype, "score_abs_delta": diff}
        elif qtype == "noul":
            try:
                diff = abs(float(pa.get("noul")) - float(ca.get("noul")))
                same = (float(pa.get("noul")) >= 0.5) == (float(ca.get("noul")) >= 0.5)
            except (TypeError, ValueError):
                diff, same = None, False
            agreements += int(same)
            deltas[key] = {"type": qtype, "noul_abs_delta": diff, "same_side": same}
    return {"status": "compared", "questions": comparable,
            "agreement_rate": (agreements / comparable) if comparable else None,
            "deltas": deltas}
