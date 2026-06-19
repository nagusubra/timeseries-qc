---
title: Report Generation — HTML Reports with timeseries-qc
description: Generate self-contained HTML quality reports with embedded Plotly charts, summary tables, and timestamp health analysis.
---

# Report Generation

`timeseries-qc` can generate a complete, self-contained HTML report with no external dependencies.

## Basic Usage

```python
result.export_report("quality_report.html")
```

## Report Contents

The generated HTML report includes:

1. **Quality Timeline** — interactive Plotly chart
2. **Summary per Tag** — good/suspect/bad percentages
3. **Issue Summary** — contiguous bad/sus segments with durations
4. **Timestamp Health** — gaps, duplicates, and other timestamp anomalies

## Self-Contained Output

The report file is fully self-contained:

- Plotly JavaScript is embedded (not loaded from CDN)
- All styles are inline
- No internet connection required to view

This makes it suitable for:

- Emailing to stakeholders
- Archiving in data management systems
- Sharing with teams that don't have Python access

## Customizing the Report

```python
result.export_report("report.html", title="Solar Farm QC Report - January 2026")
```

## Next Steps

- [Visualization](visualization.md) — customizing the timeline chart
- [API Reference](api-reference.md) — `QCResult.export_report()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
