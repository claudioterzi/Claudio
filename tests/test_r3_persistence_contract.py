from pathlib import Path

from r3.persistence_contract import ensure_persistence_marker, evaluate_durability_expectations


def test_marker_is_stable_in_same_directory(tmp_path: Path):
    first = ensure_persistence_marker(tmp_path)
    second = ensure_persistence_marker(tmp_path)
    assert first["sha256"] == second["sha256"]
    assert first["size"] == 32
    assert second["created"] is False


def test_fresh_directory_gets_independent_marker(tmp_path: Path):
    a = ensure_persistence_marker(tmp_path / "a")
    b = ensure_persistence_marker(tmp_path / "b")
    assert a["sha256"] != b["sha256"]


def test_tampered_marker_is_rejected(tmp_path: Path):
    ensure_persistence_marker(tmp_path)
    marker = tmp_path / "persistence.marker"
    marker.write_bytes(b"broken")
    try:
        ensure_persistence_marker(tmp_path)
    except RuntimeError as exc:
        assert "invalid persistence marker size" in str(exc)
    else:
        raise AssertionError("tampered marker must fail closed")


def test_incomplete_expectations_never_verify():
    r = evaluate_durability_expectations(
        marker_sha256="aa",
        verify_key_hex="bb",
        expected_marker_sha256="aa",
        expected_verify_key_hex="",
        expected_canary_doc_id="cc",
        canary_ok=True,
    )
    assert r["durability_verified"] is False
    assert r["expectation_complete"] is False


def test_all_three_exact_matches_verify():
    r = evaluate_durability_expectations(
        marker_sha256="aa",
        verify_key_hex="bb",
        expected_marker_sha256="aa",
        expected_verify_key_hex="bb",
        expected_canary_doc_id="cc",
        canary_ok=True,
    )
    assert r["expectation_complete"] is True
    assert r["marker_match"] is True
    assert r["verify_key_match"] is True
    assert r["canary_match"] is True
    assert r["durability_verified"] is True


def test_marker_mismatch_fails():
    r = evaluate_durability_expectations(
        marker_sha256="aa",
        verify_key_hex="bb",
        expected_marker_sha256="ab",
        expected_verify_key_hex="bb",
        expected_canary_doc_id="cc",
        canary_ok=True,
    )
    assert r["durability_verified"] is False


def test_verify_key_mismatch_fails():
    r = evaluate_durability_expectations(
        marker_sha256="aa",
        verify_key_hex="bb",
        expected_marker_sha256="aa",
        expected_verify_key_hex="bc",
        expected_canary_doc_id="cc",
        canary_ok=True,
    )
    assert r["durability_verified"] is False


def test_missing_canary_fails():
    r = evaluate_durability_expectations(
        marker_sha256="aa",
        verify_key_hex="bb",
        expected_marker_sha256="aa",
        expected_verify_key_hex="bb",
        expected_canary_doc_id="cc",
        canary_ok=False,
    )
    assert r["durability_verified"] is False
