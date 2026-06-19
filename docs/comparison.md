---
title: Comparison — timeseries-qc vs Alternatives
description: Compare timeseries-qc with Pecos, SaQC, and Great Expectations for time series data quality control.
---

# Comparison with Alternatives

| Feature | timeseries-qc | Pecos | SaQC | Great Expectations |
|---------|:---:|:---:|:---:|:---:|
| Classification | Good / Sus / Bad | Pass / Fail | Flags | Pass / Fail |
| Timeline chart | Yes | No | No | No |
| YAML config | Yes | No | JSON | No |
| Time-series native | Yes | Yes | Yes | No |
| Custom rules | Yes | No | Yes | Yes |
| HTML report | Yes | No | No | Yes |
| Offline report | Yes | Yes | No | No |
| License | MIT | BSD-3 | LGPL | Apache-2.0 |
| Maintenance | Active | Maintenance (since 2021) | Active | Active |

## Pecos (Sandia Labs)

Pecos offers binary pass/fail classification and has been in maintenance mode since 2021. It lacks timeline visualization and YAML-driven configuration.

## SaQC (Helmholtz UFZ)

SaQC is a rich flagging engine designed for environmental science. It has an environmental-domain-specific API, no timeline visualization, and uses an LGPL license which may be restrictive for some commercial applications.

## Great Expectations

Great Expectations is a general-purpose data validation framework that is not timeseries-native. It produces no visualization and requires writing expectations in Python.

## Why timeseries-qc?

`timeseries-qc` is the only library that combines:

1. **Three-level classification** (good/suspect/bad)
2. **Multi-tag horizontal status timeline**
3. **YAML-driven configuration** for non-Python users
4. **Self-contained HTML reports** with no external dependencies

All in a single `pip install`.

## Next Steps

- [FAQ](faq.md) — frequently asked questions
- [User Guide](user-guide.md) — walkthrough with examples
