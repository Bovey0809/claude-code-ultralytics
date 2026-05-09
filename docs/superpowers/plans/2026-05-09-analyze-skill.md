# `/ultralytics:analyze` Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `ultralytics:analyze` skill with five bundled Python scripts (`training_curves`, `val_metrics`, `dataset_audit`, `failure_analysis`, `compare_runs`) that emit stdout-only `SUMMARY / FINDINGS / RECOMMENDATIONS` reports for end-to-end YOLO model debugging.

**Architecture:** Skill lives at `skills/analyze/`. `SKILL.md` is the trigger + interpretation reference Claude reads. Each script is standalone, argparse-driven, and depends only on packages already pulled in by `ultralytics` (pandas, numpy, PIL, ultralytics). A tiny `_common.py` holds shared helpers (run-dir discovery, ASCII chart helpers, the `print_section` output-contract enforcer). Tests use pytest with synthetic fixtures (fabricated `results.csv`, tiny label dirs, mocked `model.val()` / `model.predict()` results) so the suite runs without GPU or real datasets.

**Tech Stack:** Python 3.8+, pandas, numpy, PIL, ultralytics, pytest.

---

## File structure

To be created:

```
skills/analyze/
  SKILL.md
  scripts/
    __init__.py
    _common.py
    training_curves.py
    val_metrics.py
    dataset_audit.py
    failure_analysis.py
    compare_runs.py
tests/analyze/
  __init__.py
  conftest.py
  test_common.py
  test_training_curves.py
  test_val_metrics.py
  test_dataset_audit.py
  test_failure_analysis.py
  test_compare_runs.py
```

To be modified:

- `.claude-plugin/plugin.json` — bump version to `0.6.0`
- `.claude-plugin/marketplace.json` — bump version, mention `analyze` in description
- `README.md` — list the new skill alongside existing ones

Responsibilities:

- `_common.py` — pure utilities; no script-specific logic
- Each script — one responsibility from the design (training curves, val metrics, dataset, failures, comparison); each owns its own argparse, output formatting, and exit code
- `SKILL.md` — Claude-facing reference (when to use, decision tree, interpretation cheat-sheet, output contract)
- Tests — one file per script, mirroring the source layout

---

## Task 1: Project scaffolding & shared helpers (`_common.py`)

**Files:**
- Create: `skills/analyze/scripts/__init__.py`
- Create: `skills/analyze/scripts/_common.py`
- Create: `tests/analyze/__init__.py`
- Create: `tests/analyze/conftest.py`
- Create: `tests/analyze/test_common.py`

- [ ] **Step 1: Create empty package files**

```bash
mkdir -p skills/analyze/scripts tests/analyze
: > skills/analyze/scripts/__init__.py
: > tests/analyze/__init__.py
```

- [ ] **Step 2: Write `tests/analyze/conftest.py` with fixture-builder helpers**

```python
# tests/analyze/conftest.py
"""Shared fixtures for analyze-skill tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

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
        names = names or [f"c{i}" for i in range(max(max(s) for s in class_counts_per_split.values()) + 1)]

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
                    # 1x1 white JPEG via PIL
                    from PIL import Image
                    Image.new("RGB", image_size, "white").save(img_dir / f"{stem}.jpg")
                    (lbl_dir / f"{stem}.txt").write_text(f"{cls_id} 0.5 0.5 0.2 0.2\n")

        data = {"path": str(root), "train": "images/train", "val": "images/val", "names": names}
        if "test" in class_counts_per_split:
            data["test"] = "images/test"
        yaml_path = root / "data.yaml"
        yaml_path.write_text(yaml.safe_dump(data))
        return yaml_path

    return _make
```

- [ ] **Step 3: Write the failing test `tests/analyze/test_common.py`**

```python
# tests/analyze/test_common.py
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
    # Should not blow up on zero range
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
    # Order matters
    assert out.index("## SUMMARY") < out.index("## FINDINGS") < out.index("## RECOMMENDATIONS")
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/analyze/test_common.py -v`
Expected: ImportError / ModuleNotFoundError on `_common`.

- [ ] **Step 5: Implement `skills/analyze/scripts/_common.py`**

```python
# skills/analyze/scripts/_common.py
"""Shared helpers for the analyze-skill scripts.

Intentionally small: run-dir discovery, ASCII chart helpers, and the
SUMMARY/FINDINGS/RECOMMENDATIONS output-contract enforcer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import yaml

_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def find_results_csv(run_dir: Path) -> Path:
    p = Path(run_dir) / "results.csv"
    if not p.is_file():
        raise FileNotFoundError(f"No results.csv in {run_dir}")
    return p


def find_weights(run_dir: Path, prefer: str = "best") -> Path:
    weights_dir = Path(run_dir) / "weights"
    candidates = [prefer, "last", "best"]
    seen = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        p = weights_dir / f"{name}.pt"
        if p.is_file():
            return p
    raise FileNotFoundError(f"No best.pt/last.pt under {weights_dir}")


def load_data_yaml(path: Path) -> dict:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    base = Path(raw.get("path", path.parent)).expanduser()
    if not base.is_absolute():
        base = (path.parent / base).resolve()
    out = dict(raw)
    out["path"] = base
    for key in ("train", "val", "test"):
        if key in raw and raw[key] is not None:
            sub = Path(raw[key])
            out[key] = sub if sub.is_absolute() else (base / sub).resolve()
    return out


def ascii_sparkline(values: Sequence[float], width: int = 40) -> str:
    if not values:
        return " " * width
    # Resample to `width` points by linear interpolation.
    n = len(values)
    if n == 1:
        sampled = [float(values[0])] * width
    else:
        sampled = []
        for i in range(width):
            t = i * (n - 1) / (width - 1) if width > 1 else 0
            lo = int(t)
            hi = min(lo + 1, n - 1)
            frac = t - lo
            sampled.append(float(values[lo]) * (1 - frac) + float(values[hi]) * frac)
    lo, hi = min(sampled), max(sampled)
    if hi - lo < 1e-12:
        return _SPARK_CHARS[0] * width
    span = hi - lo
    return "".join(
        _SPARK_CHARS[min(len(_SPARK_CHARS) - 1, int((v - lo) / span * (len(_SPARK_CHARS) - 1)))]
        for v in sampled
    )


def ascii_histogram(values: Iterable[float], bins: int = 10, width: int = 40) -> str:
    vals = [float(v) for v in values]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        hi = lo + 1.0
    edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in vals:
        idx = min(bins - 1, int((v - lo) / (hi - lo) * bins))
        counts[idx] += 1
    cmax = max(counts) or 1
    lines = []
    for i, c in enumerate(counts):
        bar = "█" * int(c / cmax * width)
        lines.append(f"[{edges[i]:.3g}, {edges[i+1]:.3g}) | {bar} {c}")
    return "\n".join(lines)


def print_section(
    summary_line: str,
    summary_bullets: Sequence[str],
    findings: str,
    recommendations: str,
) -> None:
    """Print the SUMMARY/FINDINGS/RECOMMENDATIONS contract.

    summary_bullets: top-3 findings as short strings.
    findings, recommendations: pre-formatted multiline blocks.
    """
    print("## SUMMARY")
    print(summary_line)
    for b in summary_bullets:
        print(f"- {b}")
    print()
    print("## FINDINGS")
    print(findings.rstrip())
    print()
    print("## RECOMMENDATIONS")
    print(recommendations.rstrip())
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/analyze/test_common.py -v`
Expected: 9 passed.

