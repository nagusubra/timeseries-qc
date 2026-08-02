"""Run-length encoding for quality segments.

Converts a row-per-observation DataFrame into a segment-per-run DataFrame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_MAX_SEGMENTS = 10_000


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
            tag_name, quality, start, end, duration_seconds, n_rows
            (+ "reasons" if reasons_col is provided and present in df)

        *end* of a segment is the start of the next segment, or
        last_timestamp + median_interval for the final segment of each tag.
    """
    _has_reasons = reasons_col is not None and reasons_col in df.columns
    _cols = ["tag_name", "quality", "start", "end", "duration_seconds", "n_rows"]
    if _has_reasons:
        _cols.append("reasons")

    if df.empty:
        return pd.DataFrame(columns=_cols)

    if tag_col is None or tag_col not in df.columns:
        work = df.copy()
        work["_tag"] = "default"
        _tc = "_tag"
    else:
        work = df
        _tc = tag_col

    segments: list[dict] = []

    for tag, group in work.groupby(_tc, sort=False):
        group = group.sort_values(time_col)
        timestamps = group[time_col].to_numpy()
        qualities = group[quality_col].to_numpy(dtype=object)

        # Compute median interval for the final-segment end time
        if len(timestamps) > 1:
            diffs = pd.Series(timestamps).diff().dropna()
            median_interval = diffs.median()
        else:
            median_interval = pd.Timedelta("1min")

        n = len(group)
        # Vectorised run-boundary detection
        if n == 0:
            continue
        change = np.empty(n, dtype=bool)
        change[0] = True
        change[1:] = qualities[1:] != qualities[:-1]
        run_starts = np.flatnonzero(change)
        run_starts = np.append(run_starts, n)  # sentinel

        reasons_arr = (
            group[reasons_col].to_numpy(dtype=object) if _has_reasons else None
        )

        for j in range(len(run_starts) - 1):
            s_idx = int(run_starts[j])
            e_idx = int(run_starts[j + 1])
            start_ts = timestamps[s_idx]
            quality = qualities[s_idx]

            if e_idx < n:
                end_ts = timestamps[e_idx]
            else:
                end_ts = timestamps[-1] + median_interval

            duration_s = (end_ts - start_ts) / np.timedelta64(1, "s")
            if isinstance(duration_s, (pd.Timedelta, np.timedelta64)):
                duration_s = pd.Timedelta(duration_s).total_seconds()
            else:
                duration_s = float(duration_s)

            seg: dict = {
                "tag_name": tag,
                "quality": quality,
                "start": start_ts,
                "end": end_ts,
                "duration_seconds": duration_s,
                "n_rows": e_idx - s_idx,
            }

            if _has_reasons and reasons_arr is not None:
                unique_reasons: set[str] = set()
                for r in reasons_arr[s_idx:e_idx]:
                    if r and isinstance(r, str) and r.strip():
                        for token in r.split("|"):
                            token = token.strip()
                            if token:
                                unique_reasons.add(token)
                seg["reasons"] = ", ".join(sorted(unique_reasons))

            segments.append(seg)

    result = pd.DataFrame(segments)
    if not result.empty and len(result) > _MAX_SEGMENTS:
        result = _coalesce_tiny_segments(result, max_segments=_MAX_SEGMENTS)
    return result


def _coalesce_tiny_segments(
    segments: pd.DataFrame,
    max_segments: int = _MAX_SEGMENTS,
    min_seconds: float = 1.0,
) -> pd.DataFrame:
    """Merge sub-second same-tag/same-quality runs until under *max_segments*."""
    if len(segments) <= max_segments:
        return segments

    rows = segments.to_dict("records")
    changed = True
    while len(rows) > max_segments and changed:
        changed = False
        merged: list[dict] = []
        i = 0
        while i < len(rows):
            cur = rows[i]
            if (
                i + 1 < len(rows)
                and cur["duration_seconds"] < min_seconds
                and rows[i + 1]["tag_name"] == cur["tag_name"]
                and rows[i + 1]["quality"] == cur["quality"]
            ):
                nxt = rows[i + 1]
                cur = {
                    **cur,
                    "end": nxt["end"],
                    "duration_seconds": cur["duration_seconds"] + nxt["duration_seconds"],
                    "n_rows": cur.get("n_rows", 0) + nxt.get("n_rows", 0),
                }
                if "reasons" in cur or "reasons" in nxt:
                    left = set(cur.get("reasons", "").split(", ")) - {""}
                    right = set(nxt.get("reasons", "").split(", ")) - {""}
                    cur["reasons"] = ", ".join(sorted(left | right))
                merged.append(cur)
                i += 2
                changed = True
            else:
                merged.append(cur)
                i += 1
        rows = merged
        if not changed:
            break
    return pd.DataFrame(rows)
