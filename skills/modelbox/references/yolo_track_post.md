---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `yolo_track_post`

**Devices:** cpu
**Group:** Postprocess

## Purpose

YOLO + tracker postprocessor. Wraps detect-head decoding with a ByteTrack
or SORT tracker to assign persistent IDs across frames. Outputs bounding
boxes with a `track_id` field. Use when you need to follow objects over
time, not just detect them per frame.

## TOML config (`yolo_track_post.toml`)

```toml
[base]
name = "yolo_track_post"
device = "cpu"
version = "1.0.0"
type = "yolo_track_post"

[config]
classes = 80
conf_threshold = 0.25
nms_threshold = 0.45
input_width = 640
input_height = 640
tracker = "bytetrack"
```

## Ports

- **Input `in_data`:** float tensor — Raw model output from inference
- **Output `out_data`:** json — Detection results with persistent track_id per instance

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `classes` | yes | 80 | Number of classes |
| `tracker` | no | bytetrack | bytetrack | sort |
| `conf_threshold` | no | 0.25 | Minimum confidence |
| `nms_threshold` | no | 0.45 | IoU NMS threshold |
| `input_width` | yes | 640 | Model input width |
| `input_height` | yes | 640 | Model input height |

## Notes / gotchas

- track_id is stable within a pipeline run; resets on restart
- For frame-by-frame (no tracking), use yolo26_post instead

## Upstream source

- `src/drivers/common/flowunit/yolo_track_post/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
