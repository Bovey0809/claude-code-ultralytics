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

## Experiment log (opt-in)

If `.ultralytics.yml` (cwd or any ancestor) sets `experiment_log: <path>`, append a row using the same table schema as `/ultralytics:train`. For exports:

- **Started**: `YYYYMMDD-HHMM` at invocation time.
- **Run name**: `<YYYYMMDD-HHMM>_export_<model-stem>_<format>` (e.g. `20260506-1545_export_yolo11n_onnx`). Exports don't take `name=`, so this is purely a log identifier.
- **Task**: `export`.
- **Command**: the exact `yolo export …` invocation.
- **Results**: the artifact path. If errored, `FAILED — <reason>`.
- **Notes**: `_(fill in)_`.

If the log file doesn't exist yet, create it with the header from `/ultralytics:train`'s spec. Always write LOCALLY even when execution is remote.
