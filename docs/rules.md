---
title: Rule Engine — timeseries-qc
description: How the timeseries-qc rule engine works — five built-in rules (NullRule, FlatlineRule, DeltaRule, RangeRule, OutlierRule with zscore/mad/iqr), custom rules, rule ordering, and severity levels.
og_title: Rule Engine — timeseries-qc
og_description: How the timeseries-qc rule engine works — five built-in rules, custom rules, rule ordering, and severity levels.
---

# Rule Engine

!!! abstract "TL;DR"
    Rules evaluate each tag's values and flag rows as `sus` or `bad`. Five built-ins cover nulls, flatlines, deltas, ranges, and outliers; use `CustomRule` for anything else. Worst level wins when multiple rules fire.

The rule engine is the core of `timeseries-qc`. Rules define what constitutes bad or suspect data.

## How do rules work?

Each rule evaluates a pandas Series of values and returns a boolean Series of flagged rows. Rules are applied **per tag** in order. When multiple rules fire for the same row, the worst quality level wins: **bad > sus > good**.

## What built-in rules are available?

`timeseries-qc` ships five built-ins: `NullRule`, `FlatlineRule`, `DeltaRule`, `RangeRule`, and `OutlierRule`.

### NullRule

Flags rows where the value is `NaN`, `None`, or `pd.NA`.

- Default level: `bad`
- Configuration: `{check: null, level: bad}`

### FlatlineRule

Flags rows where the value has not changed by more than `min_delta` within the preceding `window` time window.

An optional `min_duration` filter suppresses flags for flat runs that are shorter
than the given duration — useful when short-lived flat periods are normal
(e.g. pump starts, cloud edges).

- Default level: `sus`
- Parameters:
  - `window` (required) — pandas offset alias, e.g. `"1h"`, `"30min"`
  - `min_delta` (optional, default `0.0`) — minimum required change to NOT be flagged
  - `min_duration` (optional) — pandas offset string; minimum time a continuous flat run must last before rows are flagged. `None` = no filter
- Configuration:
  ```yaml
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus
  ```
  With min_duration:
  ```yaml
  - check: flatline
    window: 5min
    min_delta: 0.001
    min_duration: 30min
    level: sus
  ```

**DST behaviour:** The `window` parameter is measured in **elapsed UTC time** (not wall-clock time). Timestamps are normalised to UTC internally before rule evaluation, so `FlatlineRule(window="1h")` means one elapsed UTC hour. During DST transitions:
- **Spring-forward:** One local wall-clock hour of flat data will span less UTC time (a shorter window), so the rule may flag fewer points than expected.
- **Fall-back:** Ambiguous timestamps are dropped (set to `NaT` and flagged as `bad`), so the rule never evaluates on duplicate local-time rows.

### DeltaRule

Flags rows based on the absolute change from the previous reading. Two
independent thresholds are supported:

- **`max_delta`** — flags when the change is **too large** (sensor spike / step change)
- **`min_delta`** — flags when the change is **too small** (stuck / frozen sensor)

At least one of `min_delta` or `max_delta` must be provided.

- Default level: `sus`
- Parameters:
  - `min_delta` (optional) — minimum required absolute change; changes below this are flagged
  - `max_delta` (optional) — maximum allowed absolute change; changes above this are flagged
- Configuration (only max):
  ```yaml
  - check: delta
    max_delta: 100.0
    level: sus
  ```
  Only min (stuck sensor):
  ```yaml
  - check: delta
    min_delta: 0.5
    level: sus
  ```
  Both bounds:
  ```yaml
  - check: delta
    min_delta: 0.5
    max_delta: 100.0
    level: sus
  ```

### RangeRule

Flags rows where the value is outside `[min, max]`.

- Default level: `bad`
- Parameters: `min` (lower bound, optional), `max` (upper bound, optional)
- Configuration: `{check: range, min: 0, max: 100, level: bad}`

### OutlierRule

Flags rows that are statistical outliers using one of three configurable methods.
Supports both **global** (full-series) and **rolling** (time-windowed) computation.

!!! info "Which method should I use?"
    - **`zscore`** — Classic approach. Best when your data is roughly normally distributed without extreme outliers in the baseline.
    - **`mad`** — Robust variant using Median Absolute Deviation. Less sensitive to extreme values in the baseline statistics. Good for sensor data with occasional spikes.
    - **`iqr`** — Distribution-free. Works well with skewed data. Tukey's fences (k=1.5) is a standard choice.

- Default level: `sus`
- Parameters:
  - `method` (required) — One of `zscore`, `mad`, `iqr`
  - `threshold` (optional, default `3.0` for zscore/mad, `1.5` for iqr) — Sensitivity
  - `window` (optional) — pandas offset alias for rolling mode, e.g. `"24h"`, `"7d"`. Omit or set to `null` for global mode.
  - `min_periods` (optional, default `10`) — Minimum non-NaN observations needed
- Global mode (full-series):
  ```yaml
  - check: outlier
    method: zscore
    threshold: 3.0
    level: sus
  ```
- Rolling mode (time-windowed):
  ```yaml
  - check: outlier
    method: iqr
    threshold: 2.0
    window: 24h
    level: bad
  ```

## How does rule ordering work?

Rules run in definition order. Each row starts as `good`; later rules can escalate quality to `sus` or `bad`, and triggered rule names are appended to `quality_reasons`.

1. Start with quality = "good"
2. For each rule, if the rule fires:
   - If rule level is "bad" → quality = "bad"
   - If rule level is "sus" and quality is "good" → quality = "sus"
3. The triggered rule names are appended to `quality_reasons`

## What are severity levels?

`bad` means exclude from analysis; `sus` means investigate. There is no separate "warning" level beyond these two non-good classifications.

- **bad** — data should be excluded from analysis
- **sus** — data may be unreliable and warrants investigation

## How do I create custom rules?

Use `CustomRule` with a function that takes a Series and returns a boolean mask of flagged rows.

```python
from tsqc import CustomRule

def check_negative(series):
    return series < 0

rule = CustomRule(fn=check_negative, name="negative", level="bad")
```

## What are the default rules?

When no rules are provided, `timeseries-qc` auto-configures null, flatline, and 3-sigma delta rules:

```python
NullRule(level="bad")
FlatlineRule(window="1h", min_delta=0.0, level="sus")
DeltaRule(max_delta=3 * std, level="sus")
```

## FAQ

### Do tag rules replace default rules?

No. Tag rules **add** to `default_rules`; they do not replace them.

### Can one row have multiple reasons?

Yes. Triggered rule names are collected in `quality_reasons` (pipe-delimited when both external and internal reasons apply).

### Which outlier method should I pick?

Use `zscore` for roughly normal data, `mad` when the baseline has spikes, and `iqr` for skewed distributions.

### Does FlatlineRule use wall-clock or UTC time?

`window` is measured in **elapsed UTC time**. Timestamps are normalised to UTC before evaluation.

### How do I suppress short flat periods?

Pass `min_duration` on `FlatlineRule` (e.g. `min_duration: 30min`) so short flat runs are not flagged.

## Next Steps

- [YAML Configuration](yaml-configuration.md) — configuring rules via YAML
- [API Reference](api-reference.md) — complete rule class documentation
- [User Guide](user-guide.md) — walkthrough with examples
