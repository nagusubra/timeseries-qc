---
title: LLM & AI Agent Context — timeseries-qc
description: Context file optimized for LLMs and AI coding agents. Complete reference for using timeseries-qc in agent-assisted development workflows.
---

# LLM & AI Agent Context

This page provides structured context for AI coding agents (GitHub Copilot, Cursor, Aider, etc.) to help generate accurate timeseries-qc code.

---

## Library Overview

**timeseries-qc** is a Python library for quality control of time series data from SCADA, DCS, IoT, and historian systems.

**PyPI:** `pip install timeseries-qc`  
**Version:** 0.5.0 (August 2026)  
**License:** MIT  
**GitHub:** https://github.com/nagusubra/timeseries-qc

---

## Core Concept

Every row in a time series DataFrame is classified as:
- **good** - Passes all quality rules
- **sus** (suspect) - Questionable but not necessarily bad
- **bad** - Fails critical quality rules

---

## Minimal Working Example

```python
import tsqc
import pandas as pd

# Load data with columns: timestamp, tag_name, value
df = pd.read_csv("sensor_data.csv")

# Run quality check (assume_tz required for tz-naive data)
result = tsqc.check(df, assume_tz="UTC")

# View results
print(result.summary())  # Summary stats per tag
result.plot().show()      # Interactive timeline chart
```

---

## Required DataFrame Structure

### Multi-Tag Format (Default)
```python
df = pd.DataFrame({
    "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:01"]),
    "tag_name": ["TEMP_01", "TEMP_01"],
    "value": [45.2, 45.3]
})
```

### Single-Tag Format
```python
df = pd.DataFrame({
    "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:01"]),
    "value": [45.2, 45.3]
})

result = tsqc.check(df, tag_col=None, assume_tz="UTC")
```

### Custom Column Names
```python
result = tsqc.check(
    df,
    time_col="datetime",
    tag_col="sensor_id",
    value_col="measurement",
    assume_tz="UTC"
)
```

---

## Built-In Rules

### 1. NullRule
Flags null/NaN values.

```python
from tsqc.rules import NullRule
rule = NullRule(level="bad")
```

### 2. FlatlineRule
Detects values that don't change.

```python
from tsqc.rules import FlatlineRule
rule = FlatlineRule(
    window="1h",      # Rolling window
    min_delta=0.01,   # Minimum change required
    level="sus"
)
```

### 3. RangeRule
Checks values are within bounds.

```python
from tsqc.rules import RangeRule
rule = RangeRule(
    min_val=0,
    max_val=100,
    level="bad"
)
```

### 4. DeltaRule
Detects sudden changes between consecutive values.

```python
from tsqc.rules import DeltaRule
rule = DeltaRule(
    min_delta=-50,   # Optional: minimum allowed change
    max_delta=50,    # Optional: maximum allowed change
    level="sus"
)
```

### 5. OutlierRule
Statistical outlier detection.

```python
from tsqc.rules import OutlierRule

# Z-score method
rule = OutlierRule(
    method="zscore",
    threshold=3.0,
    window="24h",
    level="sus"
)

# MAD (Median Absolute Deviation) method
rule = OutlierRule(
    method="mad",
    threshold=3.5,
    window="168h",
    level="sus"
)

# IQR (Interquartile Range) method
rule = OutlierRule(
    method="iqr",
    threshold=1.5,
    window="24h",
    level="sus"
)
```

---

## YAML Configuration

### Basic Example
```yaml
default_rules:
  - check: null
    level: bad
  
  - check: flatline
    window: 1h
    min_delta: 0.01
    level: sus
  
  - check: range
    min: 0
    max: 100
    level: bad
```

### Tag-Specific Rules
```yaml
default_rules:
  - check: null
    level: bad

tag_rules:
  "TEMP.*":
    - check: range
      min: -50
      max: 150
      level: bad
  
  "PRESSURE.*":
    - check: range
      min: 0
      max: 500
      level: bad
    
    - check: flatline
      window: 30min
      min_delta: 0.5
      level: sus
```

### Usage
```python
result = tsqc.check(df, rules="config.yaml", assume_tz="UTC")
```

