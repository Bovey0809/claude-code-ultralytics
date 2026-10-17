---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `yolo26_post`

**Devices:** cpu
**Group:** Postprocess

## Purpose

YOLO detect-head postprocessor. Converts raw model output tensors into
bounding boxes + class labels + confidence scores, then applies NMS.
Supports YOLO v2-v6 anchor-based and anchor-free variants via `anchors`
config. Use for standard object detection tasks.

## TOML config (`yolo26_post.toml`)

```toml
[base]
name = "yolo26_post"
device = "cpu"
version = "1.0.0"
type = "yolo26_post"

[config]
classes = 80
conf_threshold = 0.25
nms_threshold = 0.45
input_width = 640
input_height = 640
```

## Ports

- **Input `in_data`:** float tensor — Raw model output from inference flowunit
- **Output `out_data`:** json — Detection results — list of {box, class_id, confidence}

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `classes` | yes | 80 | Number of classes (must match model head) |
| `conf_threshold` | no | 0.25 | Minimum confidence to keep a detection |
| `nms_threshold` | no | 0.45 | IoU threshold for NMS suppression |
| `input_width` | yes | 640 | Model input width (used to scale boxes back to frame coords) |
| `input_height` | yes | 640 | Model input height |

## Notes / gotchas

- input_width/input_height must match the image_process output size
- For anchor-free YOLO11/v8, anchors config is not needed

## Upstream source

- `src/drivers/common/flowunit/yolo26_post/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
