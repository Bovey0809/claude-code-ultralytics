---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
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
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
