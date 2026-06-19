---
title: API Reference — timeseries-qc
description: Complete API reference for timeseries-qc including tsqc.check(), QCResult methods, and all rule classes.
---

# API Reference

## `tsqc.check()`

The main entry point for running quality checks.

```python
result = tsqc.check(
    df: pd.DataFrame,
    *,
    time_col: str = "timestamp",
    tag_col: str | None = "tag_name",
    value_col: str = "value",
    rules: list[Rule] | str | None = None,
    quality_col: str = "quality",
    reasons_col: str = "quality_reasons",
    assume_tz: str | None = None,
) -> QCResult
```

### Parameters

| Argument | Default | Description |
|----------|---------|-------------|
| `df` | required | Input DataFrame with timestamp, value, and optionally tag_name columns |
| `time_col` | `"timestamp"` | Name of the timestamp column |
| `tag_col` | `"tag_name"` | Name of the tag column. `None` for single-tag mode |
| `value_col` | `"value"` | Name of the value column |
| `rules` | `None` | List of Rule objects, path to a YAML file, or `None` for auto-configured defaults |
| `quality_col` | `"quality"` | Output column name for quality label |
| `reasons_col` | `"quality_reasons"` | Output column name for triggered rule names |
| `assume_tz` | `None` | IANA timezone for tz-naive input, e.g. `"UTC"` or `"America/Chicago"` |

### Raises

- `ValueError`: Missing columns, unparseable timestamps, tz-naive without `assume_tz`, invalid `assume_tz`, missing YAML file

## `QCResult`

The object returned by `tsqc.check()`.

### Properties

#### `.df` -> pd.DataFrame

The original DataFrame with `quality` and `quality_reasons` columns appended.

### Methods

#### `.summary()` -> pd.DataFrame

Per-tag quality summary sorted by `pct_bad` descending.

Columns: `tag_name`, `total_rows`, `pct_good`, `pct_sus`, `pct_bad`, `n_good`, `n_sus`, `n_bad`

#### `.plot(tags, start, end, title, height)` -> go.Figure

Return a Plotly multi-tag horizontal quality timeline figure.

| Argument | Default | Description |
|----------|---------|-------------|
| `tags` | `None` | Subset of tag names to display. `None` = all tags |
| `start` | `None` | ISO datetime string to clip the left edge |
| `end` | `None` | ISO datetime string to clip the right edge |
| `title` | `"Data Quality Timeline"` | Chart title |
| `height` | `400` | Base figure height in pixels |

#### `.issue_summary()` -> pd.DataFrame

Per-issue breakdown of contiguous bad/sus segments.

Columns: `tag_name`, `issue_start_time`, `issue_end_time`, `n_rows_with_issues`, `status`, `totalDuration_hours`

#### `.check_timestamps(expected_freq, freq_tolerance)` -> pd.DataFrame

Detect timestamp anomalies.

| Argument | Default | Description |
|----------|---------|-------------|
| `expected_freq` | `None` | Expected frequency (e.g. `"1min"`). `None` = auto-infer |
| `freq_tolerance` | `0.1` | Fraction deviation before flagging drift |

Returns DataFrame with columns: `tag_name`, `issue_type`, `timestamp`, `description`, `severity`

#### `.export_report(path, title)` -> None

Write a self-contained HTML quality report to `path`.

| Argument | Default | Description |
|----------|---------|-------------|
| `path` | required | File path for the output HTML |
| `title` | `"Data Quality Report"` | Report title |

## Rule Classes

### `NullRule`

Flag rows where value is NaN, None, or pd.NA.

```python
from tsqc import NullRule

rule = NullRule(level="bad")
```

### `FlatlineRule`

Flag rows where the value has not changed by more than `min_delta` within the preceding `window`.

```python
from tsqc import FlatlineRule

rule = FlatlineRule(window="1h", min_delta=0.001, level="sus")
```

### `DeltaRule`

Flag rows where the absolute change from the previous row exceeds `threshold`.

```python
from tsqc import DeltaRule

rule = DeltaRule(threshold=50.0, level="sus")
```

### `RangeRule`

Flag rows where value is outside [min_val, max_val].

```python
from tsqc import RangeRule

rule = RangeRule(min_val=0, max_val=100, level="bad")
```

### `CustomRule`

Wrap an arbitrary user-supplied callable as a QC rule.

```python
from tsqc import CustomRule

rule = CustomRule(fn=lambda s: s > 100, name="my_check", level="bad")
```

## Next Steps

- [Rule Engine](rules.md) — deeper dive into how rules work
- [YAML Configuration](yaml-configuration.md) — configuring rules via YAML
- [User Guide](user-guide.md) — walkthrough with examples
