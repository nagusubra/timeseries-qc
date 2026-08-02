---
title: SCADA Integration — timeseries-qc
description: Integrate timeseries-qc with SCADA historians (OSIsoft PI, Wonderware, Ignition) including external quality columns and timezone handling.
---

# SCADA Integration

!!! abstract "TL;DR"
    Extract historian data to a DataFrame with `timestamp`, `tag_name`, and `value`, pass `assume_tz` for wall-clock-naive timestamps, and optionally map status codes with `external_quality_col` + `quality_map`. Use `quality_mode="combined"` to merge historian codes with internal rules, or `"exclusive"` to trust the historian alone.

`timeseries-qc` fits into SCADA data pipelines for automated quality monitoring without replacing the historian.

## Data Pipeline Integration

1. **Extract** data from SCADA historian (OSIsoft PI, Wonderware, Ignition, etc.)
2. **Transform** data into the expected DataFrame format (`timestamp`, `tag_name`, `value`)
3. **Check** quality with `tsqc.check()`
4. **Report** via `result.export_report()` or store `result.df` back to the historian / data lake

## CSV-Based Integration

Many SCADA systems can export data as CSV. Load and check with:

```python
import pandas as pd
import tsqc

df = pd.read_csv("export.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="plant_rules.yaml", assume_tz="UTC")
print(result.summary())
result.export_report("scada_qc.html")
```

## Database Integration

For SCADA systems with SQL access:

```python
import pandas as pd
import tsqc
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@host:5432/scada")
query = """
SELECT timestamp, tag_name, value
FROM measurements
WHERE timestamp >= NOW() - INTERVAL '7 days'
"""
df = pd.read_sql(query, engine)
result = tsqc.check(df, assume_tz="UTC")
```

## OSIsoft PI and historian quality codes

For OSIsoft PI systems, use the PI Web API (or CSV export) to fetch values **and** status codes, then pass the status column through:

```python
result = tsqc.check(
    df,
    rules="pi_rules.yaml",
    external_quality_col="pi_quality",
    quality_mode="combined",  # or "exclusive"
    assume_tz="America/Chicago",
)
```

| Mode | Behavior |
|------|----------|
| `exclusive` | External quality only; internal rules skipped |
| `combined` | External + internal, worst-wins |
| `none` | Internal only; ignores the external column |

Unmapped codes become `bad` with reason `source_data_quality: <value>`. Full walkthrough: [OSIsoft PI Export tutorial](tutorials/osisoft-pi-export.md).

Sketch with PI Web API:

```python
from piwebapi.pi_web_api_client import PIWebApiClient

client = PIWebApiClient("https://pisrvr/piwebapi", auth=("user", "pass"))
# Fetch recorded values + status → DataFrame with timestamp, tag_name, value, pi_quality
# Then pass to tsqc.check(...) as above
```

## Timezone handling

Most industrial historians (Aspen IP21, OSIsoft PI, Wonderware, GE Historian) return timestamps as local wall-clock time with no timezone attached. When working with such data:

1. Pass the source timezone via `assume_tz` (e.g., `assume_tz="America/Edmonton"`).
2. The library normalises to UTC internally for consistent rule evaluation.
3. **All output** — `result.df`, `result.plot()`, `issue_summary()`, `check_timestamps()` — displays timestamps in the original source timezone automatically.
4. If your timestamps are already tz-aware (e.g., ISO 8601 with offset), `assume_tz` is optional.

## API wrapper

For custom integrations, wrap `timeseries-qc` in an HTTP endpoint:

```python
from flask import Flask, request, jsonify
import pandas as pd
import tsqc

app = Flask(__name__)

@app.route("/qc/check", methods=["POST"])
def qc_check():
    data = request.get_json()
    df = pd.DataFrame(data["measurements"])
    result = tsqc.check(df, assume_tz=data.get("timezone", "UTC"))
    return jsonify(result.summary().to_dict(orient="records"))
```

## Next Steps

- [OSIsoft PI Export tutorial](tutorials/osisoft-pi-export.md) — combined vs exclusive modes
- [Industry Use Cases](industry-use-cases.md) — applications across sectors
- [YAML Configuration](yaml-configuration.md) — configure rules per tag
- [CI Gate tutorial](tutorials/ci-gate-data-quality.md) — fail jobs on `pct_bad`
