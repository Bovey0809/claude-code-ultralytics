<!-- SECTION: recipes -->
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

    video_demuxer[type=flowunit, flowunit=video_demuxer, device=cpu]
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
