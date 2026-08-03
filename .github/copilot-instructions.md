# timeseries-qc — Copilot Instructions

This project uses [timeseries-qc](https://pypi.org/project/timeseries-qc/) (v0.5.0) for time series data quality control.

## One-Shot Pattern
```python
import tsqc
import pandas as pd
df = pd.read_csv("sensor_data.csv")
result = tsqc.check(df, assume_tz="UTC")
result.plot().show()
```

## Column Contract
- `timestamp` (datetime, required) — Tz-naive requires `assume_tz`
- `tag_name` (str, optional) — `tag_col=None` for single-tag
- `value` (float, required)

## Rules
- **YAML config preferred:** `result = tsqc.check(df, rules="tsqc_rules.yaml")`
- 5 built-in rules: `null`, `flatline`, `delta`, `range`, `outlier`
- Levels: `bad` > `sus` > `good` (worst wins)
- Tag rules ADD to defaults

## External Quality Column
```python
result = tsqc.check(
    df,
    external_quality_col="status",
    quality_mode="combined",  # exclusive | combined | none
    quality_map={0: "good", 1: "sus", 2: "bad", 3: "bad", 4: "bad"},
    assume_tz="UTC",
)
```
- Unmapped values → `bad` with reason `source_data_quality: <value>`

## Common Mistakes
1. Missing `assume_tz` on tz-naive data
2. YAML `check: null` (bare, not quoted)
3. Tag rules do NOT replace defaults

## Key Methods
`result.summary()`, `result.issue_summary()`, `result.check_timestamps()`, `result.plot()`, `result.export_report("report.html")`

## Links
- [Docs](https://nagusubra.github.io/timeseries-qc/)
- [GitHub](https://github.com/nagusubra/timeseries-qc)
