"""Timestamp health checker — detects gaps, duplicates, non-monotonic,
freq_drift, and DST-ambiguous timestamps."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from tsqc.result import QCResult

_EMPTY_COLS = ["tag_name", "issue_type", "timestamp", "description", "severity"]


def _empty_issues() -> pd.DataFrame:
    return pd.DataFrame(columns=_EMPTY_COLS)


def _infer_freq(ts: pd.Series) -> pd.Timedelta | None:
    """Auto-infer the expected frequency from a timestamp Series using the mode diff."""
    if len(ts) < 3:
        return None
    diffs = ts.sort_values().diff().dropna()
    if diffs.empty:
        return None
    mode_vals = diffs.mode()
    if mode_vals.empty:
        return None
    return mode_vals.iloc[0]


def _check_single_tag(
    tag: str,
    ts: pd.Series,
    expected_freq: pd.Timedelta | None,
    freq_tolerance: float,
    dst_ambiguous_set: set,
) -> list[dict]:
    issues: list[dict] = []

    # --- Non-monotonic (check in original order, before sorting) ---
    ts_original = ts.reset_index(drop=True)
    for i in range(1, len(ts_original)):
        if pd.notna(ts_original.iloc[i]) and pd.notna(ts_original.iloc[i - 1]):
            if ts_original.iloc[i] < ts_original.iloc[i - 1]:
                issues.append(
                    {
                        "tag_name": tag,
                        "issue_type": "non_monotonic",
                        "timestamp": ts_original.iloc[i],
                        "description": (
                            f"Non-monotonic: {ts_original.iloc[i]} < preceding "
                            f"{ts_original.iloc[i - 1]}"
                        ),
                        "severity": "error",
                    }
                )

    # Sort for the remaining checks
    ts_sorted = ts.sort_values().reset_index(drop=True)

    # --- Infer freq ---
    eff_freq = expected_freq if expected_freq is not None else _infer_freq(ts_sorted)

    # --- Duplicates ---
    dup_mask = ts_sorted.duplicated(keep=False)
    for idx in ts_sorted[dup_mask].unique():
        issues.append(
            {
                "tag_name": tag,
                "issue_type": "duplicate",
                "timestamp": idx,
                "description": f"Duplicate timestamp: {idx}",
                "severity": "error",
            }
        )

    # Remove duplicates for subsequent checks
    ts_unique = ts_sorted.drop_duplicates().reset_index(drop=True)

    # --- Gaps ---
    if eff_freq is not None and len(ts_unique) > 1:
        gap_threshold = 2 * eff_freq
        diffs = ts_unique.diff().dropna()
        for i, diff in enumerate(diffs):
            if diff > gap_threshold:
                gap_start = ts_unique.iloc[i]
                gap_end = ts_unique.iloc[i + 1]
                duration = diff
                severity = "error" if duration >= pd.Timedelta("1h") else "warning"
                issues.append(
                    {
                        "tag_name": tag,
                        "issue_type": "gap",
                        "timestamp": gap_start,
                        "description": (
                            f"Gap of {duration} between {gap_start} and {gap_end} "
                            f"(expected ≤ {gap_threshold})"
                        ),
                        "severity": severity,
                    }
                )

    # --- Freq drift ---
    if eff_freq is not None and len(ts_unique) > 10:
        window_size = max(5, len(ts_unique) // 10)
        diffs = ts_unique.diff().dropna().reset_index(drop=True)
        for start_i in range(0, len(diffs) - window_size, window_size):
            window = diffs.iloc[start_i : start_i + window_size]
            median_diff = window.median()
            if pd.notna(median_diff) and eff_freq.total_seconds() > 0:
                deviation = abs((median_diff - eff_freq) / eff_freq)
                if deviation > freq_tolerance:
                    issues.append(
                        {
                            "tag_name": tag,
                            "issue_type": "freq_drift",
                            "timestamp": ts_unique.iloc[start_i + 1],
                            "description": (
                                f"Freq drift: median interval {median_diff} "
                                f"deviates {deviation:.1%} from expected {eff_freq}"
                            ),
                            "severity": "warning",
                        }
                    )

    # --- DST ambiguous (from QCResult metadata) ---
    for ambig_ts in dst_ambiguous_set:
        issues.append(
            {
                "tag_name": tag,
                "issue_type": "dst_ambiguous",
                "timestamp": ambig_ts,
                "description": (
                    f"Timestamp {ambig_ts} was ambiguous during DST localization "
                    "(fall-back fold or spring-forward gap); set to NaT in output."
                ),
                "severity": "warning",
            }
        )

    return issues


def check_timestamps(
    result: "QCResult",
    expected_freq: str | None = None,
    freq_tolerance: float = 0.1,
) -> pd.DataFrame:
    """Detect timestamp anomalies in a QCResult.

    Args:
        result: A QCResult from tsqc.check().
        expected_freq: Expected frequency as a pandas offset string (e.g. "1min").
                       None = auto-infer per tag.
        freq_tolerance: Fraction of expected_freq before flagging drift. Default 0.1.

    Returns:
        DataFrame with columns: tag_name, issue_type, timestamp, description, severity.
        Returns empty DataFrame (never None) when no issues found.
    """
    df = result.df
    time_col = result.time_col
    tag_col = result.tag_col

    if df.empty:
        return _empty_issues()

    parsed_freq: pd.Timedelta | None = None
    if expected_freq is not None:
        parsed_freq = pd.tseries.frequencies.to_offset(expected_freq).nanos * 1e-9
        parsed_freq = pd.Timedelta(expected_freq)

    # DST ambiguous timestamps (stored as wall-clock pre-localization)
    dst_set: set = set(result.ambiguous_timestamps)

    all_issues: list[dict] = []

    if tag_col is not None and tag_col in df.columns:
        for tag, group in df.groupby(tag_col):
            ts = group[time_col]
            issues = _check_single_tag(
                tag=str(tag),
                ts=ts,
                expected_freq=parsed_freq,
                freq_tolerance=freq_tolerance,
                dst_ambiguous_set=dst_set,
            )
            all_issues.extend(issues)
    else:
        issues = _check_single_tag(
            tag="default",
            ts=df[time_col],
            expected_freq=parsed_freq,
            freq_tolerance=freq_tolerance,
            dst_ambiguous_set=dst_set,
        )
        all_issues.extend(issues)

    if not all_issues:
        return _empty_issues()

    return pd.DataFrame(all_issues, columns=_EMPTY_COLS)
