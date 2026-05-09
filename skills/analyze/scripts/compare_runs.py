#!/usr/bin/env python3
"""Compare two or more YOLO training runs side-by-side.

Usage:
    python compare_runs.py <run_a> <run_b> [<run_c> ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_METRICS = [
    "metrics/precision(B)",
    "metrics/recall(B)",
    "metrics/mAP50(B)",
    "metrics/mAP50-95(B)",
]


def _load_run(run_dir: Path) -> dict:
    df = pd.read_csv(_common.find_results_csv(run_dir))
    df.columns = [c.strip() for c in df.columns]
    info = {"name": run_dir.name, "df": df}
    args_yaml = run_dir / "args.yaml"
    info["args"] = yaml.safe_load(args_yaml.read_text()) if args_yaml.is_file() else {}
    return info


def _best_metrics(df: pd.DataFrame) -> dict:
    out = {}
    if "metrics/mAP50-95(B)" in df.columns:
        idx = df["metrics/mAP50-95(B)"].idxmax()
        for m in _METRICS:
            if m in df.columns:
                out[m] = float(df.loc[idx, m])
        out["best_epoch"] = int(df.loc[idx, "epoch"]) if "epoch" in df.columns else int(idx)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dirs", nargs="+", type=Path)
    args = p.parse_args(argv)

    runs = [_load_run(r) for r in args.run_dirs]

    findings: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    header = "  metric                          " + "  ".join(f"{r['name']:>12s}" for r in runs)
    rows = [header]
    bests = [_best_metrics(r["df"]) for r in runs]
    for m in _METRICS:
        cells = []
        for b in bests:
            cells.append(f"{b.get(m, float('nan')):>12.4f}")
        rows.append(f"  {m:30s}" + "  ".join(cells))
    rows.append(
        "  best_epoch                    " + "  ".join(f"{b.get('best_epoch', -1):>12d}" for b in bests)
    )
    findings.append("- best-epoch metrics:\n" + "\n".join(rows))

    base = bests[0].get("metrics/mAP50-95(B)")
    if base is not None:
        for r, b in zip(runs[1:], bests[1:]):
            cur = b.get("metrics/mAP50-95(B)")
            if cur is None:
                continue
            delta = cur - base
            verdict = "improved" if delta > 0 else ("regressed" if delta < 0 else "unchanged")
            summary_bullets.append(f"{r['name']} vs {runs[0]['name']}: mAP50-95 {delta:+.4f} ({verdict})")

    stab = []
    for r in runs:
        col = "metrics/mAP50-95(B)"
        if col in r["df"].columns:
            stab.append(f"  {r['name']:12s} val mAP50-95 std = {r['df'][col].std():.4f}")
    if stab:
        findings.append("- training stability (lower std = smoother):\n" + "\n".join(stab))

    keys = sorted({k for r in runs for k in r["args"].keys()})
    if keys:
        diff_rows = []
        for k in keys:
            vals = [str(r["args"].get(k, "—")) for r in runs]
            if len(set(vals)) > 1:
                diff_rows.append(f"  {k:20s} " + "  ".join(f"{v:>14s}" for v in vals))
        if diff_rows:
            findings.append(
                "- args.yaml differences ("
                + ", ".join(r["name"] for r in runs)
                + "):\n"
                + "\n".join(diff_rows)
            )
            recs.append("- inspect args.yaml deltas above; isolate one variable at a time")

    if not summary_bullets:
        summary_bullets.append("runs have comparable mAP50-95")
    if not recs:
        recs.append("- pick the run with highest mAP50-95 for promotion")

    _common.print_section(
        summary_line=f"compared {len(runs)} runs",
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
