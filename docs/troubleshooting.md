---
title: Troubleshooting — timeseries-qc
description: Solutions to common issues encountered when using timeseries-qc for time series data quality control.
---

# Troubleshooting

## Installation

### `pip install` fails with build errors

Ensure you have a compatible Python version (3.9+) and an internet connection. If using an older pip, upgrade first:

```bash
pip install --upgrade pip
pip install timeseries-qc
```

### ImportError: No module named 'tsqc'

Make sure the package is installed:

```bash
pip list | findstr timeseries-qc
```

If not listed, install it. Also check you aren't naming a local file `tsqc.py` that shadows the installed package.

## Data Issues

### "Column has no timezone info" warning

Your datetime column is timezone-naive. Pass `assume_tz="UTC"` (or your local timezone):

```python
result = tsqc.check(df, assume_tz="UTC")
```

### "No valid tag_name column found" error

Ensure your DataFrame has a column named `tag_name` (or `sensor`, `point_id`, `name`). The column must contain string identifiers.

### All rows classified as "good"

This could mean no rules are being applied. Check your YAML configuration or programmatic rules. Default rules are only applied when no YAML file is provided and no explicit rule list is given.

## YAML Configuration

### YAML file not found

The path must be relative to the current working directory or absolute. Use:

```python
result = tsqc.check(df, rules="path/to/tsqc_rules.yaml")
```

### Rules not applied to expected tags

Check tag patterns for glob support. `"GENERATOR.*"` matches `GENERATOR.ACTIVE_POWER` but not `GENERATOR1.ACTIVE_POWER`.

## Visualization

### Chart doesn't render in Jupyter

Make sure Plotly is installed and you call `.show()`:

```python
result.plot().show()
```

### "No module named 'plotly'" error

Install Plotly:

```bash
pip install plotly
```

## Report

### HTML report displays blank

The report file is self-contained but must be opened in a modern browser. Some email clients may strip JavaScript — download and open locally instead.

## Next Steps

- [FAQ](faq.md) — frequently asked questions
- [Glossary](glossary.md) — definitions of technical terms
- [API Reference](api-reference.md) — complete method documentation
