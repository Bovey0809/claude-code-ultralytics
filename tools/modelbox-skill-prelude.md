<!-- SECTION: when_to_use -->
## When to use

Invoke this skill when you need to:

- Author or modify a ModelBox graph (`.toml` file in graphviz DSL)
- Configure a flowunit's TOML block (`[base]`, `[config]`, `[input.*]`, `[output.*]`)
- Choose the right flowunit for a pipeline step (source, decode, preprocess, infer, postprocess, encode, sink)
- Resolve "which flowunit handles X?" questions
- Pick the right `virtual_type` / device for a target chip

<!-- SECTION: mental_model -->
## Core mental model

A ModelBox pipeline is a directed graph of **flowunits** wired together in a `.toml` graph file using graphviz DSL. Each flowunit declares a `device` (cuda, cpu, apple_silicon, …), consumes typed input ports, and emits typed output ports. The graph file lists nodes (flowunit instances) and edges (port-to-port wires). Each flowunit node names a flowunit directory that holds its own `<name>.toml` config. See [modelbox-ai.com/modelbox-book](https://modelbox-ai.com/modelbox-book/) for the authoring guide.

<!-- SECTION: virtual_type_matrix -->
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

<!-- SECTION: gotchas -->
## Authoring gotchas

- **Device mismatch between adjacent units** forces a memory copy (acceptable, but log it — watch for excess copies in the ModelBox console).
- **`inference`'s `entry` path** is relative to the flowunit's own directory, not the graph `.toml`.
- **Image layout:** cuda flowunits prefer NHWC input; NV12 is the native format between `video_decoder` (cuda) and `image_process`.
- **`name=` in `[base]`** must match the flowunit directory name exactly — ModelBox uses this to locate the directory.
- **Port wiring** uses `:port_name` syntax; types must match across the edge (image, tensor, json, …).
- **`coreml_inference`** requires `device=apple_silicon`; using `device=cpu` silently routes to a different engine.
- **`draw_bbox` needs two input ports** wired simultaneously — the original frame (from decoder, bypassing the infer chain) and the detection JSON (from the post flowunit).

<!-- SECTION: pointers -->
## Pointers

- [ModelBox documentation](https://modelbox-ai.com/modelbox-book/)
- [Upstream source](https://github.com/modelbox-ai/modelbox)
- See the `yolo` skill for the Ultralytics side of the pipeline: training, export to TensorRT/CoreML, dataset validation.
