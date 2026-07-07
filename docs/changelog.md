---
title: Changelog — timeseries-qc Release History
description: Version history and release notes for the timeseries-qc library.
---

# Changelog

## 0.4.2 — 2026-07-07

### Features

- **Flatline Value in Reasons**: The `FlatlineRule` now includes the actual stuck value in the reason string, formatted as `flatline @ 42.5000` instead of just `flatline`. This provides immediate visibility into the severity of the flatline condition without requiring cross-reference to raw data. Special values (NaN, inf, -inf) are handled gracefully. Implemented via new `get_reason()` method in `Rule` base class, designed to be extensible for future rules. (`#46`)
- **Renamed External Quality Reason Prefix**: Changed the reason string prefix from `external_quality_value:` to `source_data_quality:` for clearer user-facing semantics. The parameter names (`external_quality_col`, `quality_mode`) remain unchanged. (`#46`)
- **Hover Tooltip Label Update**: Timeline chart hover tooltips now show `Reason:` instead of `Cause:` for consistency with the `quality_reasons` column naming convention. (`#46`)

### API Changes (Non-Breaking)

- **New Method**: `Rule.get_reason(series, idx)` — Override this method in custom rules to include contextual information (e.g., actual values) in reason strings. Default implementation returns `self.name` for backward compatibility.
- **FlatlineRule**: Now overrides `get_reason()` to append the flatline value with 4 decimal places.

### Testing

- Added 6 new tests for flatline value formatting (normal values, 4 decimal precision, NaN, inf, -inf)
- Updated 1 test for hover tooltip label change (`Cause:` → `Reason:`)
- All 169 tests pass

## 0.4.1 — 2026-07-03

### Features

- **YAML Config Validation**: YAML rule files are now batch-validated before construction. All errors (unknown top-level keys, misspelled check names, missing required params, type mismatches) are collected and reported in a single `ValueError` with location paths. Unknown keys get fuzzy-match suggestions via `difflib.get_close_matches()`. (`#26`)
- **OutlierRule**: New built-in statistical outlier detection rule with three configurable methods:
  - `zscore`: Classic `(value - mean) / std` — best for normally distributed data
  - `mad`: Robust `0.6745 * (value - median) / MAD` — handles extreme outliers in baseline
  - `iqr`: Tukey's fences `[Q1 - k·IQR, Q3 + k·IQR]` — works with skewed distributions
  - Supports both global (full-series) and rolling (time-windowed via pandas offset) modes
  - NaN values excluded from statistics, never flagged
  - `min_periods` guard (default 10) prevents flagging on insufficient data
  - Configurable via YAML (`check: outlier`) or Python (`OutlierRule(method="zscore")`) (`#25`)

### Bug Fixes

- **Critical**: Add missing `OutlierRule` import in `tests/test_rules.py` — previously caused 19 OutlierRule tests to fail with `NameError`
- **Fix `test_global_zscore_flags_outlier`**: Increase sample size from 10 to 21 points to make z-score > 3.0 mathematically achievable (with n=10, max z-score is ~2.85)
- **Fix `test_rolling_mad_flags_spike`**: Add Gaussian jitter to constant baseline to prevent MAD=0 (which causes NaN scores)

### Infrastructure

- Added `.gitattributes` with `* text=auto` for cross-platform line ending normalization
- Tightened `.gitignore` (scoped broad `*.csv`/`*.html` patterns, added `env/`, `.venv/`, `.vs/`, `.tox/`, `.eggs/`, `.python-version`)

### Documentation

- Updated all AI agent skill files: `CLAUDE.md`, `CLINE.md`, `.cursor/rules/timeseries-qc.mdc`, `docs/timeseries-qc.md` (v0.3.2 → v0.4.1)
- Added `OutlierRule` class docs to `docs/api-reference.md`
- Updated `docs/llms.txt` and `docs/llms-full.txt` with OutlierRule references
- Fixed stale version references in `README.md` and `docs/llms-full.txt`

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
