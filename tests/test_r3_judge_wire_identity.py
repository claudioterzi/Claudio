import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from r3_judge.benchmark import _classify, main, summarize


def rows():
    return [dict(id=str(i), path=f"case-{i}", expected="stub" if i < 5 else "real",
                 correct=True, model="M", backend_fingerprint="F") for i in range(10)]


@pytest.mark.parametrize("model,fingerprint", [(123, "F"), ("M", 456), (None, "F"), ("M", " ")])
def test_wire_identity_not_coerced(tmp_path, model, fingerprint):
    source = tmp_path / "case.txt"
    source.write_text("placeholder")
    response = Mock(content=b"{}")
    response.json.return_value = {"model": model, "x_rizzo": {"fingerprint": fingerprint},
                                  "answers": {"is_stub": {"noul": 1}}}
    with patch("httpx.post", return_value=response), patch("typesafe_sister.client.httpx.Client") as client:
        client.return_value.__enter__.return_value.post.return_value = response
        with pytest.raises(ValueError):
            _classify("http://local.invalid", dict(id="one", path=str(source), label="stub"),
                      model="M", api_key="", timeout=1)


def test_valid_wire_identity_uses_shared_transport(tmp_path):
    source = tmp_path / "case.txt"
    source.write_text("placeholder")
    response = Mock(content=b"{}")
    response.json.return_value = {"model": "M", "x_rizzo": {"fingerprint": "F"},
                                  "answers": {"is_stub": {"noul": 1}}}
    with patch("httpx.post", return_value=response), patch("typesafe_sister.client.httpx.Client") as client:
        post = client.return_value.__enter__.return_value.post
        post.return_value = response
        row = _classify("http://local.invalid", dict(id="one", path=str(source), label="stub"),
                        model="M", api_key="", timeout=1)
        assert row["correct"] is True
        assert row["backend_fingerprint"] == "F"
        assert post.call_args.args[0] == "http://local.invalid/v1/systemone"


@pytest.mark.parametrize("pins", [{}, {"expected_model": "M"}, {"expected_fingerprint": "F"},
                                  {"expected_model": "M", "expected_fingerprint": " "}])
def test_unpinned_report_cannot_adopt(pins):
    assert summarize(rows(), **pins)["adopt"] is False


def test_cli_refuses_missing_pin_before_inference():
    with patch.dict("os.environ", {"R3_JUDGE_EXPECT_FINGERPRINT": ""}), \
         patch("sys.argv", ["benchmark", "nonexistent.json"]), \
         patch("r3_judge.benchmark.system_one_transport", create=True) as call:
        with pytest.raises(SystemExit) as exit:
            main()
        assert exit.value.code == 2
        call.assert_not_called()
