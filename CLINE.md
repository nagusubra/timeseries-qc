# timeseries-qc — AI Agent Instructions

This project uses the [timeseries-qc](https://pypi.org/project/timeseries-qc/) library (v0.3.2) for time series data quality control.

## Quick Reference

### One-Shot Pattern
```python
import tsqc
import pandas as pd
df = pd.read_csv("sensor_data.csv")          # columns: timestamp, tag_name, value
result = tsqc.check(df, assume_tz="UTC")     # assume_tz required for tz-naive CSVs
result.plot().show()
```

### Column Requirements
- `timestamp` (datetime, required) — Tz-naive needs `assume_tz="IANA/Zone"`
- `tag_name` (str, optional) — Omit or `tag_col=None` for single-tag
- `value` (float, required)

### Key Rules
- **YAML-first:** Configure rules in `.yaml` files via `tsqc.check(df, rules="file.yaml")`
- **4 built-in rules:** `null`, `flatline` (window+min_delta), `delta` (min/max_delta), `range` (min/max)
- **Levels:** `bad` > `sus` > `good` — worst wins across all rules
- **Tag rules ADD** to defaults (do not replace)

### YAML Example
```yaml
default_rules:
  - check: null
    level: bad
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus
tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
```

### QCResult Methods
| Method | Returns |
|--------|---------|
| `result.summary()` | `pd.DataFrame` — %good/%sus/%bad per tag |
| `result.issue_summary()` | `pd.DataFrame` — per-issue runs with reasons |
| `result.check_timestamps()` | `pd.DataFrame` — gap/duplicate/drift/DST |
| `result.plot()` | `plotly.Figure` — quality timeline |
| `result.export_report("report.html")` | `None` — self-contained |

### Gotchas
1. **Always pass `assume_tz`** for CSV/tz-naive data
2. YAML `check: null` (bare, not quoted) maps to Python `None`
3. Default columns: `timestamp`, `tag_name`, `value` — use `time_col=` etc. to customize
4. Tag rules add to defaults, don't override

### Links
- [Docs](https://nagusubra.github.io/timeseries-qc/)
- [GitHub](https://github.com/nagusubra/timeseries-qc)
- [PyPI](https://pypi.org/project/timeseries-qc/)
