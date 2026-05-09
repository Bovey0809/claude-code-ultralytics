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
