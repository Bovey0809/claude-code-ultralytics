---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `yolo_pose_post`

**Devices:** cpu
**Group:** Postprocess

## Purpose

YOLO pose-estimation postprocessor. Decodes keypoint coordinates and
visibility flags from the model output. Outputs bounding boxes +
keypoints arrays. Configure `num_keypoints` to match the model
(17 for COCO, 26 for animal pose, etc.).

## TOML config (`yolo_pose_post.toml`)

```toml
[base]
name = "yolo_pose_post"
device = "cpu"
version = "1.0.0"
type = "yolo_pose_post"

[config]
classes = 1
conf_threshold = 0.25
nms_threshold = 0.45
input_width = 640
input_height = 640
num_keypoints = 17
```

## Ports

- **Input `in_data`:** float tensor — Raw pose model output
- **Output `out_data`:** json — Detection results with keypoints [[x,y,vis], ...]

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `classes` | yes | 1 | Number of classes (usually 1 = person for pose) |
| `num_keypoints` | yes | 17 | Keypoints per instance (17 = COCO human) |
| `conf_threshold` | no | 0.25 | Minimum confidence |
| `nms_threshold` | no | 0.45 | IoU NMS threshold |
| `input_width` | yes | 640 | Model input width |
| `input_height` | yes | 640 | Model input height |

## Notes / gotchas

- num_keypoints must match the exported model exactly

## Upstream source

- `src/drivers/common/flowunit/yolo_pose_post/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
