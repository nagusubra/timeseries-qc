---
title: Changelog — timeseries-qc Release History
description: Version history and release notes for the timeseries-qc library.
---

# Changelog

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
