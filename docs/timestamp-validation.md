---
title: Timestamp Validation — timeseries-qc
description: Detect timestamp anomalies in time series data — gaps, duplicates, non-monotonic timestamps, frequency drift, and DST ambiguities.
---

# Timestamp Validation

The timestamp health checker detects common timestamp issues in time series data.

## Basic Usage

```python
result = tsqc.check(df, assume_tz="UTC")
issues = result.check_timestamps()
print(issues)
```

## Detected Issues

| Issue Type | Severity | Description |
|------------|----------|-------------|
| `gap` | error/warning | Time difference exceeds 2x the expected frequency |
| `duplicate` | error | Multiple rows with the same timestamp |
| `non_monotonic` | error | Timestamps out of order |
| `freq_drift` | warning | Median interval deviates from expected frequency |
| `dst_ambiguous` | warning | Timestamp was ambiguous during DST localization |

## Customizing Frequency

By default, the expected frequency is auto-inferred per tag using the mode of timestamp diffs.

```python
result.check_timestamps(expected_freq="1h")
```

## Frequency Drift Tolerance

```python
result.check_timestamps(expected_freq="1h", freq_tolerance=0.05)
```

The `freq_tolerance` parameter controls how much deviation is allowed before flagging drift (default: 0.1 = 10%).

## Return Value

Returns a DataFrame with columns:

| Column | Description |
|--------|-------------|
| `tag_name` | Affected tag |
| `issue_type` | Type of timestamp anomaly |
| `timestamp` | The problematic timestamp |
| `description` | Human-readable explanation |
| `severity` | `"error"` or `"warning"` |

Returns an empty DataFrame (not None) when no issues are found.

## Next Steps

- [Report Generation](report-generation.md) — including timestamp health in reports
- [API Reference](api-reference.md) — `QCResult.check_timestamps()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
