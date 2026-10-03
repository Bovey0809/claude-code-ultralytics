---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `video_decoder`

**Devices:** cuda, cpu
**Group:** Video

## Purpose

Decodes H.264/H.265 packets from video_demuxer into raw frames. The
`cuda` device uses NVDEC hardware decoder; `cpu` falls back to FFmpeg
software decode. Output pixel format is configurable: NV12 (default on
cuda, best for GPU preprocessing), or RGB/BGR (for cpu preprocessing).

## TOML config (`video_decoder.toml`)

```toml
[base]
name = "video_decoder"
device = "cuda"
version = "1.0.0"
type = "video_decoder"

[config]
pix_fmt = "rgb"
```

## Ports

- **Input `in_video_packet`:** video_packet — Encoded packet from video_demuxer
- **Output `out_image`:** image — Decoded frame in configured pix_fmt

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `pix_fmt` | no | nv12 | nv12 | rgb | bgr — NV12 preferred between cuda decode and cuda preprocess |

## Notes / gotchas

- cuda device uses NVDEC; pix_fmt=nv12 avoids a CPU copy when feeding image_process on cuda
- device mismatch with next flowunit is acceptable but adds a memory copy

## Upstream source

- `src/drivers/common/flowunit/video_decoder/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
