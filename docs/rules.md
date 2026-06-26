---
title: Rule Engine — timeseries-qc
description: How the timeseries-qc rule engine works — built-in rules, custom rules, rule ordering, and severity levels.
---

# Rule Engine

The rule engine is the core of `timeseries-qc`. Rules define what constitutes bad or suspect data.

## How Rules Work

Each rule is a class that evaluates a pandas Series of values and returns a boolean Series indicating which rows are flagged.

Rules are applied **per tag** in order. When multiple rules fire for the same row, the worst quality level wins: **bad > sus > good**.

## Built-in Rules

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

## Rule Ordering

Rules are applied in the order they are defined. For each row:

1. Start with quality = "good"
2. For each rule, if the rule fires:
   - If rule level is "bad" → quality = "bad"
   - If rule level is "sus" and quality is "good" → quality = "sus"
3. The triggered rule names are appended to `quality_reasons`

## Severity Levels

- **bad** — data should be excluded from analysis
- **sus** — data may be unreliable and warrants investigation

## Custom Rules

You can create custom rules using the `CustomRule` class:

```python
from tsqc import CustomRule

def check_negative(series):
    return series < 0

rule = CustomRule(fn=check_negative, name="negative", level="bad")
```

## Default Rules

When no rules are provided, `timeseries-qc` auto-configures rules using 3-sigma delta thresholding:

```python
NullRule(level="bad")
FlatlineRule(window="1h", min_delta=0.0, level="sus")
DeltaRule(max_delta=3 * std, level="sus")
```

## Next Steps

- [YAML Configuration](yaml-configuration.md) — configuring rules via YAML
- [API Reference](api-reference.md) — complete rule class documentation
- [User Guide](user-guide.md) — walkthrough with examples
