# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [Unreleased]

### Added

- CHANGELOG.md with explicit semantic versioning convention

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