---

## External Quality Column (Historian Integration)

Use existing quality codes from historian systems (OSIsoft PI, Wonderware, etc.):

```python
# Exclusive mode: Use historian quality only
result = tsqc.check(
    df,
    external_quality_col="pi_quality",
    quality_mode="exclusive",
    quality_map={0: "good", 192: "bad", 193: "sus"},
    assume_tz="UTC"
)

# Combined mode: Merge historian + internal rules (worst-wins)
result = tsqc.check(
    df,
    external_quality_col="pi_quality",
    quality_mode="combined",
    quality_map={0: "good", 192: "bad", 193: "sus"},
    rules="rules.yaml",
    assume_tz="UTC"
)
```

**YAML with quality_map:**
```yaml
quality_map:
  0: good
  192: bad
  193: sus

default_rules:
  - check: null
    level: bad
```

---

## QCResult API

### Methods

```python
result = tsqc.check(df, assume_tz="UTC")

# Access DataFrame with quality columns
result.df  # Original + 'quality' and 'quality_reasons' columns

# Summary statistics per tag
summary = result.summary()
# Returns: tag_name, n_total, n_good, n_sus, n_bad, pct_good, pct_sus, pct_bad

# Issue summary (contiguous issue runs)
issues = result.issue_summary()
# Returns: tag_name, issue_start_time, issue_end_time, n_rows, status, reasons

# Timestamp validation
ts_issues = result.check_timestamps(expected_freq="1min", freq_tolerance=0.1)
# Returns: tag_name, issue_type, timestamp, description

# Interactive timeline chart
fig = result.plot(title="Quality Timeline")
fig.show()  # Plotly Figure object

# Export HTML report
result.export_report("report.html", title="QC Report - June 2026")
```

---

## Custom Rules

```python
from tsqc.rules import CustomRule

def is_zero(series):
    """Flag all zero values"""
    return series == 0

rule = CustomRule(fn=is_zero, name="zero_value", level="sus")

result = tsqc.check(df, rules=[rule], assume_tz="UTC")
```

---

## Common Patterns

### Pattern 1: Daily Automated Report
```python
from datetime import datetime
import tsqc
import pandas as pd

def daily_qc_report(data_path):
    df = pd.read_csv(data_path)
    result = tsqc.check(df, rules="rules.yaml", assume_tz="UTC")
    
    today = datetime.now().date()
    result.export_report(f"qc_report_{today}.html")
    
    # Alert if critical issues found
    summary = result.summary()
    if (summary["pct_bad"] > 5.0).any():
        print("⚠️ Critical quality issues detected")
        return False
    return True
```

### Pattern 2: Filter Bad Data
```python
result = tsqc.check(df, assume_tz="UTC")

# Keep only good data
good_data = result.df[result.df["quality"] == "good"]

# Remove bad data, keep suspect
usable_data = result.df[result.df["quality"] != "bad"]
```

### Pattern 3: Tag-Specific Analysis
```python
result = tsqc.check(df, assume_tz="UTC")

# Get worst-performing tags
summary = result.summary()
worst_tags = summary.nlargest(10, "pct_bad")

# Analyze specific tag
tag_data = result.df[result.df["tag_name"] == "TEMP_01"]
print(tag_data[tag_data["quality"] != "good"])
```

---

## Timezone Handling

**CRITICAL:** Always pass `assume_tz` for timezone-naive data (CSV files).

```python
# Timezone-naive data (from CSV)
result = tsqc.check(df, assume_tz="UTC")  # Required
result = tsqc.check(df, assume_tz="America/New_York")  # IANA timezone

# Timezone-aware data (already has timezone)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
result = tsqc.check(df)  # assume_tz not needed
```

---

## Quality Reasons Format

Reasons are pipe-separated strings:

```python
# Examples:
"null"
"flatline @ 45.2000"
"range-max"
"outlier-zscore"
"source_data_quality: 192"
"null|flatline @ 0.0000"  # Multiple reasons
```

---

## Error Handling

### Common Errors

