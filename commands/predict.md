---
description: Run YOLO inference on an image, directory, video, URL, or webcam. Accepts key=value args or natural language.
argument-hint: "[model=yolo11n.pt] [source=path/url/0] [conf=0.25] [save=True]"
---

# /predict

Run inference with a YOLO model.

## Argument parsing

The user input is in `$ARGUMENTS`.

1. If it contains `key=value` tokens, pass them through.
2. Otherwise, parse natural language to extract `model` and `source`. Ask the user for whichever essential is missing.

## Essentials and defaults

- `model` — required. Default if user agrees: `yolo11n.pt`.
- `source` — required. No default.
  - File path (image or video), directory, URL, or `0` for webcam.
- `conf` — default `0.25`.
- `save` — default `True` (saves annotated outputs).

## Preflight

- `command -v yolo`; if empty, instruct `pip install ultralytics` and stop.

## Execution

```bash
yolo predict model=<MODEL> source=<SOURCE> conf=<CONF> save=<SAVE> [<EXTRA_KV>]
```

After the command completes, locate the line `Results saved to runs/<task>/predict<N>` in stdout and report the directory to the user.
