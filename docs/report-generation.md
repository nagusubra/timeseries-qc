---
title: Report Generation — HTML Reports with timeseries-qc
description: Generate self-contained HTML quality reports with embedded Plotly charts, summary tables, and timestamp health analysis.
og_title: Report Generation — HTML Reports with timeseries-qc
og_description: Generate self-contained HTML quality reports with embedded Plotly charts, summary tables, and timestamp health analysis.
---

# Report Generation

!!! abstract "TL;DR"
    Call `result.export_report("quality_report.html")` for a self-contained HTML file with the quality timeline, per-tag summary, issue summary, and timestamp health — no CDN or internet required.

`timeseries-qc` can generate a complete, self-contained HTML report with no external dependencies.

## How do I generate a report?

Pass an output path to `result.export_report()` after running `tsqc.check()`:

```python
result.export_report("quality_report.html")
```

## What does the report include?

The HTML report embeds the interactive timeline plus summary, issue, and timestamp-health tables.

1. **Quality Timeline** — interactive Plotly chart
2. **Summary per Tag** — good/suspect/bad percentages
3. **Issue Summary** — contiguous bad/sus segments with durations
4. **Timestamp Health** — gaps, duplicates, and other timestamp anomalies

## Why is the report self-contained?

Plotly JavaScript and styles are embedded inline, so the file opens offline and is easy to email or archive.

- Plotly JavaScript is embedded (not loaded from CDN)
- All styles are inline
- No internet connection required to view

This makes it suitable for:

- Emailing to stakeholders
- Archiving in data management systems
- Sharing with teams that don't have Python access

## How do I customize the report title?

Pass a `title=` string to `export_report()`:

```python
result.export_report("report.html", title="Solar Farm QC Report - January 2026")
```

## FAQ

### Do recipients need Python or Plotly installed?

No. The HTML file is self-contained and opens in a browser without Python.

### Does the report need internet access?

No. Plotly JS and styles are embedded; nothing is loaded from a CDN.

### What sections are in the report?

Quality timeline, per-tag summary, issue summary, and timestamp health.

### Can I set a custom title?

Yes. Use `result.export_report("report.html", title="...")`.

### How is this different from `result.plot()`?

`plot()` returns a Plotly figure for interactive use; `export_report()` writes a full HTML document with chart and tables.

## Next Steps

- [Visualization](visualization.md) — customizing the timeline chart
- [API Reference](api-reference.md) — `QCResult.export_report()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
