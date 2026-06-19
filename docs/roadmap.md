---
title: Roadmap — timeseries-qc Future Development
description: Planned features and improvements for timeseries-qc, including visualization, performance, and integration enhancements.
---

# Roadmap

## Short Term

- [x] **Plotly timeline chart** interactive quality visualization
- [x] **YAML configuration** rule definitions without Python
- [x] **HTML report** self-contained export with embedded Plotly
- [x] **Timestamp health** gap/duplicate/drift/DST detection
- [x] **Documentation site** MkDocs Material with SEO

## Medium Term

- [ ] **Statistical rules** — mean shift detection, trend analysis, seasonality decomposition
- [ ] **Custom rule templates** — pre-built rules for common patterns
- [ ] **Batch processing API** — efficient processing of large tag inventories
- [ ] **Parquet/Feather support** — native import for columnar formats
- [ ] **CLI tool** — `tsqc check data.csv -o report.html` one-liner

## Long Term

- [ ] **Spark/Dask backend** — distributed processing for very large datasets
- [ ] **ML-based anomaly detection** — unsupervised learning for pattern-based anomalies
- [ ] **Real-time streaming** — integration with Kafka, Pulsar for live quality checks
- [ ] **REST API server** — standalone quality check service
- [ ] **Plugin system** — third-party rule and visualization plugins

## Community

We welcome contributions! See [Contributing](contributing.md) for how to help.

## Next Steps

- [Changelog](changelog.md) — version history
- [Contributing](contributing.md) — how to contribute
- [Architecture](architecture.md) — internal design
