---
description: Train an Ultralytics YOLO model. Accepts key=value args (model=, data=, epochs=, …) or natural language.
argument-hint: "[model=yolo11n.pt] [data=coco8.yaml] [epochs=100] [imgsz=640] [batch=16] [device=0]"
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

0. **Detect remote.** Read `ULTRALYTICS_REMOTE` env var; if unset, search cwd and ancestors for `.ultralytics.yml` and read its `remote`/`workdir` keys. If a remote is configured, every Bash command in steps 1, 3, and "Execution" below must be wrapped as `ssh <remote> 'bash -lc "cd <workdir> && <cmd>"'`. See the "Remote execution" section of the `yolo` skill for full pattern. Step 2 (local YAML existence) and step 4 (local YAML validation) still target the LOCAL filesystem — the dataset must also exist on the remote, which the user is responsible for syncing.
1. **`yolo` on PATH:** run `command -v yolo` (wrapped if remote). If empty, instruct the user to `pip install ultralytics` (on the remote, if applicable) and stop.
2. **`data` yaml exists locally:** if `data` ends in `.yaml`/`.yml` and is a local path, confirm it exists. If it doesn't exist locally, note that Ultralytics may auto-download named datasets like `coco8.yaml` and proceed. (When running remote, also remind the user the dataset must be on the remote at the same relative path, or be a name Ultralytics will auto-download.)
3. **GPU check:** run `python3 -c "import torch; print(torch.cuda.is_available())"` (wrapped if remote). If `False`, warn the user that training on CPU will be slow and ask whether to continue.
4. **If `data` is a local `.yaml`/`.yml` file, validate inline:** confirm `train` and `val` keys exist and resolve to directories or files. If they don't, surface the issue and ask the user to run `/ultralytics:dataset-check <data>` for a full report before training.

## Execution

Run via Bash, streaming output. Local form:

```bash
yolo train model=<MODEL> data=<DATA> epochs=<EPOCHS> imgsz=<IMGSZ> batch=<BATCH> [<EXTRA_KV>]
```

Remote form (when a remote is configured per step 0):

```bash
ssh <REMOTE> 'bash -lc "cd <WORKDIR> && yolo train model=<MODEL> data=<DATA> epochs=<EPOCHS> imgsz=<IMGSZ> batch=<BATCH> [<EXTRA_KV>]"'
```

After the command completes, report the run directory (look for `Results saved to runs/<task>/<name>` in stdout). For remote runs, the path is on the remote; offer the user a pull command:

```bash
rsync -av <REMOTE>:<WORKDIR>/runs/<task>/<name>/ ./runs/<task>/<name>/
```

## Notes for the user

- Long runs: training may take hours. Weights are saved per-epoch under `runs/<task>/<name>/weights/`. The user can Ctrl-C and resume with `resume=True`.
- If the run fails with CUDA OOM, suggest lowering `batch` (e.g., `8`, `4`) or `imgsz` (e.g., `512`).
