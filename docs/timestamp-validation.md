---
title: Timestamp Validation — timeseries-qc
description: Detect timestamp anomalies in time series data — gaps, duplicates, non-monotonic timestamps, frequency drift, and DST ambiguities.
og_title: Timestamp Validation — timeseries-qc
og_description: Detect timestamp anomalies — gaps, duplicates, non-monotonic timestamps, frequency drift, and DST ambiguities.
---

# Timestamp Validation

!!! abstract "TL;DR"
    After `tsqc.check()`, call `result.check_timestamps()` to find gaps, duplicates, non-monotonic order, frequency drift, and DST ambiguities. Returns a DataFrame (empty when clean).

The timestamp health checker detects common timestamp issues in time series data.

## How do I run timestamp validation?

Call `result.check_timestamps()` on a `QCResult` from `tsqc.check()`:

```python
result = tsqc.check(df, assume_tz="UTC")
issues = result.check_timestamps()
print(issues)
```

## What issues are detected?

Five issue types are reported: `gap`, `duplicate`, `non_monotonic`, `freq_drift`, and `dst_ambiguous`.

| Issue Type | Severity | Description |
|------------|----------|-------------|
| `gap` | error/warning | Time difference exceeds 2x the expected frequency |
| `duplicate` | error | Multiple rows with the same timestamp |
| `non_monotonic` | error | Timestamps out of order |
| `freq_drift` | warning | Median interval deviates from expected frequency |
| `dst_ambiguous` | warning | Timestamp was ambiguous during DST localization |

## How do I set the expected frequency?

By default, frequency is auto-inferred per tag from the mode of timestamp diffs. Override with `expected_freq`.

```python
result.check_timestamps(expected_freq="1h")
```

## How do I control frequency drift tolerance?

Pass `freq_tolerance` (default `0.1` = 10%) to set how much median-interval deviation is allowed before flagging drift.

```python
result.check_timestamps(expected_freq="1h", freq_tolerance=0.05)
```

## What does `check_timestamps()` return?

A DataFrame of issues (or empty when none are found) with `tag_name`, `issue_type`, `timestamp`, `description`, and `severity`.

| Column | Description |
|--------|-------------|
| `tag_name` | Affected tag |
| `issue_type` | Type of timestamp anomaly |
| `timestamp` | The problematic timestamp |
| `description` | Human-readable explanation |
| `severity` | `"error"` or `"warning"` |

Returns an empty DataFrame (not None) when no issues are found.

## FAQ

### Is timestamp validation part of `tsqc.check()`?

Quality rules run in `tsqc.check()`; timestamp health is a separate call on the result: `result.check_timestamps()`.

### What if there are no timestamp issues?

You get an empty DataFrame, not `None`.

### How is a gap defined?

A gap is flagged when the time difference exceeds 2× the expected frequency.

### Can I set frequency explicitly?

Yes. Pass `expected_freq` (e.g. `"1h"`) instead of relying on auto-inference.

### Are DST problems covered?

Yes. `dst_ambiguous` flags timestamps that were ambiguous during DST localization.

## Next Steps

- [Report Generation](report-generation.md) — including timestamp health in reports
- [API Reference](api-reference.md) — `QCResult.check_timestamps()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
