"""Tests for val_metrics.py (uses --from-cache to avoid loading a model)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "skills/analyze/scripts/val_metrics.py"


def _run(run_dir: Path, cache: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(run_dir), "--from-cache", str(cache)],
        capture_output=True,
        text=True,
        check=False,
    )


def _make_cache(tmp_path: Path) -> Path:
    cache = tmp_path / "val_cache.json"
    cache.write_text(json.dumps({
        "names": ["cat", "dog", "bird"],
        "overall": {"P": 0.8, "R": 0.7, "mAP50": 0.75, "mAP50-95": 0.55},
        "per_class": [
            {"name": "cat", "support": 100, "P": 0.9, "R": 0.85, "mAP50": 0.88, "mAP50-95": 0.7},
            {"name": "dog", "support": 80, "P": 0.7, "R": 0.6, "mAP50": 0.65, "mAP50-95": 0.45},
            {"name": "bird", "support": 5, "P": 0.4, "R": 0.2, "mAP50": 0.25, "mAP50-95": 0.15},
        ],
        "confusion_top": [
            {"true": "dog", "pred": "cat", "count": 12},
            {"true": "bird", "pred": "background", "count": 4},
        ],
        "conf_sweep": [
            {"conf": 0.1, "F1": 0.62},
            {"conf": 0.25, "F1": 0.71},
            {"conf": 0.4, "F1": 0.74},
            {"conf": 0.6, "F1": 0.68},
        ],
    }))
    return cache


def test_per_class_table_and_recommendations(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.55}])
    cache = _make_cache(tmp_path)
    proc = _run(run_dir, cache)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "## SUMMARY" in out
    assert "bird" in out
    assert "0.4" in out or "0.40" in out
    assert "dog" in out and "cat" in out


def test_low_support_class_flagged(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.55}])
    cache = _make_cache(tmp_path)
    out = _run(run_dir, cache).stdout.lower()
    assert "more data" in out or "low support" in out
