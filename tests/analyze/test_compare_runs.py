"""Tests for compare_runs.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[2] / "skills/analyze/scripts/compare_runs.py"


def _rows(scale=1.0):
    rows = []
    for i in range(10):
        rows.append({
            "epoch": i,
            "metrics/precision(B)": 0.5 * scale,
            "metrics/recall(B)": 0.5 * scale,
            "metrics/mAP50(B)": 0.6 * scale,
            "metrics/mAP50-95(B)": 0.4 * scale,
        })
    return rows


def _run(*run_dirs: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, run_dirs)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_two_run_comparison(make_results_csv):
    a = make_results_csv(_rows(1.0), run_name="A")
    b = make_results_csv(_rows(0.9), run_name="B")
    proc = _run(a, b)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "## SUMMARY" in out
    assert "A" in out and "B" in out
    assert "mAP50-95" in out


def test_args_yaml_metadata_diff(make_results_csv, tmp_path):
    a = make_results_csv(_rows(1.0), run_name="A")
    b = make_results_csv(_rows(0.9), run_name="B")
    (a / "args.yaml").write_text(yaml.safe_dump({"model": "yolo11n.pt", "imgsz": 640, "lr0": 0.01}))
    (b / "args.yaml").write_text(yaml.safe_dump({"model": "yolo11s.pt", "imgsz": 640, "lr0": 0.005}))
    out = _run(a, b).stdout
    assert "model" in out
    assert "yolo11n.pt" in out and "yolo11s.pt" in out


def test_three_run_comparison(make_results_csv):
    a = make_results_csv(_rows(1.0), run_name="A")
    b = make_results_csv(_rows(0.9), run_name="B")
    c = make_results_csv(_rows(1.1), run_name="C")
    proc = _run(a, b, c)
    assert proc.returncode == 0
    assert "C" in proc.stdout
