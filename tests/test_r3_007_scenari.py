"""R3-007 — scenari di verifica di stato sull'harness reale (sdq1.verification_harness)."""
import pytest

from sdq1.verification_harness import promotion_decision, verify_state_change


def test_success_without_authoritative_observer_is_unverified():
    ev = verify_state_change(
        action="write", trajectory_success=True, trajectory_signal="http_200",
        expected_state={"v": 1}, observer=None, postcondition_source=None,
        mode="UNAVAILABLE",
    )
    assert ev.verified_success is False
    assert promotion_decision(ev) == "UNVERIFIED_POSTCONDITION"


def test_authoritative_state_mismatch_is_flagged():
    ev = verify_state_change(
        action="write", trajectory_success=True, trajectory_signal="http_200",
        expected_state={"v": 1}, observer=lambda: {"v": 2},
        postcondition_source="db.read_after_write",
    )
    assert ev.state_match is False
    assert promotion_decision(ev) == "STATE_MISMATCH"


def test_observer_without_postcondition_source_is_rejected():
    with pytest.raises(ValueError, match="postcondition_source"):
        verify_state_change(
            action="write", trajectory_success=True, trajectory_signal="http_200",
            expected_state={"v": 1}, observer=lambda: {"v": 1},
            postcondition_source="   ",
        )


def test_proxy_match_is_not_authoritative():
    ev = verify_state_change(
        action="write", trajectory_success=True, trajectory_signal="ui_toast",
        expected_state={"v": 1}, observer=lambda: {"v": 1},
        postcondition_source="ui.reread", mode="PROXY",
    )
    assert ev.verified_success is False
    assert promotion_decision(ev) == "PROXY_MATCH_NOT_AUTHORITATIVE"


def test_observer_exception_is_verification_error():
    def broken():
        raise RuntimeError("store unavailable")

    ev = verify_state_change(
        action="write", trajectory_success=True, trajectory_signal="http_200",
        expected_state={"v": 1}, observer=broken,
        postcondition_source="db.read_after_write",
    )
    assert ev.error == "RuntimeError"
    assert promotion_decision(ev) == "VERIFICATION_ERROR"


def test_authoritative_match_is_verified():
    ev = verify_state_change(
        action="write", trajectory_success=True, trajectory_signal="http_200",
        expected_state={"v": 1}, observer=lambda: {"v": 1},
        postcondition_source="db.read_after_write",
    )
    assert ev.verified_success is True
    assert promotion_decision(ev) == "VERIFIED_POSTCONDITION"