- [ ] **Step 7: Commit**

```bash
git add skills/analyze/scripts/__init__.py skills/analyze/scripts/_common.py tests/analyze/__init__.py tests/analyze/conftest.py tests/analyze/test_common.py
git commit -m "feat(analyze): add scaffolding and shared helpers (_common)"
```

---

## Task 2: `training_curves.py`

**Files:**
- Create: `skills/analyze/scripts/training_curves.py`
- Test: `tests/analyze/test_training_curves.py`

YOLO `results.csv` columns of interest (Ultralytics 8.x): `epoch`, `train/box_loss`, `train/cls_loss`, `train/dfl_loss`, `val/box_loss`, `val/cls_loss`, `val/dfl_loss`, `metrics/precision(B)`, `metrics/recall(B)`, `metrics/mAP50(B)`, `metrics/mAP50-95(B)`, `lr/pg0`.

- [ ] **Step 1: Write the failing test**

```python
# tests/analyze/test_training_curves.py
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
    # Best mAP50-95 is at the last epoch (monotonically increasing).
    assert "best epoch" in proc.stdout.lower()
    assert str(rows[-1]["epoch"]) in proc.stdout


def test_detects_overfitting(make_results_csv):
    rows = _healthy_rows()
    # Make val loss climb in the second half while train keeps falling.
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/analyze/test_training_curves.py -v`
Expected: all fail with FileNotFoundError on the script path or non-zero exit.

- [ ] **Step 3: Implement `skills/analyze/scripts/training_curves.py`**

```python
#!/usr/bin/env python3
"""Diagnose a YOLO training run from its results.csv.

Usage:
    python training_curves.py <run_dir>
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_TRAIN_LOSS_COLS = ["train/box_loss", "train/cls_loss", "train/dfl_loss"]
_VAL_LOSS_COLS = ["val/box_loss", "val/cls_loss", "val/dfl_loss"]
_KEY_METRIC = "metrics/mAP50-95(B)"


def _classify_trend(series: pd.Series) -> str:
    s = series.dropna()
    if len(s) < 3:
        return "insufficient-data"
    first, last = s.iloc[: max(1, len(s) // 4)].mean(), s.iloc[-max(1, len(s) // 4):].mean()
    delta = last - first
    rng = s.max() - s.min()
    if rng < 1e-9:
        return "flat"
    rel = delta / (abs(first) + 1e-9)
    if abs(rel) < 0.02:
        return "plateau"
    return "decreasing" if delta < 0 else "increasing"


def _detect_overfit(df: pd.DataFrame) -> bool:
    if "val/box_loss" not in df or "train/box_loss" not in df:
        return False
    n = len(df)
    if n < 10:
        return False
    half = n // 2
    train_trend = _classify_trend(df["train/box_loss"].iloc[half:])
    val_trend = _classify_trend(df["val/box_loss"].iloc[half:])
    map_trend = _classify_trend(df[_KEY_METRIC].iloc[half:]) if _KEY_METRIC in df else "n/a"
    return train_trend == "decreasing" and val_trend in ("increasing", "plateau") and map_trend in ("plateau", "decreasing")


def _detect_underfit(df: pd.DataFrame) -> bool:
    if "train/box_loss" not in df:
        return False
    train_trend = _classify_trend(df["train/box_loss"])
    final_map = df[_KEY_METRIC].iloc[-1] if _KEY_METRIC in df else None
    return train_trend == "decreasing" and (final_map is None or final_map < 0.3)


def _detect_nans(df: pd.DataFrame) -> list[tuple[str, int]]:
    hits = []
    for col in df.columns:
        if df[col].dtype.kind in "fc":
            mask = df[col].apply(lambda v: isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
            if mask.any():
                hits.append((col, int(df.index[mask][0])))
    return hits


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    args = p.parse_args(argv)

    csv_path = _common.find_results_csv(args.run_dir)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    findings_parts: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    # Best epoch by key metric
    best_epoch = None
    best_map = None
    if _KEY_METRIC in df.columns:
        best_idx = df[_KEY_METRIC].idxmax()
        best_epoch = int(df.loc[best_idx, "epoch"]) if "epoch" in df.columns else int(best_idx)
        best_map = float(df.loc[best_idx, _KEY_METRIC])
        final_map = float(df[_KEY_METRIC].iloc[-1])
        summary_bullets.append(
            f"best epoch = {best_epoch}, mAP50-95 = {best_map:.4f} (final = {final_map:.4f})"
        )
        findings_parts.append(
            f"- best epoch (by {_KEY_METRIC}) = {best_epoch}; best mAP50-95 = {best_map:.4f}; final = {final_map:.4f}"
        )

    # Sparklines per metric
    spark_lines = []
    for col in _TRAIN_LOSS_COLS + _VAL_LOSS_COLS + ["metrics/mAP50(B)", _KEY_METRIC]:
        if col in df.columns:
            trend = _classify_trend(df[col])
            spark = _common.ascii_sparkline(df[col].fillna(method="ffill").fillna(0).tolist(), width=40)
            spark_lines.append(f"  {col:28s} [{trend:12s}] {spark}")
    if spark_lines:
        findings_parts.append("- per-metric trend (sparkline + classification):\n" + "\n".join(spark_lines))

    # Overfit / underfit
    overfit = _detect_overfit(df)
    underfit = _detect_underfit(df)
    if overfit:
        summary_bullets.append("overfitting detected (val loss rising / mAP plateau)")
        findings_parts.append("- overfitting: train loss still falling while val loss rises or mAP50-95 plateaus")
        recs.append("- reduce epochs or enable early-stopping; increase augmentation; consider weight decay")
    if underfit:
        summary_bullets.append("underfitting suspected (train loss still falling, low final mAP)")
        findings_parts.append("- underfitting: train loss has not converged and final mAP50-95 is low")
        recs.append("- train more epochs, increase model capacity, or raise learning rate")

    # NaN / Inf
    nans = _detect_nans(df)
    if nans:
        first_col, first_row = nans[0]
        summary_bullets.append(f"NaN/Inf detected in {first_col} starting row {first_row}")
        findings_parts.append("- divergence: " + "; ".join(f"{c} first NaN/Inf at row {r}" for c, r in nans))
        recs.append("- lower lr0, enable AMP only on supported hardware, or check for corrupt labels")

    # LR schedule sanity
    if "lr/pg0" in df.columns:
        lr_final = float(df["lr/pg0"].iloc[-1])
        lr_initial = float(df["lr/pg0"].iloc[0])
        findings_parts.append(f"- lr schedule: initial={lr_initial:.2e}, final={lr_final:.2e}")

    # Compose top-line summary
    if not summary_bullets:
        summary_line = "training appears healthy"
    elif overfit or nans:
        summary_line = "training has issues — see findings"
    else:
        summary_line = "training mostly healthy"

    if not recs:
        recs.append("- training looks healthy; no immediate action needed")

    _common.print_section(
        summary_line=summary_line,
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings_parts),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/analyze/test_training_curves.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/scripts/training_curves.py tests/analyze/test_training_curves.py
git commit -m "feat(analyze): add training_curves.py for results.csv diagnostics"
```

