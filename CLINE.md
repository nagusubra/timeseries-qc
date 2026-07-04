# timeseries-qc — AI Agent Instructions

This project uses the [timeseries-qc](https://pypi.org/project/timeseries-qc/) library (v0.4.1) for time series data quality control.

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
- **YAML-first:** Configure rules in `.yaml` files via `tsqc.check(df, rules="file.yaml")` — config is batch-validated with helpful error messages listing all issues
- **5 built-in rules:** `null`, `flatline` (window+min_delta), `delta` (min/max_delta), `range` (min/max), `outlier` (method+threshold+window)
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
  - check: outlier
    method: zscore
    threshold: 3.0
    window: 24h
    level: sus
tag_rules:
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
```

### External Quality Column (Historian Status)
```python
result = tsqc.check(
    df,
    external_quality_col="status",
    quality_mode="exclusive",
    rules="rules.yaml",
    assume_tz="UTC",
)
```

| Mode | Behavior |
|------|----------|
| `exclusive` | External quality **only**; no internal rules run |
| `combined` | External + internal merged (worst-wins: bad > sus > good) |
| `none` | Internal only; ignores external column (escape hatch) |

- `quality_map` in YAML takes precedence over the `quality_map=` parameter

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
