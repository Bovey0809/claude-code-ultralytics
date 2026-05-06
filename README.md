# Ultralytics Claude Code Plugin

Train, predict, export, and validate datasets with [Ultralytics YOLO](https://docs.ultralytics.com) from inside [Claude Code](https://docs.claude.com/claude-code).

All commands and the skill are namespaced under `/ultralytics:`.

## What you get

- **Skill `/ultralytics:yolo`** — concise reference Claude consults whenever you mention YOLO, dataset YAMLs, model variants, or export formats.
- **`/ultralytics:train`** — wraps `yolo train`. Hybrid args: pass `key=value` tokens through, or describe what you want in natural language.
- **`/ultralytics:predict`** — wraps `yolo predict`. Image, directory, video, URL, or webcam.
- **`/ultralytics:export`** — wraps `yolo export`. ONNX, CoreML, TensorRT, TFLite, OpenVINO, …
- **`/ultralytics:dataset-check`** — read-only validator for `data.yaml`. Catches missing paths, label/class mismatches, empty splits.

## Requirements

- `pip install ultralytics`
- Python 3.8+
- Claude Code

## Install

### From the marketplace (recommended)

In Claude Code:

```
/plugin marketplace add Bovey0809/claude-code-ultralytics
/plugin install ultralytics@ultralytics-plugins
```

Or from a shell:

```bash
claude plugin marketplace add Bovey0809/claude-code-ultralytics
claude plugin install ultralytics@ultralytics-plugins
```

### Local development

Clone anywhere, then load with `--plugin-dir`:

```bash
git clone https://github.com/Bovey0809/claude-code-ultralytics.git
claude --plugin-dir ./claude-code-ultralytics
```

Validate the manifest:

```bash
claude plugin validate ./claude-code-ultralytics
```

After editing plugin files in a running session, run `/reload-plugins` to pick up changes.

## Smoke test

In Claude Code, in a scratch directory. First, fetch a local copy of `coco8.yaml` for `/ultralytics:dataset-check`:

```bash
python3 -c "from ultralytics.utils import ROOT; import shutil; shutil.copy(ROOT/'cfg/datasets/coco8.yaml', '.')"
```

Then:

1. `/ultralytics:dataset-check coco8.yaml` — should pass with a NOTES block (the YAML's `path` resolves against Ultralytics' `datasets_dir`, not the cwd).
2. `/ultralytics:train model=yolo11n.pt data=coco8.yaml epochs=1` — completes in a minute on GPU, longer on CPU.
3. `/ultralytics:predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg` — produces an annotated image under `runs/detect/predict/`.
4. `/ultralytics:export model=yolo11n.pt format=onnx` — produces `yolo11n.onnx`.

## Remote GPU execution

Most YOLO work needs a GPU. Set a remote in either of two ways:

**Env vars (per-shell):**

```bash
export ULTRALYTICS_REMOTE=pose      # ssh host alias
export ULTRALYTICS_WORKDIR=~/yolo   # remote working directory (optional)
```

**`.ultralytics.yml` (per-project, in your repo or any ancestor of cwd):**

```yaml
remote: pose
workdir: ~/yolo
```

When set, `/ultralytics:train`, `/ultralytics:predict`, and `/ultralytics:export` wrap their `yolo` invocations as `ssh <remote> 'bash -lc "cd <workdir> && yolo …"'`. `/ultralytics:dataset-check` always runs locally (it's a static YAML validator).

Datasets, local `source=` files, and local `model=` weights must already exist on the remote — Claude will offer `rsync` commands when something is missing or when results are ready to pull back. URL sources and Ultralytics' auto-downloaded named datasets (e.g., `coco8.yaml`) work without manual sync.

## Run naming and experiment log

`/ultralytics:train` synthesizes a meaningful run name when `name=` isn't supplied — `runs/detect/20260506-1432_yolo11n_coco8_e100_b16_a1b2c3d/` instead of `runs/detect/train2/`. Pass `tag=<slug>` to append a label (e.g. `tag=lr-sweep-3`). Pass `name=<your-name>` to override entirely.

Opt in to a markdown experiment log by adding to `.ultralytics.yml`:

```yaml
experiment_log: runs/EXPERIMENTS.md
```

Each `/ultralytics:train` and `/ultralytics:export` then appends a row with the command, parsed metrics (mAP50-95, mAP50), weights path, and a `_(fill in)_` notes column you edit later. The log is always local, even when execution is remote.

## Out of scope (v1)

`yolo tune`, tracking, benchmarks, solutions, Hub login, MCP server.
