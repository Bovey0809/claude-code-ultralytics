---
name: modelbox
description: Use when authoring or modifying a ModelBox graph (.toml), configuring a ModelBox flowunit, choosing the right flowunit for a step (video decode, inference, YOLO postprocess, drawing boxes, encoding output), or resolving "which flowunit handles X". Provides a curated index of flowunits used in YOLO + video pipelines, with TOML config schema, ports, device options, and known-good recipes.
---

# ModelBox Flowunit Index

## When to use

Invoke this skill when you need to:

- Author or modify a ModelBox graph (`.toml` file in graphviz DSL)
- Configure a flowunit's TOML block (`[base]`, `[config]`, `[input.*]`, `[output.*]`)
- Choose the right flowunit for a pipeline step (source, decode, preprocess, infer, postprocess, encode, sink)
- Resolve "which flowunit handles X?" questions
- Pick the right `virtual_type` / device for a target chip

## Core mental model

A ModelBox pipeline is a directed graph of **flowunits** wired together in a `.toml` graph file using graphviz DSL. Each flowunit declares a `device` (cuda, cpu, apple_silicon, …), consumes typed input ports, and emits typed output ports. The graph file lists nodes (flowunit instances) and edges (port-to-port wires). Each flowunit node names a flowunit directory that holds its own `<name>.toml` config. See [modelbox-ai.com/modelbox-book](https://modelbox-ai.com/modelbox-book/) for the authoring guide.

## Catalog

| Flowunit | Devices | Group | Use for | Reference |
|----------|---------|-------|---------|-----------|
| `inference` | cuda, cpu | Inference | Run any model; virtual_type picks engine | [references/inference.md](references/inference.md) |
| `coreml_inference` | apple_silicon | Inference | Run CoreML models on Apple Silicon (M-series) | [references/coreml_inference.md](references/coreml_inference.md) |
| `video_input` | cpu | Input | Open a video file and stream decoded frames | [references/video_input.md](references/video_input.md) |
| `data_source_generator` | cpu | Input | File/dir source (replays paths into a stream) | [references/data_source_generator.md](references/data_source_generator.md) |
| `httpserver_async` | cpu | Input | HTTP request/reply edges | [references/httpserver_async.md](references/httpserver_async.md) |
| `video_demuxer` | cpu | Video | Split mp4/mkv container into elementary streams | [references/video_demuxer.md](references/video_demuxer.md) |
| `video_decoder` | cuda, cpu | Video | Decode H.264/H.265 to frames (NV12/RGB) | [references/video_decoder.md](references/video_decoder.md) |
| `video_encoder` | cpu | Video | Frames → H.264 mp4 | [references/video_encoder.md](references/video_encoder.md) |
| `resize` | cpu | Preprocess | Resize frames to a fixed width x height | [references/resize.md](references/resize.md) |
| `image_process` | cuda, cpu | Preprocess | Resize/letterbox/colorspace/layout convert | [references/image_process.md](references/image_process.md) |
| `normalize` | cuda, cpu | Preprocess | Per-channel normalize (mean/std) | [references/normalize.md](references/normalize.md) |
| `mean` | cuda, cpu | Preprocess | Per-channel mean subtract | [references/mean.md](references/mean.md) |
| `yolo26_post` | cpu | Postprocess | YOLO detect head -> boxes (anchors, NMS) | [references/yolo26_post.md](references/yolo26_post.md) |
| `yolo_seg_post` | cpu | Postprocess | YOLO segment head -> masks | [references/yolo_seg_post.md](references/yolo_seg_post.md) |
| `yolo_pose_post` | cpu | Postprocess | YOLO pose head -> keypoints | [references/yolo_pose_post.md](references/yolo_pose_post.md) |
| `yolo_track_post` | cpu | Postprocess | YOLO + tracker -> tracked boxes with IDs | [references/yolo_track_post.md](references/yolo_track_post.md) |
| `draw_bbox` | cpu | Output | Draw boxes/labels on frames | [references/draw_bbox.md](references/draw_bbox.md) |
| `output_broker` | cpu | Output | Send results to Kafka/RocketMQ/HTTP/file | [references/output_broker.md](references/output_broker.md) |
| `meta_mapping` | cpu | Utility | Rename/project/drop fields between units | [references/meta_mapping.md](references/meta_mapping.md) |

## Virtual-type matrix

Use `virtual_type` inside the `[base]` block of an inference flowunit to select the engine:

| Chip | `virtual_type` | `device` key | Inference flowunit |
|------|---------------|--------------|-------------------|
| NVIDIA GPU | `tensorrt` | `cuda` | `inference` |
| NVIDIA GPU | `torch` | `cuda` | `inference` |
| Apple Silicon (M-series) | `coreml` | `apple_silicon` | `coreml_inference` |
| Huawei Ascend | `acl` | `ascend` | `inference` |
| Huawei Ascend | `mindspore` | `ascend` | `inference` |
| Intel Arc / iGPU | `openvino` | `intel_gpu` | `inference` |
| CPU fallback | `onnxruntime` | `cpu` | `inference` |

## Known-good pipelines

Four canned recipes. Each shows a complete graph skeleton; fill in flowunit configs from the linked references.

---

### Recipe 1: NVIDIA — file → detect → annotate → file

**Chip:** NVIDIA GPU | **Engine:** TensorRT | **References:** inference, video_input, video_demuxer, video_decoder, image_process, yolo26_post, draw_bbox, video_encoder

```toml
# graph/nvidia_file_detect.toml
[driver]
  skip-default = false
  dir = ["${MODELBOX_SOLUTION_PATH}/flowunit"]

[graph]
  format = "graphviz"
  graphconf = """digraph nvidia_file_detect {
    node [shape=Mrecord]

    video_input[type=flowunit, flowunit=video_input, device=cpu,
                source_url="${input_video}"]
    video_demuxer[type=flowunit, flowunit=video_demuxer, device=cpu]
    video_decoder[type=flowunit, flowunit=video_decoder, device=cuda,
                  pix_fmt="rgb"]
    image_process[type=flowunit, flowunit=image_process, device=cuda,
                  width=640, height=640, interpolation="inter_linear",
                  color_mode="rgb", data_type="float"]
    detect[type=flowunit, flowunit=detect, device=cuda,
           virtual_type="tensorrt"]
    yolo26_post[type=flowunit, flowunit=yolo26_post, device=cpu,
                classes=80, conf_threshold=0.25, nms_threshold=0.45,
                input_width=640, input_height=640]
    draw_bbox[type=flowunit, flowunit=draw_bbox, device=cpu,
              thickness=2, font_size=0.6]
    video_encoder[type=flowunit, flowunit=video_encoder, device=cpu,
                  dest_url="${output_video}", encoder="libx264"]

    video_input:out_video_url   -> video_demuxer:in_video_url
    video_demuxer:out_video_packet -> video_decoder:in_video_packet
    video_decoder:out_image     -> image_process:in_image
    image_process:out_image     -> detect:input
    detect:output               -> yolo26_post:in_data
    video_decoder:out_image     -> draw_bbox:in_frame
    yolo26_post:out_data        -> draw_bbox:in_boxes
    draw_bbox:out_image         -> video_encoder:in_image
  }"""
```

> The `detect` flowunit directory must contain a `.toml` with `entry=./model.engine` and `virtual_type=tensorrt`. See [references/inference.md](references/inference.md).

---

### Recipe 2: Apple Silicon — file → detect → annotate → file

**Chip:** Apple M-series | **Engine:** CoreML | **References:** coreml_inference, video_input, video_demuxer, video_decoder, resize, yolo26_post, draw_bbox, video_encoder

This is Recipe 1 with three lines changed (marked `# ← changed`):

```toml
# graph/apple_file_detect.toml
[driver]
  skip-default = false
  dir = ["${MODELBOX_SOLUTION_PATH}/flowunit"]

[graph]
  format = "graphviz"
  graphconf = """digraph apple_file_detect {
    node [shape=Mrecord]

    video_input[type=flowunit, flowunit=video_input, device=cpu,
                source_url="${input_video}"]
    video_demuxer[type=flowunit, flowunit=video_demuxer, device=cpu]
    video_decoder[type=flowunit, flowunit=video_decoder, device=cpu,
                  pix_fmt="rgb"]
    resize[type=flowunit, flowunit=resize, device=cpu,             # ← changed
           width=640, height=640]
    detect[type=flowunit, flowunit=detect, device=apple_silicon,   # ← changed
           virtual_type="coreml"]
    yolo26_post[type=flowunit, flowunit=yolo26_post, device=cpu,
                classes=80, conf_threshold=0.25, nms_threshold=0.45,
                input_width=640, input_height=640]
    draw_bbox[type=flowunit, flowunit=draw_bbox, device=cpu,
              thickness=2, font_size=0.6]
    video_encoder[type=flowunit, flowunit=video_encoder, device=cpu,
                  dest_url="${output_video}",
                  encoder="h264_videotoolbox"]                      # ← changed

    video_input:out_video_url      -> video_demuxer:in_video_url
    video_demuxer:out_video_packet -> video_decoder:in_video_packet
    video_decoder:out_image        -> resize:in_image
    resize:out_image               -> detect:input
    detect:output                  -> yolo26_post:in_data
    video_decoder:out_image        -> draw_bbox:in_frame
    yolo26_post:out_data           -> draw_bbox:in_boxes
    draw_bbox:out_image            -> video_encoder:in_image
  }"""
```

> The `detect` flowunit directory must contain a `.toml` with `entry=./model.mlmodelc` and `device=apple_silicon`, `virtual_type=coreml`. See [references/coreml_inference.md](references/coreml_inference.md).

---

### Recipe 3: HTTP request → detect → JSON reply (chip-agnostic)

**References:** httpserver_async, image_process, inference/coreml_inference, yolo26_post

```toml
# graph/http_detect.toml
[graph]
  format = "graphviz"
  graphconf = """digraph http_detect {
    node [shape=Mrecord]

    http_in[type=flowunit, flowunit=httpserver_async, device=cpu,
            endpoint="/api/detect", port=8080]
    image_process[type=flowunit, flowunit=image_process, device=cuda,
                  width=640, height=640, color_mode="rgb", data_type="float"]
    detect[type=flowunit, flowunit=detect, device=cuda,
           virtual_type="tensorrt"]
    yolo26_post[type=flowunit, flowunit=yolo26_post, device=cpu,
                classes=80, conf_threshold=0.25, nms_threshold=0.45,
                input_width=640, input_height=640]

    http_in:out_request     -> image_process:in_image
    image_process:out_image -> detect:input
    detect:output           -> yolo26_post:in_data
    yolo26_post:out_data    -> http_in:in_reply
  }"""
```

> Swap `detect` `device`/`virtual_type` for Apple Silicon (device=apple_silicon, virtual_type=coreml) and replace `image_process` → `resize`.

---

### Recipe 4: RTSP → detect → output_broker (chip-agnostic)

**References:** video_demuxer, video_decoder, image_process, inference, yolo26_post, output_broker

```toml
# graph/rtsp_detect_broker.toml
[graph]
  format = "graphviz"
  graphconf = """digraph rtsp_detect_broker {
    node [shape=Mrecord]

    video_demuxer[type=flowunit, flowunit=video_demuxer, device=cpu,
                  source_url="${rtsp_url}"]
    video_decoder[type=flowunit, flowunit=video_decoder, device=cuda,
                  pix_fmt="rgb"]
    image_process[type=flowunit, flowunit=image_process, device=cuda,
                  width=640, height=640, color_mode="rgb", data_type="float"]
    detect[type=flowunit, flowunit=detect, device=cuda,
           virtual_type="tensorrt"]
    yolo26_post[type=flowunit, flowunit=yolo26_post, device=cpu,
                classes=80, conf_threshold=0.25, nms_threshold=0.45,
                input_width=640, input_height=640]
    sink[type=flowunit, flowunit=output_broker, device=cpu,
         broker_type="http", broker_url="http://localhost:9090/results"]

    video_demuxer:out_video_packet -> video_decoder:in_video_packet
    video_decoder:out_image        -> image_process:in_image
    image_process:out_image        -> detect:input
    detect:output                  -> yolo26_post:in_data
    yolo26_post:out_data           -> sink:in_data
  }"""
```

> Wire the RTSP URL into `video_demuxer` via `source_url` or a preceding `data_source_generator` node. For Kafka output change `broker_type="kafka"` and set `broker_url` to the bootstrap server.

## Authoring gotchas

- **Device mismatch between adjacent units** forces a memory copy (acceptable, but log it — watch for excess copies in the ModelBox console).
- **`inference`'s `entry` path** is relative to the flowunit's own directory, not the graph `.toml`.
- **Image layout:** cuda flowunits prefer NHWC input; NV12 is the native format between `video_decoder` (cuda) and `image_process`.
- **`name=` in `[base]`** must match the flowunit directory name exactly — ModelBox uses this to locate the directory.
- **Port wiring** uses `:port_name` syntax; types must match across the edge (image, tensor, json, …).
- **`coreml_inference`** requires `device=apple_silicon`; using `device=cpu` silently routes to a different engine.
- **`draw_bbox` needs two input ports** wired simultaneously — the original frame (from decoder, bypassing the infer chain) and the detection JSON (from the post flowunit).

## Pointers

- [ModelBox documentation](https://modelbox-ai.com/modelbox-book/)
- [Upstream source](https://github.com/modelbox-ai/modelbox)
- See the `yolo` skill for the Ultralytics side of the pipeline: training, export to TensorRT/CoreML, dataset validation.

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13). Re-run `python3 tools/build-modelbox-skill.py` to update._
