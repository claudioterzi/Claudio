"""R3∞ learned reuse router.

Purpose:
- retrieve the best existing lesson/path before reusing a capability;
- learn from verified outcomes;
- when routing is ambiguous, ask the existing canonical TypeSafe/Jev layer a
  bounded Choice question over the shortlisted paths;
- never execute, authorize, or promote a rewrite by itself.

The heavyweight embedding model is optional and lazy. If it is unavailable,
routing degrades to deterministic lexical similarity. Jev is also fail-soft:
its absence never becomes a fabricated judgment.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import argparse
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Callable, Iterable

import yaml

DEFAULT_MODEL = os.getenv("R3_REUSE_EMBED_MODEL", "BAAI/bge-m3")
DEFAULT_LEDGER = Path(os.getenv("R3_REUSE_LESSONS_PATH", "R3_REUSE_LESSONS.yaml"))
DEFAULT_STATE_DIR = Path(os.getenv("R3_REUSE_ML_STATE_DIR", ".r3/reuse_ml"))
DEFAULT_SHORTCUTS = Path(os.getenv("R3_REUSE_SHORTCUTS_PATH", "R3_REUSE_SHORTCUTS.yaml"))

_TOKEN_RE = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)
_STATUS_WEIGHT = {
    "OBSERVED": 0.15,
    "CANDIDATE": 0.35,
    "VERIFIED": 0.75,
    "CANONICAL": 1.0,
    "DEPRECATED": 0.0,
}


@dataclass(frozen=True)
class RankedLesson:
    lesson_id: str
    capability: str
    score: float
    semantic_score: float
    learned_success_probability: float | None
    status: str
    canonical_short_path: tuple[str, ...]


@dataclass(frozen=True)
class RouteDecision:
    selected_lesson_id: str
    route: str
    confidence_signal: float
    ambiguous: bool
    jev_used: bool
    jev_available: bool
    candidates: tuple[str, ...]
    reason: str


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{k} {_flatten(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(v) for v in value)
    return str(value)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text) if len(m.group(0)) > 1}


def lexical_similarity(query: str, document: str) -> float:
    q = _tokens(query)
    d = _tokens(document)
    if not q or not d:
        return 0.0
    return len(q & d) / math.sqrt(len(q) * len(d))


def lesson_text(lesson: dict[str, Any]) -> str:
    return " ".join(
        _flatten(lesson.get(key))
        for key in (
            "capability", "trigger", "verified_facts", "failure_modes",
            "canonical_short_path", "preconditions", "verification", "cleanup",
        )
        if lesson.get(key)
    )


def load_lessons(path: Path = DEFAULT_LEDGER) -> list[dict[str, Any]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    lessons = raw.get("lessons") or []
    if not isinstance(lessons, list):
        raise ValueError("invalid R3 reuse lessons ledger")
    return [x for x in lessons if isinstance(x, dict) and x.get("id")]


class SemanticEncoder:
    """Lazy local semantic encoder.

    No model is loaded or downloaded on import. This keeps Vercel/serverless
    paths light and lets local R3 nodes opt into the stronger model.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(
            self.model_name,
            trust_remote_code=False,
            local_files_only=os.getenv("R3_REUSE_ML_LOCAL_ONLY", "0") == "1",
            device=(os.getenv("R3_REUSE_ML_DEVICE") or None),
        )
        return self._model

    def similarities(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        model = self._load()
        if hasattr(model, "encode_query") and hasattr(model, "encode_document"):
            q = model.encode_query(
                query, normalize_embeddings=True, convert_to_numpy=True,
                show_progress_bar=False,
            )
            docs = model.encode_document(
                documents, normalize_embeddings=True, convert_to_numpy=True,
                show_progress_bar=False,
            )
        else:
            vectors = model.encode(
                [query, *documents],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            q, docs = vectors[0], vectors[1:]
        return [float(q @ vector) for vector in docs]

    def warmup(self) -> dict[str, Any]:
        scores = self.similarities(
            "reuse the canonical Jev path",
            ["TypeSafe Jev canonical transport", "perfume bottle image rendering"],
        )
        return {"model": self.model_name, "loaded": True, "probe_scores": scores}


class OutcomeLearner:
    """Small supervised reranker trained only on verified outcome records."""

    FEATURE_KEYS = (
        "semantic_score", "prior_success_rate", "prior_attempts_log",
        "canonical_status", "known_failure_penalty",
    )

    def __init__(self, state_dir: Path = DEFAULT_STATE_DIR) -> None:
        self.state_dir = Path(state_dir)
        self.events_path = self.state_dir / "outcomes.jsonl"
        self.model_path = self.state_dir / "ranker.joblib"
        self._model = None

    def _vector(self, features: dict[str, float]) -> list[float]:
        return [float(features.get(key, 0.0)) for key in self.FEATURE_KEYS]

    def record_verified_outcome(
        self,
        *,
        lesson_id: str,
        features: dict[str, float],
        verified_success: bool,
        evidence_ref: str,
    ) -> None:
        if not evidence_ref.strip():
            raise ValueError("evidence_ref is required")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        event = {
            "lesson_id": str(lesson_id),
            "features": {key: float(features.get(key, 0.0)) for key in self.FEATURE_KEYS},
            "verified_success": bool(verified_success),
            "evidence_ref": evidence_ref.strip(),
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        self._model = None

    def _events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and isinstance(item.get("verified_success"), bool):
                events.append(item)
        return events

    def train(self) -> bool:
        events = self._events()
        labels = {item["verified_success"] for item in events}
        if len(events) < 8 or labels != {False, True}:
            return False
        from sklearn.linear_model import SGDClassifier
        import joblib

        X = [self._vector(item.get("features") or {}) for item in events]
        y = [1 if item["verified_success"] else 0 for item in events]
        model = SGDClassifier(
            loss="log_loss",
            alpha=0.0005,
            class_weight="balanced",
            max_iter=2000,
            tol=1e-4,
            random_state=3,
        )
        model.fit(X, y)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, self.model_path)
        self._model = model
        return True

    def _load_model(self):
        if self._model is not None:
            return self._model
        if not self.model_path.exists() and not self.train():
            return None
        import joblib
        self._model = joblib.load(self.model_path)
        return self._model

    def probability(self, features: dict[str, float]) -> float | None:
        model = self._load_model()
        if model is None:
            return None
        return float(self._model.predict_proba([self._vector(features)])[0][1])


def _features(lesson: dict[str, Any], semantic_score: float) -> dict[str, float]:
    metrics = lesson.get("metrics") or {}
    attempts = max(0.0, float(metrics.get("verified_attempts", 0) or 0))
    successes = max(0.0, float(metrics.get("verified_successes", 0) or 0))
    return {
        "semantic_score": float(semantic_score),
        "prior_success_rate": (successes / attempts) if attempts else 0.5,
        "prior_attempts_log": math.log1p(attempts) / 5.0,
        "canonical_status": _STATUS_WEIGHT.get(str(lesson.get("status", "")).upper(), 0.1),
        "known_failure_penalty": min(1.0, len(lesson.get("failure_modes") or []) / 10.0),
    }


def rank_lessons(
    query: str,
    lessons: Iterable[dict[str, Any]],
    *,
    top_k: int = 5,
    encoder: SemanticEncoder | None = None,
    learner: OutcomeLearner | None = None,
) -> list[RankedLesson]:
    items = [x for x in lessons if str(x.get("status", "")).upper() != "DEPRECATED"]
    if not items:
        return []
    docs = [lesson_text(item) for item in items]
    if encoder:
        try:
            semantics = encoder.similarities(query, docs)
        except (ImportError, OSError, RuntimeError, ValueError):
            semantics = [lexical_similarity(query, doc) for doc in docs]
    else:
        semantics = [lexical_similarity(query, doc) for doc in docs]

    result: list[RankedLesson] = []
    for lesson, semantic in zip(items, semantics):
        features = _features(lesson, semantic)
        learned = learner.probability(features) if learner else None
        score = (
            0.68 * semantic
            + 0.08 * features["canonical_status"]
            + 0.06 * features["prior_success_rate"]
            + (0.18 * learned if learned is not None else 0.0)
        )
        result.append(RankedLesson(
            lesson_id=str(lesson["id"]),
            capability=str(lesson.get("capability", "")),
            score=float(score),
            semantic_score=float(semantic),
            learned_success_probability=learned,
            status=str(lesson.get("status", "")),
            canonical_short_path=tuple(str(x) for x in lesson.get("canonical_short_path") or []),
        ))
    result.sort(key=lambda item: (item.score, item.semantic_score, item.lesson_id), reverse=True)
    return result[:max(1, int(top_k))]


def _ambiguous(ranked: list[RankedLesson], *, min_score: float, min_margin: float) -> bool:
    if not ranked:
        return True
    if ranked[0].score < min_score:
        return True
    if len(ranked) > 1 and (ranked[0].score - ranked[1].score) < min_margin:
        return True
    return False


def _jev_choice(
    query: str,
    ranked: list[RankedLesson],
    *,
    caller: Callable[..., dict[str, Any]] | None = None,
) -> str | None:
    """Ask canonical Jev to choose only among shortlisted existing paths."""
    if not ranked:
        return None
    if caller is None:
        from typesafe_sister.client import system_one
        caller = system_one

    criteria = {
        item.lesson_id: (
            f"Capability: {item.capability}. Existing canonical path: "
            + " -> ".join(item.canonical_short_path[:8])
        )
        for item in ranked[:5]
    }
    state = {
        "routing_need": query[:4000],
        "candidates": [
            {
                "lesson_id": item.lesson_id,
                "capability": item.capability,
                "semantic_score": round(item.semantic_score, 6),
                "status": item.status,
            }
            for item in ranked[:5]
        ],
        "rule": "Choose an existing candidate only. Do not invent a new engine or path.",
    }
    questions = {
        "reuse_shortcut": {
            "type": "choice",
            "instructions": (
                "Which existing canonical lesson/path best fits this reuse need? "
                "Prefer the path that resolves the task with least rediscovery and "
                "without expanding authority. This is routing advice only."
            ),
            "criteria": criteria,
        }
    }
    result = caller(state, questions, model="jev-latest", timeout=8)
    answer = (result.get("answers") or {}).get("reuse_shortcut") or {}
    choice = answer.get("choice")
    return choice if choice in criteria else None



def _configured_provider_models() -> list[tuple[str, str]]:
    """Reuse the shared SDQ-1 provider/model discovery path."""
    from sdq1.llm.router import configured_provider_models
    return configured_provider_models()

def _provider_jury_choice(
    query: str,
    ranked: list[RankedLesson],
    *,
    provider_pairs: list[tuple[str, str]] | None = None,
    timeout_seconds: float = 24.0,
) -> tuple[str | None, list[dict[str, Any]]]:
    """Use every available secret-backed/local provider as a parallel failover jury.

    Each provider is attempted once with its preferred configured model. Secret
    values never leave the provider class. Votes are advisory routing signals only.
    """
    if not ranked:
        return None, []

    from sdq1.llm.router import PROVIDER_REGISTRY

    pairs = provider_pairs if provider_pairs is not None else _configured_provider_models()
    candidates = {item.lesson_id: item for item in ranked[:5]}
    candidate_text = "\n".join(
        f"- {item.lesson_id}: {item.capability}; path={' -> '.join(item.canonical_short_path[:6])}"
        for item in ranked[:5]
    )
    system = (
        "You are a bounded routing reviewer inside R3. Choose only one supplied "
        "existing lesson ID. Do not invent a new tool, model, engine or path. "
        "Return exactly the lesson ID and nothing else."
    )
    user = (
        f"Routing need: {query[:3000]}\nExisting candidates:\n{candidate_text}\n"
        "Pick the candidate that best reuses existing verified capability with least rediscovery."
    )

    def call_pair(pair: tuple[str, str]) -> dict[str, Any]:
        provider_name, model = pair
        entry = PROVIDER_REGISTRY.get(provider_name)
        if not entry:
            return {"provider": provider_name, "model": model, "valid": False, "choice": None, "latency_ms": 0}
        cls, _ = entry
        try:
            provider = cls(
                modello=model,
                api_key=None,
                max_token=32,
                temperatura=0.0,
                timeout_secondi=timeout_seconds,
            )
        except Exception:
            return {"provider": provider_name, "model": model, "valid": False, "choice": None, "latency_ms": 0}
        if not getattr(provider, "disponibile", False):
            return {"provider": provider_name, "model": model, "valid": False, "choice": None, "latency_ms": 0}
        response = provider.completa(system, user)
        choice = (response.testo or "").strip()
        valid = bool(response.via_api and choice in candidates)
        return {
            "provider": provider_name,
            "model": model,
            "valid": valid,
            "choice": choice if valid else None,
            "latency_ms": response.latenza_ms,
        }

    evidence: list[dict[str, Any]] = []
    workers = max(1, min(len(pairs), 12))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(call_pair, pair) for pair in pairs]
        for future in concurrent.futures.as_completed(futures):
            try:
                evidence.append(future.result())
            except Exception:
                continue

    evidence.sort(key=lambda item: str(item.get("provider", "")))
    votes: dict[str, int] = {lesson_id: 0 for lesson_id in candidates}
    for item in evidence:
        if item.get("valid") and item.get("choice") in votes:
            votes[str(item["choice"])] += 1

    valid_votes = [(count, lesson_id) for lesson_id, count in votes.items() if count > 0]
    if not valid_votes:
        return None, evidence
    valid_votes.sort(reverse=True)
    best_count, best_choice = valid_votes[0]
    tied = len(valid_votes) > 1 and valid_votes[1][0] == best_count
    if tied:
        for item in ranked:
            if votes.get(item.lesson_id, 0) == best_count:
                return item.lesson_id, evidence
    return best_choice, evidence

def choose_route(
    query: str,
    *,
    lessons: list[dict[str, Any]] | None = None,
    encoder: SemanticEncoder | None = None,
    learner: OutcomeLearner | None = None,
    jev_caller: Callable[..., dict[str, Any]] | None = None,
    provider_jury: Callable[[str, list[RankedLesson]], tuple[str | None, list[dict[str, Any]]]] | None = None,
    min_score: float = 0.40,
    min_margin: float = 0.08,
) -> tuple[RouteDecision, list[RankedLesson]]:
    lessons = lessons if lessons is not None else load_lessons()
    ranked = rank_lessons(query, lessons, top_k=5, encoder=encoder, learner=learner)
    if not ranked:
        raise LookupError("no reusable lessons available")

    ambiguous = _ambiguous(ranked, min_score=min_score, min_margin=min_margin)
    if ambiguous:
        try:
            chosen = _jev_choice(query, ranked, caller=jev_caller)
            if chosen:
                selected = next(item for item in ranked if item.lesson_id == chosen)
                return RouteDecision(
                    selected_lesson_id=chosen,
                    route="ml_shortlist+jev_choice",
                    confidence_signal=selected.score,
                    ambiguous=True,
                    jev_used=True,
                    jev_available=True,
                    candidates=tuple(item.lesson_id for item in ranked),
                    reason="ML ranking was ambiguous; canonical Jev Choice resolved among existing paths.",
                ), ranked
        except Exception:
            # No fabricated Jev answer. Continue to existing-provider failover.
            pass

        jury = provider_jury or _provider_jury_choice
        jury_choice, jury_evidence = jury(query, ranked)
        if jury_choice:
            selected = next(item for item in ranked if item.lesson_id == jury_choice)
            providers = ",".join(
                sorted({str(item.get("provider")) for item in jury_evidence if item.get("valid")})
            )
            return RouteDecision(
                selected_lesson_id=jury_choice,
                route="ml_shortlist+provider_jury",
                confidence_signal=selected.score,
                ambiguous=True,
                jev_used=False,
                jev_available=False,
                candidates=tuple(item.lesson_id for item in ranked),
                reason=(
                    "Jev was unavailable/invalid; dynamically discovered available providers "
                    f"resolved among existing paths ({providers or 'provider jury'})."
                ),
            ), ranked

        return RouteDecision(
            selected_lesson_id=ranked[0].lesson_id,
            route="deterministic_ranked_fallback",
            confidence_signal=ranked[0].score,
            ambiguous=True,
            jev_used=False,
            jev_available=False,
            candidates=tuple(item.lesson_id for item in ranked),
            reason=(
                "Jev and the available provider jury were unavailable/invalid; "
                "used deterministic top-ranked existing lesson without inventing a route."
            ),
        ), ranked

    return RouteDecision(
        selected_lesson_id=ranked[0].lesson_id,
        route="learned_reuse_shortcut",
        confidence_signal=ranked[0].score,
        ambiguous=False,
        jev_used=False,
        jev_available=True,
        candidates=tuple(item.lesson_id for item in ranked),
        reason="Top existing lesson cleared the routing score and margin.",
    ), ranked


def verified_shortcut_record(
    *,
    shortcut_id: str,
    trigger: str,
    decision: RouteDecision,
    verified_success: bool,
    evidence_ref: str,
) -> dict[str, Any]:
    """Build a persistable shortcut record only from a verified outcome."""
    if not evidence_ref.strip():
        raise ValueError("verified shortcut requires evidence_ref")
    return {
        "id": shortcut_id,
        "trigger": trigger,
        "lesson_id": decision.selected_lesson_id,
        "verified_success": bool(verified_success),
        "evidence_ref": evidence_ref.strip(),
        "source_route": decision.route,
        "jev_used": decision.jev_used,
        "status": "CANONICAL" if verified_success else "REJECTED",
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="R3 learned reuse router")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--lexical-only", action="store_true")
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    if args.warmup:
        print(json.dumps(SemanticEncoder().warmup(), ensure_ascii=False, indent=2))
        return 0
    if not args.query:
        parser.error("query is required unless --warmup is used")

    lessons = load_lessons(Path(args.ledger))
    encoder = None if args.lexical_only else SemanticEncoder()
    decision, ranked = choose_route(args.query, lessons=lessons, encoder=encoder, learner=OutcomeLearner())
    print(json.dumps({
        "decision": asdict(decision),
        "ranked": [asdict(item) for item in ranked],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
