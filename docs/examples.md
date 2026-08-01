---
title: Examples — Real-World Code Samples
description: Real-world code examples for using timeseries-qc with SCADA data, historian systems, IoT sensors, and industrial automation. Includes solar farm, oil & gas, and manufacturing use cases.
---

# Examples

Real-world code examples for common use cases. Each example includes complete, runnable code you can adapt for your own data.

---

## Solar Farm SCADA Data

Detect inverter faults, irradiance sensor failures, and tracker angle anomalies.

```python
import tsqc
import pandas as pd
from tsqc.rules import FlatlineRule, RangeRule, DeltaRule

# Load solar farm SCADA data
df = pd.read_csv("solar_scada.csv")  # timestamp, tag_name, value

# Define rules in Python
rules = [
    FlatlineRule(window="1h", min_delta=0.01, level="sus"),
    RangeRule(min_val=-10, max_val=2000, level="bad"),  # Catch invalid readings
    DeltaRule(max_delta=500, level="sus"),  # Catch spikes
]

# Run check
result = tsqc.check(df, rules=rules, assume_tz="America/Phoenix")

# View summary
print(result.summary())

# Generate interactive chart
fig = result.plot(title="Solar Farm Quality Timeline")
fig.show()

# Export report
result.export_report("solar_qc_report.html", title="Solar Farm QC - June 2026")
```

**YAML version:**

```yaml
# solar_rules.yaml
default_rules:
  - check: flatline
    window: 1h
    min_delta: 0.01
    level: sus
  
  - check: range
    min: -10
    max: 2000
    level: bad
  
  - check: delta
    max_delta: 500
    level: sus

tag_rules:
  "INVERTER.*":
    - check: range
      min: 0
      max: 5000
      level: bad
  
  "MET.IRRADIANCE":
    - check: range
      min: 0
      max: 1500
      level: bad
    
    - check: flatline
      window: 30min
      min_delta: 1.0
      level: sus
```

```python
# Use YAML config
result = tsqc.check(df, rules="solar_rules.yaml", assume_tz="America/Phoenix")
```

