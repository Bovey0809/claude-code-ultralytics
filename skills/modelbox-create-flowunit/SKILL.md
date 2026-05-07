---
name: modelbox-create-flowunit
description: Use when authoring a NEW custom ModelBox flowunit — Python, C++, or an inference (model-wrapper) flowunit — and wiring it into a graph. Generates the flowunit directory (`<name>.toml` plus code/CMake), wires it to a graph .toml, and validates the layout. Use when the user asks to "create a flowunit", "scaffold a flowunit", "add a custom postprocess unit", "wrap a model as a flowunit", or "register a new flowunit". Distinct from the `modelbox` skill, which only indexes existing built-in flowunits.
---

# Create a ModelBox Flowunit

## When to use

Invoke when the user wants to **author a new flowunit** — not when they want to use an existing one (for that, use the `modelbox` skill, which catalogs built-ins like `inference`, `image_process`, `yolo26_post`, etc.).

Triggers:
- "create / scaffold / generate a flowunit"
- "wrap this `.engine` / `.mlpackage` / `.onnx` as a flowunit"
- "add a custom preprocess/postprocess flowunit"
- "register a new flowunit and wire it into the graph"

Do NOT use when:
- The user just wants to configure an **existing** flowunit's TOML — use `modelbox` skill.
- The user is editing only the graph DSL — use `modelbox` skill.

## Output layout

Default output directory: **`./src/flowunit/<name>/`** (standard ModelBox project layout).

Every flowunit lives in its own directory. The directory name **must** match `[base].name`. ModelBox locates the unit by directory name.

```
src/flowunit/<name>/
├── <name>.toml         # required — flowunit descriptor
├── <name>.py           # python flowunit
│   OR
├── <name>.cc           # c++ flowunit source
├── <name>.h            # c++ flowunit header
├── CMakeLists.txt      # c++ build
│   OR
└── <model_file>        # inference flowunit: .engine / .mlpackage / .onnx / .om
```

## The three flowunit kinds

| Kind | When to use | Files |
|------|-------------|-------|
| **python** | Glue code, postprocess, business logic, prototyping | `<name>.toml` + `<name>.py` |
| **c++** | Hot-path preprocessors, custom CUDA kernels, perf-critical | `<name>.toml` + `<name>.cc` + `<name>.h` + `CMakeLists.txt` |
| **inference** | Wrap a single trained model file | `<name>.toml` + the model file (no code) |

## Workflow

1. **Ask** (if not given): unit name, kind (python/c++/inference), input port name(s), output port name(s), device (`cpu`, `cuda`, `apple_silicon`, `ascend`).
2. **For inference kind** also need: model path and `virtual_type` (`tensorrt`, `coreml`, `onnxruntime`, `torch`, `acl`, `mindspore`, `openvino`).
3. **Scaffold** the directory under `./src/flowunit/<name>/` using the templates below. Verify the parent dir exists with `ls` before writing.
4. **Wire** into the target graph `.toml` if the user identifies one — add a node line and the edges (`:port -> :port`).
5. **Validate** the unit: directory name matches `[base].name`, port names referenced in graph match `[input.*].name` / `[output.*].name`, `entry` is correct (Python: `<modulename>@<ClassName>`; inference: relative path to model file).

## Templates

### Python flowunit — `<name>.toml`

```toml
[base]
name = "<name>"
device = "cpu"             # cpu | cuda | apple_silicon | ascend
version = "1.0.0"
description = "<one line>"
entry = "<name>@<ClassName>"   # python module @ class
type = "python"            # fixed

# Flowunit type flags (almost always all false — flip only if you know why)
stream = false
condition = false
collapse = false
collapse_all = false
expand = false

[config]
# user-tunable knobs read in open()
threshold = 0.5

[input]
[input.input1]
name = "in_data"
device = "cpu"

[output]
[output.output1]
name = "out_data"
```

### Python flowunit — `<name>.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import _flowunit as modelbox


