---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `draw_bbox`

**Devices:** cpu
**Group:** Output

## Purpose

Draws bounding boxes, class labels, and confidence scores onto frames
in-place. Input: decoded frame + detection JSON from a post flowunit.
Output: annotated frame ready for video_encoder. Configure color,
thickness, and font_size.

## TOML config (`draw_bbox.toml`)

```toml
[base]
name = "draw_bbox"
device = "cpu"
version = "1.0.0"
type = "draw_bbox"

[config]
thickness = 2
font_size = 0.6
```

## Ports

- **Input `in_frame`:** image — Original decoded frame (pass through from video_decoder)
- **Input `in_boxes`:** json — Detection JSON from yolo26_post / yolo_seg_post / yolo_pose_post
- **Output `out_image`:** image — Annotated frame

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `thickness` | no | 2 | Box line thickness in pixels |
| `font_size` | no | 0.6 | Label font scale |

## Notes / gotchas

- Two input ports — both must be wired (frame + boxes)
- The original frame must be wired directly from video_decoder, bypassing inference/postprocess

## Upstream source

- `src/drivers/common/flowunit/draw_bbox/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
