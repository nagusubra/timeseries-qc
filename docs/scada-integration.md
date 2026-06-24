---
title: SCADA Integration — timeseries-qc
description: Integrate timeseries-qc with SCADA systems for automated data quality monitoring in industrial environments.
---

# SCADA Integration

## Data Pipeline Integration

`timeseries-qc` can be integrated into SCADA data pipelines for automated quality monitoring:

1. **Extract** data from SCADA historian (OSIsoft PI, Wonderware, Ignition, etc.)
2. **Transform** data into the expected DataFrame format (timestamp, tag_name, value)
3. **Check** quality with `tsqc.check()`
4. **Report** via `result.export_report()` or store `result.df` back to the historian

## CSV-Based Integration

Many SCADA systems can export data as CSV. Load and check with:

```python
import pandas as pd
import tsqc

df = pd.read_csv("export.csv", parse_dates=["timestamp"])
result = tsqc.check(df, assume_tz="UTC")
```

## Database Integration

For SCADA systems with SQL access:

```python
import pandas as pd
import tsqc
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@host:5432/scada")
query = "SELECT timestamp, tag_name, value FROM measurements WHERE timestamp >= NOW() - INTERVAL '7 days'"
df = pd.read_sql(query, engine)
result = tsqc.check(df, assume_tz="UTC")
```

## OSIsoft PI

For OSIsoft PI systems, use the PI Web API client to fetch data:

```python
from piwebapi.pi_web_api_client import PIWebApiClient

client = PIWebApiClient("https://pisrvr/piwebapi", auth=("user", "pass"))
# Fetch data and convert to DataFrame
# Then pass to tsqc.check()
```

## API Integration

### Historical Context: Timezone Handling

Most industrial historians (Aspen IP21, OSIsoft PI, Wonderware, GE Historian) return timestamps as local wall-clock time with no timezone attached. When working with such data:

1. Pass the source timezone via `assume_tz` (e.g., `assume_tz="America/Edmonton"`).
2. The library normalises to UTC internally for consistent rule evaluation.
3. **All output** — `result.df`, `result.plot()`, `issue_summary()`, `check_timestamps()` — displays timestamps in the original source timezone automatically.
4. If your timestamps are already tz-aware (e.g., ISO 8601 with offset), `assume_tz` is optional.

## API Integration

For custom integrations, `timeseries-qc` can be wrapped in an API endpoint:

```python
from flask import Flask, request, jsonify
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

- [Industry Use Cases](industry-use-cases.md) — applications across sectors
- [YAML Configuration](yaml-configuration.md) — configure rules per tag
- [User Guide](user-guide.md) — walkthrough with examples
