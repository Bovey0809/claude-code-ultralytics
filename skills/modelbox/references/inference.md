---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `inference`

**Devices:** cuda, cpu
**Group:** Inference

## Purpose

Generic inference flowunit. Loads a model file and runs it through the
engine selected by `virtual_type`. Supports TensorRT, Torch, ONNX Runtime,
ACL, MindSpore, and OpenVINO via a single TOML interface — swap
`virtual_type` and `entry` to change chip target.

## TOML config (`inference.toml`)

```toml
[base]
name = "inference"
device = "cuda"
version = "1.0.0"
type = "inference"
virtual_type = "tensorrt"
entry = "./model.engine"

[config]
plugin = ""

[input.input1]
name = "input"
type = "float"

[output.output1]
name = "output"
type = "float"
```

## Ports

- **Input `input`:** float tensor — NHWC float32 [1,H,W,3] by default; shape depends on model
- **Output `output`:** float tensor — Model-defined shape

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `entry` | yes | — | Path to model file, relative to the flowunit directory |
| `virtual_type` | yes | — | tensorrt | torch | onnxruntime | acl | mindspore | openvino |
| `device` | yes | — | cuda | cpu | ascend | intel_gpu |
| `plugin` | no | "" | "yolo" enables upsample layer for legacy YOLOv3 only |

## Notes / gotchas

- `entry` is relative to the flowunit's own directory, not the graph TOML
- Use `plugin=\"yolo\"` only for YOLOv3 upsample compat; omit for all other models
- Input tensor shape must match the model's expected input exactly

## Upstream source

- `src/drivers/common/flowunit/inference/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
