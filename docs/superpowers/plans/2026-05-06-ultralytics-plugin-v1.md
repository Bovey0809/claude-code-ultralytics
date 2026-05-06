# Ultralytics Claude Code Plugin v1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Claude Code plugin (`ultralytics`) with one teaching skill (`yolo`) and four slash commands (`/train`, `/predict`, `/export`, `/dataset-check`) that wrap the Ultralytics `yolo` CLI.

**Architecture:** Pure markdown + JSON plugin. The skill provides understanding; commands are thin Bash wrappers using a hybrid argument pattern (`key=value` pass-through, otherwise natural-language parse). No bundled scripts, no MCP server, no hooks.

**Tech Stack:** Claude Code plugin format, markdown SKILL.md and command files, Bash, `yolo` CLI from the `ultralytics` PyPI package.

---

## File Structure

```
claude-code-ultralytics/
├── .claude-plugin/plugin.json       # plugin manifest
├── README.md                        # install + smoke test instructions
├── skills/yolo/SKILL.md             # teaching skill (~150 lines)
└── commands/
    ├── train.md
    ├── predict.md
    ├── export.md
    └── dataset-check.md
```

Each file has a single responsibility. Commands are independent — none import the others. The skill is a passive reference Claude consults; commands are active dispatch points.

---

### Task 1: Plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Write the manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "ultralytics",
  "version": "0.1.0",
  "description": "Train, predict, export, and validate datasets with Ultralytics YOLO from inside Claude Code.",
  "author": {
    "name": "Ultralytics",
    "url": "https://ultralytics.com"
  },
  "homepage": "https://github.com/ultralytics/ultralytics",
  "keywords": ["yolo", "ultralytics", "computer-vision", "object-detection"]
}
```

- [ ] **Step 2: Verify JSON parses**

Run: `python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "Add plugin manifest"
```

---

### Task 2: The `yolo` skill

**Files:**
- Create: `skills/yolo/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `skills/yolo/SKILL.md`:

```markdown
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
```

- [ ] **Step 2: Verify frontmatter parses**

Run: `python3 -c "import re,sys; t=open('skills/yolo/SKILL.md').read(); m=re.match(r'^---\n(.*?)\n---', t, re.S); assert m, 'no frontmatter'; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add skills/yolo/SKILL.md
git commit -m "Add yolo teaching skill"
```

---

### Task 3: `/train` command

**Files:**
- Create: `commands/train.md`

- [ ] **Step 1: Write the command**

Create `commands/train.md`:

````markdown
---
description: Train an Ultralytics YOLO model. Accepts key=value args (model=, data=, epochs=, …) or natural language.
argument-hint: [model=yolo11n.pt] [data=coco8.yaml] [epochs=100] [imgsz=640] [batch=16] [device=0]
---

# /train

Train a YOLO model via the `yolo` CLI.

## Argument parsing

The user input is in `$ARGUMENTS`.

1. **If `$ARGUMENTS` contains tokens matching `key=value`** (e.g., `model=yolo11n.pt data=coco8.yaml epochs=10`), pass them through verbatim.
2. **Otherwise**, parse as natural language to extract `model`, `data`, `epochs`. Ask the user for any essentials still missing.

## Essentials and defaults

- `model` — required. Default if user agrees: `yolo11n.pt`.
- `data` — required. No default; must be provided.
- `epochs` — required. Default if user agrees: `100`.
- `imgsz` — default `640`.
- `batch` — default `16`.

## Preflight checks (do these before running)

1. **`yolo` on PATH:** run `command -v yolo`. If empty, instruct the user to `pip install ultralytics` and stop.
2. **`data` yaml exists:** if `data` ends in `.yaml`/`.yml` and is a local path, confirm it exists. If it doesn't exist locally, note that Ultralytics may auto-download named datasets like `coco8.yaml` and proceed.
3. **GPU check:** run `python3 -c "import torch; print(torch.cuda.is_available())"`. If `False`, warn the user that training on CPU will be slow and ask whether to continue.
4. **Run `/dataset-check` logic on the `data` yaml** if it's a local file (delegate to commands/dataset-check.md guidance — at minimum, confirm `train` and `val` keys resolve).