class <ClassName>(modelbox.FlowUnit):
    def __init__(self):
        super().__init__()

    def open(self, config):
        # Read [config] keys here; cache anything expensive
        self.threshold = config.get_float("threshold", 0.5)
        return modelbox.Status.StatusCode.STATUS_SUCCESS

    def process(self, data_context):
        in_data = data_context.input("in_data")
        out_data = data_context.output("out_data")

        for buffer in in_data:
            payload = buffer.as_object()           # bytes/str depending on upstream
            result = payload                        # ← your transformation here
            out = modelbox.Buffer(self.get_bind_device(), result)
            out_data.push_back(out)

        return modelbox.Status.StatusCode.STATUS_SUCCESS

    def close(self):
        return modelbox.Status()

    def data_pre(self, data_context):
        # Called once per stream before the first process() — only relevant if stream=true
        return modelbox.Status()

    def data_post(self, data_context):
        # Called once per stream after the last process() — only relevant if stream=true
        return modelbox.Status()
```

### C++ flowunit — `<name>.toml`

```toml
[base]
name = "<name>"
device = "cpu"             # cpu | cuda | ascend
version = "1.0.0"
description = "<one line>"
entry = "lib<name>.so"     # built shared object
type = "c++"

stream = false
condition = false
collapse = false
collapse_all = false
expand = false

[config]
threshold = 0.5

[input]
[input.input1]
name = "in_data"
device = "cpu"

[output]
[output.output1]
name = "out_data"
```

### C++ flowunit — `<name>.h`

```cpp
#ifndef <NAME>_FLOWUNIT_H_
#define <NAME>_FLOWUNIT_H_

#include <modelbox/flowunit.h>
#include <modelbox/base/configuration.h>

class <ClassName>FlowUnit : public modelbox::FlowUnit {
 public:
  <ClassName>FlowUnit() = default;
  ~<ClassName>FlowUnit() override = default;

  modelbox::Status Open(
      const std::shared_ptr<modelbox::Configuration> &opts) override;
  modelbox::Status Close() override;
  modelbox::Status Process(
      std::shared_ptr<modelbox::DataContext> data_ctx) override;

 private:
  float threshold_{0.5f};
};

#endif  // <NAME>_FLOWUNIT_H_
```

### C++ flowunit — `<name>.cc`

```cpp
#include "<name>.h"

#include <modelbox/base/log.h>

modelbox::Status <ClassName>FlowUnit::Open(
    const std::shared_ptr<modelbox::Configuration> &opts) {
  threshold_ = opts->GetFloat("threshold", 0.5f);
  return modelbox::STATUS_OK;
}

modelbox::Status <ClassName>FlowUnit::Close() { return modelbox::STATUS_OK; }

modelbox::Status <ClassName>FlowUnit::Process(
    std::shared_ptr<modelbox::DataContext> data_ctx) {
  auto input_bufs = data_ctx->Input("in_data");
  auto output_bufs = data_ctx->Output("out_data");
  if (input_bufs == nullptr || output_bufs == nullptr) {
    return {modelbox::STATUS_FAULT, "missing in_data/out_data port"};
  }

  for (size_t i = 0; i < input_bufs->Size(); ++i) {
    auto in_buf = input_bufs->At(i);
    auto out_buf = std::make_shared<modelbox::Buffer>(GetBindDevice());
    out_buf->Build(in_buf->GetBytes());
    std::memcpy(out_buf->MutableData(), in_buf->ConstData(), in_buf->GetBytes());
    output_bufs->PushBack(out_buf);
  }
  return modelbox::STATUS_OK;
}

// Driver registration
class <ClassName>FlowUnitFactory : public modelbox::FlowUnitFactory {
 public:
  std::map<std::string, std::shared_ptr<modelbox::FlowUnitDesc>>
  FlowUnitProbe() override {
    auto desc = std::make_shared<modelbox::FlowUnitDesc>();
    desc->SetFlowUnitName("<name>");
    desc->SetFlowUnitGroupType("Generic");
    desc->AddFlowUnitInput({"in_data"});
    desc->AddFlowUnitOutput({"out_data"});
    return {{"<name>", desc}};
  }
  std::shared_ptr<modelbox::FlowUnit> CreateFlowUnit(
      const std::string &, const std::string &) override {
    return std::make_shared<<ClassName>FlowUnit>();
  }
};
```

### C++ flowunit — `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.10)
project(<name>)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(modelbox REQUIRED)

add_library(<name> SHARED <name>.cc)
target_link_libraries(<name> PRIVATE modelbox::modelbox)

