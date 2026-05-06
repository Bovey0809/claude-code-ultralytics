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

- `command -v yolo`; if empty, instruct `pip install ultralytics` and stop.
- Note that some formats require extra deps (e.g., `engine` needs TensorRT, `coreml` needs `coremltools`). If the user hasn't installed them, `yolo export` will print a clear error — surface it.

## Execution

```bash
yolo export model=<MODEL> format=<FORMAT> [<EXTRA_KV>]
```

After completion, locate the artifact path in stdout (lines like `... export success ✅ ... saved as '<path>'`) and report it to the user.
