---
title: FAQ — timeseries-qc Frequently Asked Questions
description: Frequently asked questions about timeseries-qc and time series data quality control.
---

# Frequently Asked Questions

## General

### What is time series quality control?

Time series quality control is the process of detecting and classifying data quality issues in sequential measurements. This includes identifying null values, flatline sensors, out-of-range readings, sudden spikes, timestamp gaps, and other anomalies that can corrupt downstream analysis.

### What is SCADA data quality?

SCADA (Supervisory Control and Data Acquisition) data quality refers to the reliability and accuracy of measurements collected from industrial control systems. Poor SCADA data quality can lead to incorrect operational decisions, false alarms, and inaccurate reporting.

### How does timeseries-qc classify data?

Every row is classified as **good** (passes all rules), **suspect** (may be unreliable), or **bad** (should be excluded). This three-level system provides more nuance than binary pass/fail approaches.

## Usage

### How do I install timeseries-qc?

```bash
pip install timeseries-qc
```

See the [Installation Guide](installation.md) for details.

### Can I use timeseries-qc with CSV files?

Yes. Load your CSV with pandas and pass the DataFrame to `tsqc.check()`:

```python
import pandas as pd
import tsqc
df = pd.read_csv("sensor_data.csv")
result = tsqc.check(df, assume_tz="UTC")
```

### Can I use multiple tags?

Yes. Include a `tag_name` column in your DataFrame. Each unique value is treated as a separate sensor. You can apply different rules to different tags using [YAML configuration](yaml-configuration.md).

### Can I use UTC?

Yes. Pass `assume_tz="UTC"` for tz-naive data, or pass tz-aware timestamps already in UTC.

Internally, the library normalizes all timestamps to UTC for consistent rule evaluation (flatline windows, gap detection, etc.). However, `result.df`, `result.plot()`, `issue_summary()`, and `check_timestamps()` all return timestamps in the **original input timezone** — so the chart x-axis, hover tooltips, and summary tables all show local time automatically.

### What timezone does the chart display?

The chart x-axis and hover tooltips always display timestamps in the same timezone as your input data. If you pass `assume_tz="America/Edmonton"`, the chart shows Edmonton local time. If your timestamps are already tz-aware, their existing timezone is used. No extra parameter is needed.

### Can I see what timezone the library is using?

Yes. `result.display_tz` returns the IANA timezone string (e.g., `"America/Edmonton"`, `"UTC"`) used for all timestamp display.

### Can I export HTML reports?

Yes. `result.export_report("report.html")` produces a self-contained HTML file. See [Report Generation](report-generation.md).

## Rules

### What is a flatline sensor?

A flatline sensor is one that reports the same (or nearly the same) value for an extended period, indicating the sensor may be stuck, frozen, or disconnected.

### How do I detect sensor drift?

Use the `DeltaRule` to flag readings that change too much between consecutive measurements. The 3-sigma auto-configured threshold catches unusually large changes.

### How do I detect timestamp gaps?

Use `result.check_timestamps()` which identifies gaps where the time difference exceeds twice the expected frequency.

### How do I detect duplicate timestamps?

`result.check_timestamps()` also detects duplicate timestamps automatically.

## Configuration

### How does YAML configuration work?

Create a YAML file with `default_rules` (applied to all tags) and `tag_rules` (applied to specific tags or glob patterns). See [YAML Configuration](yaml-configuration.md).

### Can I use glob patterns for tag matching?

Yes. Tag patterns support `*` and `?` wildcards, e.g. `"GENERATOR.*"` matches all tags starting with `GENERATOR.`.

## Comparison

### How does timeseries-qc compare to Great Expectations?

Great Expectations is a general-purpose data validation framework with no timeseries-specific features. It offers binary pass/fail classification and no timeline visualization.

### How does it compare to SaQC?

SaQC is designed for environmental science data with an environmental-domain-specific API. It lacks timeline visualization and uses an LGPL license.

### How does it compare to Pecos?

Pecos (Sandia Labs) has been in maintenance mode since 2021. It offers binary pass/fail classification without timeline charts or YAML configuration.

## Troubleshooting

### Why am I getting "Column has no timezone info"?

Your timestamp column is tz-naive. Pass `assume_tz="UTC"` (or your timezone) to `tsqc.check()`.

### Why is my YAML file not being found?

The path to your YAML file must exist. If the file is in the current directory, use `rules="tsqc_rules.yaml"`. See [Troubleshooting](troubleshooting.md) for more.

## Next Steps

- [Comparison](comparison.md) — detailed comparison with alternatives
- [Glossary](glossary.md) — definitions of technical terms
- [Troubleshooting](troubleshooting.md) — common issues and solutions
