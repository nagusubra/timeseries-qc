"""Run-length encoding for quality segments.

Converts a row-per-observation DataFrame into a segment-per-run DataFrame.
"""

from __future__ import annotations

import pandas as pd


def encode_quality_runs(
    df: pd.DataFrame,
    time_col: str = "timestamp",
    tag_col: str | None = "tag_name",
    quality_col: str = "quality",
) -> pd.DataFrame:
    """Convert a row-per-observation DataFrame into a segment-per-run DataFrame.

    A "run" is a maximal sequence of consecutive rows for the same tag
    with the same quality label.

    Args:
        df: Annotated DataFrame with timestamp, tag_name, and quality columns.
        time_col: Name of the timestamp column.
        tag_col: Name of the tag column. None = treat entire df as one tag.
        quality_col: Name of the quality column.

    Returns:
        DataFrame with columns:
            tag_name, quality, start, end, duration_seconds

        *end* of a segment is the start of the next segment, or
        last_timestamp + median_interval for the final segment of each tag.
    """
    if df.empty:
        return pd.DataFrame(columns=["tag_name", "quality", "start", "end", "duration_seconds"])

    if tag_col is None or tag_col not in df.columns:
        work = df.copy()
        work["_tag"] = "default"
        _tc = "_tag"
    else:
        work = df.copy()
        _tc = tag_col

    segments: list[dict] = []

    for tag, group in work.groupby(_tc, sort=False):
        group = group.sort_values(time_col).reset_index(drop=True)
        timestamps = group[time_col]
        qualities = group[quality_col]

        # Compute median interval for the final-segment end time
        if len(timestamps) > 1:
            diffs = timestamps.diff().dropna()
            median_interval = diffs.median()
        else:
            median_interval = pd.Timedelta("1min")

        # Build runs via change detection
        n = len(group)
        run_starts = [0]
        for i in range(1, n):
            if qualities.iloc[i] != qualities.iloc[i - 1]:
                run_starts.append(i)
        run_starts.append(n)  # sentinel

        for j in range(len(run_starts) - 1):
            s_idx = run_starts[j]
            e_idx = run_starts[j + 1]
            start_ts = timestamps.iloc[s_idx]
            quality = qualities.iloc[s_idx]

            if e_idx < n:
                end_ts = timestamps.iloc[e_idx]
            else:
                end_ts = timestamps.iloc[-1] + median_interval

            duration_s = (end_ts - start_ts).total_seconds()
            segments.append(
                {
                    "tag_name": tag,
                    "quality": quality,
                    "start": start_ts,
                    "end": end_ts,
                    "duration_seconds": duration_s,
                }
            )

    result = pd.DataFrame(segments)
    if "_tag" in work.columns and tag_col is None:
        result["tag_name"] = result["tag_name"].replace("default", "default")
    return result
