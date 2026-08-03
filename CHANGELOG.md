# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [Unreleased]

## [0.5.0] - 2026-08-02

### Changed
- Removed dead code from the library (`_VALID_LEVELS` in checker.py, unused `**kwargs` in `build_timeline_figure`, redundant inner `import warnings` in `_normalize_timestamps`)
- Restored `data/` directory at repo root for generated example datasets (git-ignored, reproducible)
- Fixed example notebooks (`examples/solar_farm.ipynb`, `examples/oilfield.ipynb`) to work end-to-end — generator subprocess paths and rules paths now correctly point to `synthetic_data_generation/`
- Generators (`generate_solar_data.py`, `generate_oilfield_data.py`, `generate_hydro_data.py`) now write CSVs to repo-root `data/` instead of next to the script
- `smoke_test.py` path-anchored to repo root via `ROOT` variable
- Updated all version references from 0.4.2 → 0.5.0 across docs, skills, and agent instructions

### Fixed
- CI workflow now declares read-only `contents` permissions (CodeQL least-privilege)
- Synthetic data generators no longer crash on Windows consoles (replaced unencodable `→` characters in output)
- `synthetic_data_generation/smoke_test.py` resolves `hydro_rules.yaml` from its own directory instead of a non-existent `data/` path
- Corrected package name in `CONTRIBUTING.md` clone command
- Aligned documented coverage threshold (75%) with CI enforcement

## [0.4.2] - 2026-07-07

### Added
- FlatlineRule includes stuck value in reason strings (`flatline @ 42.5000`)
- `Rule.get_reason(series, idx)` extensibility hook for contextual reason strings

### Changed
- External quality reason prefix renamed from `external_quality_value:` to `source_data_quality:`
- Timeline hover tooltip label updated from `Cause:` to `Reason:`

## [0.4.1] - 2026-07-04

### Added
- OutlierRule with three detection methods (Z-score, MAD, IQR)
- Rolling-window mode for all outlier methods
- Batch YAML config validation with structural error reporting
- Fuzzy "Did you mean?" hints for misspelled YAML keys
- External quality column support (historian status column ingestion)
- quality_map YAML config for mapping numeric status codes
- quality_mode parameter (exclusive, combined, none modes)
- issue-report button on docs site
- llms.txt and llms-full.txt for AI crawlers

### Fixed

- Missing OutlierRule import in test fixtures
- Edge case tests for zero-stddev and zero-MAD scenarios
- README image paths to reference docs/assets/images/
- Ruff import sorting compliance (I001)

### Changed

- YAML parser now validates all structural errors before rule construction
- Docs updated for v0.4.1 feature set
- AI instruction files (CLAUDE.md, CLINE.md) updated

## [0.3.2] - 2026-06-28

### Added
- FlatlineRule min_duration parameter
- DeltaRule min_delta/max_delta independent thresholds
- reasons column in issue_summary() output
- timeseries-qc.md skill file for AI coding agents

### Fixed
- Ruff import sorting compliance in checker.py
- Remove tracked build artifacts from git (.pyc, egg-info)

## [0.2.0] - 2026-06-15

### Added
- Timezone-aware display for plot, result.df, and summaries
- Timestamp health checker (gaps, duplicates, freq drift, DST)

### Changed
- Plot x-axis now shows timestamps in original input timezone

## [0.1.3] - 2026-06-01

### Added
- Initial PyPI release
- NullRule, FlatlineRule, DeltaRule, RangeRule built-in rules
- YAML rule configuration
- Plotly quality timeline chart with hover tooltips
- Multi-tag support with per-tag quality summary
- Issue summary with contiguous bad/sus segment detection
- MkDocs documentation site with 20+ pages
- Synthetic data generators (solar, oilfield)
- Example notebooks (solar_farm, oilfield)
