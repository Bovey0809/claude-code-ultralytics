# Ultralytics Claude Code Plugin — v1 Design

**Date:** 2026-05-06
**Status:** Approved (brainstorm)

## Goal

Ship a minimal Claude Code plugin that gives users a teaching skill plus four
slash commands for the Ultralytics YOLO workflow. The skill provides
*understanding*; the commands provide *action*.

## Audience

Both researchers/ML engineers and beginners. The skill teaches concepts on
demand, while commands stay as thin wrappers over the `yolo` CLI with sensible
defaults.

## Plugin layout

```
claude-code-ultralytics/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── yolo/
│       └── SKILL.md
└── commands/
    ├── train.md
    ├── predict.md
    ├── export.md
    └── dataset-check.md
```

`plugin.json` carries `name`, `version` (`0.1.0`), `description`, and author
metadata. No MCP server, no hooks, no scripts.

## The `yolo` skill

`skills/yolo/SKILL.md` — concise reference (~150 lines max), not a tutorial.

**Frontmatter description triggers on:** Ultralytics, YOLO, training a
detector, `data.yaml`, `.pt` weights, ONNX/CoreML/TensorRT export, model
variants (`yolo11n/s/m/l/x`), tasks (`detect`/`segment`/`classify`/`pose`/`obb`).

**Sections:**

1. **When to use** — trigger conditions.
2. **Core mental model** — `model + data + task → train/val/predict/export`;
   task inferred from model suffix (`-seg`, `-cls`, `-pose`, `-obb`).
3. **Key arguments cheatsheet** — `model`, `data`, `epochs`, `imgsz`, `batch`,
   `device`, `project`, `name`, `resume` with typical values.
4. **Dataset YAML shape** — minimum viable example with `path`, `train`,
   `val`, `names`.
5. **Command dispatch rules** — when the user asks to train/predict/export,
   prefer invoking the matching slash command.
6. **Common pitfalls** — CUDA OOM → lower `batch`/`imgsz`; class mismatch;
   relative vs absolute dataset paths; `yolo` CLI vs `ultralytics` Python.

## Commands

All four use the **hybrid argument** pattern: if `$ARGUMENTS` contains
`key=value` tokens, pass through to `yolo` verbatim; otherwise parse natural
language and ask for any missing essentials before building the command. Each
runs via Bash and streams output.

Each command file has frontmatter with `description` and `argument-hint`, plus
a body telling Claude how to parse args and the exact Bash invocation.

### `/train`

- Essentials: `model`, `data`, `epochs`.
- Defaults when unspecified: `model=yolo11n.pt`, `epochs=100`, `imgsz=640`.
- Before running: apply `dataset-check` logic to the `data` yaml; warn if no
  GPU detected.
- Runs: `yolo train model=… data=… epochs=… …`.
- Notes long runs in output; user can Ctrl-C or background.

### `/predict`

- Essentials: `model` (weights path or pretrained name), `source`
  (image/dir/video/URL/`0` for webcam).
- Defaults: `save=True`, `conf=0.25`.
- Runs: `yolo predict model=… source=… …`.
- Reports the `runs/predict/…` output dir on completion.

### `/export`

- Essentials: `model` (`.pt` path), `format`.
- If `format` omitted: list options
  (`onnx/coreml/engine/tflite/openvino/torchscript/saved_model/pb/paddle/ncnn`)
  and ask.
- Runs: `yolo export model=… format=… …`.
- Reports the produced artifact path.

### `/dataset-check`

- Input: path to a `data.yaml`, or auto-find one in cwd.
- Validates:
  - YAML parses; `path`, `train`, `val` keys present and resolve on disk.
  - Image counts per split (non-zero).
  - Labels directory exists; sampled label files non-empty.
  - `len(names)` matches the max class id seen in a sample of label files.
- Pure validation — does **not** invoke `yolo`.
- Output: pass/fail report listing all problems with actionable fixes.

## Dependencies and preconditions

- Each command checks `command -v yolo`; if missing, instructs
  `pip install ultralytics`.
- `dataset-check` uses Python one-liners with `pyyaml` (a transitive dep of
  `ultralytics`).
- Plugin ships pure markdown + JSON. No bundled Python scripts.

## Error handling

- Missing essentials → ask the user, don't guess.
- `yolo` non-zero exit → surface stderr verbatim. For known errors (CUDA OOM,
  missing dataset file, class-count mismatch), the skill's "Common pitfalls"
  section provides the remedy.
- `dataset-check` reports all failures at once as a list, not a single fatal.

## Smoke test plan

Manual, on a machine with `ultralytics` installed:

1. `/dataset-check` on bundled `coco8.yaml` → pass.
2. `/train model=yolo11n.pt data=coco8.yaml epochs=1` → completes.
3. `/predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg` →
   produces output.
4. `/export model=yolo11n.pt format=onnx` → produces `.onnx`.

No automated tests in v1.

## Out of scope (v1)

- `yolo tune` (hyperparameter tuning).
- Benchmarking, tracking, solutions.
- Hub login / integration.
- MCP server.
- Automated tests.
