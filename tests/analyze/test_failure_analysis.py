"""Tests for failure_analysis.py via --from-cache."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "skills/analyze/scripts/failure_analysis.py"


def _run(run_dir: Path, cache: Path, top: int = 5):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(run_dir), "--from-cache", str(cache), "--top", str(top)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_failure_modes_reported(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.5}])
    cache = tmp_path / "fail.json"
    cache.write_text(json.dumps({
        "errors": [
            {"image": "/abs/img1.jpg", "mode": "FP", "pred_class": "dog", "score": 0.9},
            {"image": "/abs/img2.jpg", "mode": "FN", "true_class": "cat"},
            {"image": "/abs/img3.jpg", "mode": "localization", "pred_class": "cat", "iou": 0.3},
            {"image": "/abs/img4.jpg", "mode": "class-confusion", "pred_class": "cat", "true_class": "dog", "iou": 0.7},
            {"image": "/abs/img4.jpg", "mode": "class-confusion", "pred_class": "cat", "true_class": "dog", "iou": 0.6},
            {"image": "/abs/img5.jpg", "mode": "FP", "pred_class": "bird", "score": 0.6},
        ],
    }))
    proc = _run(run_dir, cache, top=2)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "## SUMMARY" in out
    for mode in ("FP", "FN", "localization", "class-confusion"):
        assert mode in out
    assert "/abs/img4.jpg" in out


def test_empty_errors(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.5}])
    cache = tmp_path / "fail.json"
    cache.write_text(json.dumps({"errors": []}))
    out = _run(run_dir, cache).stdout.lower()
    assert "no errors" in out or "no failures" in out