## Execution

Run via Bash, streaming output:

```bash
yolo train model=<MODEL> data=<DATA> epochs=<EPOCHS> imgsz=<IMGSZ> batch=<BATCH> [<EXTRA_KV>]
```

After the command completes, report the run directory (look for `Results saved to runs/<task>/<name>` in stdout).

## Notes for the user

- Long runs: training may take hours. Weights are saved per-epoch under `runs/<task>/<name>/weights/`. The user can Ctrl-C and resume with `resume=True`.
- If the run fails with CUDA OOM, suggest lowering `batch` (e.g., `8`, `4`) or `imgsz` (e.g., `512`).
````

- [ ] **Step 2: Commit**

```bash
git add commands/train.md
git commit -m "Add /train command"
```

---

### Task 4: `/predict` command

**Files:**
- Create: `commands/predict.md`

- [ ] **Step 1: Write the command**

Create `commands/predict.md`:

````markdown
---
description: Run YOLO inference on an image, directory, video, URL, or webcam. Accepts key=value args or natural language.
argument-hint: [model=yolo11n.pt] [source=path/url/0] [conf=0.25] [save=True]
---

# /predict

Run inference with a YOLO model.

## Argument parsing

The user input is in `$ARGUMENTS`.

1. If it contains `key=value` tokens, pass them through.
2. Otherwise, parse natural language to extract `model` and `source`. Ask the user for whichever essential is missing.

## Essentials and defaults

- `model` — required. Default if user agrees: `yolo11n.pt`.
- `source` — required. No default.
  - File path (image or video), directory, URL, or `0` for webcam.
- `conf` — default `0.25`.
- `save` — default `True` (saves annotated outputs).

## Preflight

- `command -v yolo`; if empty, instruct `pip install ultralytics` and stop.

## Execution

```bash
yolo predict model=<MODEL> source=<SOURCE> conf=<CONF> save=<SAVE> [<EXTRA_KV>]
```

After the command completes, locate the line `Results saved to runs/<task>/predict<N>` in stdout and report the directory to the user.
````

- [ ] **Step 2: Commit**

```bash
git add commands/predict.md
git commit -m "Add /predict command"
```

---

### Task 5: `/export` command

**Files:**
- Create: `commands/export.md`

- [ ] **Step 1: Write the command**

Create `commands/export.md`:

````markdown
---
description: Export a YOLO .pt model to ONNX, CoreML, TensorRT, TFLite, OpenVINO, etc.
argument-hint: model=path/to/best.pt format=onnx|coreml|engine|tflite|openvino|torchscript|saved_model|pb|paddle|ncnn
---

# /export

Export a trained YOLO `.pt` model to another runtime format.

## Argument parsing

The user input is in `$ARGUMENTS`.

1. If it contains `key=value` tokens, pass them through.
2. Otherwise, parse natural language to extract `model` and `format`.

## Essentials

- `model` — required. Path to a `.pt` file, or a pretrained name like `yolo11n.pt`.
- `format` — required. If omitted, list the supported formats and ask the user to pick:
  - `onnx`, `torchscript`, `coreml`, `engine` (TensorRT), `tflite`, `openvino`, `saved_model`, `pb`, `paddle`, `ncnn`.

## Preflight

- `command -v yolo`; if empty, instruct `pip install ultralytics` and stop.
- Note that some formats require extra deps (e.g., `engine` needs TensorRT, `coreml` needs `coremltools`). If the user hasn't installed them, `yolo export` will print a clear error — surface it.

## Execution

```bash
yolo export model=<MODEL> format=<FORMAT> [<EXTRA_KV>]
```

After completion, locate the artifact path in stdout (lines like `... export success ✅ ... saved as '<path>'`) and report it to the user.
````

- [ ] **Step 2: Commit**

```bash
git add commands/export.md
git commit -m "Add /export command"
```

---

### Task 6: `/dataset-check` command

**Files:**
- Create: `commands/dataset-check.md`

