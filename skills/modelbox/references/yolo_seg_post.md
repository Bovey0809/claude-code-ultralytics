---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `yolo_seg_post`

**Devices:** cpu
**Group:** Postprocess

## Purpose

YOLO segmentation-head postprocessor. Extends yolo26_post with per-instance
mask decoding. Outputs bounding boxes + instance masks. Requires the model
to emit both the detection head and the mask prototype head outputs.

## TOML config (`yolo_seg_post.toml`)

```toml
[base]
name = "yolo_seg_post"
device = "cpu"
version = "1.0.0"
type = "yolo_seg_post"

[config]
classes = 80
conf_threshold = 0.25
nms_threshold = 0.45
input_width = 640
input_height = 640
```

## Ports

- **Input `in_det`:** float tensor — Detection head output
- **Input `in_proto`:** float tensor — Mask prototype head output
- **Output `out_data`:** json — Detection results with mask arrays

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `classes` | yes | 80 | Number of classes |
| `conf_threshold` | no | 0.25 | Minimum confidence |
| `nms_threshold` | no | 0.45 | IoU threshold for NMS |
| `input_width` | yes | 640 | Model input width |
| `input_height` | yes | 640 | Model input height |

## Notes / gotchas

- Requires a segmentation model export (yolo export format=tensorrt task=segment)
- Two input ports — both must be wired from the inference flowunit

## Upstream source

- `src/drivers/common/flowunit/yolo_seg_post/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
