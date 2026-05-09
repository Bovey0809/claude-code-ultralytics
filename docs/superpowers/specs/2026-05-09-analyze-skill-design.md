# `/ultralytics:analyze` skill — design

**Date:** 2026-05-09
**Status:** Approved for implementation planning
**Plugin:** claude-code-ultralytics

## Purpose

Provide an Ultralytics-YOLO-specific skill that helps Claude analyze and debug a model end-to-end: training dynamics, validation metrics, dataset quality, prediction failures, and run-vs-run comparison. The skill ships bundled Python scripts that emit structured stdout text (no PNGs, no HTML); Claude reads the stdout and synthesizes findings for the user.

## Non-goals (v1)

- HTML or markdown report generation, dashboards, persisted plots
- Frameworks other than Ultralytics YOLO (no PyTorch-generic, no TF, no Keras)
- Live training monitoring (analysis is post-hoc against a finished or in-progress `runs/` directory)
- Hyperparameter recommendations beyond simple heuristics (LR, conf threshold, augmentation hints)
- New slash commands — scripts are invoked directly by Claude

## Scope

End-to-end model debugging for YOLO, covering:

1. Training-curve diagnostics (loss/mAP from `results.csv`)
2. Validation metrics deep-dive (per-class P/R/mAP, confusion matrix, PR/F1 curves)
3. Dataset balance and quality (class distribution, bbox stats, label sanity, near-duplicate detection)
4. Prediction / failure analysis (FP / FN / localization / class-confusion clustering, worst-N images)
5. Model comparison across two or more `runs/` directories

## Layout

```
skills/analyze/
  SKILL.md
  scripts/
    _common.py
    training_curves.py
    val_metrics.py
    dataset_audit.py
    failure_analysis.py
    compare_runs.py
```

The skill is registered as `ultralytics:analyze` with description triggers on phrases such as: "analyze loss", "analyze training", "training results", "data balance", "data quality", "label sanity", "failure cases", "why is mAP low", "compare runs", "per-class accuracy", "confusion matrix interpretation".

## SKILL.md contents

- **When to use** — trigger phrases and a short decision tree (training-curve question? → `training_curves.py`; per-class weak? → `val_metrics.py`; suspect data? → `dataset_audit.py`; need failure breakdown? → `failure_analysis.py`; comparing runs? → `compare_runs.py`).
- **Script index** — one-line description and example invocation for each script.
- **Interpretation cheat-sheet** — short reference Claude consults while explaining results:
  - Overfitting signs in `results.csv` (train loss ↓, val loss ↑ or val mAP plateau/decline)
  - Underfitting signs (both losses still trending down at last epoch; low train mAP)
  - Plateau / LR-too-low signs
  - NaN / divergence patterns
  - Class-imbalance thresholds (e.g. ratio max/min > 10× flagged; > 50× critical)
  - Bbox-size red flags (median area < 0.1% of image, or > 50% of images with tiny boxes)
  - Confusion-matrix top-confusion patterns
- **Output contract** — every script prints `## SUMMARY`, `## FINDINGS`, `## RECOMMENDATIONS`. Claude is instructed to surface SUMMARY first, then drill into FINDINGS only when relevant.

## Scripts

Each script is standalone, uses `argparse`, and depends only on packages already pulled in by `ultralytics` (pandas, numpy, PIL, ultralytics itself). All scripts print to stdout; ASCII sparklines/histograms are inline. None write files.

### `_common.py`

Tiny shared helpers; not a framework. Functions:

- `find_results_csv(run_dir) -> Path`
- `find_weights(run_dir, prefer="best") -> Path`
- `load_data_yaml(path) -> dict` (resolves `path:`, `train:`, `val:`, `test:` to absolute paths)
- `ascii_sparkline(values, width=40) -> str`
- `ascii_histogram(values, bins=10, width=40) -> str`
- `print_section(title, body)` (enforces the SUMMARY/FINDINGS/RECOMMENDATIONS layout)

### `training_curves.py <run_dir>`

Parses `results.csv`. Reports:

