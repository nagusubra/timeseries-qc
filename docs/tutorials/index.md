---
title: Tutorials — timeseries-qc
description: Step-by-step tutorials for solar farm CSV QC, YAML rules, OSIsoft PI historian exports, and CI data-quality gates with timeseries-qc 0.4.2.
---

# Tutorials

Hands-on walkthroughs for common `timeseries-qc` workflows. Each tutorial uses the real v0.4.2 API (`tsqc.check`, YAML rules, and `QCResult` methods).

!!! abstract "TL;DR"
    Start with the [Solar Farm CSV](solar-farm-csv.md) walkthrough if you are new. Use [YAML Rules From Scratch](yaml-rules-from-scratch.md) when you need per-tag configuration, [OSIsoft PI Export](osisoft-pi-export.md) for historian quality columns, and [CI Gate](ci-gate-data-quality.md) to fail builds on bad data.

<div class="tsqc-grid" markdown="1">
<div class="tsqc-grid-item" markdown="1">
**[Solar Farm CSV Walkthrough](solar-farm-csv.md)**

Load a multi-tag solar CSV, run `tsqc.check` with `assume_tz`, then inspect `summary()`, `plot()`, and `export_report()`.
</div>
<div class="tsqc-grid-item" markdown="1">
**[YAML Rules From Scratch](yaml-rules-from-scratch.md)**

Author `default_rules` and `tag_rules` covering null, flatline, delta, range, and outlier — plus optional `quality_map`.
</div>
<div class="tsqc-grid-item" markdown="1">
**[OSIsoft PI Export](osisoft-pi-export.md)**

Wire a historian export with `external_quality_col` and `quality_mode` (`combined` / `exclusive`).
</div>
<div class="tsqc-grid-item" markdown="1">
**[CI Gate on Data Quality](ci-gate-data-quality.md)**

Fail a GitHub Actions job when `result.summary()` `pct_bad` exceeds a threshold.
</div>
</div>

## Prerequisites

- Python 3.10+
- `pip install timeseries-qc` (v0.4.2)
- A CSV or DataFrame with `timestamp`, `value`, and optionally `tag_name`

## Suggested order

1. [Solar Farm CSV](solar-farm-csv.md) — end-to-end happy path
2. [YAML Rules From Scratch](yaml-rules-from-scratch.md) — configuration depth
3. [OSIsoft PI Export](osisoft-pi-export.md) — external quality columns
4. [CI Gate](ci-gate-data-quality.md) — automation

## Related pages

- [Quickstart](../quickstart.md) — five-line intro
- [YAML Configuration](../yaml-configuration.md) — rule schema reference
- [SCADA Integration](../scada-integration.md) — historian pipeline patterns
- [Why timeseries-qc?](../why-timeseries-qc.md) — positioning vs alternatives