---

## Task 3: `dataset_audit.py`

This script does not need a model — pure dataset analysis. We test before the model-dependent scripts because mocking is not required.

**Files:**
- Create: `skills/analyze/scripts/dataset_audit.py`
- Test: `tests/analyze/test_dataset_audit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/analyze/test_dataset_audit.py
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
    # class index 1 only in val
    yaml_path = make_data_yaml({"train": [5, 0], "val": [2, 2]})
    out = _run(yaml_path).stdout.lower()
    assert "missing" in out or "absent" in out or "divergen" in out


def test_label_sanity_out_of_bounds(make_data_yaml, tmp_path):
    yaml_path = make_data_yaml({"train": [3], "val": [1]})
    # Corrupt one label file with out-of-bounds coordinates.
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/analyze/test_dataset_audit.py -v`
Expected: all fail (script not found).

- [ ] **Step 3: Implement `skills/analyze/scripts/dataset_audit.py`**

```python
#!/usr/bin/env python3
"""Audit a YOLO dataset for class balance, geometry, and label sanity.

Usage:
    python dataset_audit.py <data.yaml>
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def _list_images(img_dir: Path) -> list[Path]:
    if not img_dir.is_dir():
        return []
    return [p for p in img_dir.rglob("*") if p.suffix.lower() in _IMG_EXTS]


def _label_path_for(img: Path, img_root: Path, lbl_root: Path) -> Path:
    rel = img.relative_to(img_root).with_suffix(".txt")
    return lbl_root / rel


def _parse_label(text: str) -> list[tuple[int, float, float, float, float]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        cls = int(float(parts[0]))
        x, y, w, h = (float(v) for v in parts[1:5])
        out.append((cls, x, y, w, h))
    return out


def _audit_split(name: str, img_dir: Path, lbl_dir: Path):
    images = _list_images(img_dir)
    class_counts: Counter[int] = Counter()
    box_areas: list[float] = []
    box_aspects: list[float] = []
    resolutions: list[tuple[int, int]] = []
    out_of_bounds = 0
    zero_area = 0
    missing_labels = 0
    orphan_labels = 0

    for img in images:
        try:
            with Image.open(img) as im:
                resolutions.append(im.size)
        except Exception:
            pass
        lbl = _label_path_for(img, img_dir, lbl_dir)
        if not lbl.is_file():
            missing_labels += 1
            continue
        for cls, x, y, w, h in _parse_label(lbl.read_text()):
            class_counts[cls] += 1
            if w <= 0 or h <= 0:
                zero_area += 1
                continue
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                out_of_bounds += 1
            if x - w / 2 < 0 or x + w / 2 > 1 or y - h / 2 < 0 or y + h / 2 > 1:
                out_of_bounds += 1
            box_areas.append(w * h)
            box_aspects.append(w / h)

    if lbl_dir.is_dir():
        for lbl in lbl_dir.rglob("*.txt"):
            rel = lbl.relative_to(lbl_dir).with_suffix("")
            if not any((img_dir / f"{rel}{ext}").is_file() for ext in _IMG_EXTS):
                orphan_labels += 1

    return {
        "name": name,
        "n_images": len(images),
        "class_counts": class_counts,
        "box_areas": box_areas,
        "box_aspects": box_aspects,
        "resolutions": resolutions,
        "out_of_bounds": out_of_bounds,
        "zero_area": zero_area,
        "missing_labels": missing_labels,
        "orphan_labels": orphan_labels,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data_yaml", type=Path)
    args = p.parse_args(argv)

    data = _common.load_data_yaml(args.data_yaml)
    names = data.get("names", [])
    splits = []
    for split in ("train", "val", "test"):
        if split in data:
            img_dir = data[split]
            lbl_dir = Path(str(img_dir).replace("/images/", "/labels/"))
            splits.append(_audit_split(split, img_dir, lbl_dir))

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    # Class distribution + imbalance
    for s in splits:
        cc = s["class_counts"]
        if not cc:
            findings.append(f"- {s['name']}: no labeled boxes found")
            continue
        total = sum(cc.values())
        rows = []
        for idx in sorted(cc):
            label = names[idx] if idx < len(names) else f"class_{idx}"
            rows.append(f"    {idx:3d} {label:20s} {cc[idx]:6d}  ({cc[idx]/total*100:5.1f}%)")
        ratio = max(cc.values()) / max(1, min(cc.values()))
        verdict = "balanced" if ratio < 3 else ("mild imbalance" if ratio < 10 else ("imbalance" if ratio < 50 else "severe imbalance"))
        findings.append(
            f"- {s['name']}: {s['n_images']} images, {total} boxes, {len(cc)} classes; "
            f"imbalance ratio max/min = {ratio:.1f}x ({verdict})\n" + "\n".join(rows)
        )
        if ratio >= 10:
            summary_bullets.append(f"{s['name']} class imbalance {ratio:.0f}x ({verdict})")
            recs.append(f"- {s['name']}: oversample / augment minority classes or collect more data")

    # Train/val class divergence
    if len(splits) >= 2:
        train = next((s for s in splits if s["name"] == "train"), None)
        val = next((s for s in splits if s["name"] == "val"), None)
        if train and val:
            only_in_val = set(val["class_counts"]) - set(train["class_counts"])
            only_in_train = set(train["class_counts"]) - set(val["class_counts"])
            if only_in_val:
                summary_bullets.append(f"classes missing from train: {sorted(only_in_val)}")
                findings.append(f"- divergence: classes present in val but absent from train: {sorted(only_in_val)}")
                recs.append("- add training samples for classes absent from train split")
            if only_in_train:
                findings.append(f"- divergence: classes present in train but absent from val: {sorted(only_in_train)}")

    # Geometry
    for s in splits:
        if s["box_areas"]:
            areas = sorted(s["box_areas"])
            mid = areas[len(areas) // 2]
            findings.append(
                f"- {s['name']} bbox area distribution (normalized):\n"
                + _common.ascii_histogram(s["box_areas"], bins=8, width=30)
                + f"\n  median area = {mid:.4f}"
            )
            if mid < 0.001:
                recs.append(f"- {s['name']}: median bbox area very small (<0.1%); consider higher imgsz")

    # Resolutions
    for s in splits:
        if s["resolutions"]:
            uniq = set(s["resolutions"])
            findings.append(f"- {s['name']} resolutions: {len(uniq)} distinct; example {next(iter(uniq))}")

    # Label sanity
    sanity_total = 0
    for s in splits:
        bad = s["out_of_bounds"] + s["zero_area"] + s["missing_labels"] + s["orphan_labels"]
        sanity_total += bad
        if bad:
            findings.append(
                f"- {s['name']} label sanity: out-of-bounds={s['out_of_bounds']}, "
                f"zero-area={s['zero_area']}, images-without-labels={s['missing_labels']}, "
                f"labels-without-images={s['orphan_labels']}"
            )
    if sanity_total:
        summary_bullets.append(f"{sanity_total} label-sanity issues found")
        recs.append("- fix label-sanity issues (out-of-bounds, zero-area, orphans) before retraining")

    if not summary_bullets:
        summary_line = "dataset looks healthy"
        summary_bullets.append("class distribution within tolerable bounds")
    else:
        summary_line = "dataset has issues — see findings"

    if not recs:
        recs.append("- no immediate action required")

    _common.print_section(
        summary_line=summary_line,
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/analyze/test_dataset_audit.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/scripts/dataset_audit.py tests/analyze/test_dataset_audit.py
git commit -m "feat(analyze): add dataset_audit.py for class balance and label sanity"
```