[See solar farm use cases →](industry-use-cases.md#solar-energy)

---

## Oil & Gas Well Pad

Monitor pressure sensors, flow meters, and temperature readings.

```python
import tsqc
import pandas as pd

# Load well pad data
df = pd.read_csv("wellpad_data.csv")

# Detect flatlines at zero (common sensor failure)
from tsqc.rules import FlatlineRule, CustomRule, RangeRule

def is_zero_flatline(series):
    """Detect flatlines specifically at zero value"""
    return (series == 0) & (series.shift(1) == 0)

rules = [
    CustomRule(fn=is_zero_flatline, name="zero_flatline", level="bad"),
    FlatlineRule(window="2h", min_delta=0.5, level="sus"),
    RangeRule(min_val=0, max_val=10000, level="bad"),  # Physical limits
]

result = tsqc.check(df, rules=rules, assume_tz="America/Chicago")

# Find problematic tags
issue_summary = result.issue_summary()
worst_tags = issue_summary.groupby("tag_name")["n_rows_with_issues"].sum().sort_values(ascending=False)
print("Tags with most issues:")
print(worst_tags.head(10))
```

[See oil & gas use cases →](industry-use-cases.md#oil-gas)

---

## OSIsoft PI Historian Integration

Use existing PI quality codes alongside internal rules.

```python
import tsqc
import pandas as pd

# Load data from PI with quality column
# Assume quality codes: 0=Good, 192=Bad, 193=Questionable
df = pd.read_csv("pi_export.csv")  # includes 'pi_quality' column

# Define quality map
quality_map = {
    0: "good",
    192: "bad",
    193: "sus",
    194: "bad",  # I/O Timeout
    195: "bad",  # Bad Input
}

# Combined mode: merge PI quality with internal rules
result = tsqc.check(
    df,
    external_quality_col="pi_quality",
    quality_mode="combined",
    quality_map=quality_map,
    rules="pi_rules.yaml",
    assume_tz="UTC",
)

# Rows flagged by both PI and internal rules will show combined reasons
print(result.df[["timestamp", "tag_name", "value", "quality", "quality_reasons"]].head())

# Example output:
# quality_reasons: "source_data_quality: 192|flatline @ 45.2000"
```

**YAML with quality_map:**

```yaml
# pi_rules.yaml
quality_map:
  0: good
  192: bad
  193: sus
  194: bad
  195: bad

default_rules:
  - check: null
    level: bad
  
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus
```

[See full historian integration guide →](scada-integration.md)

---

## Manufacturing Line Monitoring

Detect machine downtime, sensor drift, and out-of-spec conditions.

```python
import tsqc
import pandas as pd
from tsqc.rules import OutlierRule, RangeRule, DeltaRule

# Load production line sensor data
df = pd.read_csv("production_sensors.csv")

# Use statistical outlier detection for anomaly detection
rules = [
    OutlierRule(method="zscore", threshold=3.0, window="24h", level="sus"),
    RangeRule(min_val=0, max_val=100, level="bad"),  # Process limits
    DeltaRule(max_delta=10, level="sus"),  # Sudden changes
]

result = tsqc.check(df, rules=rules, assume_tz="Europe/Berlin")

# Flag rows where machine downtime occurred
downtime_mask = (result.df["tag_name"].str.contains("SPEED")) & (result.df["value"] == 0)
print(f"Detected {downtime_mask.sum()} downtime events")

# Visualize
fig = result.plot(title="Production Line Quality - Week 27")
fig.show()
```

---

## Multi-Site Battery Storage

Monitor voltage, current, and temperature across multiple battery sites.

```python
import tsqc
import pandas as pd

# Load data from multiple sites
df = pd.read_csv("battery_fleet_data.csv")

# Tag-specific rules using glob patterns
yaml_config = """
default_rules:
  - check: null
    level: bad
  
  - check: outlier
    method: mad
    threshold: 3.5
    window: 168h  # 1 week
    level: sus

tag_rules:
  "SITE_*.VOLTAGE":
    - check: range
      min: 800
      max: 1000
      level: bad
  
  "SITE_*.CURRENT":
    - check: range
      min: -500
      max: 500
      level: bad
  
  "SITE_*.TEMP_C":
    - check: range
      min: -10
      max: 60
      level: bad
    
    - check: delta
      max_delta: 5
      level: sus
"""

with open("battery_rules.yaml", "w") as f:
    f.write(yaml_config)

result = tsqc.check(df, rules="battery_rules.yaml", assume_tz="UTC")

# Group issues by site
result.df["site"] = result.df["tag_name"].str.extract(r"(SITE_\d+)")
site_summary = result.df.groupby("site")["quality"].value_counts().unstack(fill_value=0)
print(site_summary)
```

---

## Automated Daily Reporting

Schedule quality checks and email reports automatically.

```python
import tsqc
import pandas as pd
from datetime import datetime, timedelta

def daily_quality_report(data_source, output_dir="./reports"):
    """
    Run daily quality check and generate HTML report.
    Can be scheduled with cron or Task Scheduler.
    """
    # Load today's data
    today = datetime.now().date()
    df = pd.read_csv(f"{data_source}/data_{today}.csv")
    
    # Run check
    result = tsqc.check(df, rules="production_rules.yaml", assume_tz="UTC")
    
    # Generate report
    report_path = f"{output_dir}/qc_report_{today}.html"
    result.export_report(report_path, title=f"Daily QC Report - {today}")
    
    # Get summary stats
    summary = result.summary()
    critical_tags = summary[summary["pct_bad"] > 5.0]
    
    # Log results
    print(f"Report generated: {report_path}")
    print(f"Tags with >5% bad quality: {len(critical_tags)}")
    
    if len(critical_tags) > 0:
        print("⚠️ Critical quality issues detected:")
        print(critical_tags[["tag_name", "pct_bad", "n_bad"]])
        # Send alert email here
    
    return result, report_path

# Run daily report
result, report_path = daily_quality_report("/data/scada_exports")
```

**Cron schedule (Linux):**
```bash
# Run at 6 AM every day
0 6 * * * /usr/bin/python3 /path/to/daily_report.py
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\scripts\daily_report.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 6am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "DailyQC" -Description "Run timeseries-qc daily report"
```

---

## Timestamp Quality Validation

Detect gaps, duplicates, and frequency drift in your time series.

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensor_data.csv")
result = tsqc.check(df, assume_tz="UTC")

# Check timestamp health
ts_issues = result.check_timestamps(expected_freq="1min", freq_tolerance=0.1)

print("Timestamp Issues:")
print(ts_issues)

# Example output:
#   tag_name     issue_type              timestamp         description
#   TAG_001      gap                     2026-01-01 05:00  Gap of 15.0 minutes
#   TAG_002      duplicate               2026-01-01 12:30  Duplicate timestamp
#   TAG_003      non_monotonic           2026-01-01 18:00  Earlier than previous
#   TAG_004      freq_drift              2026-01-01 23:45  Actual: 1.2min vs expected: 1.0min
```

---

## Next Steps

- [Quickstart Tutorial](quickstart.md) - Get started in 5 lines
- [User Guide](user-guide.md) - Complete walkthrough
- [API Reference](api-reference.md) - Full API documentation
- [YAML Configuration](yaml-configuration.md) - Configure rules in YAML
- [SCADA Integration Guide](scada-integration.md) - OSIsoft PI, OPC UA, etc.
- [Tutorials](tutorials/index.md) - Step-by-step industry-specific guides
