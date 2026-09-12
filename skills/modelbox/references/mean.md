---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `mean`

**Devices:** cuda, cpu
**Group:** Preprocess

## Purpose

Per-channel mean subtraction. Subtracts a constant from each channel.
Simpler than `normalize` when std=1.0 (no division needed). Used by
some older detection models (e.g. SSD variants with mean=[104,117,123]).

## TOML config (`mean.toml`)

```toml
[base]
name = "mean"
device = "cuda"
version = "1.0.0"
type = "mean"

[config]
mean = "104.0, 117.0, 123.0"
```

## Ports

- **Input `in_data`:** float tensor — Float32 tensor
- **Output `out_data`:** float tensor — Mean-subtracted float32 tensor

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `mean` | yes | — | Comma-separated per-channel mean values |

## Notes / gotchas

- Use normalize instead when you also need to divide by std

## Upstream source

- `src/drivers/common/flowunit/mean/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
