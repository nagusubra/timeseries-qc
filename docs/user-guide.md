---
title: User Guide — timeseries-qc Walkthrough
description: Complete walkthrough of timeseries-qc with loading data, running checks, interpreting results, and generating reports.
og_title: User Guide — timeseries-qc Walkthrough
og_description: Complete walkthrough of timeseries-qc with loading data, running checks, interpreting results, and generating reports.
---

# User Guide

!!! abstract "TL;DR"
    Load a DataFrame with `timestamp` and `value` columns, call `tsqc.check(df, assume_tz="UTC")`, then use `summary()`, `plot()`, and `export_report()` to inspect and share results.

A comprehensive walkthrough of the `timeseries-qc` library.

## How do I load data?

`timeseries-qc` works with any pandas DataFrame that has a `timestamp` column, a numeric `value` column, and an optional `tag_name` for multi-sensor data.

| Column | Required | Description |
|--------|----------|-------------|
| `timestamp` | Yes | Datetime column (tz-aware or tz-naive) |
| `tag_name` | No | Sensor identifier for multi-tag data |
| `value` | Yes | Numeric measurement to check |

### Multi-Tag Data

```python
import pandas as pd

df = pd.DataFrame({
    "timestamp": ["2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 02:00"],
    "tag_name": ["SENSOR.A", "SENSOR.A", "SENSOR.B"],
    "value": [100.0, 100.0, 200.0],
})
```

### Single-Tag Data

Omit the `tag_name` column or pass `tag_col=None`:

```python
result = tsqc.check(df, tag_col=None, assume_tz="UTC")
```

## How do I run quality checks?

Call `tsqc.check()` with your DataFrame and `assume_tz` for tz-naive data. You can use auto-configured defaults, a YAML rules file, or a programmatic list of rule objects.

### Auto-Configured Defaults

```python
result = tsqc.check(df, assume_tz="UTC")
```

When no rules are provided, `timeseries-qc` automatically configures rules based on 3-sigma delta thresholding. This covers the majority of real-world use cases.

### YAML-Driven Rules

```python
result = tsqc.check(df, rules="tsqc_rules.yaml")
```

See the [YAML Configuration Guide](yaml-configuration.md) for the full syntax.

### Programmatic Rules

```python
from tsqc import FlatlineRule, RangeRule

rules = [
    FlatlineRule(window="1h", min_delta=0.5, level="sus"),
    RangeRule(min_val=0, max_val=100, level="bad"),
]
result = tsqc.check(df, rules=rules, assume_tz="UTC")
```

## How does timezone handling work?

`timeseries-qc` preserves your input timezone end-to-end: pass `assume_tz` for tz-naive data, or rely on detected tz-aware timestamps.

- **Tz-naive input:** Pass `assume_tz="America/Edmonton"` (or your source timezone). The library normalises to UTC internally for consistent rule evaluation, then converts all output back to your source timezone.
- **Tz-aware input:** Your existing timezone is detected and used automatically. `assume_tz` is optional.
- **Chart display:** `result.plot()` shows the x-axis and hover tooltips in the input timezone.
- **Data inspection:** `result.df` contains timestamps in the input timezone. Use `result.display_tz` to see which timezone was applied.

```python
result = tsqc.check(df, assume_tz="America/Edmonton")
print(result.display_tz)  # "America/Edmonton"
```

## How do I interpret results?

Every row is classified as `good`, `sus`, or `bad`, with worst-wins when multiple rules fire. Use `summary()` and `issue_summary()` for per-tag and per-issue views.

### Quality Classification

Every row is classified as one of three levels:

- **good** — data passed all rules
- **sus** — data triggered a suspect-level rule (e.g., flatline warning)
- **bad** — data triggered a bad-level rule (e.g., null value, out of range)

When multiple rules fire, the worst level wins: **bad > sus > good**.

### Summary

```python
result.summary()
```

