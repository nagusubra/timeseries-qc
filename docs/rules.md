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

- Default level: `sus`
- Parameters: `window` (pandas offset alias), `min_delta` (minimum required change)
- Configuration: `{check: flatline, window: 1h, min_delta: 0.001, level: sus}`

### DeltaRule

Flags rows where the absolute change from the previous row exceeds `threshold`.

- Default level: `sus`
- Parameters: `threshold` (maximum allowed absolute change)
- Configuration: `{check: delta, threshold: 50.0, level: sus}`

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
DeltaRule(threshold=3 * std, level="sus")
```

## Next Steps

- [YAML Configuration](yaml-configuration.md) — configuring rules via YAML
- [API Reference](api-reference.md) — complete rule class documentation
- [User Guide](user-guide.md) — walkthrough with examples