**Missing timestamp column:**
```python
# Error: KeyError: 'timestamp'
# Fix: Specify custom column name
result = tsqc.check(df, time_col="datetime", assume_tz="UTC")
```

**Missing assume_tz for naive data:**
```python
# Error: ValueError: Timezone-naive data requires assume_tz parameter
# Fix: Add assume_tz
result = tsqc.check(df, assume_tz="UTC")
```

**Invalid YAML:**
```python
# Error: ValueError: Invalid rule configuration
# Fix: Check YAML syntax and required fields
```

---

## Performance Tips

1. **Use YAML for large configs** - Faster than Python rule objects
2. **Pre-filter data** - Remove unnecessary tags before QC
3. **Adjust window sizes** - Larger windows = slower processing
4. **Batch processing** - Process data in chunks for very large datasets

---

## Integration Examples

### OSIsoft PI System
```python
import pandas as pd
from PIconnect import PIServer
import tsqc

# Fetch data from PI
server = PIServer()
points = server.search("REACTOR.*")
df = pd.DataFrame({
    "timestamp": points[0].recorded_values(start_time, end_time).index,
    "tag_name": "REACTOR_01",
    "value": points[0].recorded_values(start_time, end_time).values
})

result = tsqc.check(df, rules="pi_rules.yaml", assume_tz="UTC")
```

### Pandas Integration
```python
import pandas as pd
import tsqc

# Read from various sources
df = pd.read_csv("data.csv")
df = pd.read_parquet("data.parquet")
df = pd.read_sql("SELECT * FROM sensor_data", conn)

# Run QC
result = tsqc.check(df, assume_tz="UTC")

# Export with original data preserved
result.df.to_csv("qc_output.csv", index=False)
```

---

## Testing Checklist

When generating code using timeseries-qc, verify:

- [ ] `assume_tz` parameter included for CSV/naive data
- [ ] DataFrame has required columns: timestamp, value (and tag_name for multi-tag)
- [ ] Rule parameters are valid (e.g., `window` is time string like "1h")
- [ ] Quality levels are "good", "sus", or "bad" (not "suspect" or other variants)
- [ ] YAML check names are: null, flatline, range, delta, outlier
- [ ] External quality mode is "exclusive", "combined", or "none"

---

## Version-Specific Features

### v0.5.0 (Current)
- Removed dead code (`_VALID_LEVELS`, unused `**kwargs`, redundant import)
- Restored `data/` directory for generated example datasets (git-ignored)
- Example notebooks fixed to work end-to-end (solar farm, oilfield)
- Full 0.5.0 release (see changelog)

### v0.4.2
- Flatline reasons include value: `"flatline @ 45.2000"`
- External quality reasons use prefix: `"source_data_quality: <value>"`
- Hover tooltip label: "Reason:"

### v0.4.1
- Added OutlierRule (zscore, mad, iqr methods)
- Statistical outlier detection

### v0.4.0
- Added external quality column support
- Quality modes: exclusive, combined, none

---

## Quick Reference

```python
# Most common usage patterns
import tsqc

# 1. Basic check
result = tsqc.check(df, assume_tz="UTC")

# 2. With YAML config
result = tsqc.check(df, rules="config.yaml", assume_tz="UTC")

# 3. With Python rules
from tsqc.rules import FlatlineRule, RangeRule
result = tsqc.check(
    df,
    rules=[
        FlatlineRule(window="1h", min_delta=0.01, level="sus"),
        RangeRule(min_val=0, max_val=100, level="bad")
    ],
    assume_tz="UTC"
)

# 4. With historian quality
result = tsqc.check(
    df,
    external_quality_col="status",
    quality_mode="combined",
    quality_map={0: "good", 1: "sus", 2: "bad"},
    rules="rules.yaml",
    assume_tz="UTC"
)

# 5. View results
print(result.summary())
result.plot().show()
result.export_report("report.html")
```

---

## Related Pages

- [API Reference](api-reference.md) - Full API documentation
- [Examples](examples.md) - Real-world code examples
- [YAML Configuration](yaml-configuration.md) - Complete YAML guide
- [Quickstart](quickstart.md) - 5-minute tutorial
