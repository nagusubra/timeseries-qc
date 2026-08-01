---
title: timeseries-qc vs Pandera
description: Compare timeseries-qc and Pandera for validating pandas DataFrames and industrial time series quality control.
---

# timeseries-qc vs Pandera

!!! abstract "TL;DR"
    Use **timeseries-qc** for per-row good/sus/bad quality control of multi-tag time series with timelines and YAML plant rules. Use **Pandera** when you need declarative **DataFrame schema validation** (dtypes, nullability, checks) as part of pandas/polars pipelines.

## What problem does each tool solve?

**timeseries-qc** answers: “Which samples are good, suspect, or bad — and why — across sensors over time?”

**Pandera** answers: “Does this DataFrame match the schema and column checks I declared before I trust it downstream?”

## How do they classify results?

timeseries-qc appends `quality` and `quality_reasons` per row and aggregates with `summary()` / `issue_summary()`.

Pandera validates schemas and raises or returns failure cases when checks fail; it is not a three-level SCADA quality classifier.

## Are they time-series native?

timeseries-qc includes flatline windows, delta limits, rolling outliers, timestamp anomaly helpers, and `assume_tz` for naive historian CSVs.

Pandera can check datetime columns and custom hypotheses, but does not ship multi-tag quality timelines, historian `quality_map`, or built-in stuck-sensor rules.

## How do you configure rules?

timeseries-qc uses YAML `default_rules` / `tag_rules` (and optional `quality_map`) or Python rule objects passed to `tsqc.check`.

Pandera uses `DataFrameSchema` / `Column` definitions in Python (or YAML schema serialization) focused on types, nulls, uniqueness, and value checks.

## What about visualization and reports?

timeseries-qc: `plot()` timeline + `export_report()` HTML for operators.

Pandera: validation error reporting aimed at developers and pipeline failures — not a SCADA quality UI.

## Comparison table

| Capability | timeseries-qc | Pandera |
|------------|:-------------:|:-------:|
| Primary domain | Time series QC | DataFrame schema validation |
| Classification | good / sus / bad | Schema pass / fail |
| Multi-tag quality timeline | Yes | No |
| YAML plant rules + tag globs | Yes | Schema YAML (different) |
| Flatline / delta / outlier windows | Built-in | Custom checks |
| Historian `external_quality_col` | Yes | DIY |
| `summary()` pct_bad for CI gates | Yes | N/A (different) |
| Strong dtype / nullability contracts | Light | Core strength |
| License | MIT | MIT |
| Typical install | `pip install timeseries-qc` | `pip install pandera` |

## When should you use timeseries-qc?

Choose timeseries-qc when operators need actionable sample-level QC on SCADA/IoT extracts:

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensors.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="rules.yaml", assume_tz="UTC")
if (result.summary()["pct_bad"] > 5).any():
    raise SystemExit("QC gate failed")
```

## When should you use Pandera?

Choose Pandera when you need pipeline contracts before analytics code runs:

```python
import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "timestamp": pa.Column(pa.DateTime, nullable=False),
    "tag_name": pa.Column(str),
    "value": pa.Column(float, nullable=True),
})
df = schema.validate(df)
```

A common pattern: Pandera validates shape/types on ingest; timeseries-qc classifies sample quality afterward.

## Related pages

- [Why timeseries-qc?](../why-timeseries-qc.md)
- [FAQ](../faq.md)
- [Quickstart](../quickstart.md)
- [vs Great Expectations](vs-great-expectations.md) · [vs Pecos](vs-pecos.md) · [vs SaQC](vs-saqc.md)
