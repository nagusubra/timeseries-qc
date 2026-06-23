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
    reasons_col: str | None = None,
) -> pd.DataFrame:
    """Convert a row-per-observation DataFrame into a segment-per-run DataFrame.

    A "run" is a maximal sequence of consecutive rows for the same tag
    with the same quality label.

    Args:
        df: Annotated DataFrame with timestamp, tag_name, and quality columns.
        time_col: Name of the timestamp column.
        tag_col: Name of the tag column. None = treat entire df as one tag.
        quality_col: Name of the quality column.
        reasons_col: Name of the column containing pipe-delimited rule names
            (e.g. "quality_reasons"). If provided, each segment will include
            a "reasons" column with the union of all distinct rule names.

    Returns:
        DataFrame with columns:
            tag_name, quality, start, end, duration_seconds
            (+ "reasons" if reasons_col is provided and present in df)

        *end* of a segment is the start of the next segment, or
        last_timestamp + median_interval for the final segment of each tag.
    """
    _has_reasons = reasons_col is not None and reasons_col in df.columns
    _cols = ["tag_name", "quality", "start", "end", "duration_seconds"]
    if _has_reasons:
        _cols.append("reasons")

    if df.empty:
        return pd.DataFrame(columns=_cols)

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

            seg: dict = {
                "tag_name": tag,
                "quality": quality,
                "start": start_ts,
                "end": end_ts,
                "duration_seconds": duration_s,
            }

            if _has_reasons:
                segment_reasons = group[reasons_col].iloc[s_idx:e_idx]
                unique_reasons: set[str] = set()
                for r in segment_reasons:
                    if r and isinstance(r, str) and r.strip():
                        for token in r.split("|"):
                            token = token.strip()
                            if token:
                                unique_reasons.add(token)
                seg["reasons"] = ", ".join(sorted(unique_reasons))

            segments.append(seg)

    result = pd.DataFrame(segments)
    if "_tag" in work.columns and tag_col is None:
        result["tag_name"] = result["tag_name"].replace("default", "default")
    return result
