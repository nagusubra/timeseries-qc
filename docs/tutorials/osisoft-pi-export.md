---
title: OSIsoft PI Export — timeseries-qc Tutorial
description: Wire an OSIsoft PI / historian CSV export with external_quality_col and quality_mode combined or exclusive in timeseries-qc 0.5.0.
---

# OSIsoft PI Export

Use historian quality codes from an OSIsoft PI (or similar) export alongside — or instead of — internal tsqc rules.

!!! abstract "TL;DR"
    Pass the status column as `external_quality_col`, map codes with YAML `quality_map` or `quality_map=`, and choose `quality_mode="combined"` (merge, worst-wins) or `"exclusive"` (historian only). Unmapped codes become `bad` with reason `source_data_quality: <value>`. Library version: **0.5.0**.

## When to use this tutorial

You already have PI / Aspen / Wonderware / OPC UA quality integers on each row and want tsqc to:

- Respect those codes as first-class quality, and/or
- Layer flatline / range / outlier checks on top

## Expected export shape

| timestamp | tag_name | value | pi_quality |
|-----------|----------|-------|------------|
| 2026-06-01 12:00:00 | GENERATOR.MW | 145.2 | 0 |
| 2026-06-01 12:00:00 | GENERATOR.MW | 0.0 | 192 |
| 2026-06-01 13:00:00 | FOREBAY.LEVEL | 1002.1 | 193 |

Rename columns if needed (`time_col`, `tag_col`, `value_col`) so they match what you pass to `tsqc.check`.

## Quality modes

| Mode | Behavior |
|------|----------|
| `exclusive` | External quality **only** — internal rules do not run |
| `combined` | External + internal, worst-wins (`bad` > `sus` > `good`) |
| `none` | Internal only; ignores the external column (escape hatch; no `quality_map` required) |

## Step 1 — Define a quality map

Common PI System status examples (adjust to your site’s dictionary):

| Code | Typical meaning | tsqc level |
|------|-----------------|------------|
| `0` | Good | `good` |
| `192` | Bad | `bad` |
| `193` | Questionable | `sus` |
| `194` | I/O Timeout | `bad` |
| `195` | Bad Input | `bad` |

### In YAML (preferred)

```yaml
# pi_rules.yaml
quality_map:
  0: good
  192: bad
  193: sus
  194: bad
  195: bad

default_rules:
  - check: null
    level: bad
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus

tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
```

### As a Python dict

```python
quality_map = {
    0: "good",
    192: "bad",
    193: "sus",
    194: "bad",
    195: "bad",
}
```

If both YAML and `quality_map=` are provided, **YAML wins**.

## Step 2 — Combined mode (recommended default)

Historian codes and internal rules both contribute. Worst level wins; reasons are pipe-delimited.

```python
import tsqc
import pandas as pd

df = pd.read_csv("pi_export.csv", parse_dates=["timestamp"])

result = tsqc.check(
    df,
    rules="pi_rules.yaml",
    external_quality_col="pi_quality",
    quality_mode="combined",
    assume_tz="America/Chicago",  # plant wall-clock zone for tz-naive exports
)

print(result.df[["timestamp", "tag_name", "value", "quality", "quality_reasons"]].head())
```

Example reasons:

```text
source_data_quality: 192
flatline @ 45.2000
source_data_quality: 192|flatline @ 45.2000
```

Unmapped codes (for example `99`) become `bad` with:

```text
source_data_quality: 99
```

## Step 3 — Exclusive mode (trust the historian)

Skip internal rule evaluation; only the mapped external column drives quality.

```python
result = tsqc.check(
    df,
    external_quality_col="pi_quality",
    quality_mode="exclusive",
    quality_map={
        0: "good",
        192: "bad",
        193: "sus",
        194: "bad",
        195: "bad",
    },
    assume_tz="America/Chicago",
)
```

Use exclusive mode when you only need a uniform good/sus/bad timeline and HTML report over existing PI quality — without re-running flatline/range logic.

## Step 4 — Escape hatch (`quality_mode="none"`)

Temporarily ignore the status column without dropping it from the DataFrame:

```python
result = tsqc.check(
    df,
    rules="pi_rules.yaml",
    external_quality_col="pi_quality",
    quality_mode="none",
    assume_tz="America/Chicago",
)
```

No `quality_map` is required in this mode.

## Column name conflicts

If your input already has a column named `quality` (or `quality_reasons`), tsqc auto-renames the **output** columns to `qc_quality` / `qc_quality_reasons` and preserves the input column. Prefer renaming the historian column (e.g. `pi_quality`) up front for clarity.

## Inspect and report

```python
summary = result.summary()
print(summary.sort_values("pct_bad", ascending=False).head())

# Rows driven by historian codes
ext = result.df[result.df["quality_reasons"].str.contains("source_data_quality", na=False)]
print(ext[["tag_name", "quality", "quality_reasons"]].value_counts())

result.plot(title="PI Export QC").show()
result.export_report("pi_qc_report.html", title="PI Historian QC")
```

## From PI Web API to DataFrame (sketch)

```python
# Pseudocode — adapt to your PI Web API client
# Fetch recorded values + status, then:
df = pd.DataFrame({
    "timestamp": timestamps,       # often tz-naive local wall clock
    "tag_name": tags,
    "value": values,
    "pi_quality": status_codes,    # integers from PI
})

result = tsqc.check(
    df,
    rules="pi_rules.yaml",
    external_quality_col="pi_quality",
    quality_mode="combined",
    assume_tz="America/Chicago",
)
```

Always set `assume_tz` to the historian’s wall-clock zone for naive timestamps.

## Next steps

- [SCADA Integration](../scada-integration.md) — broader historian patterns
- [YAML Rules From Scratch](yaml-rules-from-scratch.md) — author internal rules
- [CI Gate on Data Quality](ci-gate-data-quality.md) — fail builds on `pct_bad`
- [User Guide](../user-guide.md) — external quality reference
