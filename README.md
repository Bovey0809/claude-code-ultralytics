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

## Install (local dev)

Clone anywhere, then load with `--plugin-dir`:

```bash
git clone https://github.com/Bovey0809/claude-code-ultralytics.git
claude --plugin-dir ./claude-code-ultralytics
```

Validate the manifest at any time:

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

## Out of scope (v1)

`yolo tune`, tracking, benchmarks, solutions, Hub login, MCP server.