install(TARGETS <name> LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}/modelbox-flowunit)
install(FILES <name>.toml DESTINATION ${CMAKE_INSTALL_PREFIX}/share/modelbox-flowunit/<name>)
```

### Inference flowunit — `<name>.toml`

A pure-config flowunit that wraps one model file. No code.

```toml
[base]
name = "<name>"
device = "cuda"            # cuda (TRT/Torch/ORT) | apple_silicon (CoreML) | cpu | ascend
version = "1.0.0"
description = "<model purpose>"
entry = "./<model_file>"   # RELATIVE to this flowunit dir, NOT the graph
type = "inference"
virtual_type = "tensorrt"  # tensorrt | torch | onnxruntime | coreml | acl | mindspore | openvino

[config]
plugin = ""                # "yolo" only for legacy YOLOv3 upsample compat

[input]
[input.input1]
name = "input"
type = "float"

[output]
[output.output1]
name = "output"
type = "float"
```

Drop the model file (`<model_file>`) into the same directory.

## Graph wiring

A graph (`graph/<name>.toml`) lists nodes and edges in graphviz DSL. Add a node for the new flowunit and wire its ports.

```toml
[graph]
  format = "graphviz"
  graphconf = """digraph my_pipeline {
    node [shape=Mrecord]

    upstream[type=flowunit, flowunit=<upstream>, device=cuda]
    <name>[type=flowunit, flowunit=<name>, device=cpu, threshold=0.5]
    downstream[type=flowunit, flowunit=<downstream>, device=cpu]

    upstream:out_image -> <name>:in_data
    <name>:out_data    -> downstream:in_data
  }"""
```

Rules:
- The `flowunit=<name>` token in the node line must match `[base].name` and the directory name.
- Per-node config keys (e.g. `threshold=0.5`) override the unit's `[config]` defaults.
- Port suffixes after `:` must match `[input.*].name` / `[output.*].name`.
- ModelBox auto-resolves device mismatch between adjacent units with a memory copy — fine, but flag if it happens on the hot path.

## Quick reference

| Field | Purpose | Gotcha |
|-------|---------|--------|
| `[base].name` | Unit identifier in graphs | MUST equal directory name |
| `[base].type` | `python` / `c++` / `inference` | Picks the loader |
| `[base].entry` | Python: `mod@Class`; C++: `lib<name>.so`; inference: relative path | Inference path is relative to flowunit dir, not graph |
| `[base].device` | Target device | `apple_silicon` only with `coreml` virtual_type |
| `virtual_type` | Inference engine | tensorrt/torch/onnxruntime/coreml/acl/mindspore/openvino |
| `stream` | Process across data stream lifecycle | If true, also implement `data_pre`/`data_post` |
| `[input.inputN].name` | Port name used in graph edges | Multiple ports → multiple `[input.inputN]` blocks (N=1,2,…) |
| `[config].*` | Tunable knobs read in `open()` | Override per-node in graph DSL |

## Common mistakes

- **Directory name ≠ `[base].name`** → ModelBox can't find the flowunit. Always match.
- **Python `entry` wrong** → must be `<filename_without_py>@<ClassName>`, e.g. `entry = "yolox_post@YoloxPost"` for `yolox_post.py` defining `class YoloxPost`.
- **Inference `entry` resolved against graph dir** — it's not; it's relative to the flowunit's own directory.
- **Adding `[input.input1]` AND `[input.input2]` but only wiring one in the graph** — every declared input is required; either remove it or wire it.
- **Picking `device="cuda"` with `virtual_type="coreml"`** — silently mismatched; CoreML needs `device="apple_silicon"`.
- **Forgetting `stream=true` then expecting `data_pre/data_post` to fire** — those callbacks only fire for stream flowunits.
- **C++ unit not installed to `modelbox-flowunit/`** — the loader scans that directory; verify with `ls $PREFIX/lib/modelbox-flowunit/`.

## Pointers

- ModelBox authoring guide: https://modelbox-ai.com/modelbox-book/
- Reference templates in upstream: `examples/flowunit/python/`, `examples/flowunit/c++/`, `examples/flowunit/infer/`
- Real demos to crib from: `src/demo/hello_world/` (python), `src/demo/car_detection/flowunit/yolox_post/` (python postprocess), `src/demo/apple_silicon_yolo/flowunit/yolo_detect/` (inference unit)
- Sister skill `modelbox` — indexes built-in flowunits and graph recipes.
