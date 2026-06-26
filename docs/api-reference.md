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
| `assume_tz` | `None` | IANA timezone for tz-naive input, e.g. `"UTC"` or `"America/Chicago"`. Optional if timestamps are already tz-aware — the existing timezone is used as-is. |

### Raises

- `ValueError`: Missing columns, unparseable timestamps, tz-naive without `assume_tz`, invalid `assume_tz`, missing YAML file

## `QCResult`

The object returned by `tsqc.check()`.

### Properties

#### `.df` -> pd.DataFrame

The original DataFrame with `quality` and `quality_reasons` columns appended. Timestamps are in the **input timezone** (the timezone specified via `assume_tz`, or the timezone of tz-aware input).

#### `.display_tz` -> str

IANA timezone used for all timestamp display (chart, summaries, tables). Examples: `"UTC"`, `"America/Edmonton"`, `"America/Chicago"`.

### Methods

#### `.summary()` -> pd.DataFrame

Per-tag quality summary sorted by `pct_bad` descending.

Columns: `tag_name`, `total_rows`, `pct_good`, `pct_sus`, `pct_bad`, `n_good`, `n_sus`, `n_bad`

#### `.plot(tags, start, end, title, height)` -> go.Figure

Return a Plotly multi-tag horizontal quality timeline figure.

Hover tooltips show tag name, quality level, start/end timestamps, duration, and — for suspect/bad segments — the **cause** (e.g. `Cause: null values`, `Cause: flatline`, `Cause: delta, null values`).

The x-axis and all timestamps are displayed in the **input timezone** — same as `result.df`. Bare `start`/`end` strings (without `+` or `Z`) are interpreted in that input timezone.

| Argument | Default | Description |
|----------|---------|-------------|
| `tags` | `None` | Subset of tag names to display. `None` = all tags |
| `start` | `None` | ISO datetime string to clip the left edge. Bare strings use the input timezone. |
| `end` | `None` | ISO datetime string to clip the right edge. Bare strings use the input timezone. |
| `title` | `"Data Quality Timeline"` | Chart title |
| `height` | `400` | Base figure height in pixels |

#### `.issue_summary()` -> pd.DataFrame

Per-issue breakdown of contiguous bad/sus segments.

Columns: `tag_name`, `issue_start_time`, `issue_end_time`, `n_rows_with_issues`, `status`, `totalDuration_hours`, `reasons` (comma-separated rule names that triggered the issue)

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

Optional `min_duration` suppresses flags for flat runs shorter than the given duration.

```python
from tsqc import FlatlineRule

rule = FlatlineRule(window="1h", min_delta=0.001, level="sus")
rule = FlatlineRule(window="5min", min_delta=0.0, min_duration="30min", level="sus")
```

### `DeltaRule`

Flag rows based on the absolute change from the previous reading. Supports
two independent thresholds: `max_delta` (spikes) and `min_delta` (stuck sensor).

At least one of `min_delta` or `max_delta` must be provided.

```python
from tsqc import DeltaRule

rule = DeltaRule(max_delta=100.0, level="sus")       # spike detection
rule = DeltaRule(min_delta=0.5, level="sus")          # stuck sensor
rule = DeltaRule(min_delta=0.5, max_delta=100.0)      # both
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
