---
title: Quickstart — timeseries-qc in 5 Lines
description: Run your first time series quality check in 5 lines of Python with timeseries-qc. Classify every row as good, suspect, or bad.
---

# Quickstart

Run a complete quality check on your time series data in 5 lines.

## Step 1: Import and Load Data

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensor_data.csv")
```

Your data must contain at least a `timestamp` column and a `value` column. An optional `tag_name` column lets you run checks on multiple sensors at once.

## Step 2: Run the Check

```python
result = tsqc.check(df, assume_tz="UTC")
```

The `assume_tz` parameter tells the library what timezone your timestamps are in. If your CSV already contains UTC-aware timestamps (ISO 8601 with `+00:00`), you can omit it.

## Step 3: View Results

```python
result.plot().show()
print(result.summary())
```

The timeline chart shows a color-coded horizontal bar for each tag. The summary table shows the percentage of good, suspect, and bad data per tag.

## Complete Example

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensor_data.csv")
result = tsqc.check(df, assume_tz="UTC")
result.plot().show()
print(result.summary())
result.export_report("report.html")
```

## Output Schema

`result.df` adds two columns:

| Column | Values | Notes |
|--------|--------|-------|
| `quality` | `"good"`, `"sus"`, `"bad"` | Worst-level rule wins |
| `quality_reasons` | e.g. `"flatline\|range"` | Pipe-delimited triggered rule names |

## Next Steps

- [User Guide](user-guide.md) — detailed walkthrough
- [YAML Configuration](yaml-configuration.md) — create rules without Python
- [API Reference](api-reference.md) — full method documentation
