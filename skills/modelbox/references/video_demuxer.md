---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `video_demuxer`

**Devices:** cpu
**Group:** Video

## Purpose

Splits a video container (mp4, mkv, ts, …) into elementary streams.
Emits raw encoded packets; wire into video_decoder. Use when you need
explicit demux/decode separation (e.g. to route audio and video
independently). For simple file-to-frame pipelines prefer video_input.

## TOML config (`video_demuxer.toml`)

```toml
[base]
name = "video_demuxer"
device = "cpu"
version = "1.0.0"
type = "video_demuxer"
```

## Ports

- **Input `in_video_url`:** string — Video file path or URL from video_input
- **Output `out_video_packet`:** video_packet — Encoded packet stream for video_decoder

## Config keys

None required beyond `[base]`.

## Notes / gotchas

- Wire out_video_packet directly into video_decoder:in_video_packet
- Audio packets are currently dropped; video only

## Upstream source

- `src/drivers/common/flowunit/video_demuxer/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
