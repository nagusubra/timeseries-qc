"""Core check() function — applies QC rules to a timeseries DataFrame."""

from __future__ import annotations

import zoneinfo
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from tsqc.rules.base import Rule
from tsqc.rules.builtins import DeltaRule, FlatlineRule, NullRule

if TYPE_CHECKING:
    from tsqc.result import QCResult

# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

_VALID_LEVELS = {"sus", "bad"}
_LEVEL_ORDER = {"good": 0, "sus": 1, "bad": 2}


def _validate_iana_tz(tz_name: str) -> None:
    """Raise ValueError if tz_name is not a recognised IANA timezone."""
    try:
        zoneinfo.ZoneInfo(tz_name)
    except (zoneinfo.ZoneInfoNotFoundError, KeyError):
        raise ValueError(
            f"{tz_name!r} is not a valid IANA timezone name. "
            "Examples: 'UTC', 'America/Chicago', 'Europe/London'."
        )


def _normalize_timestamps(
    col: pd.Series,
    time_col: str,
    assume_tz: str | None,
) -> tuple[pd.Series, list[pd.Timestamp], str]:
    """Convert timestamps to UTC; return (utc_series, dst_ambiguous_timestamps, display_tz).

    *display_tz* is the timezone the user's data is in — either the *assume_tz*
    value for naive input, or the original timezone of tz-aware input.
    """
    import warnings as _warnings

    ambiguous_ts: list[pd.Timestamp] = []

    # Try to parse strings → datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(col):
        col = pd.to_datetime(col, utc=False)

    # Check tz-awareness
    if col.dt.tz is None:
        # Tz-naive
        if assume_tz is None:
            raise ValueError(
                f"Column {time_col!r} has no timezone info. "
                "Pass assume_tz='UTC' if your data is UTC, "
                "or assume_tz='America/Chicago' for local time."
            )
        _validate_iana_tz(assume_tz)
        display_tz = assume_tz

        # First attempt — strict (raises on ambiguous/nonexistent)
        try:
            col = col.dt.tz_localize(assume_tz, ambiguous="raise", nonexistent="raise")
        except Exception:
            # Second pass — lenient (NaT for problem rows); record which were NaT
            col_nat = col.dt.tz_localize(assume_tz, ambiguous="NaT", nonexistent="NaT")
            nat_mask = col_nat.isna() & col.notna()
            ambiguous_ts = list(col[nat_mask])
            col = col_nat

        col = col.dt.tz_convert("UTC")
    else:
        # Already tz-aware
        display_tz = str(col.dt.tz)
        if assume_tz is not None and assume_tz != display_tz:
            _warnings.warn(
                f"assume_tz={assume_tz!r} ignored because timestamps already have "
                f"timezone {display_tz!r}. Using the existing timezone.",
                UserWarning,
                stacklevel=3,
            )
        col = col.dt.tz_convert("UTC")

    return col, ambiguous_ts, display_tz


def _build_default_rules(series: pd.Series) -> list[Rule]:
    """Build the default rule set for a single-tag series (3-sigma delta)."""
    std = series.std()
    max_delta = 3 * std if pd.notna(std) and std > 0 else float("inf")
    return [
        NullRule(level="bad"),
        FlatlineRule(window="1h", min_delta=0.0, level="sus"),
        DeltaRule(max_delta=max_delta, level="sus"),
    ]


def _apply_rules_to_tag(
    tag_series: pd.Series,
    rules: list[Rule],
) -> tuple[pd.Series, pd.Series]:
    """Apply rules to a single tag's value series.

    Returns:
        quality: str Series ('good'/'sus'/'bad')
        reasons: str Series with pipe-delimited triggered rule names
        Both Series carry the same index as tag_series.

    Uses vectorised numpy operations so performance scales to hundreds of
    thousands of rows without Python-loop overhead.
    """
    n = len(tag_series)
    quality = np.full(n, "good", dtype=object)
    reasons: list[str] = [""] * n

    for rule in rules:
        flagged_np = rule.check(tag_series).to_numpy().astype(bool)
        flagged_positions = flagged_np.nonzero()[0]
        if len(flagged_positions) == 0:
            continue

        # Append rule name to reasons for each flagged row
        for pos in flagged_positions:
            reasons[pos] = f"{reasons[pos]}|{rule.name}" if reasons[pos] else rule.name

        # Update quality level (bad > sus > good)
        if rule.level == "bad":
            quality[flagged_np] = "bad"
        elif rule.level == "sus":
            quality[flagged_np & (quality == "good")] = "sus"

    return (
        pd.Series(quality.tolist(), index=tag_series.index, dtype=str),
        pd.Series(reasons, index=tag_series.index, dtype=str),
    )


# --------------------------------------------------------------------------- #
#  Public check() function
# --------------------------------------------------------------------------- #


