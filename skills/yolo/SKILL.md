---
name: yolo
description: Use when the user mentions Ultralytics or YOLO — training a detector/segmenter/classifier/pose/OBB model, dataset YAML files, .pt weights, predicting on images/video, or exporting to ONNX/CoreML/TensorRT/TFLite/OpenVINO. Provides the conceptual model and dispatches to the matching slash command (/train, /predict, /export, /dataset-check) for actions.
---

# Ultralytics YOLO

A concise reference for working with Ultralytics YOLO via the `yolo` CLI. The four slash commands (`/train`, `/predict`, `/export`, `/dataset-check`) do the work; this skill explains the concepts and dispatches.

## When to use

The user mentions: Ultralytics, YOLO, `yolo11n/s/m/l/x` (or `yolov8`/`yolov9`/`yolov10`), training a detector, `data.yaml`, `.pt` weights, ONNX/CoreML/TensorRT/TFLite/OpenVINO export, segmentation/classification/pose/OBB tasks.

## Core mental model

Every Ultralytics workflow is `model + data + task → operation`:

- **model** — a `.pt` file or pretrained name (`yolo11n.pt`, `yolo11s-seg.pt`, `yolo11m-cls.pt`, `yolo11l-pose.pt`, `yolo11x-obb.pt`).
- **task** — inferred from the model suffix: no suffix = `detect`, `-seg` = `segment`, `-cls` = `classify`, `-pose` = `pose`, `-obb` = `obb`.
- **data** — for detect/segment/pose/obb: a `data.yaml`. For classify: a directory in ImageFolder layout.
- **operation** — `train`, `val`, `predict`, `export`, `track`, `benchmark`.

## Key arguments

| arg | meaning | typical |
|---|---|---|
| `model` | weights path or pretrained name | `yolo11n.pt` |
| `data` | dataset yaml or class-dir | `coco8.yaml` |
| `epochs` | training epochs | `100` |
| `imgsz` | input size | `640` |
| `batch` | batch size; `-1` = auto | `16` |
| `device` | `0`, `0,1`, `cpu`, `mps` | auto |
| `project` / `name` | output dir | `runs/detect/train` |
| `resume` | resume last run | `False` |
| `conf` | predict confidence threshold | `0.25` |
| `source` | predict input (img/dir/video/URL/`0`) | — |
| `format` | export target | `onnx` |

## Dataset YAML shape

Minimum viable:

```yaml
path: /abs/or/rel/dataset/root
train: images/train
val: images/val
names:
  0: person
  1: car
```

Labels live alongside images at `labels/train/...txt` and `labels/val/...txt`. Each line: `class_id cx cy w h` (normalized 0–1).

## Command dispatch rules

When the user asks to:

- **train a model** → invoke `/train` (parses args or asks for `model`/`data`/`epochs`).
- **run inference / predict / detect on an image** → invoke `/predict`.
- **export to ONNX / CoreML / TensorRT / etc.** → invoke `/export`.
- **validate a dataset / check data.yaml** → invoke `/dataset-check`.

Pass any `key=value` tokens the user already provided through to the command verbatim.

## Common pitfalls

- **CUDA OOM** → lower `batch` (try `8`, `4`) or `imgsz` (`512`, `416`).
- **Class count mismatch** → labels reference a `class_id` higher than `len(names) - 1`. Run `/dataset-check`.
- **Dataset path errors** → `path` in YAML can be relative; `train`/`val` are joined to `path`. Prefer absolute `path` if running from different cwds.
- **`yolo` command not found** → `pip install ultralytics`.
- **CLI vs Python** — `yolo train …` and `from ultralytics import YOLO; YOLO('yolo11n.pt').train(...)` are equivalent. The slash commands use the CLI.
- **Long trainings** — runs may take hours. The user can Ctrl-C; weights are saved per epoch under `runs/<task>/<name>/weights/`.

## What this skill does NOT cover (v1)

`yolo tune` (hyperparameter search), tracking, benchmarks, solutions, Hub login. Defer to upstream docs at https://docs.ultralytics.com.
