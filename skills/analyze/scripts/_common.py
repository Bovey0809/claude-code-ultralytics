"""Shared helpers for the analyze-skill scripts.

Intentionally small: run-dir discovery, ASCII chart helpers, and the
SUMMARY/FINDINGS/RECOMMENDATIONS output-contract enforcer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import yaml

_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def find_results_csv(run_dir: Path) -> Path:
    p = Path(run_dir) / "results.csv"
    if not p.is_file():
        raise FileNotFoundError(f"No results.csv in {run_dir}")
    return p


def find_weights(run_dir: Path, prefer: str = "best") -> Path:
    weights_dir = Path(run_dir) / "weights"
    candidates = [prefer, "last", "best"]
    seen = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        p = weights_dir / f"{name}.pt"
        if p.is_file():
            return p
    raise FileNotFoundError(f"No best.pt/last.pt under {weights_dir}")


def load_data_yaml(path: Path) -> dict:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    base = Path(raw.get("path", path.parent)).expanduser()
    if not base.is_absolute():
        base = (path.parent / base).resolve()
    out = dict(raw)
    out["path"] = base
    for key in ("train", "val", "test"):
        if key in raw and raw[key] is not None:
            sub = Path(raw[key])
            out[key] = sub if sub.is_absolute() else (base / sub).resolve()
    return out


def ascii_sparkline(values: Sequence[float], width: int = 40) -> str:
    if not values:
        return " " * width
    n = len(values)
    if n == 1:
        sampled = [float(values[0])] * width
    else:
        sampled = []
        for i in range(width):
            t = i * (n - 1) / (width - 1) if width > 1 else 0
            lo = int(t)
            hi = min(lo + 1, n - 1)
            frac = t - lo
            sampled.append(float(values[lo]) * (1 - frac) + float(values[hi]) * frac)
    lo, hi = min(sampled), max(sampled)
    if hi - lo < 1e-12:
        return _SPARK_CHARS[0] * width
    span = hi - lo
    return "".join(
        _SPARK_CHARS[min(len(_SPARK_CHARS) - 1, int((v - lo) / span * (len(_SPARK_CHARS) - 1)))]
        for v in sampled
    )


def ascii_histogram(values: Iterable[float], bins: int = 10, width: int = 40) -> str:
    vals = [float(v) for v in values]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        hi = lo + 1.0
    edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in vals:
        idx = min(bins - 1, int((v - lo) / (hi - lo) * bins))
        counts[idx] += 1
    cmax = max(counts) or 1
    lines = []
    for i, c in enumerate(counts):
        bar = "█" * int(c / cmax * width)
        lines.append(f"[{edges[i]:.3g}, {edges[i+1]:.3g}) | {bar} {c}")
    return "\n".join(lines)


def print_section(
    summary_line: str,
    summary_bullets: Sequence[str],
    findings: str,
    recommendations: str,
) -> None:
    """Print the SUMMARY/FINDINGS/RECOMMENDATIONS contract.

    summary_bullets: top-3 findings as short strings.
    findings, recommendations: pre-formatted multiline blocks.
    """
    print("## SUMMARY")
    print(summary_line)
    for b in summary_bullets:
        print(f"- {b}")
    print()
    print("## FINDINGS")
    print(findings.rstrip())
    print()
    print("## RECOMMENDATIONS")
    print(recommendations.rstrip())