---

## Task 4: `compare_runs.py`

**Files:**
- Create: `skills/analyze/scripts/compare_runs.py`
- Test: `tests/analyze/test_compare_runs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/analyze/test_compare_runs.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/analyze/test_compare_runs.py -v`
Expected: all fail.

- [ ] **Step 3: Implement `skills/analyze/scripts/compare_runs.py`**

```python
#!/usr/bin/env python3
"""Compare two or more YOLO training runs side-by-side.

Usage:
    python compare_runs.py <run_a> <run_b> [<run_c> ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_METRICS = [
    "metrics/precision(B)",
    "metrics/recall(B)",
    "metrics/mAP50(B)",
    "metrics/mAP50-95(B)",
]


def _load_run(run_dir: Path) -> dict:
    df = pd.read_csv(_common.find_results_csv(run_dir))
    df.columns = [c.strip() for c in df.columns]
    info = {"name": run_dir.name, "df": df}
    args_yaml = run_dir / "args.yaml"
    info["args"] = yaml.safe_load(args_yaml.read_text()) if args_yaml.is_file() else {}
    return info


def _best_metrics(df: pd.DataFrame) -> dict:
    out = {}
    if "metrics/mAP50-95(B)" in df.columns:
        idx = df["metrics/mAP50-95(B)"].idxmax()
        for m in _METRICS:
            if m in df.columns:
                out[m] = float(df.loc[idx, m])
        out["best_epoch"] = int(df.loc[idx, "epoch"]) if "epoch" in df.columns else int(idx)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dirs", nargs="+", type=Path)
    args = p.parse_args(argv)

    runs = [_load_run(r) for r in args.run_dirs]

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    # Side-by-side metrics
    header = "  metric                          " + "  ".join(f"{r['name']:>12s}" for r in runs)
    rows = [header]
    bests = [_best_metrics(r["df"]) for r in runs]
    for m in _METRICS:
        cells = []
        for b in bests:
            cells.append(f"{b.get(m, float('nan')):>12.4f}")
        rows.append(f"  {m:30s}" + "  ".join(cells))
    rows.append(
        "  best_epoch                    " + "  ".join(f"{b.get('best_epoch', -1):>12d}" for b in bests)
    )
    findings.append("- best-epoch metrics:\n" + "\n".join(rows))

    # Pairwise mAP delta vs first run
    base = bests[0].get("metrics/mAP50-95(B)")
    if base is not None:
        for r, b in zip(runs[1:], bests[1:]):
            cur = b.get("metrics/mAP50-95(B)")
            if cur is None:
                continue
            delta = cur - base
            verdict = "improved" if delta > 0 else ("regressed" if delta < 0 else "unchanged")
            summary_bullets.append(f"{r['name']} vs {runs[0]['name']}: mAP50-95 {delta:+.4f} ({verdict})")

    # Stability: epoch-to-epoch variance of mAP50-95
    stab = []
    for r in runs:
        col = "metrics/mAP50-95(B)"
        if col in r["df"].columns:
            stab.append(f"  {r['name']:12s} val mAP50-95 std = {r['df'][col].std():.4f}")
    if stab:
        findings.append("- training stability (lower std = smoother):\n" + "\n".join(stab))

    # args.yaml diff
    keys = sorted({k for r in runs for k in r["args"].keys()})
    if keys:
        diff_rows = []
        for k in keys:
            vals = [str(r["args"].get(k, "—")) for r in runs]
            if len(set(vals)) > 1:
                diff_rows.append(f"  {k:20s} " + "  ".join(f"{v:>14s}" for v in vals))
        if diff_rows:
            findings.append(
                "- args.yaml differences ("
                + ", ".join(r["name"] for r in runs)
                + "):\n"
                + "\n".join(diff_rows)
            )
            recs.append("- inspect args.yaml deltas above; isolate one variable at a time")

    if not summary_bullets:
        summary_bullets.append("runs have comparable mAP50-95")
    if not recs:
        recs.append("- pick the run with highest mAP50-95 for promotion")

    _common.print_section(
        summary_line=f"compared {len(runs)} runs",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/analyze/test_compare_runs.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/scripts/compare_runs.py tests/analyze/test_compare_runs.py
git commit -m "feat(analyze): add compare_runs.py for cross-run metric diff"
```

