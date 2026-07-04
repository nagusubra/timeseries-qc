---
title: Changelog — timeseries-qc Release History
description: Version history and release notes for the timeseries-qc library.
---

# Changelog

## 0.4.1 — 2026-07-03

### Bug Fixes

- **Critical**: Add missing `OutlierRule` import in `tests/test_rules.py` — previously caused 19 OutlierRule tests to fail with `NameError`
- **Fix `test_global_zscore_flags_outlier`**: Increase sample size from 10 to 21 points to make z-score > 3.0 mathematically achievable (with n=10, max z-score is ~2.85)
- **Fix `test_rolling_mad_flags_spike`**: Add Gaussian jitter to constant baseline to prevent MAD=0 (which causes NaN scores)

### Testing

- All 163 tests now pass (previously 19 failing due to import error)
- Comprehensive test coverage documented in `TEST_RESULTS.md`
- Created and ran 105-test smoke test suite validating all features

## 0.4.0 — 2026-07-02

### Features

- **External Quality Column** (`external_quality_col`): Intake a pre-existing quality/status column from SCADA historians and either use it exclusively (`quality_mode="exclusive"`) or merge it with internal rules (`quality_mode="combined"`). Value-to-level mapping via YAML `quality_map` section or `quality_map=` dict parameter. Unmapped values become `bad`. Configure via `quality_mode="none"` to ignore the external column entirely. (`#PR`)
- **Column Conflict Auto-Rename**: When the external quality column name matches the default output column name (e.g. both named `quality`), the output is automatically renamed to `qc_quality` / `qc_quality_reasons` and the input column is preserved. A warning is issued.

## 0.3.2 — 2026-06-26

### Bug Fixes & Housekeeping

- Fix DeltaRule handling of NaN series (no crash on all-NaN input)
- Fix deprecated `datetime.utcnow()` in `result.py` — now uses timezone-aware `datetime.now(timezone.utc)`
- Fix `__init__.py` version string to match `pyproject.toml`
- Update README stale version reference

## 0.3.1 — 2026-06-25

### Documentation & Configuration

- Update all synthetic data YAMLs (`solar_rules.yaml`, `oilfield_rules.yaml`, `hydro_rules.yaml`) from `threshold:` to `max_delta:` syntax
- Update `sample_rules.yaml` fixture
- Update rule engine and API reference docs for new DeltaRule signature

## 0.3.0 — 2026-06-25

### Features

- **FlatlineRule**: Added optional `min_duration` parameter. Suppresses flags for flat runs shorter than the given duration (pandas offset string). Useful when short-lived flat periods are normal (e.g. pump starts, cloud edges).
- **DeltaRule**: Replaced single `threshold` parameter with two independent thresholds:
  - `max_delta`: flags when absolute change is too large (sensor spike / step change)
  - `min_delta`: flags when absolute change is too small (stuck / frozen sensor)
  - At least one of `min_delta` or `max_delta` must be provided
  - **Breaking change**: old `threshold` parameter removed; existing YAML configs must be updated

## 0.2.0 — 2026-03-15

### Features

- Automatic timezone display — `result.df`, `.plot()`, `.summary()`, `.issue_summary()`, and `.check_timestamps()` all honour the input timezone
- `issue_summary()` now includes `reasons` column with comma-separated rule names
- Hover tooltips in timeline chart show "Cause: ..." for suspect/bad segments
- Self-contained HTML report export (`.export_report()`) with embedded Plotly chart, per-tag summary, per-issue summary, and timestamp health table
- Timestamp anomaly detection: DST ambiguous timestamps stored in metadata, shown in `check_timestamps()`

## 0.1.0 — 2026-01-15

### Initial Release

- `tsqc.check()` — core data quality check function
- `QCResult` — result object with summary, plot, and export methods
- Built-in rules: NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule
- YAML configuration with `default_rules` and `tag_rules`
- Rule application with worst-level-wins strategy
- Interactive Plotly timeline chart (`.plot()`)
- Self-contained HTML report export (`.export_report()`)
- Timestamp health checking (gaps, duplicates, non-monotonic, DST, frequency drift)
- Column name auto-detection (timestamp, tag_name, value)
- Python 3.9+ support

## Next Steps

- [Roadmap](roadmap.md) — planned features
- [Contributing](contributing.md) — how to contribute
- [Architecture](architecture.md) — internal design
