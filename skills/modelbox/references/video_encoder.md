---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `video_encoder`

**Devices:** cpu
**Group:** Video

## Purpose

Encodes frames to H.264 and muxes into an mp4 container. On macOS set
`encoder=h264_videotoolbox` for hardware encode. On Linux with Intel
Quick Sync use `encoder=h264_qsv`. Default `libx264` works on any OS.

## TOML config (`video_encoder.toml`)

```toml
[base]
name = "video_encoder"
device = "cpu"
version = "1.0.0"
type = "video_encoder"

[config]
dest_url = "${output_video}"
encoder = "libx264"
bitrate = 2097152
```

## Ports

- **Input `in_image`:** image — Annotated frame (RGB or BGR)

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `dest_url` | yes | — | Output file path; supports ${var} expansion |
| `encoder` | no | libx264 | libx264 (any) | h264_videotoolbox (macOS) | h264_qsv (Linux/Intel) |
| `bitrate` | no | 2097152 | Target bitrate in bits/s |

## Notes / gotchas

- Use h264_videotoolbox on macOS for hardware encode (Apple Silicon pipeline)
- VideoToolbox's h264 hardware encoder additionally requires width divisible by 16 for its internal macroblock alignment.
- dest_url directory must exist before the pipeline starts

## Upstream source

- `src/drivers/common/flowunit/video_encoder/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
