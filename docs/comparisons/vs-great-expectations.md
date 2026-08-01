---
title: timeseries-qc vs Great Expectations
description: Compare timeseries-qc and Great Expectations for SCADA and industrial time series data quality control.
---

# timeseries-qc vs Great Expectations

!!! abstract "TL;DR"
    Use **timeseries-qc** when you need per-row good/sus/bad classification, multi-tag quality timelines, and YAML rules for SCADA/historian series. Use **Great Expectations** when you need a general data-validation platform across tables, warehouses, and non-time-series pipelines with expectation suites and data docs.

## What problem does each tool solve?

**timeseries-qc** is a focused library for industrial and IoT **time series** quality control: classify every sample as good, suspect, or bad, then plot and report across tags.

**Great Expectations (GX)** is a general-purpose **data validation** framework for batch and pipeline checks across many data shapes — relational tables, files, and warehouses — with expectation suites, validation results, and Data Docs.

## How do they classify results?

timeseries-qc uses three levels — `good`, `sus`, `bad` — with worst-wins merging across rules and optional historian `external_quality_col` mapping.

Great Expectations typically yields **pass/fail** (or success/failure) validation results against expectations; it does not ship a built-in good/suspect/bad sensor timeline.

## Are they time-series native?

timeseries-qc is built for timestamped sensor streams: flatline windows, delta spikes, rolling outliers, gap/duplicate checks, and timezone handling via `assume_tz`.

Great Expectations can validate columns that happen to be time series, but it is not specialized for SCADA-style multi-tag QC, stuck-sensor windows, or quality timelines.

## How do you configure rules?

timeseries-qc prefers YAML (`default_rules`, `tag_rules`, optional `quality_map`) with batch config validation, plus a Python API for the same rules.

Great Expectations configures **expectations** in Python or JSON/YAML suite formats aimed at schema, null rates, value sets, and statistical column checks — not tag-glob flatline windows out of the box.

## What about visualization and reports?

timeseries-qc provides `result.plot()` (Plotly multi-tag quality timeline) and `result.export_report()` (self-contained HTML).

Great Expectations provides Data Docs and validation result pages oriented around expectation suites, not a horizontal SCADA quality timeline.

## Comparison table

| Capability | timeseries-qc | Great Expectations |
|------------|:-------------:|:------------------:|
| Primary domain | Time series / SCADA QC | General data validation |
| Classification | good / sus / bad | Pass / fail (validation) |
| Multi-tag quality timeline | Yes (`plot()`) | No |
| YAML rules for sensors | Yes | Suites (different model) |
| Flatline / delta / rolling outlier | Built-in | Custom expectations |
| Historian quality column | `external_quality_col` | Custom mapping |
| Self-contained HTML QC report | Yes | Data Docs (different) |
| Warehouse / multi-asset orchestration | Minimal | Strong |
| License | MIT | Apache-2.0 |
| Typical install | `pip install timeseries-qc` | GX / cloud stack |

## When should you use timeseries-qc?

Choose timeseries-qc when:

- Data is long-format `timestamp` / `tag_name` / `value` (or close)
- You need suspect vs bad nuance for operators
- You want a quality timeline and offline HTML report in a few lines
- YAML-first plant rules and historian `quality_map` matter

```python
import tsqc
import pandas as pd

df = pd.read_csv("scada_export.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="plant_rules.yaml", assume_tz="UTC")
print(result.summary())
result.plot().show()
result.export_report("qc_report.html")
```

## When should you use Great Expectations?

Choose Great Expectations when:

- You validate many non-time-series assets (dimensions, facts, files)
- You need expectation suites, checkpoint orchestration, and Data Docs at org scale
- Pass/fail column and table contracts matter more than per-sample sensor QC

You can still use both: GX for warehouse contracts, timeseries-qc for tag-level SCADA QC on extracts.

## Related pages

- [Why timeseries-qc?](../why-timeseries-qc.md)
- [FAQ](../faq.md)
- [Quickstart](../quickstart.md)
- [vs Pandera](vs-pandera.md) · [vs Pecos](vs-pecos.md) · [vs SaQC](vs-saqc.md)
