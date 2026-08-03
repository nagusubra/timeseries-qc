---
title: CI Gate on Data Quality — timeseries-qc Tutorial
description: Fail GitHub Actions builds when result.summary() pct_bad exceeds a threshold using timeseries-qc 0.5.0.
---

# CI Gate on Data Quality

Treat sensor / fixture data quality as a merge gate: fail the job when any tag’s `pct_bad` exceeds a threshold.

!!! abstract "TL;DR"
    Run `tsqc.check`, call `result.summary()`, and `sys.exit(1)` (or raise) when `(summary["pct_bad"] > threshold).any()`. Wire the script into GitHub Actions after installing `timeseries-qc`. Library version: **0.5.0**.

## Why gate on quality?

Unit tests catch code bugs. A QC gate catches **bad fixtures and broken exports** before they poison training sets, dashboards, or acceptance tests.

## Step 1 — Write a gate script

```python
# scripts/qc_gate.py
"""Fail CI when any tag exceeds pct_bad threshold. timeseries-qc 0.5.0"""
from __future__ import annotations

import argparse
import sys

import pandas as pd
import tsqc


def main() -> int:
    parser = argparse.ArgumentParser(description="timeseries-qc CI gate")
    parser.add_argument("--csv", required=True, help="Path to long-format CSV")
    parser.add_argument("--rules", default=None, help="Optional YAML rules path")
    parser.add_argument("--assume-tz", default="UTC", help="IANA zone for tz-naive data")
    parser.add_argument(
        "--max-pct-bad",
        type=float,
        default=5.0,
        help="Fail if any tag has pct_bad above this value",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to write HTML report (always written before exit)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv, parse_dates=["timestamp"])
    kwargs = {"assume_tz": args.assume_tz}
    if args.rules:
        kwargs["rules"] = args.rules

    result = tsqc.check(df, **kwargs)
    summary = result.summary()

    if args.report:
        result.export_report(args.report, title="CI QC Gate Report")

    critical = summary[summary["pct_bad"] > args.max_pct_bad]
    print(summary.to_string(index=False))

    if len(critical) == 0:
        print(f"PASS: all tags <= {args.max_pct_bad}% bad")
        return 0

    print(f"FAIL: {len(critical)} tag(s) exceed {args.max_pct_bad}% bad:")
    print(critical[["tag_name", "pct_bad", "n_bad", "total_rows"]].to_string(index=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Local dry run:

```bash
python scripts/qc_gate.py \
  --csv fixtures/sensor_week.csv \
  --rules rules/plant_rules.yaml \
  --assume-tz UTC \
  --max-pct-bad 5 \
  --report artifacts/qc_report.html
```

## Step 2 — Optional historian column in CI fixtures

If fixtures include a status column:

```python
result = tsqc.check(
    df,
    rules="rules/plant_rules.yaml",
    external_quality_col="status",
    quality_mode="combined",
    assume_tz="UTC",
)
```

Unmapped status values count as `bad` with reason `source_data_quality: <value>`, which increases `pct_bad` and can trip the gate — intentional if you want unknown codes to fail CI.

## Step 3 — GitHub Actions workflow

```yaml
# .github/workflows/qc-gate.yml
name: Data quality gate

on:
  push:
    paths:
      - "fixtures/**"
      - "rules/**"
      - "scripts/qc_gate.py"
  pull_request:
    paths:
      - "fixtures/**"
      - "rules/**"
      - "scripts/qc_gate.py"

jobs:
  qc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install timeseries-qc
        run: pip install "timeseries-qc==0.5.0"

      - name: Run QC gate
        run: |
          python scripts/qc_gate.py \
            --csv fixtures/sensor_week.csv \
            --rules rules/plant_rules.yaml \
            --assume-tz UTC \
            --max-pct-bad 5 \
            --report artifacts/qc_report.html

      - name: Upload QC report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: qc-report
          path: artifacts/qc_report.html
```

`if: always()` uploads the HTML report even when the gate fails, so reviewers can open the timeline in the Actions artifact.

## Step 4 — Choose thresholds

| Threshold | Typical use |
|-----------|-------------|
| `0` | Golden fixtures must be fully clean |
| `1`–`5` | Production-like samples with rare known faults |
| Per-tag policies | Filter `summary` before the check (see below) |

Per-tag critical list:

```python
CRITICAL_TAGS = {"INVERTER.MW", "MET.IRRADIANCE"}
MAX_PCT_BAD = 2.0

summary = result.summary()
subset = summary[summary["tag_name"].isin(CRITICAL_TAGS)]
if (subset["pct_bad"] > MAX_PCT_BAD).any():
    raise SystemExit("Critical tags failed QC gate")
```

## Step 5 — Surface failures in PR checks

Keep the gate as a required status check on protected branches. Pair with:

- `result.issue_summary()` printed on failure for start/end/reason
- Artifact HTML from `export_report`
- A comment bot only if you already have one — not required

```python
issues = result.issue_summary()
print(issues.sort_values("totalDuration_hours", ascending=False).head(20))
```

## Complete minimal inline gate

For a one-off job without a separate script:

```python
import sys
import pandas as pd
import tsqc

df = pd.read_csv("fixtures/sensor_week.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="rules/plant_rules.yaml", assume_tz="UTC")
summary = result.summary()
result.export_report("qc_report.html")

if (summary["pct_bad"] > 5.0).any():
    print(summary[summary["pct_bad"] > 5.0])
    sys.exit(1)
```

## Next steps

- [Solar Farm CSV](solar-farm-csv.md) — generate a report locally first
- [YAML Rules From Scratch](yaml-rules-from-scratch.md) — tighten rules before gating
- [Report Generation](../report-generation.md) — HTML report options
- [Quickstart](../quickstart.md) — API refresher
