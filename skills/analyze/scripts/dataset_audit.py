#!/usr/bin/env python3
"""Audit a YOLO dataset for class balance, geometry, and label sanity.

Usage:
    python dataset_audit.py <data.yaml>
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def _labels_dir_for(img_dir: Path) -> Path:
    """Map .../images/<split> -> .../labels/<split>; portable across OSes."""
    parts = img_dir.parts
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            return Path(*parts[:i], "labels", *parts[i + 1 :])
    return img_dir  # fallback: caller will see no labels and surface as missing


def _list_images(img_dir: Path) -> list[Path]:
    if not img_dir.is_dir():
        return []
    return [p for p in img_dir.rglob("*") if p.suffix.lower() in _IMG_EXTS]


def _label_path_for(img: Path, img_root: Path, lbl_root: Path) -> Path:
    rel = img.relative_to(img_root).with_suffix(".txt")
    return lbl_root / rel


def _parse_label(text: str) -> list[tuple[int, float, float, float, float]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        cls = int(float(parts[0]))
        x, y, w, h = (float(v) for v in parts[1:5])
        out.append((cls, x, y, w, h))
    return out


def _audit_split(name: str, img_dir: Path, lbl_dir: Path):
    images = _list_images(img_dir)
    class_counts: Counter[int] = Counter()
    box_areas: list[float] = []
    box_aspects: list[float] = []
    resolutions: list[tuple[int, int]] = []
    out_of_bounds = 0
    zero_area = 0
    missing_labels = 0
    orphan_labels = 0

    for img in images:
        try:
            with Image.open(img) as im:
                resolutions.append(im.size)
        except Exception:
            pass
        lbl = _label_path_for(img, img_dir, lbl_dir)
        if not lbl.is_file():
            missing_labels += 1
            continue
        for cls, x, y, w, h in _parse_label(lbl.read_text()):
            class_counts[cls] += 1
            if w <= 0 or h <= 0:
                zero_area += 1
                continue
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                out_of_bounds += 1
            elif x - w / 2 < 0 or x + w / 2 > 1 or y - h / 2 < 0 or y + h / 2 > 1:
                out_of_bounds += 1
            box_areas.append(w * h)
            box_aspects.append(w / h)

    if lbl_dir.is_dir():
        for lbl in lbl_dir.rglob("*.txt"):
            rel = lbl.relative_to(lbl_dir).with_suffix("")
            if not any((img_dir / f"{rel}{ext}").is_file() for ext in _IMG_EXTS):
                orphan_labels += 1

    return {
        "name": name,
        "n_images": len(images),
        "class_counts": class_counts,
        "box_areas": box_areas,
        "box_aspects": box_aspects,
        "resolutions": resolutions,
        "out_of_bounds": out_of_bounds,
        "zero_area": zero_area,
        "missing_labels": missing_labels,
        "orphan_labels": orphan_labels,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data_yaml", type=Path)
    args = p.parse_args(argv)

    data = _common.load_data_yaml(args.data_yaml)
    names = data.get("names", [])
    splits = []
    for split in ("train", "val", "test"):
        if split in data:
            img_dir = data[split]
            lbl_dir = _labels_dir_for(img_dir)
            splits.append(_audit_split(split, img_dir, lbl_dir))

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    for s in splits:
        cc = s["class_counts"]
        if not cc:
            findings.append(f"- {s['name']}: no labeled boxes found")
            continue
        total = sum(cc.values())
        rows = []
        for idx in sorted(cc):
            label = names[idx] if idx < len(names) else f"class_{idx}"
            rows.append(f"    {idx:3d} {label:20s} {cc[idx]:6d}  ({cc[idx]/total*100:5.1f}%)")
        ratio = max(cc.values()) / max(1, min(cc.values()))
        verdict = "balanced" if ratio < 3 else ("mild imbalance" if ratio < 10 else ("imbalance" if ratio < 50 else "severe imbalance"))
        findings.append(
            f"- {s['name']}: {s['n_images']} images, {total} boxes, {len(cc)} classes; "
            f"imbalance ratio max/min = {ratio:.1f}x ({verdict})\n" + "\n".join(rows)
        )
        if ratio >= 10:
            summary_bullets.append(f"{s['name']} class imbalance {ratio:.0f}x ({verdict})")
            recs.append(f"- {s['name']}: oversample / augment minority classes or collect more data")

    if len(splits) >= 2:
        train = next((s for s in splits if s["name"] == "train"), None)
        val = next((s for s in splits if s["name"] == "val"), None)
        if train and val:
            only_in_val = set(val["class_counts"]) - set(train["class_counts"])
            only_in_train = set(train["class_counts"]) - set(val["class_counts"])
            if only_in_val:
                summary_bullets.append(f"classes missing from train: {sorted(only_in_val)}")
                findings.append(f"- divergence: classes present in val but absent from train: {sorted(only_in_val)}")
                recs.append("- add training samples for classes absent from train split")
            if only_in_train:
                findings.append(f"- divergence: classes present in train but absent from val: {sorted(only_in_train)}")

    for s in splits:
        if s["box_areas"]:
            areas = sorted(s["box_areas"])
            mid = areas[len(areas) // 2]
            findings.append(
                f"- {s['name']} bbox area distribution (normalized):\n"
                + _common.ascii_histogram(s["box_areas"], bins=8, width=30)
                + f"\n  median area = {mid:.4f}"
            )
            if mid < 0.001:
                recs.append(f"- {s['name']}: median bbox area very small (<0.1%); consider higher imgsz")

    for s in splits:
        if s["resolutions"]:
            uniq = set(s["resolutions"])
            findings.append(f"- {s['name']} resolutions: {len(uniq)} distinct; example {next(iter(uniq))}")

    sanity_total = 0
    for s in splits:
        bad = s["out_of_bounds"] + s["zero_area"] + s["missing_labels"] + s["orphan_labels"]
        sanity_total += bad
        if bad:
            findings.append(
                f"- {s['name']} label sanity: out-of-bounds={s['out_of_bounds']}, "
                f"zero-area={s['zero_area']}, images without labels={s['missing_labels']}, "
                f"labels without images={s['orphan_labels']}"
            )
    if sanity_total:
        summary_bullets.append(f"{sanity_total} label-sanity issues found")
        recs.append("- fix label-sanity issues (out-of-bounds, zero-area, orphans) before retraining")

    if not summary_bullets:
        summary_line = "dataset looks healthy"
        summary_bullets.append("class distribution within tolerable bounds")
    else:
        summary_line = "dataset has issues — see findings"

    if not recs:
        recs.append("- no immediate action required")

    _common.print_section(
        summary_line=summary_line,
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