def check(
    df: pd.DataFrame,
    *,
    time_col: str = "timestamp",
    tag_col: str | None = "tag_name",
    value_col: str = "value",
    rules: list[Rule] | str | None = None,
    quality_col: str = "quality",
    reasons_col: str = "quality_reasons",
    assume_tz: str | None = None,
) -> "QCResult":
    """Run quality checks on a timeseries DataFrame.

    Args:
        df: Input DataFrame with timestamp, tag_name, and value columns.
        time_col: Name of the timestamp column. Default "timestamp".
        tag_col: Name of the tag column. None = single-tag mode ("default").
        value_col: Name of the value column. Default "value".
        rules: List of Rule objects, path to a YAML file, or None for defaults.
        quality_col: Output column name for quality label. Default "quality".
        reasons_col: Output column name for triggered rule names. Default "quality_reasons".
        assume_tz: IANA timezone name for tz-naive input. Required if timestamps have no tz.

    Returns:
        QCResult wrapping the annotated DataFrame.

    Raises:
        ValueError: Missing columns, unparseable timestamps, tz-naive without assume_tz,
                    invalid assume_tz, missing YAML file.
    """
    from tsqc.result import QCResult  # avoid circular import

    # --- Validate required columns ---
    required = [time_col, value_col]
    if tag_col is not None:
        required.append(tag_col)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required column(s) not found in DataFrame: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # --- Resolve rules argument ---
    if isinstance(rules, str):
        from tsqc.config.yaml_parser import parse_yaml_rules

        parsed = parse_yaml_rules(rules)
        # Store for later use per-tag; rules stays as the parsed dict
        yaml_rules = parsed
        rules = None  # sentinel: use yaml_rules per tag
    else:
        yaml_rules = None

    # --- Work on a copy ---
    out = df.copy()

    # --- Normalize timestamps ---
    ts_col, ambiguous_ts, display_tz = _normalize_timestamps(out[time_col], time_col, assume_tz)
    out[time_col] = ts_col

    # --- Determine tags ---
    if tag_col is None or tag_col not in out.columns:
        out = out.copy()
        out["_tag_internal"] = "default"
        _tag_col = "_tag_internal"
    else:
        _tag_col = tag_col

    tags = out[_tag_col].unique()

    quality_parts = []
    reasons_parts = []

    for tag in tags:
        mask = out[_tag_col] == tag
        tag_df = out.loc[mask].copy()
        original_idx = tag_df.index

        # Sort by time and drop NaT rows before rules processing.
        # NaT rows (from DST ambiguity) are "bad" by default; rolling requires
        # a monotonic, NaT-free DatetimeIndex.
        tag_df_sorted = tag_df.sort_values(time_col)
        nat_time_mask = tag_df_sorted[time_col].isna()
        valid_df = tag_df_sorted[~nat_time_mask]
        nat_df = tag_df_sorted[nat_time_mask]

        valid_idx = valid_df.index
        valid_df_indexed = valid_df.set_index(time_col)
        tag_series = valid_df_indexed[value_col].astype(float)

        # Resolve rules for this tag
        if yaml_rules is not None:
            from tsqc.config.yaml_parser import get_rules_for_tag

            tag_rules = get_rules_for_tag(yaml_rules, tag)
            if not tag_rules:
                tag_rules = _build_default_rules(tag_series)
        elif rules is not None:
            tag_rules = list(rules)
        else:
            tag_rules = _build_default_rules(tag_series)

        q, r = _apply_rules_to_tag(tag_series, tag_rules)
        q.index = valid_idx
        r.index = valid_idx

        # NaT-timestamped rows are always "bad" (NullRule implicit)
        if not nat_df.empty:
            nat_q = pd.Series("bad", index=nat_df.index, dtype=str, name=quality_col)
            nat_r = pd.Series("null values", index=nat_df.index, dtype=str, name=reasons_col)
            q = pd.concat([q, nat_q])
            r = pd.concat([r, nat_r])

        # Restore original (unsorted) order
        q = q.reindex(original_idx)
        r = r.reindex(original_idx)

        quality_parts.append(q.rename(quality_col))
        reasons_parts.append(r.rename(reasons_col))

    quality_all = pd.concat(quality_parts)
    reasons_all = pd.concat(reasons_parts)

    out[quality_col] = quality_all
    out[reasons_col] = reasons_all

    # Drop internal tag column if we added it
    if _tag_col == "_tag_internal":
        out = out.drop(columns=["_tag_internal"])

    # Convert timestamps back to the display timezone so the user sees
    # their original local timestamps in result.df, plot(), etc.
    out[time_col] = out[time_col].dt.tz_convert(display_tz)

    return QCResult(
        df=out,
        time_col=time_col,
        tag_col=tag_col,
        value_col=value_col,
        quality_col=quality_col,
        reasons_col=reasons_col,
        ambiguous_timestamps=ambiguous_ts,
        display_tz=display_tz,
    )
