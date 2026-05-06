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
- `name` — auto-generated if not supplied; see "Run naming" below.
- `tag` — **not a `yolo` arg**; if the user passes `tag=<slug>`, do NOT forward it to `yolo` — instead append `_<slug>` to the auto-generated `name`.

## Run naming

If the user did not pass `name=…`, synthesize one and pass it as `name=<synthesized>` so the run lands at `runs/<task>/<synthesized>/` instead of an opaque `runs/<task>/train`/`train2`/`train3`.

Format:

```
<YYYYMMDD-HHMM>_<model-stem>_<data-stem>_e<epochs>_b<batch>[_<git-sha7>][_<tag>]
```

- `YYYYMMDD-HHMM`: local time, e.g. `20260506-1432`.
- `<model-stem>`: model basename without `.pt`, e.g. `yolo11n`, `yolo11s-seg`.
- `<data-stem>`: data basename without `.yaml`/`.yml`, e.g. `coco8`. For ImageFolder dirs, the directory name.
- `e<epochs>` / `b<batch>`: the actual values being passed.
- `<git-sha7>`: only if cwd is inside a git repo — `git rev-parse --short=7 HEAD`. Append `-dirty` if `git status --porcelain` is non-empty.
- `<tag>`: only if the user passed a `tag=<slug>` token (slug-cased, no spaces).

If `name=` was supplied by the user, use it verbatim and skip synthesis (still record the user-supplied name in the experiment log per below).

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

## Experiment log (opt-in)

If `.ultralytics.yml` (cwd or any ancestor) sets `experiment_log: <path>` (e.g. `runs/EXPERIMENTS.md`), append a row to that file after the run completes — successful or failed. Resolve the path relative to the YAML's directory. Always write to the LOCAL filesystem (not the remote), even when execution is remote.

If the file doesn't exist, create it with this header:

```markdown
# Experiments

| Started | Run name | Task | Command | Results | Notes |
|---|---|---|---|---|---|
```

Then append one row per run:

```markdown
| 20260506-1432 | 20260506-1432_yolo11n_coco8_e100_b16_a1b2c3d | detect | `yolo train model=yolo11n.pt data=coco8.yaml epochs=100 batch=16 name=20260506-1432_yolo11n_coco8_e100_b16_a1b2c3d` | mAP50-95 0.612, mAP50 0.831, weights `runs/detect/20260506-1432_…/weights/best.pt` | _(fill in)_ |
```

Field rules:
- **Started**: same `YYYYMMDD-HHMM` used in the name.
- **Run name**: the synthesized or user-supplied name.
- **Task**: detect/segment/classify/pose/obb (infer from the model suffix).
- **Command**: the exact `yolo …` invocation, NOT the ssh wrapper. Backtick-quoted.
- **Results**: parse the final-summary lines from `yolo` stdout. Look for `all` row of the metrics table — capture mAP50-95 and mAP50. Add the relative path to `weights/best.pt`. If the run errored, write `FAILED — <one-line reason>` instead.
- **Notes**: literal placeholder `_(fill in)_` so the user edits later.

When `experiment_log` is unset, do nothing.

## Notes for the user

- Long runs: training may take hours. Weights are saved per-epoch under `runs/<task>/<name>/weights/`. The user can Ctrl-C and resume with `resume=True`.
- If the run fails with CUDA OOM, suggest lowering `batch` (e.g., `8`, `4`) or `imgsz` (e.g., `512`).
