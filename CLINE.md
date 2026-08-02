# timeseries-qc — AI Agent Instructions (Cline)

This project uses the [timeseries-qc](https://pypi.org/project/timeseries-qc/) library (v0.4.2) for time series data quality control.

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
# Use an existing historian status column — exclusive mode (skip internal checks)
result = tsqc.check(
    df,
    external_quality_col="status",       # column with 0,1,2,3,4 values
    quality_mode="exclusive",            # or "combined" to merge with internal
    rules="rules.yaml",                  # quality_map lives here or use quality_map=dict
    assume_tz="UTC",
)
```

Also accepts `quality_map` as a dict parameter:
```python
result = tsqc.check(
    df, external_quality_col="status", quality_mode="combined",
    quality_map={0: "good", 1: "sus", 2: "bad", 3: "bad", 4: "bad"},
    rules=[NullRule(), RangeRule(min_val=0, max_val=100)],
    assume_tz="UTC",
)
```

### YAML with quality_map Example
```yaml
quality_map:
  0: good
  1: sus
  2: bad
  3: bad
  4: bad

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

| Mode | Behavior |
|------|----------|
| `exclusive` | External quality **only**; no internal rules run |
| `combined` | External + internal merged (worst-wins: bad > sus > good) |
| `none` | Internal only; ignores external column (escape hatch) |

- Unmapped quality values → `bad` with reason `"source_data_quality: <value>"`
- Column conflict (input col == output col name) → auto-renamed to `qc_quality` / `qc_quality_reasons`; input col preserved
- `quality_map` in YAML takes precedence over the `quality_map=` parameter
- `quality_mode='none'` does NOT require a `quality_map`

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
