---
title: Visualization — Timeline Charts with timeseries-qc
description: Interactive multi-tag quality timeline charts with Plotly. Customize views, filter by tag/time, and export.
og_title: Visualization — Timeline Charts with timeseries-qc
og_description: Interactive multi-tag quality timeline charts with Plotly. Customize views, filter by tag/time, and export.
---

# Visualization

!!! abstract "TL;DR"
    Call `result.plot().show()` for a Plotly Gantt-style quality timeline (green/yellow/red). Filter by tags or time range, then export with Plotly or include the chart via `export_report()`.

`timeseries-qc` produces a Plotly-based horizontal Gantt chart showing quality over time for every tag.

## How do I plot quality results?

Call `result.plot().show()` after `tsqc.check()`. Each tag is a horizontal row colored by quality level.

```python
result.plot().show()
```

Each tag gets a horizontal row. Color coding:

- <span style="color:#16a34a">**Green** = good</span>
- <span style="color:#ca8a04">**Yellow** = suspect</span>
- <span style="color:#dc2626">**Red** = bad</span>

## How do I customize the plot?

Pass optional arguments to `result.plot()` to filter tags, restrict the time range, or set title and height.

### Filter by Tags

```python
result.plot(tags=["INVERTER.MW", "MET.IRRADIANCE"])
```

### Filter by Time Range

```python
result.plot(start="2026-01-01", end="2026-01-07")
```

### Custom Title and Height

```python
result.plot(title="Solar Farm Quality", height=600)
```

## What interactive features are available?

Hover for segment details and triggering reasons; use range selectors, the range slider, and the legend to explore the timeline.

- **Hover** over segments for details (tag, quality, start, end, duration)
- **Reason tooltip**: Hovering over suspect or bad segments shows the triggering rule(s) — e.g. `Reason: null values`, `Reason: flatline @ 42.5000`, `Reason: delta, null values` — so you can immediately see _why_ a segment was flagged
- **Range selector** buttons: 1d, 1w, 1m, All
- **Range slider** at the bottom for zooming
- **Legend** toggles visibility of good/suspect/bad segments

## How does timezone display work?

The chart uses the same timezone as your input data — set via `assume_tz` for tz-naive series, or the timestamps' own zone if already tz-aware.

- If you pass tz-naive data with `assume_tz="America/Edmonton"`, the x-axis and hover tooltips show Edmonton local time.
- If you pass tz-aware timestamps (e.g., `datetime64[ns, America/Chicago]`), the chart uses that timezone.
- The annotated DataFrame `result.df` also contains timestamps in the input timezone.
- Bare date strings in `start`/`end` parameters (e.g., `start="2026-01-01"`) are interpreted in the input timezone.

## How do I export the chart?

Use Plotly's `write_html` / `write_image` on the figure returned by `result.plot()`, or embed it in a full report with `export_report()`.

```python
fig = result.plot()
fig.write_html("chart.html")
fig.write_image("chart.png")  # requires kaleido or orca
```

## How do I include the chart in a report?

For a complete report with chart and tables, call `result.export_report()`:

```python
result.export_report("report.html")
```

See [Report Generation](report-generation.md) for details.

## FAQ

### What colors mean what?

Green is `good`, yellow is `sus`, red is `bad`.

### Can I plot only some tags?

Yes. Pass `tags=[...]` to `result.plot()`.

### Which timezone does the chart use?

The input timezone — from `assume_tz` for tz-naive data, or the timestamps' own timezone if tz-aware.

### Why don't I see a reason on good segments?

Reason tooltips appear on suspect and bad segments, showing which rule(s) triggered.

### How is this different from `export_report()`?

`plot()` returns a Plotly figure; `export_report()` writes a self-contained HTML file with the chart plus summary and timestamp tables.

## Next Steps

- [Report Generation](report-generation.md) — self-contained HTML reports
- [API Reference](api-reference.md) — `QCResult.plot()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
