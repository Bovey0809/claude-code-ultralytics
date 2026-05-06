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

- **Detect remote.** Read `ULTRALYTICS_REMOTE` env var; if unset, search cwd and ancestors for `.ultralytics.yml` and read its `remote`/`workdir` keys. If a remote is configured, wrap every Bash invocation below as `ssh <remote> 'bash -lc "cd <workdir> && <cmd>"'`. See the "Remote execution" section of the `yolo` skill.
- `command -v yolo` (wrapped if remote); if empty, instruct `pip install ultralytics` and stop.
- **`source` translation.** `source=https://…` and webcam (`source=0`) work over SSH unchanged. A local file/dir path will fail when wrapped — either have the user `rsync` the file to the remote first, or fall back to running locally for that one invocation. Ask the user which.

## Execution

Local form:

```bash
yolo predict model=<MODEL> source=<SOURCE> conf=<CONF> save=<SAVE> [<EXTRA_KV>]
```

Remote form:

```bash
ssh <REMOTE> 'bash -lc "cd <WORKDIR> && yolo predict model=<MODEL> source=<SOURCE> conf=<CONF> save=<SAVE> [<EXTRA_KV>]"'
```

After the command completes, locate the line `Results saved to runs/<task>/predict<N>` in stdout and report the directory to the user. For remote runs, offer:

```bash
rsync -av <REMOTE>:<WORKDIR>/runs/detect/predict<N>/ ./runs/detect/predict<N>/
```
