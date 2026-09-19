---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `normalize`

**Devices:** cuda, cpu
**Group:** Preprocess

## Purpose

Per-channel normalization. Applies `(pixel - mean) / std` to each channel.
Configure `mean` and `std` as comma-separated floats matching the channel
count. Use when the model expects ImageNet-normalized input.

## TOML config (`normalize.toml`)

```toml
[base]
name = "normalize"
device = "cuda"
version = "1.0.0"
type = "normalize"

[config]
mean = "0.485, 0.456, 0.406"
std = "0.229, 0.224, 0.225"
```

## Ports

- **Input `in_data`:** float tensor — Float32 tensor from image_process
- **Output `out_data`:** float tensor — Normalized float32 tensor

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `mean` | yes | — | Comma-separated per-channel mean values (e.g. "0.485, 0.456, 0.406") |
| `std` | yes | — | Comma-separated per-channel std values (e.g. "0.229, 0.224, 0.225") |

## Notes / gotchas

- Channel count inferred from comma count; must match the input tensor
- YOLO models typically do not need this (internal normalization in the model)

## Upstream source

- `src/drivers/common/flowunit/normalize/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
