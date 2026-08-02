---
title: Glossary — timeseries-qc Terminology
description: A glossary of technical terms used in time series data quality control and the timeseries-qc library.
og_title: Glossary — timeseries-qc Terminology
og_description: A glossary of technical terms used in time series data quality control and the timeseries-qc library.
---

# Glossary

!!! abstract "TL;DR"
    Key timeseries-qc terms: quality levels (`good` / `sus` / `bad`), the five built-in rules plus custom rules, industrial concepts like SCADA and tags, and timestamp/timezone-related vocabulary used throughout the docs.

## Quality Levels

### Bad

A data quality classification indicating that a data point should be excluded from analysis due to a confirmed issue.

### Good

A data quality classification indicating that a data point passes all applied rules and can be used for analysis.

### Quality

The classification assigned to each data point — good, suspect, or bad — indicating its reliability for downstream use.

### Suspect

A data quality classification indicating a potential issue that needs manual review. Suspect data may or may not be usable depending on the context.

## Rules

### Custom Rule

A user-defined rule implemented as a Python function or class. Custom rules receive a tag's DataFrame and return classification results.

### Delta Rule

A rule that flags readings that change abruptly from the previous measurement. Useful for detecting sensor spikes or communication glitches.

### Flatline Rule

A rule that detects sensors reporting constant (or near-constant) values over time, which may indicate a stuck or frozen sensor.

### Null Rule

A rule that flags null (NaN) values in the data. Missing values are commonly encountered in sensor data during communication outages.

### Range Rule

A rule that flags values outside a specified minimum-maximum range. Ranges can be static (e.g., 0–100) or dynamic (e.g., based on rolling statistics).

### Rule

A check applied to each tag's data to determine data quality. Each rule produces a value (or NaN), a good/suspect/bad classification, and a reason string.

### YAML Rule File

A file containing rule definitions in YAML format, with `default_rules` (applied to all tags) and `tag_rules` (applied to specific tags or patterns).

## Industrial Systems

### SCADA

Supervisory Control and Data Acquisition — an industrial control system used to monitor and control infrastructure and equipment.

### Tag

A named measurement point, also referred to as a sensor, channel, or signal. Each tag produces a time series of values.

## Visualization & Encoding

### RLE (Run-Length Encoding)

An algorithm that compresses consecutive identical quality values into segments. Used to produce the timeline chart efficiently.

### Timeline

A horizontal Gantt-style chart showing quality (good/suspect/bad) over time for each tag. The primary visualization output of `timeseries-qc`.

## Timestamps & Timezones

### Timestamp Health

An analysis of timestamp quality that detects gaps, duplicates, non-monotonic timestamps, frequency drift, and DST issues.

## Next Steps

- [FAQ](faq.md) — frequently asked questions
- [API Reference](api-reference.md) — complete method documentation
- [Architecture](architecture.md) — how the library is structured