- Best epoch (by val mAP50-95) and metric values at best vs final epoch
- Trend per metric: train loss components (box/cls/dfl), val loss, mAP50, mAP50-95 — each as ASCII sparkline plus monotonicity classification (decreasing / plateau / increasing / oscillating)
- Overfitting heuristic: train loss decreasing while val loss increasing or val mAP plateaued for last N epochs
- Underfitting heuristic: train loss still decreasing at last epoch and final train mAP < threshold
- NaN / Inf detection in any column, with first epoch where it occurred
- LR schedule sanity: log final LR and whether plateau coincides with LR floor

### `val_metrics.py <run_dir> [--data data.yaml]`

Loads `best.pt`, runs `model.val()` (or re-uses cached `results.csv` per-class block when present). Reports:

- Overall P / R / mAP50 / mAP50-95
- Per-class table sorted by mAP50-95 ascending (weakest first); columns: class, support, P, R, mAP50, mAP50-95
- Top-K confusion-matrix off-diagonals (which class gets confused with which, with counts)
- Confidence-threshold sweep: for confs `[0.1, 0.2, ... 0.9]`, F1 at each, suggested optimal conf
- Recommendations: classes flagged for "needs more data" (low support + low recall) vs "needs better labels" (high support + low precision)

### `dataset_audit.py <data.yaml>`

Pure dataset analysis, no model required. Reports:

- Class distribution per split (train/val/test): counts, percentages, max/min ratio, imbalance verdict
- Bbox geometry: ASCII histogram of normalized area, aspect ratio; flags if median area < 0.001 or > 0.5
- Image resolution: distinct sizes, min/median/max
- Label sanity: out-of-bounds coordinates, zero-area boxes, duplicate boxes within an image, images-without-labels count, labels-without-images count
- Near-duplicate detection via perceptual hash (PIL `Image.thumbnail` + dhash); reports clusters with ≥ 2 members
- Train/val class-set divergence: classes present in val but absent from train (and vice versa)

### `failure_analysis.py <run_dir> [--data data.yaml] [--top N=20] [--split val]`

Runs the model on the requested split, matches predictions to ground truth (IoU 0.5 default), classifies each error:

- **FP** — prediction with no GT match
- **FN** — GT with no prediction match
- **Localization** — correct class, IoU < 0.5
- **Class-confusion** — IoU ≥ 0.5 but wrong class

Reports per-mode counts, per-class breakdown of each mode, and the worst-N image paths per mode (ranked by error count or confidence×IoU-deficit). Prints absolute file paths so the user can open them; does not save annotated copies.

### `compare_runs.py <run_a> <run_b> [<run_c> ...]`

Loads `results.csv` (and per-class blocks where available) from each run. Reports:

- Side-by-side overall metrics table (P / R / mAP50 / mAP50-95, best-epoch values)
- Per-class delta table sorted by absolute change (regressions and improvements)
- Training-stability comparison: epoch-to-epoch val-mAP variance, time-to-best-epoch
- Run metadata diff (model variant, imgsz, batch, epochs, optimizer, lr0) read from `args.yaml`

## Output contract (enforced by `_common.print_section`)

Every script prints exactly three sections in this order:

```
## SUMMARY
<one-line verdict>
- <top finding 1>
- <top finding 2>
- <top finding 3>

## FINDINGS
<structured bullets with concrete numbers, tables, ASCII sparklines>

## RECOMMENDATIONS
- <actionable next step, e.g. "lower lr0 to 0.005", "augment class 7", "raise conf to 0.35">
```

The skill instructs Claude to (1) read the SUMMARY, (2) decide which FINDINGS are relevant to the user's question, and (3) surface RECOMMENDATIONS as concrete next steps.

## Dependencies

No new dependencies. Everything runs against what `pip install ultralytics` already provides: `pandas`, `numpy`, `PIL`, `ultralytics`. `dataset_audit.py` perceptual-hash uses PIL only.

## Testing

Each script must be runnable in isolation against a fixture `runs/` directory. Manual verification on an existing trained YOLO run (e.g. on the `pose` GPU server) is acceptable for v1; automated tests are out of scope.

## Open questions

None remaining — design approved 2026-05-09.
