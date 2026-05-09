#!/usr/bin/env python3
"""Diagnose a YOLO training run from its results.csv.

Usage:
    python training_curves.py <run_dir>
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common  # noqa: E402


_TRAIN_LOSS_COLS = ["train/box_loss", "train/cls_loss", "train/dfl_loss"]
_VAL_LOSS_COLS = ["val/box_loss", "val/cls_loss", "val/dfl_loss"]
_KEY_METRIC = "metrics/mAP50-95(B)"


def _classify_trend(series: pd.Series) -> str:
    s = series.dropna()
    if len(s) < 3:
        return "insufficient-data"
    first, last = s.iloc[: max(1, len(s) // 4)].mean(), s.iloc[-max(1, len(s) // 4):].mean()
    delta = last - first
    rng = s.max() - s.min()
    if rng < 1e-9:
        return "flat"
    rel = delta / (abs(first) + 1e-9)
    if abs(rel) < 0.02:
        return "plateau"
    return "decreasing" if delta < 0 else "increasing"


def _detect_overfit(df: pd.DataFrame) -> bool:
    if "val/box_loss" not in df or "train/box_loss" not in df:
        return False
    n = len(df)
    if n < 10:
        return False
    half = n // 2
    train_trend = _classify_trend(df["train/box_loss"].iloc[half:])
    val_trend = _classify_trend(df["val/box_loss"].iloc[half:])
    map_trend = _classify_trend(df[_KEY_METRIC].iloc[half:]) if _KEY_METRIC in df else "n/a"
    return train_trend == "decreasing" and val_trend in ("increasing", "plateau") and map_trend in ("plateau", "decreasing", "flat")


def _detect_underfit(df: pd.DataFrame) -> bool:
    if "train/box_loss" not in df:
        return False
    train_trend = _classify_trend(df["train/box_loss"])
    final_map = df[_KEY_METRIC].iloc[-1] if _KEY_METRIC in df else None
    return train_trend == "decreasing" and (final_map is None or final_map < 0.3)


def _detect_nans(df: pd.DataFrame) -> list[tuple[str, int]]:
    hits = []
    for col in df.columns:
        if df[col].dtype.kind in "fc":
            mask = df[col].apply(lambda v: isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
            if mask.any():
                hits.append((col, int(df.index[mask][0])))
    return hits


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path)
    args = p.parse_args(argv)

    csv_path = _common.find_results_csv(args.run_dir)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    findings_parts: list[str] = []
    summary_bullets: list[str] = []
    recs: list[str] = []

    best_epoch = None
    best_map = None
    if _KEY_METRIC in df.columns:
        best_idx = df[_KEY_METRIC].idxmax()
        best_epoch = int(df.loc[best_idx, "epoch"]) if "epoch" in df.columns else int(best_idx)
        best_map = float(df.loc[best_idx, _KEY_METRIC])
        final_map = float(df[_KEY_METRIC].iloc[-1])
        summary_bullets.append(
            f"best epoch = {best_epoch}, mAP50-95 = {best_map:.4f} (final = {final_map:.4f})"
        )
        findings_parts.append(
            f"- best epoch (by {_KEY_METRIC}) = {best_epoch}; best mAP50-95 = {best_map:.4f}; final = {final_map:.4f}"
        )

    spark_lines = []
    for col in _TRAIN_LOSS_COLS + _VAL_LOSS_COLS + ["metrics/mAP50(B)", _KEY_METRIC]:
        if col in df.columns:
            trend = _classify_trend(df[col])
            spark = _common.ascii_sparkline(df[col].ffill().fillna(0).tolist(), width=40)
            spark_lines.append(f"  {col:28s} [{trend:12s}] {spark}")
    if spark_lines:
        findings_parts.append("- per-metric trend (sparkline + classification):\n" + "\n".join(spark_lines))

    overfit = _detect_overfit(df)
    underfit = _detect_underfit(df)
    if overfit:
        summary_bullets.append("overfitting detected (val loss rising / mAP plateau)")
        findings_parts.append("- overfitting: train loss still falling while val loss rises or mAP50-95 plateaus")
        recs.append("- reduce epochs or enable early-stopping; increase augmentation; consider weight decay")
    if underfit:
        summary_bullets.append("underfitting suspected (train loss still falling, low final mAP)")
        findings_parts.append("- underfitting: train loss has not converged and final mAP50-95 is low")
        recs.append("- train more epochs, increase model capacity, or raise learning rate")

    nans = _detect_nans(df)
    if nans:
        first_col, first_row = nans[0]
        summary_bullets.append(f"NaN/Inf detected in {first_col} starting row {first_row}")
        findings_parts.append("- divergence: " + "; ".join(f"{c} first NaN/Inf at row {r}" for c, r in nans))
        recs.append("- lower lr0, enable AMP only on supported hardware, or check for corrupt labels")

    if "lr/pg0" in df.columns:
        lr_final = float(df["lr/pg0"].iloc[-1])
        lr_initial = float(df["lr/pg0"].iloc[0])
        findings_parts.append(f"- lr schedule: initial={lr_initial:.2e}, final={lr_final:.2e}")

    if not summary_bullets:
        summary_line = "training appears healthy"
    elif overfit or nans:
        summary_line = "training has issues — see findings"
    else:
        summary_line = "training mostly healthy"

    if not recs:
        recs.append("- training looks healthy; no immediate action needed")

    _common.print_section(
        summary_line=summary_line,
        summary_bullets=summary_bullets[:3],
        findings="\n".join(findings_parts),
        recommendations="\n".join(recs),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
