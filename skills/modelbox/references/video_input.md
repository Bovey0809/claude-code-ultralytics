---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `video_input`

**Devices:** cpu
**Group:** Input

## Purpose

File-based video source. Emits the source URL as a string token for
downstream processing. Preferred over `data_source_generator` when the
source is a single video file — it handles source registration internally.
Wire `out_video_url` into `video_demuxer` → `video_decoder` to get frames.

## TOML config (`video_input.toml`)

```toml
[base]
name = "video_input"
device = "cpu"
version = "1.0.0"
type = "video_input"

[config]
source_url = "${input_video}"
```

## Ports

- **Output `out_video_url`:** string — Source URL forwarded to downstream demuxer/decoder chain

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `source_url` | yes | — | File path or URL to the video file; supports ${var} expansion |

## Notes / gotchas

- Prefer this over data_source_generator for single video file inputs
- Does not demux/decode itself — wire out_video_url into video_demuxer

## Upstream source

- `src/drivers/common/flowunit/video_input/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
