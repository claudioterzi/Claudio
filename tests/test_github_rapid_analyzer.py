from sdq1.github_rapid_analyzer import (
    assess_github_state,
    build_github_state,
    rapid_plan,
)
from typesafe_sister.policy import github_rapid_questions


def _answers(focus="verification_gap"):
    result = {}
    for key, spec in github_rapid_questions().items():
        if spec["type"] == "choice":
            result[key] = {"choice": focus}
        elif spec["type"] == "score":
            result[key] = {"score": 1}
        else:
            result[key] = {"choice": False}
    return result


def test_clm_provenance_uses_same_rubric_without_claiming_jev():
    seen = {}

    def caller(state, questions, timeout):
        seen["questions"] = questions
        return {
            "_r3_provider": "clm",
            "model": "clm-native",
            "answers": _answers(),
        }

    state = build_github_state(repository="claudioterzi/Claudio", target="candidate")
    advisory = assess_github_state(state, caller=caller)

    assert seen["questions"] == github_rapid_questions()
    assert advisory["provider"] == "clm"
    plan = rapid_plan(state, advisory)
    assert plan["system_one_used"] is True
    assert plan["jev_used"] is False


def test_typesafe_fallback_is_reported_as_jev_without_changing_rubric():
    seen = {}

    def caller(state, questions, timeout):
        seen["questions"] = questions
        return {
            "_r3_provider": "typesafe",
            "model": "jev-latest",
            "answers": _answers("regression"),
        }

    state = build_github_state(repository="claudioterzi/Claudio", target="candidate")
    advisory = assess_github_state(state, caller=caller)

    assert seen["questions"] == github_rapid_questions()
    assert advisory["provider"] == "typesafe"
    plan = rapid_plan(state, advisory)
    assert plan["system_one_used"] is True
    assert plan["jev_used"] is True


def test_unavailable_system_one_does_not_claim_provider_use():
    state = build_github_state(repository="claudioterzi/Claudio", target="candidate")
    plan = rapid_plan(state, {"status": "not_configured"})

    assert plan["system_one_used"] is False
    assert plan["jev_used"] is False