- [ ] **Step 1: Write the command**

Create `commands/dataset-check.md`:

````markdown
---
description: Validate an Ultralytics dataset YAML — checks paths resolve, splits have images, labels exist, class ids match `names`. Pure validation, does not invoke yolo.
argument-hint: [path/to/data.yaml]
---

# /dataset-check

Validate a YOLO dataset YAML before training. Pure read-only — does **not** invoke `yolo`.

## Argument parsing

`$ARGUMENTS` is either a path to a `.yaml` / `.yml` file, or empty.

If empty: search the cwd for `data.yaml`, `dataset.yaml`, or any single `*.yaml` at the top level. If exactly one candidate, use it; otherwise ask the user which file to check.

## Validation

Run this Python one-liner via Bash, substituting `<YAML_PATH>`:

```bash
python3 - <<'PY'
import os, sys, glob, yaml, random
yaml_path = "<YAML_PATH>"
problems = []
ok = []

try:
    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)
except Exception as e:
    print(f"FAIL: cannot parse YAML: {e}")
    sys.exit(1)

root = cfg.get("path", os.path.dirname(os.path.abspath(yaml_path)))
if not os.path.isabs(root):
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(yaml_path)), root))

if not os.path.isdir(root):
    problems.append(f"path '{root}' is not a directory")
else:
    ok.append(f"path resolves: {root}")

names = cfg.get("names")
if names is None:
    problems.append("missing 'names'")
else:
    n_classes = len(names) if isinstance(names, (list, dict)) else 0
    ok.append(f"names: {n_classes} classes")

max_class_seen = -1
for split in ("train", "val"):
    rel = cfg.get(split)
    if rel is None:
        problems.append(f"missing '{split}' key")
        continue
    split_dir = rel if os.path.isabs(rel) else os.path.join(root, rel)
    if not os.path.isdir(split_dir):
        # could be a .txt list file
        if os.path.isfile(split_dir):
            ok.append(f"{split}: list file {split_dir}")
            continue
        problems.append(f"{split} '{split_dir}' does not exist")
        continue
    imgs = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
        imgs += glob.glob(os.path.join(split_dir, "**", ext), recursive=True)
    if not imgs:
        problems.append(f"{split}: no images found in {split_dir}")
        continue
    ok.append(f"{split}: {len(imgs)} images")
    labels_dir = split_dir.replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)
    if labels_dir == split_dir:
        labels_dir = os.path.join(os.path.dirname(split_dir), "labels", os.path.basename(split_dir))
    if not os.path.isdir(labels_dir):
        problems.append(f"{split}: labels dir not found at {labels_dir}")
        continue
    sample = random.sample(imgs, min(20, len(imgs)))
    empties = 0
    for img in sample:
        stem = os.path.splitext(os.path.basename(img))[0]
        lbl = os.path.join(labels_dir, stem + ".txt")
        if not os.path.isfile(lbl):
            empties += 1
            continue
        try:
            with open(lbl) as lf:
                for line in lf:
                    parts = line.split()
                    if parts:
                        max_class_seen = max(max_class_seen, int(parts[0]))
        except Exception as e:
            problems.append(f"{split}: cannot read {lbl}: {e}")
    if empties:
        problems.append(f"{split}: {empties}/{len(sample)} sampled images missing label files")

if isinstance(names, (list, dict)) and max_class_seen >= 0:
    n_classes = len(names)
    if max_class_seen >= n_classes:
        problems.append(f"label class id {max_class_seen} >= len(names)={n_classes}")
    else:
        ok.append(f"max class id seen: {max_class_seen} (within {n_classes})")

print("CHECKS PASSED:")
for line in ok:
    print(f"  - {line}")
if problems:
    print("PROBLEMS:")
    for line in problems:
        print(f"  - {line}")
    sys.exit(1)
print("OK")
PY
```

## Reporting

