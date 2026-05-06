---
description: Train an Ultralytics YOLO model. Accepts key=value args (model=, data=, epochs=, …) or natural language.
argument-hint: [model=yolo11n.pt] [data=coco8.yaml] [epochs=100] [imgsz=640] [batch=16] [device=0]
---

# /train

Train a YOLO model via the `yolo` CLI.

## Argument parsing

The user input is in `$ARGUMENTS`.

1. **If `$ARGUMENTS` contains tokens matching `key=value`** (e.g., `model=yolo11n.pt data=coco8.yaml epochs=10`), pass them through verbatim.
2. **Otherwise**, parse as natural language to extract `model`, `data`, `epochs`. Ask the user for any essentials still missing.

## Essentials and defaults

- `model` — required. Default if user agrees: `yolo11n.pt`.
- `data` — required. No default; must be provided.
- `epochs` — required. Default if user agrees: `100`.
- `imgsz` — default `640`.
- `batch` — default `16`.

## Preflight checks (do these before running)

1. **`yolo` on PATH:** run `command -v yolo`. If empty, instruct the user to `pip install ultralytics` and stop.
2. **`data` yaml exists:** if `data` ends in `.yaml`/`.yml` and is a local path, confirm it exists. If it doesn't exist locally, note that Ultralytics may auto-download named datasets like `coco8.yaml` and proceed.
3. **GPU check:** run `python3 -c "import torch; print(torch.cuda.is_available())"`. If `False`, warn the user that training on CPU will be slow and ask whether to continue.
4. **Run `/dataset-check` logic on the `data` yaml** if it's a local file (delegate to commands/dataset-check.md guidance — at minimum, confirm `train` and `val` keys resolve).

## Execution

Run via Bash, streaming output:

```bash
yolo train model=<MODEL> data=<DATA> epochs=<EPOCHS> imgsz=<IMGSZ> batch=<BATCH> [<EXTRA_KV>]
```

After the command completes, report the run directory (look for `Results saved to runs/<task>/<name>` in stdout).

## Notes for the user

- Long runs: training may take hours. Weights are saved per-epoch under `runs/<task>/<name>/weights/`. The user can Ctrl-C and resume with `resume=True`.
- If the run fails with CUDA OOM, suggest lowering `batch` (e.g., `8`, `4`) or `imgsz` (e.g., `512`).