---

## Task 5: `val_metrics.py` (model-dependent, mocked)

The script wraps `ultralytics.YOLO(weights).val()`. To test without GPU/datasets, the script reads a synthetic per-class block from `results.csv`-adjacent files when available, AND supports a `--from-cache` flag that reads a pre-computed JSON. Tests use `--from-cache`. Real-model invocation is exercised manually on the pose server.

**Files:**
- Create: `skills/analyze/scripts/val_metrics.py`
- Test: `tests/analyze/test_val_metrics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/analyze/test_val_metrics.py
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
    assert "bird" in out  # weakest class shown
    # Suggested confidence threshold should reflect best F1 (conf 0.4)
    assert "0.4" in out or "0.40" in out
    # Top confusion present
    assert "dog" in out and "cat" in out


def test_low_support_class_flagged(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.55}])
    cache = _make_cache(tmp_path)
    out = _run(run_dir, cache).stdout.lower()
    assert "more data" in out or "low support" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/analyze/test_val_metrics.py -v`
Expected: all fail.

- [ ] **Step 3: Implement `skills/analyze/scripts/val_metrics.py`**

```python
#!/usr/bin/env python3
"""Per-class validation metrics, confusion-matrix top confusions, and a confidence sweep.

Usage:
    python val_metrics.py <run_dir> [--data data.yaml]
    python val_metrics.py <run_dir> --from-cache <json>   # for tests / re-runs

The cache JSON shape is documented in tests/analyze/test_val_metrics.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


def _from_model(run_dir: Path, data_yaml: Path | None) -> dict:
    from ultralytics import YOLO  # imported lazily so tests don't pay the cost
    weights = _common.find_weights(run_dir)
    model = YOLO(str(weights))
    kwargs = {}
    if data_yaml:
        kwargs["data"] = str(data_yaml)
    res = model.val(**kwargs)
    names = list(res.names.values()) if hasattr(res, "names") else []
    box = res.box  # ultralytics Metric
    overall = {
        "P": float(box.mp),
        "R": float(box.mr),
        "mAP50": float(box.map50),
        "mAP50-95": float(box.map),
    }
    per_class = []
    if hasattr(box, "ap_class_index") and len(box.ap_class_index):
        for i, cls_idx in enumerate(box.ap_class_index):
            name = names[cls_idx] if cls_idx < len(names) else f"class_{cls_idx}"
            per_class.append({
                "name": name,
                "support": int(box.nt_per_class[cls_idx]) if hasattr(box, "nt_per_class") else 0,
                "P": float(box.p[i]) if i < len(box.p) else float("nan"),
                "R": float(box.r[i]) if i < len(box.r) else float("nan"),
                "mAP50": float(box.ap50[i]) if i < len(box.ap50) else float("nan"),
                "mAP50-95": float(box.ap[i]) if i < len(box.ap) else float("nan"),
            })
    return {"names": names, "overall": overall, "per_class": per_class, "confusion_top": [], "conf_sweep": []}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--from-cache", dest="from_cache", type=Path, default=None)
    args = p.parse_args(argv)

    if args.from_cache:
        payload = json.loads(args.from_cache.read_text())
    else:
        payload = _from_model(args.run_dir, args.data)

    overall = payload.get("overall", {})
    per_class = payload.get("per_class", [])
    conf_sweep = payload.get("conf_sweep", [])
    confusion_top = payload.get("confusion_top", [])

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    if overall:
        summary_bullets.append(
            f"overall mAP50={overall.get('mAP50', float('nan')):.3f}, "
            f"mAP50-95={overall.get('mAP50-95', float('nan')):.3f}"
        )
        findings.append(
            "- overall: " + ", ".join(f"{k}={v:.3f}" for k, v in overall.items())
        )

    if per_class:
        per_class_sorted = sorted(per_class, key=lambda r: r.get("mAP50-95", 0.0))
        rows = [f"  {'class':20s} {'support':>8s} {'P':>6s} {'R':>6s} {'mAP50':>7s} {'mAP50-95':>9s}"]
        for r in per_class_sorted:
            rows.append(
                f"  {r['name']:20s} {r['support']:8d} "
                f"{r['P']:6.3f} {r['R']:6.3f} {r['mAP50']:7.3f} {r['mAP50-95']:9.3f}"
            )
        findings.append("- per-class metrics (weakest first):\n" + "\n".join(rows))

        weakest = per_class_sorted[0]
        summary_bullets.append(f"weakest class = {weakest['name']} (mAP50-95={weakest['mAP50-95']:.3f})")
        # Heuristic recommendations
        for r in per_class_sorted[:3]:
            if r["support"] < 20 and r["R"] < 0.5:
                recs.append(f"- '{r['name']}': low support ({r['support']}) and recall — needs more data")
            elif r["P"] < 0.5 and r["support"] >= 20:
                recs.append(f"- '{r['name']}': high support ({r['support']}) but low precision — likely needs better labels")

    if confusion_top:
        rows = [f"  true={c['true']:15s} pred={c['pred']:15s} count={c['count']}" for c in confusion_top]
        findings.append("- top confusion-matrix off-diagonals:\n" + "\n".join(rows))

    if conf_sweep:
        best = max(conf_sweep, key=lambda r: r["F1"])
        rows = [f"  conf={r['conf']:.2f}  F1={r['F1']:.3f}" for r in conf_sweep]
        findings.append("- confidence threshold sweep:\n" + "\n".join(rows))
        summary_bullets.append(f"suggested conf = {best['conf']:.2f} (F1={best['F1']:.3f})")
        recs.append(f"- set predict conf={best['conf']:.2f} to maximize F1")

    if not summary_bullets:
        summary_bullets.append("no metrics available")
    if not recs:
        recs.append("- no class-level interventions suggested")

    _common.print_section(
        summary_line="validation summary",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/analyze/test_val_metrics.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/scripts/val_metrics.py tests/analyze/test_val_metrics.py
git commit -m "feat(analyze): add val_metrics.py with per-class deep-dive and conf sweep"
```

