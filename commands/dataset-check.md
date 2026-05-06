---
description: Validate an Ultralytics dataset YAML — checks paths resolve, splits have images, labels exist, class ids match `names`. Pure validation, does not invoke yolo.
argument-hint: [path/to/data.yaml]
---

# /dataset-check

Validate a YOLO dataset YAML before training. Pure read-only — does **not** invoke `yolo`.

## Argument parsing

`$ARGUMENTS` is either a path to a `.yaml` / `.yml` file, or empty.

If empty: search the cwd for `data.yaml`, `dataset.yaml`, or any single `*.yaml` at the top level. If exactly one candidate, use it; otherwise ask the user which file to check.

## Validation

Run this Python one-liner via Bash, substituting `<YAML_PATH>`:

```bash
python3 - <<'PY'
import os, sys, glob, yaml, random
yaml_path = "<YAML_PATH>"
problems = []
ok = []
info = []

try:
    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)
except Exception as e:
    print(f"FAIL: cannot parse YAML: {e}")
    sys.exit(1)

skip_fs_checks = False
raw_path = cfg.get("path")
if raw_path is None:
    info.append("'path' key missing; Ultralytics may resolve splits against its datasets_dir (typically ~/datasets) — absence here does not necessarily block training")
    skip_fs_checks = True
    root = os.path.dirname(os.path.abspath(yaml_path))
else:
    root = raw_path
    if not os.path.isabs(root):
        root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(yaml_path)), root))
    if not os.path.isdir(root):
        info.append(f"'path' resolved to '{root}' which does not exist on disk; Ultralytics may resolve this against its datasets_dir — absence here does not necessarily block training")
        skip_fs_checks = True
    else:
        ok.append(f"path resolves: {root}")

names = cfg.get("names")
if names is None:
    problems.append("missing 'names'")
else:
    n_classes = len(names) if isinstance(names, (list, dict)) else 0
    ok.append(f"names: {n_classes} classes")

max_class_seen = -1
for split in ("train", "val"):
    rel = cfg.get(split)
    if rel is None:
        problems.append(f"missing '{split}' key")
        continue
    if skip_fs_checks:
        ok.append(f"{split}: key present (filesystem check skipped — path not resolved locally)")
        continue
    if isinstance(rel, str):
        entries = [rel]
    elif isinstance(rel, list):
        entries = rel
    else:
        problems.append(f"{split}: unsupported type {type(rel).__name__}; expected str or list[str]")
        continue
    total_imgs = 0
    for entry in entries:
        if not isinstance(entry, str):
            problems.append(f"{split}: unsupported entry type {type(entry).__name__} in list; expected str")
            continue
        split_dir = entry if os.path.isabs(entry) else os.path.join(root, entry)
        if not os.path.isdir(split_dir):
            # could be a .txt list file
            if os.path.isfile(split_dir):
                ok.append(f"{split}: list file {split_dir}")
                continue
            problems.append(f"{split} '{split_dir}' does not exist")
            continue
        imgs = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
            imgs += glob.glob(os.path.join(split_dir, "**", ext), recursive=True)
        if not imgs:
            problems.append(f"{split}: no images found in {split_dir}")
            continue
        total_imgs += len(imgs)
        labels_dir = split_dir.replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)
        if labels_dir == split_dir:
            labels_dir = os.path.join(os.path.dirname(split_dir), "labels", os.path.basename(split_dir))
        if not os.path.isdir(labels_dir):
            problems.append(f"{split}: labels dir not found at {labels_dir}")
            continue
        sample = random.sample(imgs, min(20, len(imgs)))
        empties = 0
        for img in sample:
            stem = os.path.splitext(os.path.basename(img))[0]
            lbl = os.path.join(labels_dir, stem + ".txt")
            if not os.path.isfile(lbl):
                empties += 1
                continue
            try:
                with open(lbl) as lf:
                    for line in lf:
                        parts = line.split()
                        if parts:
                            max_class_seen = max(max_class_seen, int(parts[0]))
            except Exception as e:
                problems.append(f"{split}: cannot read {lbl}: {e}")
        if empties:
            problems.append(f"{split}: {empties}/{len(sample)} sampled images missing label files")
    if total_imgs > 0:
        ok.append(f"{split}: {total_imgs} images")

if isinstance(names, list):
    n_max = len(names) - 1
elif isinstance(names, dict):
    n_max = max(int(k) for k in names.keys())
else:
    n_max = None
if n_max is not None and max_class_seen > n_max:
    problems.append(f"label class id {max_class_seen} > max valid id {n_max}")
elif n_max is not None and max_class_seen >= 0:
    ok.append(f"max class id seen: {max_class_seen} (within {n_max})")

print("CHECKS PASSED:")
for line in ok:
    print(f"  - {line}")
if info:
    print("NOTES:")
    for line in info:
        print(f"  - {line}")
if problems:
    print("PROBLEMS:")
    for line in problems:
        print(f"  - {line}")
    sys.exit(1)
print("OK")
PY
```

## Reporting

- If the script exits 0 with `OK`, report success and list the passed checks.
- If it exits non-zero, report each problem and suggest fixes:
  - `path` not a directory → check `path:` is correct relative to YAML location.
  - missing `train`/`val` key → add it.
  - no images → check the split subdirectory.
  - labels dir not found → Ultralytics expects `images/<split>/` paired with `labels/<split>/`.
  - missing label files → either remove unlabeled images or create empty `.txt` for negatives.
  - class id ≥ `len(names)` → either expand `names` or fix labels.

## Preflight

- Requires `python3` and `pyyaml`. `pyyaml` is installed by `pip install ultralytics`. If import fails, instruct: `pip install pyyaml`.
