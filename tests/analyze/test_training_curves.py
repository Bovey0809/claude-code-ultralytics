"""Tests for training_curves.py."""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "skills/analyze/scripts/training_curves.py"


def _run(run_dir: Path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc


def _healthy_rows(n=20):
    rows = []
    for i in range(n):
        rows.append({
            "epoch": i,
            "train/box_loss": 1.0 - i * 0.04,
            "train/cls_loss": 0.8 - i * 0.03,
            "train/dfl_loss": 0.9 - i * 0.03,
            "val/box_loss": 1.1 - i * 0.04,
            "val/cls_loss": 0.9 - i * 0.03,
            "val/dfl_loss": 1.0 - i * 0.03,
            "metrics/precision(B)": 0.5 + i * 0.02,
            "metrics/recall(B)": 0.4 + i * 0.02,
            "metrics/mAP50(B)": 0.3 + i * 0.03,
            "metrics/mAP50-95(B)": 0.2 + i * 0.025,
            "lr/pg0": 0.01,
        })
    return rows


def test_summary_findings_recommendations_present(make_results_csv):
    run_dir = make_results_csv(_healthy_rows())
    proc = _run(run_dir)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "## SUMMARY" in out
    assert "## FINDINGS" in out
    assert "## RECOMMENDATIONS" in out


def test_reports_best_epoch(make_results_csv):
    rows = _healthy_rows()
    run_dir = make_results_csv(rows)
    proc = _run(run_dir)
    assert "best epoch" in proc.stdout.lower()
    assert str(rows[-1]["epoch"]) in proc.stdout


def test_detects_overfitting(make_results_csv):
    rows = _healthy_rows()
    for i, r in enumerate(rows):
        if i >= 10:
            r["val/box_loss"] = 1.1 + (i - 10) * 0.05
            r["val/cls_loss"] = 0.9 + (i - 10) * 0.04
            r["metrics/mAP50-95(B)"] = 0.45  # plateau
    run_dir = make_results_csv(rows)
    out = _run(run_dir).stdout.lower()
    assert "overfit" in out


def test_detects_nan(make_results_csv):
    rows = _healthy_rows()
    rows[5]["train/box_loss"] = float("nan")
    run_dir = make_results_csv(rows)
    out = _run(run_dir).stdout.lower()
    assert "nan" in out


def test_missing_results_csv_errors(tmp_path):
    proc = _run(tmp_path)
    assert proc.returncode != 0
    assert "results.csv" in (proc.stderr + proc.stdout).lower()
