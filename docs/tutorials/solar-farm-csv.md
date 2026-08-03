---
title: Solar Farm CSV Walkthrough — timeseries-qc Tutorial
description: Load a multi-tag solar farm CSV, run tsqc.check with assume_tz, and use summary, plot, and export_report. timeseries-qc 0.5.0.
---

# Solar Farm CSV Walkthrough

End-to-end quality control on multi-tag solar SCADA data exported as CSV.

!!! abstract "TL;DR"
    Load a CSV with `timestamp`, `tag_name`, and `value`, call `tsqc.check(df, assume_tz="UTC")`, then use `result.summary()`, `result.plot().show()`, and `result.export_report("report.html")`. Always pass `assume_tz` for tz-naive CSV timestamps. Library version: **0.5.0**.

## What you will build

A short script that:

1. Loads one week of hourly solar farm tags
2. Runs built-in QC rules (or a YAML file)
3. Prints a per-tag quality summary
4. Opens a Plotly quality timeline
5. Writes a self-contained HTML report

## Example data shape

Use long-format SCADA data — one row per timestamp per tag:

| timestamp | tag_name | value |
|-----------|----------|-------|
| 2026-06-01 00:00:00 | INVERTER.MW | 0.0 |
| 2026-06-01 00:00:00 | MET.IRRADIANCE | 0.0 |
| 2026-06-01 00:00:00 | TRACKER.ANGLE | 0.0 |
| 2026-06-01 12:00:00 | INVERTER.MW | 8.4 |
| … | … | … |

Typical tags for a single-axis tracking plant:

| Tag | Description | Units |
|-----|-------------|-------|
| `INVERTER.MW` | AC inverter output | MW |
| `MET.IRRADIANCE` | Global horizontal irradiance | W/m² |
| `TRACKER.ANGLE` | Tracker tilt | degrees |

## Step 1 — Install and import

```python
# Requires timeseries-qc 0.5.0
import tsqc
import pandas as pd

print(tsqc.__version__)  # expect 0.5.0
```

## Step 2 — Load the CSV

```python
df = pd.read_csv(
    "solar_farm.csv",
    parse_dates=["timestamp"],
)

print(df.head())
print(df["tag_name"].unique())
print(f"Rows: {len(df)}, date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
```

CSV exports are almost always timezone-naive. Pass `assume_tz` in the next step so windows, gaps, and charts stay consistent.

## Step 3 — Run the quality check

### Minimal (built-in defaults)

```python
result = tsqc.check(df, assume_tz="UTC")
```

### With plant-specific YAML rules

```python
result = tsqc.check(
    df,
    rules="solar_rules.yaml",
    assume_tz="UTC",
)
```

Example `solar_rules.yaml`:

```yaml
default_rules:
  - check: null
    level: bad

tag_rules:
  INVERTER.MW:
    - check: range
      min: 0.0
      max: 11.0
      level: bad
    - check: delta
      max_delta: 5.0
      level: sus
    - check: flatline
      window: 3h
      min_delta: 0.05
      level: sus

  MET.IRRADIANCE:
    - check: range
      min: 0.0
      max: 1050.0
      level: bad
    - check: delta
      max_delta: 400.0
      level: sus
    - check: flatline
      window: 2h
      min_delta: 1.0
      level: sus

  TRACKER.ANGLE:
    - check: range
      min: -90.0
      max: 90.0
      level: bad
    - check: delta
      max_delta: 30.0
      level: sus
    - check: flatline
      window: 4h
      min_delta: 1.0
      level: sus
```

Tag rules **add** to `default_rules`; they do not replace them.

## Step 4 — Inspect the summary

```python
summary = result.summary()
print(summary)
```

`summary()` returns a DataFrame sorted by `pct_bad` descending:

| Column | Meaning |
|--------|---------|
| `tag_name` | Sensor / tag id |
| `total_rows` | Rows for that tag |
| `pct_good` / `pct_sus` / `pct_bad` | Percent of rows at each level |
| `n_good` / `n_sus` / `n_bad` | Row counts |

```python
critical = summary[summary["pct_bad"] > 5.0]
print(critical[["tag_name", "pct_bad", "n_bad"]])
```

For contiguous issue runs (start/end/duration/reasons):

```python
print(result.issue_summary())
```

## Step 5 — Plot the quality timeline

```python
fig = result.plot(title="Solar Farm QC — Week of 2026-06-01")
fig.show()
```

Each tag is a horizontal bar colored by `good` / `sus` / `bad`. Hover tooltips show reasons such as `flatline @ 42.5000` or `null values`. Timestamps display in the same timezone you passed via `assume_tz` (`UTC` here).

Clip to a daylight window if needed:

```python
fig = result.plot(
    tags=["INVERTER.MW", "MET.IRRADIANCE"],
    start="2026-06-03T06:00:00",
    end="2026-06-03T20:00:00",
    title="Daylight QC slice",
)
fig.show()
```

## Step 6 — Export an HTML report

```python
result.export_report(
    "solar_farm_qc_report.html",
    title="Solar Farm QC Report",
)
```

The report is self-contained (no CDN required) and suitable for emailing ops or attaching to a ticket.

## Complete script

```python
import tsqc
import pandas as pd

df = pd.read_csv("solar_farm.csv", parse_dates=["timestamp"])

result = tsqc.check(
    df,
    rules="solar_rules.yaml",
    assume_tz="UTC",
)

print(result.summary())
print(result.issue_summary())

# Optional: timestamp gaps / duplicates / drift
print(result.check_timestamps(expected_freq="1h"))

result.plot(title="Solar Farm QC").show()
result.export_report("solar_farm_qc_report.html", title="Solar Farm QC Report")
```

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| `ValueError` about timezone-naive timestamps | Pass `assume_tz="UTC"` (or the plant IANA zone) |
| Wide-format CSV (one column per tag) | Melt to long format with `tag_name` / `value` |
| Chart shows unexpected local time | Output always uses the input/`assume_tz` zone |
| Tag rules seem to “override” defaults | They **add** to defaults — put shared rules in `default_rules` only once |

## Next steps

- [YAML Rules From Scratch](yaml-rules-from-scratch.md) — author all five built-in checks
- [OSIsoft PI Export](osisoft-pi-export.md) — merge historian quality codes
- [Quickstart](../quickstart.md) — five-line overview
- [Visualization](../visualization.md) — plot options in depth