---

## Task 6: `failure_analysis.py` (model-dependent, mocked)

Same pattern as val_metrics: real path uses `model.predict()`, tests use `--from-cache` with a pre-classified error list.

**Files:**
- Create: `skills/analyze/scripts/failure_analysis.py`
- Test: `tests/analyze/test_failure_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/analyze/test_failure_analysis.py
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
    # Worst image with most class-confusion errors
    assert "/abs/img4.jpg" in out


def test_empty_errors(tmp_path, make_results_csv):
    run_dir = make_results_csv([{"epoch": 0, "metrics/mAP50-95(B)": 0.5}])
    cache = tmp_path / "fail.json"
    cache.write_text(json.dumps({"errors": []}))
    out = _run(run_dir, cache).stdout.lower()
    assert "no errors" in out or "no failures" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/analyze/test_failure_analysis.py -v`
Expected: all fail.

- [ ] **Step 3: Implement `skills/analyze/scripts/failure_analysis.py`**

```python
#!/usr/bin/env python3
"""Classify per-image failure modes for a YOLO model.

Modes: FP (prediction with no GT match), FN (GT with no prediction),
localization (correct class, IoU<0.5), class-confusion (IoU>=0.5, wrong class).

Usage:
    python failure_analysis.py <run_dir> [--data data.yaml] [--split val] [--top N]
    python failure_analysis.py <run_dir> --from-cache <json>     # for tests / re-runs
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_MODES = ("FP", "FN", "localization", "class-confusion")


def _iou_xywh(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax1, ay1, ax2, ay2 = ax - aw / 2, ay - ah / 2, ax + aw / 2, ay + ah / 2
    bx1, by1, bx2, by2 = bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    ua = max(1e-9, aw * ah + bw * bh - inter)
    return inter / ua


def _from_model(run_dir: Path, data_yaml: Path | None, split: str, iou_thr: float = 0.5) -> dict:
    from ultralytics import YOLO  # lazy
    if data_yaml is None:
        raise SystemExit("--data is required when not using --from-cache")
    data = _common.load_data_yaml(data_yaml)
    img_dir = data[split]
    lbl_dir = Path(str(img_dir).replace("/images/", "/labels/"))
    weights = _common.find_weights(run_dir)
    model = YOLO(str(weights))
    names = list(model.names.values()) if hasattr(model, "names") else []

    errors = []
    for img in sorted(Path(img_dir).rglob("*")):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        lbl = lbl_dir / img.relative_to(img_dir).with_suffix(".txt")
        gts = []
        if lbl.is_file():
            for line in lbl.read_text().splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    gts.append((int(float(parts[0])), tuple(float(p) for p in parts[1:5])))
        result = model.predict(str(img), verbose=False)[0]
        preds = []
        if result.boxes is not None:
            xywhn = result.boxes.xywhn.cpu().numpy()
            cls = result.boxes.cls.cpu().numpy().astype(int)
            conf = result.boxes.conf.cpu().numpy()
            for c, b, s in zip(cls, xywhn, conf):
                preds.append((int(c), tuple(b.tolist()), float(s)))

        gt_matched = [False] * len(gts)
        pred_matched = [False] * len(preds)
        for i, (pc, pb, ps) in enumerate(preds):
            best, best_iou = -1, 0.0
            for j, (gc, gb) in enumerate(gts):
                if gt_matched[j]:
                    continue
                iou = _iou_xywh(pb, gb)
                if iou > best_iou:
                    best, best_iou = j, iou
            if best >= 0 and best_iou >= iou_thr:
                gc = gts[best][0]
                if gc == pc:
                    gt_matched[best] = True
                    pred_matched[i] = True
                else:
                    gt_matched[best] = True
                    pred_matched[i] = True
                    errors.append({
                        "image": str(img),
                        "mode": "class-confusion",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "true_class": names[gc] if gc < len(names) else str(gc),
                        "iou": float(best_iou),
                    })
            elif best >= 0 and best_iou > 0:
                gt_matched[best] = True
                pred_matched[i] = True
                gc = gts[best][0]
                if gc == pc:
                    errors.append({
                        "image": str(img),
                        "mode": "localization",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "iou": float(best_iou),
                    })
                else:
                    errors.append({
                        "image": str(img),
                        "mode": "class-confusion",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "true_class": names[gc] if gc < len(names) else str(gc),
                        "iou": float(best_iou),
                    })
        for i, m in enumerate(pred_matched):
            if not m:
                pc, _, ps = preds[i]
                errors.append({
                    "image": str(img),
                    "mode": "FP",
                    "pred_class": names[pc] if pc < len(names) else str(pc),
                    "score": ps,
                })
        for j, m in enumerate(gt_matched):
            if not m:
                gc = gts[j][0]
                errors.append({
                    "image": str(img),
                    "mode": "FN",
                    "true_class": names[gc] if gc < len(names) else str(gc),
                })
    return {"errors": errors}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--split", default="val")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--from-cache", dest="from_cache", type=Path, default=None)
    args = p.parse_args(argv)

    payload = (
        json.loads(args.from_cache.read_text())
        if args.from_cache
        else _from_model(args.run_dir, args.data, args.split)
    )
    errors = payload.get("errors", [])

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    if not errors:
        _common.print_section(
            summary_line="no errors / no failures detected on this split",
            summary_bullets=["model matched all ground-truth boxes within IoU threshold"],
            findings="- no FP, FN, localization, or class-confusion errors recorded",
            recommendations="- (no action — verify your data path is correct if this is unexpected)",
        )
        return 0

    mode_counts = Counter(e["mode"] for e in errors)
    summary_bullets.append(", ".join(f"{m}={mode_counts.get(m, 0)}" for m in _MODES))

    findings.append("- error counts by mode: " + ", ".join(f"{m}={mode_counts.get(m, 0)}" for m in _MODES))

    # Per-class breakdown per mode
    for mode in _MODES:
        per_cls: Counter[str] = Counter()
        for e in errors:
            if e["mode"] != mode:
                continue
            key = e.get("pred_class") or e.get("true_class") or "?"
            per_cls[key] += 1
        if per_cls:
            findings.append(
                f"- {mode} per class: "
                + ", ".join(f"{k}={v}" for k, v in per_cls.most_common())
            )

    # Worst-N images per mode
    for mode in _MODES:
        per_img: Counter[str] = Counter()
        for e in errors:
            if e["mode"] == mode:
                per_img[e["image"]] += 1
        if per_img:
            top = per_img.most_common(args.top)
            rows = [f"  {count:4d}  {path}" for path, count in top]
            findings.append(f"- worst-{args.top} images for {mode}:\n" + "\n".join(rows))

    # Recommendations
    if mode_counts.get("FN", 0) > mode_counts.get("FP", 0) * 2:
        recs.append("- many FNs vs FPs: lower confidence threshold or add training data for missed classes")
    if mode_counts.get("FP", 0) > mode_counts.get("FN", 0) * 2:
        recs.append("- many FPs vs FNs: raise confidence threshold or harden negative samples")
    if mode_counts.get("localization", 0) > mode_counts.get("class-confusion", 0):
        recs.append("- localization > class-confusion: train at higher imgsz or refine bbox labels")
    else:
        recs.append("- class-confusion ≥ localization: review label consistency for confused class pairs")

    _common.print_section(
        summary_line=f"{sum(mode_counts.values())} errors across {len(_MODES)} modes",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/analyze/test_failure_analysis.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/scripts/failure_analysis.py tests/analyze/test_failure_analysis.py
git commit -m "feat(analyze): add failure_analysis.py with per-mode classification"
```

