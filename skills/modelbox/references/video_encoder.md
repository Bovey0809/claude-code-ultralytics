---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
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
- dest_url directory must exist before the pipeline starts

## Upstream source

- `src/drivers/common/flowunit/video_encoder/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
