---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `resize`

**Devices:** cpu
**Group:** Preprocess

## Purpose

Standalone resize flowunit. Scales frames to a target width/height.
Simpler than image_process when you only need resize — one config key
each for width and height, no colorspace or layout options. Used in the
Apple Silicon pipeline (resize → coreml_inference) where image_process
is not available on apple_silicon device.

## TOML config (`resize.toml`)

```toml
[base]
name = "resize"
device = "cpu"
version = "1.0.0"
type = "resize"

[config]
width = 640
height = 640
```

## Ports

- **Input `in_image`:** image — Input frame; any resolution
- **Output `out_image`:** image — Resized frame at configured width x height

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `width` | yes | — | Target width in pixels |
| `height` | yes | — | Target height in pixels |

## Notes / gotchas

- No letterboxing — frame is stretched; use image_process for letterbox
- Device variants available for ascend and rockchip (not in v0.4 allowlist)

## Upstream source

- `src/drivers/common/flowunit/resize/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