---

## Task 7: Author `SKILL.md`

**Files:**
- Create: `skills/analyze/SKILL.md`

- [ ] **Step 1: Write `skills/analyze/SKILL.md`**

```markdown
---
name: analyze
description: Use when the user wants to analyze, debug, or explain a YOLO model's training, validation, dataset, or predictions — questions like "why is mAP low", "is my dataset balanced", "did this overfit", "what classes does it confuse", "compare these two runs", "analyze loss", "find failure cases". Dispatches to bundled scripts under skills/analyze/scripts/.
---

# Analyze — end-to-end YOLO debugging

A reference + decision-tree skill. Five bundled scripts handle the work; this file tells you *which* to run and *how to read* what they emit.

## When to use

User mentions any of: analyze loss, training results, results.csv, overfitting, underfitting, mAP plateau, class imbalance, label sanity, dataset audit, weakest class, confusion matrix, false positives, failure cases, worst predictions, compare runs, regression vs previous run.

## Decision tree

| User question | Script |
|---|---|
| "Why did training do X?" / "is this overfit?" / "loss curve looks weird" | `training_curves.py <run_dir>` |
| "Which classes are weak?" / "what's the best confidence threshold?" / "per-class metrics" | `val_metrics.py <run_dir>` |
| "Is my dataset balanced?" / "are my labels OK?" / "check the data" | `dataset_audit.py <data.yaml>` |
| "Where does the model fail?" / "show me the worst predictions" / "FP vs FN breakdown" | `failure_analysis.py <run_dir> --data <data.yaml>` |
| "Compare these runs" / "did the new run regress?" | `compare_runs.py <run_a> <run_b> [...]` |

When in doubt, run `training_curves.py` first — it's cheap and frames the rest.

## How to invoke

All scripts live under `skills/analyze/scripts/`. From the plugin root:

```bash
python skills/analyze/scripts/training_curves.py runs/detect/train
python skills/analyze/scripts/val_metrics.py runs/detect/train
python skills/analyze/scripts/dataset_audit.py path/to/data.yaml
python skills/analyze/scripts/failure_analysis.py runs/detect/train --data path/to/data.yaml --top 20
python skills/analyze/scripts/compare_runs.py runs/detect/train runs/detect/train2
```

`val_metrics.py` and `failure_analysis.py` load `best.pt` and run `.val()` / `.predict()` — they need the same environment (and GPU if applicable) you used to train.

## Output contract

Every script prints exactly three sections, in order:

```
## SUMMARY
<one-line verdict>
- <top finding 1>
- <top finding 2>
- <top finding 3>

## FINDINGS
<numbers, tables, ASCII sparklines/histograms>

