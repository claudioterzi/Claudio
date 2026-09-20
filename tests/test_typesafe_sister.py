from __future__ import annotations

import pytest
from fastapi import HTTPException

from r3 import typesafe_sister as sister


def test_wire_questions_supports_choice_noul_score():
    raw = {
        "route": sister.QuestionSpec(type="choice", instructions="route", criteria={"a": None, "b": None}),
        "present": sister.QuestionSpec(type="noul", instructions="present?", criteria={"true": "yes", "false": "no"}),
        "priority": sister.QuestionSpec(type="score", instructions="priority", criteria=["low", "mid", "high"]),
    }
    out = sister._wire_questions(raw)
    assert out["route"]["type"] == "choice"
    assert out["present"]["type"] == "noul"
    assert out["priority"]["criteria"] == ["low", "mid", "high"]


def test_hash_is_order_stable():
    assert sister._canonical_hash({"a": 1, "b": 2}) == sister._canonical_hash({"b": 2, "a": 1})


def test_choice_requires_criteria():
    with pytest.raises(HTTPException) as exc:
        sister._wire_questions({"route": sister.QuestionSpec(type="choice", instructions="route")})
    assert exc.value.status_code == 422


def test_score_requires_ordered_levels():
    with pytest.raises(HTTPException) as exc:
        sister._wire_questions({"priority": sister.QuestionSpec(type="score", instructions="priority", criteria={})})
    assert exc.value.status_code == 422


def test_missing_typesafe_secret_fails_closed(monkeypatch):
    monkeypatch.setattr(sister, "TYPESAFE_API_KEY", "")
    with pytest.raises(HTTPException) as exc:
        sister._system_one("state", {"present": {"type": "noul", "instructions": "present?"}}, None)
    assert exc.value.status_code == 503
