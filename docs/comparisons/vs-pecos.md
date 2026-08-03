---
title: timeseries-qc vs Pecos
description: Compare timeseries-qc and Sandia Pecos for photovoltaic and industrial time series performance and quality monitoring.
---

# timeseries-qc vs Pecos

!!! abstract "TL;DR"
    Use **timeseries-qc** for modern multi-tag good/sus/bad QC with YAML rules, Plotly timelines, and HTML reports (active MIT library, v0.5.0). Use **Pecos** if you already depend on its PV performance monitoring workflows; note that Pecos has been in maintenance mode since around 2021 and uses binary pass/fail style results.

## What problem does each tool solve?

**timeseries-qc** is a general industrial time series QC library for SCADA, historians, and IoT — not limited to solar — with three-level classification and operator-facing visuals.

**Pecos** (Sandia National Laboratories) targets performance monitoring and quality for time series, with historical roots in photovoltaic system analysis.

## How do they classify results?

timeseries-qc: `good` / `sus` / `bad` with pipe-delimited reasons and worst-wins merging (including optional historian quality columns).

Pecos: typically **pass/fail** oriented masking and reporting rather than a first-class three-level quality model with suspect nuance.

## Are they time-series native?

Both are time-series oriented. timeseries-qc emphasizes multi-tag pipelines, YAML tag globs, `assume_tz`, `check_timestamps()`, and historian `external_quality_col`.

Pecos provides time series performance/QC utilities shaped by its PV monitoring heritage.

## How do you configure rules?

timeseries-qc: YAML-first `default_rules` + `tag_rules`, batch-validated, plus Python rule objects.

Pecos: Python configuration / API without the same YAML-driven multi-tag plant rule model.

## What about visualization and reports?

timeseries-qc: interactive Plotly quality timeline (`plot()`) and self-contained `export_report()` HTML.

Pecos: reporting suited to its performance dashboards; no equivalent multi-tag good/sus/bad Plotly timeline as a core product feature.

## Comparison table

| Capability | timeseries-qc | Pecos |
|------------|:-------------:|:-----:|
| Primary domain | Industrial / IoT time series QC | PV / performance QC heritage |
| Classification | good / sus / bad | Pass / fail style |
| Multi-tag quality timeline | Yes | No (equivalent) |
| YAML config | Yes | No |
| Historian quality column | Yes | Limited / DIY |
| Self-contained HTML QC report | Yes | Different reporting |
| Maintenance status | Active (0.5.0) | Maintenance (since ~2021) |
| License | MIT | BSD-3-Clause |

## When should you use timeseries-qc?

Choose timeseries-qc for new projects — solar included — when you want active maintenance, suspect-level nuance, YAML plant rules, and operator timelines:

```python
import tsqc
import pandas as pd

df = pd.read_csv("solar_farm.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="solar_rules.yaml", assume_tz="UTC")
result.plot(title="Solar QC").show()
result.export_report("solar_qc.html")
```

See the [Solar Farm CSV tutorial](../tutorials/solar-farm-csv.md).

## When should you use Pecos?

Choose Pecos when an existing codebase already depends on its APIs or reports, or when a specific Pecos performance metric is required and migration cost is high.

For greenfield QC with HTML timelines and CI `pct_bad` gates, prefer timeseries-qc.

## Related pages

- [Why timeseries-qc?](../why-timeseries-qc.md)
- [FAQ](../faq.md)
- [Quickstart](../quickstart.md)
- [vs Great Expectations](vs-great-expectations.md) · [vs Pandera](vs-pandera.md) · [vs SaQC](vs-saqc.md)
