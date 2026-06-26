# timeseries-qc — Copilot Instructions

This project uses [timeseries-qc](https://pypi.org/project/timeseries-qc/) (v0.3.2) for time series data quality control.

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
- 4 built-in rules: `null`, `flatline`, `delta`, `range`
- Levels: `bad` > `sus` > `good` (worst wins)
- Tag rules ADD to defaults

## Common Mistakes
1. Missing `assume_tz` on tz-naive data
2. YAML `check: null` (bare, not quoted)
3. Tag rules do NOT replace defaults

## Key Methods
`result.summary()`, `result.issue_summary()`, `result.check_timestamps()`, `result.plot()`, `result.export_report("report.html")`

## Links
- [Docs](https://nagusubra.github.io/timeseries-qc/)
- [GitHub](https://github.com/nagusubra/timeseries-qc)
