"""Shared fixtures for analyze-skill tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml
from PIL import Image

# Make `from skills.analyze.scripts import _common` importable.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def make_results_csv(tmp_path):
    """Return a callable that writes a synthetic results.csv inside a run dir."""

    def _make(rows, run_name="train"):
        run_dir = tmp_path / "runs" / "detect" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        df.to_csv(run_dir / "results.csv", index=False)
        return run_dir

    return _make


@pytest.fixture
def make_data_yaml(tmp_path):
    """Return a callable that writes a tiny data.yaml + label dirs."""

    def _make(class_counts_per_split, names=None, image_size=(640, 640)):
        root = tmp_path / "dataset"
        root.mkdir(exist_ok=True)
        names = names or [f"c{i}" for i in range(max(len(s) for s in class_counts_per_split.values()))]

        for split, counts in class_counts_per_split.items():
            img_dir = root / "images" / split
            lbl_dir = root / "labels" / split
            img_dir.mkdir(parents=True, exist_ok=True)
            lbl_dir.mkdir(parents=True, exist_ok=True)
            idx = 0
            for cls_id, count in enumerate(counts):
                for _ in range(count):
                    stem = f"{split}_{idx:04d}"
                    idx += 1
                    Image.new("RGB", image_size, "white").save(img_dir / f"{stem}.jpg")
                    (lbl_dir / f"{stem}.txt").write_text(f"{cls_id} 0.5 0.5 0.2 0.2\n")

        data = {"path": str(root), "train": "images/train", "val": "images/val", "names": names}
        if "test" in class_counts_per_split:
            data["test"] = "images/test"
        yaml_path = root / "data.yaml"
        yaml_path.write_text(yaml.safe_dump(data))
        return yaml_path

    return _make
