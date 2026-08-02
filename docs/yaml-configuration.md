---
title: YAML Configuration — timeseries-qc
description: Configure timeseries-qc rules using YAML files with batch config validation. No Python required. Supports outlier detection, glob patterns for tag matching, and quality maps for historian status columns.
og_title: YAML Configuration — timeseries-qc
og_description: Configure timeseries-qc rules using YAML files with batch config validation. No Python required.
---

# YAML Configuration

!!! abstract "TL;DR"
    Put rules in a YAML file with `default_rules` and optional `tag_rules` / `quality_map`, then pass the path to `tsqc.check(df, rules="tsqc_rules.yaml")`. Tag rules add to defaults; configs are batch-validated with helpful error messages.

You can define quality control rules in a plain YAML file — no Python required.

## What does a YAML rules file look like?

A rules file has optional `quality_map`, a `default_rules` list applied to every tag, and optional `tag_rules` keyed by tag name or glob pattern.

```yaml
# tsqc_rules.yaml
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
  "FOREBAY.LEVEL":
    - check: range
      min: 900
      max: 1100
      level: bad
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
    - check: flatline
      window: 30min
      min_delta: 0.5
      level: sus
    - check: outlier
      method: iqr
      threshold: 2.0
      level: bad
```

## What sections are supported?

YAML configs support three top-level sections: `quality_map`, `default_rules`, and `tag_rules`.

### `quality_map` (optional)

Maps raw external quality column values to tsqc levels (`good`, `sus`, `bad`). Used together with `external_quality_col` in `tsqc.check()`. Unmapped values are treated as `bad` with reason `source_data_quality: <value>`.

```yaml
quality_map:
  0: good
  1: sus
  2: bad
  3: bad
  4: bad
```

If both YAML `quality_map` and the `quality_map=` function parameter are provided, the YAML version takes precedence.

### `default_rules`

Rules applied to **every** tag in the dataset. Each entry is a rule specification with a `check` type and optional parameters.

### `tag_rules`

Rules applied to **specific** tags only, identified by tag name or glob pattern.

## Which check types are supported?

Five check types map to the built-in rules: `null`, `flatline`, `delta`, `range`, and `outlier`.

| Check | Parameters | Default Level |
|-------|-----------|---------------|
| `null` | none | `bad` |
| `flatline` | `window` (required), `min_delta`, `min_duration` | `sus` |
| `delta` | `min_delta`, `max_delta` (at least one required) | `sus` |
| `range` | `min`, `max` (at least one required) | `bad` |
| `outlier` | `method` (`zscore`, `mad`, or `iqr`), `threshold`, `window`, `min_periods` | `sus` |

## How do glob patterns work?

Tag patterns support `*` and `?` wildcards via `fnmatch`, so one entry can cover a family of sensors.

| Pattern | Matches |
|---------|---------|
| `GENERATOR.*` | `GENERATOR.MW`, `GENERATOR.VAR`, etc. |
| `*.TEMP` | `REACTOR.TEMP`, `BOILER.TEMP`, etc. |
| `SENSOR?` | `SENSOR1`, `SENSORA`, etc. |

## How do I use a YAML rules file?

Pass the file path to the `rules=` argument of `tsqc.check()`:

```python
result = tsqc.check(df, rules="tsqc_rules.yaml")
```

## How are YAML rules loaded and applied?

Defaults apply to every tag; matching `tag_rules` are appended. Invalid configs are batch-validated so you see all issues at once.

When you pass a YAML file path to `tsqc.check()`, the file is parsed and rules are applied per tag:

1. All `default_rules` are applied to every tag
2. Matching `tag_rules` are appended to the default rules
3. If no rules match a tag, the auto-configured defaults are used

## FAQ

### Do tag rules override default rules?

No. Tag rules **add** to `default_rules` for matching tags; they do not replace them.

### Why does `check: null` look weird in YAML?

In YAML, bare `null` is a null literal (Python `None`). That is intentional — `check: null` maps to `NullRule`.

### Does YAML `quality_map` override the Python parameter?

Yes. When both are provided, the YAML `quality_map` takes precedence over `quality_map=`.

### What happens to unmapped quality codes?

Unmapped values become `bad` with reason `source_data_quality: <value>`.

### Can I configure outliers in YAML?

Yes. Use `check: outlier` with `method` (`zscore`, `mad`, or `iqr`) and optional `threshold`, `window`, and `min_periods`.

## Next Steps

- [Rule Engine](rules.md) — how rules work
- [User Guide](user-guide.md) — walkthrough with examples
