"""Tests for dataset_audit.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "skills/analyze/scripts/dataset_audit.py"


def _run(yaml_path: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(yaml_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_balanced_dataset(make_data_yaml):
    yaml_path = make_data_yaml({"train": [10, 10, 10], "val": [3, 3, 3]})
    proc = _run(yaml_path)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "## SUMMARY" in out
    assert "balanced" in out.lower() or "imbalance ratio" in out.lower()


def test_imbalance_flagged(make_data_yaml):
    yaml_path = make_data_yaml({"train": [100, 5, 1], "val": [10, 1, 1]})
    out = _run(yaml_path).stdout.lower()
    assert "imbalance" in out


def test_class_missing_in_train(make_data_yaml):
    yaml_path = make_data_yaml({"train": [5, 0], "val": [2, 2]})
    out = _run(yaml_path).stdout.lower()
    assert "missing" in out or "absent" in out or "divergen" in out


def test_label_sanity_out_of_bounds(make_data_yaml):
    yaml_path = make_data_yaml({"train": [3], "val": [1]})
    train_lbl_dir = yaml_path.parent / "labels" / "train"
    bad = next(train_lbl_dir.iterdir())
    bad.write_text("0 1.5 0.5 0.2 0.2\n")
    out = _run(yaml_path).stdout.lower()
    assert "out-of-bounds" in out or "out of bounds" in out


def test_zero_area_box_flagged(make_data_yaml):
    yaml_path = make_data_yaml({"train": [3], "val": [1]})
    train_lbl_dir = yaml_path.parent / "labels" / "train"
    bad = next(train_lbl_dir.iterdir())
    bad.write_text("0 0.5 0.5 0.0 0.2\n")
    out = _run(yaml_path).stdout.lower()
    assert "zero-area" in out or "zero area" in out


def test_image_without_label(make_data_yaml):
    from PIL import Image
    yaml_path = make_data_yaml({"train": [3], "val": [1]})
    extra = yaml_path.parent / "images" / "train" / "orphan.jpg"
    Image.new("RGB", (640, 640), "white").save(extra)
    out = _run(yaml_path).stdout.lower()
    assert "without label" in out or "missing label" in out
