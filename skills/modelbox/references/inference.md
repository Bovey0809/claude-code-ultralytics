---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `inference`

**Devices:** cuda, cpu
**Group:** Inference

## Purpose

Generic inference flowunit. Loads a model file and runs it through the
engine selected by `virtual_type`. Supports TensorRT, Torch, ONNX Runtime,
ACL, MindSpore, and OpenVINO via a single TOML interface — swap
`virtual_type` and `entry` to change chip target.

## TOML config (`inference.toml`)

```toml
#
# Copyright 2021 The Modelbox Project Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

[base]
name = "example"
device = "cuda"  
version = "1.0.0"
description = "description"
entry = "./model.pb"  # model file path
type = "inference" 
virtual_type = "tensorflow" # inference engine type: 'tensorflow', 'tensorrt', 'torch', 'acl', 'mindspore' 
group_type = "Inference"  # flowunit group attribution 

[config]
plugin = ""  # it take effect when 'virtual_type' is 'tensorrt', it can be set to 'yolo' to provide upsampling layer 

# input port description, suporrt multiple input ports
[input]
[input.input1] # input port number, Format is input.input[N]
name = "in_1" # input port name
type = "float" # input port data type ,e.g. float or int. optional.

# output port description, suporrt multiple output ports
[output]
[output.output1] # output port number, Format is output.output[N]
name = "out_1" # output port name
```

## Ports

- **Input `input`:** float tensor — NHWC float32 [1,H,W,3] by default; shape depends on model
- **Output `output`:** float tensor — Model-defined shape

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `entry` | yes | — | Path to model file, relative to the flowunit directory |
| `virtual_type` | yes | — | tensorrt | torch | onnxruntime | acl | mindspore | openvino |
| `device` | yes | — | cuda | cpu | ascend | intel_gpu |
| `plugin` | no | "" | "yolo" enables upsample layer for legacy YOLOv3 only |

## Notes / gotchas

- `entry` is relative to the flowunit's own directory, not the graph TOML
- Use `plugin=\"yolo\"` only for YOLOv3 upsample compat; omit for all other models
- Input tensor shape must match the model's expected input exactly

## Upstream source

- `src/drivers/common/flowunit/inference/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
