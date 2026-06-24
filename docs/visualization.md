---
title: Visualization — Timeline Charts with timeseries-qc
description: Interactive multi-tag quality timeline charts with Plotly. Customize views, filter by tag/time, and export.
---

# Visualization

`timeseries-qc` produces a Plotly-based horizontal Gantt chart showing quality over time for every tag.

## Basic Usage

```python
result.plot().show()
```

Each tag gets a horizontal row. Color coding:

- <span style="color:#16a34a">**Green** = good</span>
- <span style="color:#ca8a04">**Yellow** = suspect</span>
- <span style="color:#dc2626">**Red** = bad</span>

## Customizing the Plot

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

## Interactive Features

- **Hover** over segments for details (tag, quality, start, end, duration)
- **Cause tooltip**: Hovering over suspect or bad segments shows the triggering rule(s) — e.g. `Cause: null values`, `Cause: flatline`, `Cause: delta, null values` — so you can immediately see _why_ a segment was flagged
- **Range selector** buttons: 1d, 1w, 1m, All
- **Range slider** at the bottom for zooming
- **Legend** toggles visibility of good/suspect/bad segments

## Timezone Behavior

The chart automatically displays timestamps in the same timezone as the input data — no extra configuration needed.

- If you pass tz-naive data with `assume_tz="America/Edmonton"`, the x-axis and hover tooltips show Edmonton local time.
- If you pass tz-aware timestamps (e.g., `datetime64[ns, America/Chicago]`), the chart uses that timezone.
- The annotated DataFrame `result.df` also contains timestamps in the input timezone.
- Bare date strings in `start`/`end` parameters (e.g., `start="2026-01-01"`) are interpreted in the input timezone.

## Exporting the Chart

The chart can be saved as HTML or PNG using Plotly's export options:

```python
fig = result.plot()
fig.write_html("chart.html")
fig.write_image("chart.png")  # requires kaleido or orca
```

## Report Export

For a complete report with chart and tables:

```python
result.export_report("report.html")
```

See [Report Generation](report-generation.md) for details.

## Next Steps

- [Report Generation](report-generation.md) — self-contained HTML reports
- [API Reference](api-reference.md) — `QCResult.plot()` documentation
- [User Guide](user-guide.md) — walkthrough with examples