Returns a DataFrame with per-tag percentages of good, suspect, and bad data, sorted by `pct_bad` descending.

### Issue Breakdown

```python
result.issue_summary()
```

Lists contiguous segments of non-good quality with start/end timestamps, row counts, durations, and the rule names that triggered the issue.

## How do I use an external quality column?

If your data already has a historian status column, pass `external_quality_col` with `quality_mode` set to `exclusive`, `combined`, or `none`, plus a `quality_map`.

### Exclusive Mode — External Quality Only

```python
result = tsqc.check(
    df,
    external_quality_col="status",       # column with 0,1,2,3,4 values
    quality_mode="exclusive",
    quality_map={0: "good", 1: "sus", 2: "bad", 3: "bad", 4: "bad"},
    assume_tz="UTC",
)
```

When a value is not present in `quality_map`, it is automatically treated as `bad` with reason `source_data_quality: <raw_value>`.

### Combined Mode — External + Internal Rules

Merges both sources with worst-wins logic:

```python
result = tsqc.check(
    df,
    external_quality_col="status",
    quality_mode="combined",
    quality_map={0: "good", 1: "sus", 2: "bad"},
    rules=[NullRule(), RangeRule(min_val=0, max_val=100)],
    assume_tz="UTC",
)
```

- If external says `bad` and internal says `good` → final is `bad` with reason `source_data_quality: <raw_value>`
- If external says `good` and internal says `bad` → final is `bad` with reason `null values` (internal reason preserved)
- If both say `bad` → reasons are pipe-delimited: `null values|source_data_quality: <raw_value>`

### None Mode — Internal Only

Ignores the external column entirely. Does not require a `quality_map`.

```python
result = tsqc.check(df, external_quality_col="status", quality_mode="none", assume_tz="UTC")
```

This is useful when you want to keep the same code path but toggle off external quality handling.

### Column Conflict Handling

If your external quality column has the same name as the output column (e.g. both are `"quality"`), the output is automatically renamed to `qc_quality` / `qc_quality_reasons` and the original input column is preserved. A warning is issued.

### YAML `quality_map`

You can also define the quality map in your YAML rules file:

```yaml
quality_map:
  0: good
  1: sus
  2: bad
  3: bad
  4: bad

default_rules:
  - check: null
    level: bad
```

YAML `quality_map` takes precedence over the `quality_map=` function parameter when both are provided.

## How do I check timestamp health?

Call `result.check_timestamps()` to detect gaps, duplicates, non-monotonic timestamps, frequency drift, and DST ambiguities.

```python
result.check_timestamps()
```

## How do I generate reports?

Call `result.export_report("quality_report.html")` for a self-contained HTML report with the timeline chart, summary tables, and timestamp health.

```python
result.export_report("quality_report.html")
```

Produces a self-contained HTML report with the timeline chart, summary tables, and timestamp health — no internet connection required.

## FAQ

### Do I always need `assume_tz`?

For tz-naive data (typical CSV loads), yes — pass an IANA zone such as `"UTC"` or `"America/Edmonton"`. Tz-aware timestamps do not require it.

### What columns does `tsqc.check()` expect?

`timestamp` and `value` are required. `tag_name` is optional for multi-tag data; use `tag_col=None` for single-tag DataFrames.

### What does worst-wins mean?

When multiple rules flag the same row, the worse level is kept: **bad > sus > good**.

### What happens to unmapped external quality values?

They become `bad` with reason `source_data_quality: <value>`.

### Can I use YAML and Python rules together?

Pass either a YAML path (`rules="file.yaml"`) or a list of rule objects — not both as mixed sources in one call. Prefer YAML for reusable configs; use Python objects for programmatic control.

## Next Steps

- [API Reference](api-reference.md) — complete method documentation
- [Rule Engine](rules.md) — understanding how rules work
- [YAML Configuration](yaml-configuration.md) — creating YAML rule files