- If the script exits 0 with `OK`, report success and list the passed checks.
- If it exits non-zero, report each problem and suggest fixes:
  - `path` not a directory → check `path:` is correct relative to YAML location.
  - missing `train`/`val` key → add it.
  - no images → check the split subdirectory.
  - labels dir not found → Ultralytics expects `images/<split>/` paired with `labels/<split>/`.
  - missing label files → either remove unlabeled images or create empty `.txt` for negatives.
  - class id ≥ `len(names)` → either expand `names` or fix labels.

## Preflight

- Requires `python3` and `pyyaml`. `pyyaml` is installed by `pip install ultralytics`. If import fails, instruct: `pip install pyyaml`.
````

- [ ] **Step 2: Commit**

```bash
git add commands/dataset-check.md
git commit -m "Add /dataset-check command"
```

---

### Task 7: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README**

Create `README.md`:

````markdown
# Ultralytics Claude Code Plugin

Train, predict, export, and validate datasets with [Ultralytics YOLO](https://docs.ultralytics.com) from inside [Claude Code](https://docs.claude.com/claude-code).

## What you get

- **Skill `yolo`** — concise reference Claude consults whenever you mention YOLO, dataset YAMLs, model variants, or export formats.
- **`/train`** — wraps `yolo train`. Hybrid args: pass `key=value` tokens through, or describe what you want in natural language.
- **`/predict`** — wraps `yolo predict`. Image, directory, video, URL, or webcam.
- **`/export`** — wraps `yolo export`. ONNX, CoreML, TensorRT, TFLite, OpenVINO, …
- **`/dataset-check`** — read-only validator for `data.yaml`. Catches missing paths, label/class mismatches, empty splits.

## Requirements

- `pip install ultralytics`
- Python 3.8+

## Install (local dev)

```bash
git clone https://github.com/ultralytics/claude-code-ultralytics.git ~/.claude/plugins/ultralytics
```

Then restart Claude Code. The skill and commands become available automatically.

## Smoke test

In Claude Code, in any directory:

1. `/dataset-check coco8.yaml` — uses the bundled coco8 dataset; should pass.
2. `/train model=yolo11n.pt data=coco8.yaml epochs=1` — completes in a minute on GPU, longer on CPU.
3. `/predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg` — produces an annotated image under `runs/detect/predict/`.
4. `/export model=yolo11n.pt format=onnx` — produces `yolo11n.onnx`.

## Out of scope (v1)

`yolo tune`, tracking, benchmarks, solutions, Hub login, MCP server.
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Add README with install and smoke test instructions"
```

---

### Task 8: End-to-end smoke test

**Files:** none (manual verification)

- [ ] **Step 1: Symlink the plugin into Claude Code**

```bash
ln -snf "$PWD" ~/.claude/plugins/ultralytics
```

- [ ] **Step 2: Verify ultralytics is installed**

Run: `command -v yolo && yolo version`
Expected: prints a path and a version string. If not, `pip install ultralytics`.

- [ ] **Step 3: Restart Claude Code, then run each smoke step from README**

Cycle through:

1. `/dataset-check coco8.yaml` → expect `OK` and a list of passed checks.
2. `/train model=yolo11n.pt data=coco8.yaml epochs=1` → expect "Results saved to runs/detect/train" line.
3. `/predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg` → expect "Results saved to runs/detect/predict" line; the directory contains `bus.jpg` annotated.
4. `/export model=yolo11n.pt format=onnx` → expect `yolo11n.onnx` file in cwd.

- [ ] **Step 4: Final commit (if any tweaks needed during smoke test)**

```bash
git add -A
git commit -m "Smoke test fixes" || echo "nothing to commit"
```

---

## Self-Review

- **Spec coverage:** plugin layout (Task 1), skill (Task 2), four commands (Tasks 3–6), smoke tests (Task 8). README is extra but useful. ✓
- **Placeholders:** none. Every code/markdown block is complete. ✓
- **Type/name consistency:** `yolo11n.pt`, `coco8.yaml`, `model`/`data`/`epochs`/`source`/`format` used uniformly across all command files and the skill. ✓
- **Pitfalls coverage:** CUDA OOM, dataset paths, `yolo` not found, class mismatch — all appear in skill and referenced in commands. ✓
