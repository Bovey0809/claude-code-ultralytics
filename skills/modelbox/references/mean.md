---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
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
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
