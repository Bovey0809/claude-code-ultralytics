---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `image_process`

**Devices:** cuda, cpu
**Group:** Preprocess

## Purpose

Generic image-processing flowunit. Handles resize, letterbox padding,
colorspace conversion (BGR<->RGB, NV12->RGB), and memory layout conversion
(HWC<->CHW). The Swiss-army knife for building a preprocessing chain before
inference on NVIDIA. Prefer `resize` for Apple Silicon (apple_silicon device
is not supported by image_process).

## TOML config (`image_process.toml`)

```toml
[base]
name = "image_process"
device = "cuda"
version = "1.0.0"
type = "image_process"

[config]
width = 640
height = 640
interpolation = "inter_linear"
color_mode = "bgr"
data_type = "float"
```

## Ports

- **Input `in_image`:** image — Input frame (NV12 from cuda decoder or RGB/BGR from cpu decoder)
- **Output `out_image`:** image/tensor — Preprocessed tensor in configured layout and dtype

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `width` | yes | — | Target width |
| `height` | yes | — | Target height |
| `interpolation` | no | inter_linear | inter_linear | inter_nearest | inter_cubic |
| `color_mode` | no | bgr | bgr | rgb — output colorspace |
| `data_type` | no | float | float | uint8 |

## Notes / gotchas

- NV12 input from cuda video_decoder is handled automatically when device=cuda
- Does not support apple_silicon device; use resize for Apple Silicon pipelines

## Upstream source

- `src/drivers/common/flowunit/image_process/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
