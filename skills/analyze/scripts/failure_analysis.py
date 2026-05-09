#!/usr/bin/env python3
"""Classify per-image failure modes for a YOLO model.

Modes: FP (prediction with no GT match), FN (GT with no prediction),
localization (correct class, IoU<0.5), class-confusion (IoU>=0.5, wrong class).

Usage:
    python failure_analysis.py <run_dir> [--data data.yaml] [--split val] [--top N]
    python failure_analysis.py <run_dir> --from-cache <json>     # for tests / re-runs
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_MODES = ("FP", "FN", "localization", "class-confusion")


def _iou_xywh(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax1, ay1, ax2, ay2 = ax - aw / 2, ay - ah / 2, ax + aw / 2, ay + ah / 2
    bx1, by1, bx2, by2 = bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    ua = max(1e-9, aw * ah + bw * bh - inter)
    return inter / ua


def _from_model(run_dir: Path, data_yaml: Path | None, split: str, iou_thr: float = 0.5) -> dict:
    from ultralytics import YOLO
    if data_yaml is None:
        raise SystemExit("--data is required when not using --from-cache")
    data = _common.load_data_yaml(data_yaml)
    img_dir = Path(data[split])
    # Derive labels dir by replacing the "images" path component with "labels".
    parts = img_dir.parts
    lbl_dir = img_dir
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            lbl_dir = Path(*parts[:i], "labels", *parts[i + 1:])
            break
    weights = _common.find_weights(run_dir)
    model = YOLO(str(weights))
    names = list(model.names.values()) if hasattr(model, "names") else []

    errors = []
    for img in sorted(img_dir.rglob("*")):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        lbl = lbl_dir / img.relative_to(img_dir).with_suffix(".txt")
        gts = []
        if lbl.is_file():
            for line in lbl.read_text().splitlines():
                row = line.split()
                if len(row) >= 5:
                    gts.append((int(float(row[0])), tuple(float(v) for v in row[1:5])))
        result = model.predict(str(img), verbose=False)[0]
        preds = []
        if result.boxes is not None:
            xywhn = result.boxes.xywhn.cpu().numpy()
            cls = result.boxes.cls.cpu().numpy().astype(int)
            conf = result.boxes.conf.cpu().numpy()
            for c, b, s in zip(cls, xywhn, conf):
                preds.append((int(c), tuple(b.tolist()), float(s)))

        gt_matched = [False] * len(gts)
        pred_matched = [False] * len(preds)
        for i, (pc, pb, ps) in enumerate(preds):
            best, best_iou = -1, 0.0
            for j, (gc, gb) in enumerate(gts):
                if gt_matched[j]:
                    continue
                iou = _iou_xywh(pb, gb)
                if iou > best_iou:
                    best, best_iou = j, iou
            if best >= 0 and best_iou >= iou_thr:
                gc = gts[best][0]
                gt_matched[best] = True
                pred_matched[i] = True
                if gc != pc:
                    errors.append({
                        "image": str(img),
                        "mode": "class-confusion",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "true_class": names[gc] if gc < len(names) else str(gc),
                        "iou": float(best_iou),
                    })
            elif best >= 0 and best_iou > 0:
                gt_matched[best] = True
                pred_matched[i] = True
                gc = gts[best][0]
                if gc == pc:
                    errors.append({
                        "image": str(img),
                        "mode": "localization",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "iou": float(best_iou),
                    })
                else:
                    errors.append({
                        "image": str(img),
                        "mode": "class-confusion",
                        "pred_class": names[pc] if pc < len(names) else str(pc),
                        "true_class": names[gc] if gc < len(names) else str(gc),
                        "iou": float(best_iou),
                    })
        for i, m in enumerate(pred_matched):
            if not m:
                pc, _, ps = preds[i]
                errors.append({
                    "image": str(img),
                    "mode": "FP",
                    "pred_class": names[pc] if pc < len(names) else str(pc),
                    "score": ps,
                })
        for j, m in enumerate(gt_matched):
            if not m:
                gc = gts[j][0]
                errors.append({
                    "image": str(img),
                    "mode": "FN",
                    "true_class": names[gc] if gc < len(names) else str(gc),
                })
    return {"errors": errors}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--split", default="val")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--from-cache", dest="from_cache", type=Path, default=None)
    args = p.parse_args(argv)

    payload = (
        json.loads(args.from_cache.read_text())
        if args.from_cache
        else _from_model(args.run_dir, args.data, args.split)
    )
    errors = payload.get("errors", [])

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    if not errors:
        _common.print_section(
            summary_line="no errors / no failures detected on this split",
            summary_bullets=["model matched all ground-truth boxes within IoU threshold"],
            findings="- no FP, FN, localization, or class-confusion errors recorded",
            recommendations="- (no action — verify your data path is correct if this is unexpected)",
        )
        return 0

    mode_counts = Counter(e["mode"] for e in errors)
    summary_bullets.append(", ".join(f"{m}={mode_counts.get(m, 0)}" for m in _MODES))

    findings.append("- error counts by mode: " + ", ".join(f"{m}={mode_counts.get(m, 0)}" for m in _MODES))

    for mode in _MODES:
        per_cls: Counter[str] = Counter()
        for e in errors:
            if e["mode"] != mode:
                continue
            key = e.get("pred_class") or e.get("true_class") or "?"
            per_cls[key] += 1
        if per_cls:
            findings.append(
                f"- {mode} per class: "
                + ", ".join(f"{k}={v}" for k, v in per_cls.most_common())
            )

    for mode in _MODES:
        per_img: Counter[str] = Counter()
        for e in errors:
            if e["mode"] == mode:
                per_img[e["image"]] += 1
        if per_img:
            top = per_img.most_common(args.top)
            rows = [f"  {count:4d}  {path}" for path, count in top]
            findings.append(f"- worst-{args.top} images for {mode}:\n" + "\n".join(rows))

    if mode_counts.get("FN", 0) > mode_counts.get("FP", 0) * 2:
        recs.append("- many FNs vs FPs: lower confidence threshold or add training data for missed classes")
    if mode_counts.get("FP", 0) > mode_counts.get("FN", 0) * 2:
        recs.append("- many FPs vs FNs: raise confidence threshold or harden negative samples")
    if mode_counts.get("localization", 0) > mode_counts.get("class-confusion", 0):
        recs.append("- localization > class-confusion: train at higher imgsz or refine bbox labels")
    else:
        recs.append("- class-confusion >= localization: review label consistency for confused class pairs")

    _common.print_section(
        summary_line=f"{sum(mode_counts.values())} errors across {len(_MODES)} modes",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