## RECOMMENDATIONS
- <actionable next step>
```

When responding to the user: lead with the SUMMARY, surface only the FINDINGS that bear on their question, and turn RECOMMENDATIONS into concrete next steps (often a follow-up `/ultralytics:train` or `/ultralytics:predict` invocation).

## Interpretation cheat-sheet

**Overfitting** — train loss decreasing while val loss rises or val mAP plateaus/declines in the last quarter of training. Fix: more augmentation, weight decay, fewer epochs, or earlier stopping.

**Underfitting** — train loss still trending down at the final epoch and final mAP50-95 < 0.3. Fix: train longer, larger model, higher LR.

**Plateau / LR-too-low** — both losses flat for the last third while LR has bottomed out. Fix: cosine restart or higher `lr0`.

**NaN / Inf** — divergence; usually too-high LR, AMP on unsupported hardware, or corrupt labels.

**Class imbalance** — `max/min` count ratio:
- < 3× — balanced
- 3–10× — mild, usually fine
- 10–50× — imbalanced, expect minority classes to underperform
- > 50× — severe; oversample, augment, or collect more data

**Bbox size red flags** — median normalized area < 0.001 (tiny boxes) suggests imgsz should be raised. Median > 0.5 suggests cropped or already-zoomed data.

**Confusion-matrix patterns** — high off-diagonals between visually similar classes ⇒ label-consistency or feature-resolution problem. High row to "background" ⇒ FN problem (missed detections). High column from "background" ⇒ FP problem.

**FP vs FN balance** — many FPs ⇒ raise conf threshold or add hard negatives. Many FNs ⇒ lower conf threshold or add training data for missed classes. Localization >> class-confusion ⇒ raise imgsz or refine bboxes; reverse ⇒ review labels.

## Heuristics applied automatically

- `training_curves.py` flags overfit / underfit / NaN and suggests fixes.
- `val_metrics.py` flags weakest classes as "needs more data" (low support + low recall) vs "needs better labels" (high support + low precision), and recommends a confidence threshold.
- `dataset_audit.py` flags imbalance ratios ≥ 10× and class divergence between train and val splits.
- `failure_analysis.py` recommends conf-threshold direction based on FP/FN ratio and imgsz changes based on localization/class-confusion ratio.
- `compare_runs.py` reports per-metric delta and surfaces `args.yaml` differences so you can isolate one variable at a time.
```

- [ ] **Step 2: Verify the skill is structurally valid by reading it back**

Run: `head -3 skills/analyze/SKILL.md`
Expected: starts with `---` frontmatter line.

- [ ] **Step 3: Commit**

```bash
git add skills/analyze/SKILL.md
git commit -m "docs(analyze): add SKILL.md with decision tree and interpretation cheat-sheet"
```

---

## Task 8: Plugin metadata + README

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

- [ ] **Step 1: Bump version and mention `analyze` in `.claude-plugin/plugin.json`**

Set `"version": "0.6.0"`. Update `description` to include `"analyze"` (e.g. `"Train, predict, export, validate datasets, and analyze YOLO models from inside Claude Code. Includes ModelBox flowunit index and a scaffolder for new custom flowunits."`). Update `"keywords"` to add `"analysis"` and `"debugging"`.

- [ ] **Step 2: Bump version in `.claude-plugin/marketplace.json`**

Set `"version": "0.6.0"` on the `ultralytics` entry. Update its `description` similarly.

- [ ] **Step 3: Add the new skill to `README.md`**

Find the "What you get" section and add a new bullet, in the same style as the existing skill bullets:

```markdown
- **Skill `/ultralytics:analyze`** — end-to-end YOLO model debugging. Five bundled scripts emit `SUMMARY / FINDINGS / RECOMMENDATIONS` reports for training-curve diagnostics (`training_curves.py`), per-class validation metrics (`val_metrics.py`), dataset balance and label sanity (`dataset_audit.py`), prediction failure clustering (`failure_analysis.py`), and run-vs-run comparison (`compare_runs.py`).
```

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "chore: bump plugin to 0.6.0; document /ultralytics:analyze skill"
```

---

## Task 9: Full test sweep

- [ ] **Step 1: Run the entire analyze test suite**

Run: `pytest tests/analyze -v`
Expected: all tests pass (≈27 tests across 6 files).

- [ ] **Step 2: Sanity-check scripts can be invoked with `--help`**

```bash
for f in skills/analyze/scripts/*.py; do
  [ "$(basename "$f")" = "_common.py" ] && continue
  [ "$(basename "$f")" = "__init__.py" ] && continue
  echo "--- $f ---"
  python "$f" --help
done
```

Expected: each prints argparse help without traceback.

- [ ] **Step 3: If anything fails, fix and amend the relevant per-script commit; otherwise nothing to commit here.**

---

## Task 10: Manual smoke test on real run (optional but recommended)

The `pose` GPU server has a real YOLO setup. After all unit tests pass, validate the model-dependent scripts against a real run.

- [ ] **Step 1: Pick or create a real run on `pose`**

```bash
ssh pose 'ls runs/detect 2>/dev/null | tail'
```

If empty, run a tiny training job: `ssh pose 'cd ~/yolo && yolo detect train model=yolo11n.pt data=coco8.yaml epochs=3 imgsz=320'`.

- [ ] **Step 2: Sync the analyze scripts to the server and run them**

```bash
rsync -a skills/analyze/scripts/ pose:~/analyze-scripts/
ssh pose 'cd ~/yolo && python ~/analyze-scripts/training_curves.py runs/detect/train'
ssh pose 'cd ~/yolo && python ~/analyze-scripts/val_metrics.py runs/detect/train'
ssh pose 'cd ~/yolo && python ~/analyze-scripts/failure_analysis.py runs/detect/train --data coco8.yaml --top 5'
ssh pose 'cd ~/yolo && python ~/analyze-scripts/dataset_audit.py $(python -c "import ultralytics, pathlib; print(pathlib.Path(ultralytics.__file__).parent / \"cfg/datasets/coco8.yaml\")")'
```

Expected: each prints the three-section report. Note any traceback or contract violation and fix in a follow-up commit before merging.

- [ ] **Step 3: Nothing to commit if the smoke test passes; otherwise fix forward.**

---

## Self-review summary

- Spec coverage — every section of the design spec maps to a task: `_common`/scaffolding (T1), training curves (T2), dataset audit (T3), compare runs (T4), val metrics (T5), failure analysis (T6), SKILL.md trigger + cheat-sheet + output contract (T7), plugin metadata bump (T8), test sweep (T9), real-run smoke test (T10).
- Placeholder scan — every code step contains complete, self-contained code; commands have expected output; no "TBD" or "similar to Task N".
- Type consistency — `_common.print_section` signature matches every caller in T2/T3/T4/T5/T6 (`summary_line`, `summary_bullets`, `findings`, `recommendations`). Cache JSON shapes in T5/T6 match what the test fixtures construct.
