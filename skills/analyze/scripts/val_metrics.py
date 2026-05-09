#!/usr/bin/env python3
"""Per-class validation metrics, confusion-matrix top confusions, and a confidence sweep.

Usage:
    python val_metrics.py <run_dir> [--data data.yaml]
    python val_metrics.py <run_dir> --from-cache <json>   # for tests / re-runs

The cache JSON shape is documented in tests/analyze/test_val_metrics.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


def _from_model(run_dir: Path, data_yaml: Path | None) -> dict:
    from ultralytics import YOLO
    weights = _common.find_weights(run_dir)
    model = YOLO(str(weights))
    kwargs = {}
    if data_yaml:
        kwargs["data"] = str(data_yaml)
    res = model.val(**kwargs)
    names = list(res.names.values()) if hasattr(res, "names") else []
    box = res.box
    overall = {
        "P": float(box.mp),
        "R": float(box.mr),
        "mAP50": float(box.map50),
        "mAP50-95": float(box.map),
    }
    per_class = []
    if hasattr(box, "ap_class_index") and len(box.ap_class_index):
        for i, cls_idx in enumerate(box.ap_class_index):
            name = names[cls_idx] if cls_idx < len(names) else f"class_{cls_idx}"
            per_class.append({
                "name": name,
                "support": int(box.nt_per_class[cls_idx]) if hasattr(box, "nt_per_class") else 0,
                "P": float(box.p[i]) if i < len(box.p) else float("nan"),
                "R": float(box.r[i]) if i < len(box.r) else float("nan"),
                "mAP50": float(box.ap50[i]) if i < len(box.ap50) else float("nan"),
                "mAP50-95": float(box.ap[i]) if i < len(box.ap) else float("nan"),
            })
    return {"names": names, "overall": overall, "per_class": per_class, "confusion_top": [], "conf_sweep": []}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--from-cache", dest="from_cache", type=Path, default=None)
    args = p.parse_args(argv)

    if args.from_cache:
        payload = json.loads(args.from_cache.read_text())
    else:
        payload = _from_model(args.run_dir, args.data)

    overall = payload.get("overall", {})
    per_class = payload.get("per_class", [])
    conf_sweep = payload.get("conf_sweep", [])
    confusion_top = payload.get("confusion_top", [])

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    if overall:
        summary_bullets.append(
            f"overall mAP50={overall.get('mAP50', float('nan')):.3f}, "
            f"mAP50-95={overall.get('mAP50-95', float('nan')):.3f}"
        )
        findings.append(
            "- overall: " + ", ".join(f"{k}={v:.3f}" for k, v in overall.items())
        )

    if per_class:
        per_class_sorted = sorted(per_class, key=lambda r: r.get("mAP50-95", 0.0))
        rows = [f"  {'class':20s} {'support':>8s} {'P':>6s} {'R':>6s} {'mAP50':>7s} {'mAP50-95':>9s}"]
        for r in per_class_sorted:
            rows.append(
                f"  {r['name']:20s} {r['support']:8d} "
                f"{r['P']:6.3f} {r['R']:6.3f} {r['mAP50']:7.3f} {r['mAP50-95']:9.3f}"
            )
        findings.append("- per-class metrics (weakest first):\n" + "\n".join(rows))

        weakest = per_class_sorted[0]
        summary_bullets.append(f"weakest class = {weakest['name']} (mAP50-95={weakest['mAP50-95']:.3f})")
        for r in per_class_sorted[:3]:
            if r["support"] < 20 and r["R"] < 0.5:
                recs.append(f"- '{r['name']}': low support ({r['support']}) and recall — needs more data")
            elif r["P"] < 0.5 and r["support"] >= 20:
                recs.append(f"- '{r['name']}': high support ({r['support']}) but low precision — likely needs better labels")

    if confusion_top:
        rows = [f"  true={c['true']:15s} pred={c['pred']:15s} count={c['count']}" for c in confusion_top]
        findings.append("- top confusion-matrix off-diagonals:\n" + "\n".join(rows))

    if conf_sweep:
        best = max(conf_sweep, key=lambda r: r["F1"])
        rows = [f"  conf={r['conf']:.2f}  F1={r['F1']:.3f}" for r in conf_sweep]
        findings.append("- confidence threshold sweep:\n" + "\n".join(rows))
        summary_bullets.append(f"suggested conf = {best['conf']:.2f} (F1={best['F1']:.3f})")
        recs.append(f"- set predict conf={best['conf']:.2f} to maximize F1")

    if not summary_bullets:
        summary_bullets.append("no metrics available")
    if not recs:
        recs.append("- no class-level interventions suggested")

    _common.print_section(
        summary_line="validation summary",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
