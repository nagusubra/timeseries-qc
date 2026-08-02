---
title: timeseries-qc vs SaQC
description: Compare timeseries-qc and SaQC for environmental and industrial time series quality control and flagging.
---

# timeseries-qc vs SaQC

!!! abstract "TL;DR"
    Use **timeseries-qc** for SCADA/historian workflows that need good/sus/bad labels, YAML plant rules, Plotly timelines, and MIT licensing. Use **SaQC** when you need a rich environmental-science flagging engine and are comfortable with its domain-specific API and LGPL license.

## What problem does each tool solve?

**timeseries-qc** targets industrial IoT and SCADA quality control: multi-tag DataFrames, operator timelines, HTML reports, and optional historian quality columns.

**SaQC** (Helmholtz UFZ) is a sophisticated **flagging** toolkit aimed largely at environmental and observational time series, with an extensive set of scientific QC methods.

## How do they classify results?

timeseries-qc maps every row to `good`, `sus`, or `bad` with human-readable `quality_reasons`.

SaQC attaches **flags** according to its flagging scheme — powerful for scientific pipelines, but a different mental model than three-level industrial quality plus Plotly timelines.

## Are they time-series native?

Yes for both. SaQC is deep in environmental QC methods; timeseries-qc is oriented around SCADA tags, YAML glob rules, `assume_tz`, and historian integration (`external_quality_col`, `quality_map`).

## How do you configure rules?

timeseries-qc: YAML `default_rules` / `tag_rules` (optional `quality_map`) or Python rules via `tsqc.check`.

SaQC: domain-specific configuration (including JSON-oriented workflows) and a richer scientific method catalog — steeper for plant engineers who want a short YAML file and a timeline chart.

## What about visualization and reports?

timeseries-qc ships `result.plot()` and `export_report()` aimed at ops handoff.

SaQC focuses on flagging machinery rather than a built-in multi-tag industrial quality timeline + offline HTML report combo.

## Comparison table

| Capability | timeseries-qc | SaQC |
|------------|:-------------:|:----:|
| Primary domain | SCADA / industrial IoT QC | Environmental flagging |
| Classification | good / sus / bad | Scientific flags |
| Multi-tag quality timeline | Yes | No (equivalent) |
| YAML plant rules + tag globs | Yes | Different config model |
| Historian quality column | Yes | DIY |
| Self-contained HTML QC report | Yes | Not the same focus |
| Method breadth (scientific) | Focused built-ins | Very extensive |
| License | MIT | LGPL |
| Commercial embedding ease | Permissive MIT | LGPL considerations |

## When should you use timeseries-qc?

Choose timeseries-qc for plant historians, CI quality gates, and ops-facing reports:

```python
import tsqc
import pandas as pd

df = pd.read_csv("historian_export.csv", parse_dates=["timestamp"])
result = tsqc.check(
    df,
    rules="plant_rules.yaml",
    external_quality_col="status",
    quality_mode="combined",
    assume_tz="UTC",
)
print(result.summary())
result.export_report("plant_qc.html")
```

Unmapped historian codes become `bad` with reason `source_data_quality: <value>`.

## When should you use SaQC?

Choose SaQC when your team already works in environmental monitoring flagging workflows and needs its specialized method set more than SCADA timelines and MIT-licensed embedding.

If LGPL obligations are a concern for proprietary products, evaluate carefully or prefer MIT-licensed timeseries-qc for the industrial QC slice.

## Related pages

- [Why timeseries-qc?](../why-timeseries-qc.md)
- [FAQ](../faq.md)
- [Quickstart](../quickstart.md)
- [vs Great Expectations](vs-great-expectations.md) · [vs Pandera](vs-pandera.md) · [vs Pecos](vs-pecos.md)
