---
title: YAML Rules From Scratch — timeseries-qc Tutorial
description: Author default_rules and tag_rules YAML covering null, flatline, delta, range, outlier, and quality_map for timeseries-qc 0.5.0.
---

# YAML Rules From Scratch

Build a complete rules file from an empty YAML document — defaults, per-tag overrides, and optional historian `quality_map`.

!!! abstract "TL;DR"
    Put shared checks under `default_rules`, add tag-specific checks under `tag_rules` (glob patterns allowed), and optionally define `quality_map` for an external status column. Tag rules **add** to defaults; they never replace them. Use with `tsqc.check(df, rules="rules.yaml", assume_tz="UTC")`. Library version: **0.5.0**.

## Why YAML-first?

Operators and analysts can edit thresholds without touching Python. Config is batch-validated: if the file has multiple problems, `tsqc.check` reports **all** of them in one error message.

## File skeleton

```yaml
# rules.yaml
quality_map:        # optional — only if using external_quality_col
  0: good
  1: sus
  2: bad

default_rules:
  - check: null
    level: bad

tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
```

## Step 1 — Choose levels

Every rule has a `level`:

| Level | Meaning | Typical use |
|-------|---------|-------------|
| `bad` | Exclude from analysis / fail gate | nulls, hard physical limits |
| `sus` | Investigate; may still be usable | flatlines, spikes, soft outliers |
| `good` | Pass (default when no rule fires) | — |

Across all rules on a row, **worst wins**: `bad` > `sus` > `good`.

## Step 2 — Add all five built-in checks

### `null`

Flags missing values. YAML `check: null` is bare (not quoted) — YAML maps it to Python `None`, which the loader expects.

```yaml
default_rules:
  - check: null
    level: bad
```

### `flatline`

Sensor stuck within `min_delta` for at least `window`.

```yaml
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus
```

| Parameter | Required | Notes |
|-----------|----------|-------|
| `window` | yes | Duration string, e.g. `30min`, `1h`, `24h` |
| `min_delta` | no | Maximum variation to still count as flat |
| `min_duration` | no | Optional minimum stuck duration |

### `delta`

Sudden step changes between consecutive samples.

```yaml
  - check: delta
    max_delta: 50.0
    level: sus
```

Provide `min_delta`, `max_delta`, or both.

### `range`

Hard physical or process limits.

```yaml
  - check: range
    min: 0
    max: 100
    level: bad
```

### `outlier`

Rolling statistical anomaly detection.

```yaml
  - check: outlier
    method: zscore   # zscore | mad | iqr
    threshold: 3.0
    window: 24h
    level: sus
```

| Parameter | Notes |
|-----------|-------|
| `method` | `zscore`, `mad`, or `iqr` |
| `threshold` | Method-specific cutoff |
| `window` | Rolling lookback |
| `min_periods` | Optional minimum samples in the window |

## Step 3 — Add tag rules with globs

```yaml
tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
    - check: flatline
      window: 30min
      min_delta: 0.5
      level: sus

  "FOREBAY.LEVEL":
    - check: range
      min: 900
      max: 1100
      level: bad

  "*.TEMP":
    - check: outlier
      method: iqr
      threshold: 2.0
      window: 12h
      level: sus
```

Patterns use `fnmatch` wildcards (`*`, `?`). Matching tag rules are **appended** to the defaults for that tag.

## Step 4 — Optional `quality_map`

When your DataFrame has a historian status column, map raw codes to tsqc levels:

```yaml
quality_map:
  0: good
  1: sus
  2: bad
  3: bad
  4: bad
```

Then call:

```python
result = tsqc.check(
    df,
    rules="rules.yaml",
    external_quality_col="status",
    quality_mode="combined",  # or "exclusive"
    assume_tz="UTC",
)
```

YAML `quality_map` takes precedence over a `quality_map=` dict argument. Unmapped codes become `bad` with reason `source_data_quality: <value>` (for example `source_data_quality: 99`).

See [OSIsoft PI Export](osisoft-pi-export.md) for a full historian walkthrough.

## Complete example file

```yaml
# plant_rules.yaml — timeseries-qc 0.5.0

quality_map:
  0: good
  1: sus
  2: bad
  3: bad
  4: bad

default_rules:
  - check: null
    level: bad

  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus

  - check: delta
    max_delta: 50.0
    level: sus

  - check: outlier
    method: zscore
    threshold: 3.0
    window: 24h
    level: sus

tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad

  "MET.IRRADIANCE":
    - check: range
      min: 0
      max: 1050
      level: bad
    - check: delta
      max_delta: 400
      level: sus
```

## Run the check

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensor_data.csv", parse_dates=["timestamp"])

result = tsqc.check(
    df,
    rules="plant_rules.yaml",
    assume_tz="UTC",
)

print(result.summary())
result.plot().show()
result.export_report("plant_qc.html")
```

## Validation tips

- Fix every issue listed in a batch validation error before re-running.
- Quote tag patterns that contain `*` so YAML does not mis-parse them.
- Prefer putting shared null/flatline/outlier rules in `default_rules` once.
- Put plant limits that differ by sensor under `tag_rules`.

## Next steps

- [Solar Farm CSV](solar-farm-csv.md) — apply rules to a real multi-tag file
- [YAML Configuration](../yaml-configuration.md) — schema reference
- [Rule Engine](../rules.md) — how worst-wins merging works
- [OSIsoft PI Export](osisoft-pi-export.md) — `quality_map` with historian codes
