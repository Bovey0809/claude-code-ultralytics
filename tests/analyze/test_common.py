"""Tests for skills/analyze/scripts/_common.py."""
from __future__ import annotations

import pandas as pd
import pytest

from skills.analyze.scripts import _common


def test_find_results_csv_returns_path(make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50(B)": 0.1}])
    assert _common.find_results_csv(run_dir) == run_dir / "results.csv"


def test_find_results_csv_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        _common.find_results_csv(tmp_path)


def test_find_weights_prefers_best(tmp_path):
    weights = tmp_path / "weights"
    weights.mkdir()
    (weights / "best.pt").write_bytes(b"x")
    (weights / "last.pt").write_bytes(b"x")
    assert _common.find_weights(tmp_path).name == "best.pt"


def test_find_weights_falls_back_to_last(tmp_path):
    weights = tmp_path / "weights"
    weights.mkdir()
    (weights / "last.pt").write_bytes(b"x")
    assert _common.find_weights(tmp_path).name == "last.pt"


def test_load_data_yaml_resolves_paths(make_data_yaml):
    yaml_path = make_data_yaml({"train": [2, 1], "val": [1, 1]})
    data = _common.load_data_yaml(yaml_path)
    assert data["train"].is_absolute()
    assert data["val"].is_absolute()
    assert data["names"] == ["c0", "c1"]


def test_ascii_sparkline_length():
    s = _common.ascii_sparkline([0.1, 0.2, 0.3, 0.4, 0.5], width=10)
    assert len(s) == 10


def test_ascii_sparkline_handles_constant():
    s = _common.ascii_sparkline([1.0, 1.0, 1.0], width=5)
    assert len(s) == 5


def test_ascii_histogram_returns_lines():
    out = _common.ascii_histogram([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], bins=4, width=20)
    lines = out.splitlines()
    assert len(lines) == 4
    assert all("|" in line for line in lines)


def test_print_section_layout(capsys):
    _common.print_section(
        summary_line="model is healthy",
        summary_bullets=["best mAP50 = 0.91 at epoch 87"],
        findings="- box loss decreasing",
        recommendations="- ship it",
    )
    out = capsys.readouterr().out
    assert "## SUMMARY" in out
    assert "## FINDINGS" in out
    assert "## RECOMMENDATIONS" in out
    assert out.index("## SUMMARY") < out.index("## FINDINGS") < out.index("## RECOMMENDATIONS")
