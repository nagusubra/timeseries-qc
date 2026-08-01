#!/usr/bin/env python3
"""Stdlib benchmark harness for tsqc.check() — no extra deps.

Usage:
    python benchmarks/bench_check.py
    python benchmarks/bench_check.py --write-baseline benchmarks/baseline.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

import tsqc
from tsqc import DeltaRule, FlatlineRule, NullRule, OutlierRule, RangeRule


def _make_df(n_rows: int, n_tags: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows_per_tag = n_rows // n_tags
    frames = []
    for t in range(n_tags):
        ts = pd.date_range("2026-01-01", periods=rows_per_tag, freq="1min", tz="UTC")
        values = 50 + rng.normal(0, 5, rows_per_tag)
        # Inject ~2% nulls, ~1% spikes
        null_idx = rng.choice(rows_per_tag, size=max(1, rows_per_tag // 50), replace=False)
        spike_idx = rng.choice(rows_per_tag, size=max(1, rows_per_tag // 100), replace=False)
        values[null_idx] = np.nan
        values[spike_idx] = 9999.0
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": ts,
                    "tag_name": f"TAG_{t:03d}",
                    "value": values,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _run_once(df: pd.DataFrame, rules: list) -> float:
    t0 = time.perf_counter()
    tsqc.check(df, rules=rules, assume_tz="UTC")
    return time.perf_counter() - t0


def bench_case(n_rows: int, n_tags: int, repeats: int = 3) -> dict:
    df = _make_df(n_rows, n_tags)
    rules = [
        NullRule(level="bad"),
        FlatlineRule(window="1h", min_delta=0.001, level="sus"),
        DeltaRule(max_delta=50.0, level="sus"),
        RangeRule(min_val=-100, max_val=200, level="bad"),
        OutlierRule(method="zscore", threshold=3.0, level="sus"),
    ]

    # Warmup
    _run_once(df, rules)

    times: list[float] = []
    peak_mib = 0.0
    for _ in range(repeats):
        tracemalloc.start()
        elapsed = _run_once(df, rules)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        times.append(elapsed)
        peak_mib = max(peak_mib, peak / (1024 * 1024))

    return {
        "n_rows": n_rows,
        "n_tags": n_tags,
        "repeats": repeats,
        "median_s": round(statistics.median(times), 6),
        "min_s": round(min(times), 6),
        "max_s": round(max(times), 6),
        "peak_tracemalloc_mib": round(peak_mib, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-baseline",
        type=Path,
        default=None,
        help="Write results JSON to this path",
    )
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    cases = [
        (10_000, 10),
        (100_000, 50),
        (500_000, 100),
    ]
    results = []
    for n_rows, n_tags in cases:
        print(f"Benchmarking {n_rows:,} rows × {n_tags} tags ...")
        result = bench_case(n_rows, n_tags, repeats=args.repeats)
        results.append(result)
        print(
            f"  median={result['median_s']:.4f}s  "
            f"peak_mem~={result['peak_tracemalloc_mib']:.1f} MiB"
        )

    payload = {
        "library": "timeseries-qc",
        "cases": results,
    }
    if args.write_baseline:
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.write_baseline.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote baseline to {args.write_baseline}")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
