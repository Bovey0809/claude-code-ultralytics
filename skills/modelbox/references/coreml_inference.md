---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `coreml_inference`

**Devices:** apple_silicon
**Group:** Inference

## Purpose

Apple Silicon inference flowunit. Loads a CoreML model (.mlmodelc or
.mlpackage) and runs it via the CoreML framework on the Neural Engine /
GPU. Use in place of `inference` when targeting Apple Silicon — set
`device=apple_silicon` and `virtual_type=coreml`.

## TOML config (`coreml_inference.toml`)

```toml
[base]
name = "coreml_inference"
device = "apple_silicon"
version = "1.0.0"
type = "coreml_inference"
```

## Ports

- **Input `input`:** image tensor — Float32 tensor in model's expected layout
- **Output `output`:** float tensor — Model-defined shape

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `entry` | yes | — | Path to .mlmodelc or .mlpackage, relative to flowunit directory |
| `device` | yes | apple_silicon | Must be `apple_silicon`; any other value selects a different engine |
| `virtual_type` | yes | coreml | Must be `coreml` |

## Notes / gotchas

- device must be `apple_silicon` exactly; omitting or using `cpu` will fail
- Pair with `video_encoder` using `encoder=h264_videotoolbox` on macOS for hardware encode
- Export model with `yolo export format=coreml` before use

## Upstream source

- `src/drivers/devices/apple_silicon/flowunit/coreml_inference/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
