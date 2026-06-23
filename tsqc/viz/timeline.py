"""Build the Plotly quality timeline figure."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_COLOR_MAP = {
    "good": "#008000",
    "sus": "#FFFF00",
    "bad": "#FF0000",
}

# Draw bad first so good segments render on top when segments overlap at borders
_QUALITY_ORDER = ["bad", "sus", "good"]


def _human_duration(seconds: float) -> str:
    """Convert seconds to a human-readable string like '2h 15m' or '45s'."""
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def build_timeline_figure(
    segments: pd.DataFrame,
    summary: pd.DataFrame | None = None,
    title: str = "Data Quality Timeline",
    height: int = 400,
    **kwargs,
) -> go.Figure:
    """Build a Plotly Gantt-style quality timeline figure.

    Args:
        segments: Output of encode_quality_runs() — columns: tag_name, quality,
                  start, end, duration_seconds.
        summary: Per-tag summary DataFrame (from QCResult.summary()). Used for
                 Y-axis ordering (worst-first). If None, tags ordered by appearance.
        title: Figure title.
        height: Base figure height in px. Auto-scales +30px per tag beyond 10.

    Returns:
        plotly.graph_objects.Figure
    """
    if segments.empty:
        return go.Figure(layout=go.Layout(title=title))

    # Determine tag order (worst-first by pct_bad)
    if summary is not None and not summary.empty:
        tag_order = list(summary.sort_values("pct_bad", ascending=False)["tag_name"])
    else:
        tag_order = list(segments["tag_name"].unique())

    present_tags = set(segments["tag_name"].unique())
    tag_order = [t for t in tag_order if t in present_tags]

    n_tags = len(tag_order)
    auto_height = height + max(0, n_tags - 10) * 30

    # Build hover text
    segments = segments.copy()
    segments["duration_str"] = segments["duration_seconds"].apply(_human_duration)
    segments["hover"] = (
        "<b>" + segments["tag_name"].astype(str) + "</b><br>"
        + "Quality: " + segments["quality"].astype(str) + "<br>"
        + "Start: " + segments["start"].astype(str) + "<br>"
        + "End: " + segments["end"].astype(str) + "<br>"
        + "Duration: " + segments["duration_str"]
    )

    # Append "Cause: ..." for non-good segments that have reasons
    if "reasons" in segments.columns:
        cause_mask = segments["reasons"].str.len() > 0
        segments.loc[cause_mask, "hover"] += "<br>Cause: " + segments.loc[cause_mask, "reasons"]

    fig = go.Figure()

    # One group of traces per quality level — produces exactly 3 legend items.
    # showlegend=True only for the first trace in each group; all others share
    # the same legendgroup so clicking the legend item toggles all of them.
    for quality_level in _QUALITY_ORDER:
        sub = segments[segments["quality"] == quality_level]
        if sub.empty:
            continue

        color = _COLOR_MAP[quality_level]
        first_in_group = True

        for _, seg_row in sub.iterrows():
            duration_ms = int((seg_row["end"] - seg_row["start"]).total_seconds() * 1000)
            base_ts = seg_row["start"].isoformat()
            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[seg_row["tag_name"]],
                base=[base_ts],
                orientation="h",
                marker_color=color,
                hovertext=seg_row["hover"],
                hoverinfo="text",
                name=quality_level,
                legendgroup=quality_level,
                showlegend=first_in_group,
                opacity=0.85,
                width=0.5,
                offsetgroup=quality_level,
            ))
            first_in_group = False

    fig.update_layout(
        title=title,
        height=auto_height + 60,  # extra room for range slider
        xaxis=dict(
            type="date",
            rangeslider=dict(visible=True, thickness=0.06),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ],
                bgcolor="#f0f0f0",
                activecolor="#cccccc",
            ),
        ),
        yaxis=dict(
            title="Tag",
            categoryorder="array",
            categoryarray=list(reversed(tag_order)),
        ),
        barmode="overlay",
        legend=dict(title="Quality"),
        showlegend=True,
    )

    return fig
