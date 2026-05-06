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
