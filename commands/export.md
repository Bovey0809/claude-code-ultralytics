---
description: Export a YOLO .pt model to ONNX, CoreML, TensorRT, TFLite, OpenVINO, etc.
argument-hint: "model=path/to/best.pt format=onnx|coreml|engine|tflite|openvino|torchscript|saved_model|pb|paddle|ncnn"
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

- **Detect remote.** Read `ULTRALYTICS_REMOTE` env var; if unset, search cwd and ancestors for `.ultralytics.yml` and read its `remote`/`workdir` keys. If a remote is configured, wrap every Bash invocation below as `ssh <remote> 'bash -lc "cd <workdir> && <cmd>"'`. See the "Remote execution" section of the `yolo` skill.
- `command -v yolo` (wrapped if remote); if empty, instruct `pip install ultralytics` and stop.
- **`model` location.** When running remote, `<MODEL>` must resolve on the remote — either a pretrained name like `yolo11n.pt`, an absolute path on the remote, or a path relative to `<workdir>`. If the user gave a local path that doesn't exist on the remote, ask whether to `rsync` the `.pt` up first.
- Note that some formats require extra deps (e.g., `engine` needs TensorRT, `coreml` needs `coremltools`). `coreml` in particular only runs on macOS — incompatible with most Linux GPU servers; warn before wrapping. If the user hasn't installed a needed dep, `yolo export` will print a clear error — surface it.

## Execution

Local form:

```bash
yolo export model=<MODEL> format=<FORMAT> [<EXTRA_KV>]
```

Remote form:

```bash
ssh <REMOTE> 'bash -lc "cd <WORKDIR> && yolo export model=<MODEL> format=<FORMAT> [<EXTRA_KV>]"'
```

After completion, locate the artifact path in stdout (lines like `... export success ✅ ... saved as '<path>'`) and report it to the user. For remote runs, offer:

```bash
rsync -av <REMOTE>:<WORKDIR>/<artifact> ./<artifact>
```
