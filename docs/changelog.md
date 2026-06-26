---
title: Changelog — timeseries-qc Release History
description: Version history and release notes for the timeseries-qc library.
---

# Changelog

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
