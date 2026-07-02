"""Core check() function — applies QC rules to a timeseries DataFrame."""

from __future__ import annotations

import warnings as _warnings
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


def _validate_quality_map(quality_map: dict) -> None:
    """Raise ValueError if any quality_map value is not good/sus/bad."""
    valid = {"good", "sus", "bad"}
    for key, val in quality_map.items():
        if val not in valid:
            raise ValueError(
                f"quality_map value {val!r} is invalid. "
                f"Must be one of {sorted(valid)}."
            )


def _apply_external_quality_map(
    ext_raw: pd.Series,
    quality_map: dict,
) -> tuple[pd.Series, pd.Series]:
    """Map external quality values to good/sus/bad levels with reasons.

    Returns:
        quality: str Series ('good'/'sus'/'bad')
        reasons: str Series with "external_quality: <raw_value>" for non-good rows
    """
    mapped = ext_raw.map(quality_map).fillna("bad")

    raw_vals = ext_raw.to_numpy()
    levels = mapped.to_numpy()
    reasons_list: list[str] = []
    for i, level in enumerate(levels):
        if level != "good":
            reasons_list.append(f"external_quality_value: {raw_vals[i]}")
        else:
            reasons_list.append("")

    return (
        pd.Series(levels, index=ext_raw.index, dtype=str),
        pd.Series(reasons_list, index=ext_raw.index, dtype=str),
    )


def _merge_external_internal(
    internal_q: pd.Series,
    internal_r: pd.Series,
    external_q: pd.Series,
    external_r: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """Merge external quality with internal rules using worst-wins logic.

    bad > sus > good — the worse level across both sources wins.
    When external is worse, its reason is appended (pipe-delimited) to
    the existing internal reason string.
    """
    level_order = {"good": 0, "sus": 1, "bad": 2}

    merged_q = internal_q.copy()
    merged_r = internal_r.copy()

    for i in range(len(external_q)):
        ext_level = external_q.iloc[i]
        int_level = internal_q.iloc[i]

        ext_val = level_order.get(ext_level, 2)
        int_val = level_order.get(int_level, 0)

        if ext_val > int_val:
            merged_q.iloc[i] = ext_level
            ext_reason = external_r.iloc[i]
            if ext_reason:
                int_reason = internal_r.iloc[i]
                if int_reason:
                    merged_r.iloc[i] = f"{int_reason}|{ext_reason}"
                else:
                    merged_r.iloc[i] = ext_reason

    return merged_q, merged_r


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
    external_quality_col: str | None = None,
    quality_mode: str = "combined",
    quality_map: dict | None = None,
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
        external_quality_col: Name of a column in *df* that contains pre-existing
            quality codes from a historian / SCADA system (e.g. 0=good, 1=sus, 2=bad).
            None = feature disabled. Requires *quality_map* (dict or YAML) to define
            how raw values map to good/sus/bad.
        quality_mode: One of "exclusive", "combined", "none". Ignored when
            *external_quality_col* is None.
            - "exclusive" — use the external column **only**; skip all internal rules.
            - "combined" — merge external + internal with worst-wins (bad > sus > good).
            - "none" — ignore the external column; pure internal rules only.
            Default "combined" when *external_quality_col* is provided.
        quality_map: Dict mapping raw external quality values to tsqc levels, e.g.
            {0: "good", 1: "sus", 2: "bad", 3: "bad", 4: "bad"}. Alternative to
            defining the map in a YAML rules file. YAML takes precedence if both given.

    Returns:
        QCResult wrapping the annotated DataFrame.

    Raises:
        ValueError: Missing columns, unparseable timestamps, tz-naive without assume_tz,
                    invalid assume_tz, missing YAML file, missing quality_map when required,
                    invalid quality_mode or quality_map values.
    """
    from tsqc.result import QCResult  # avoid circular import

    # --- Validate external_quality_col & quality_mode ---
    _VALID_QUALITY_MODES = {"exclusive", "combined", "none"}
    if external_quality_col is not None:
        if external_quality_col not in df.columns:
            raise ValueError(
                f"Column {external_quality_col!r} (external_quality_col) not found "
                f"in DataFrame. Available columns: {list(df.columns)}"
            )
        if quality_mode not in _VALID_QUALITY_MODES:
            raise ValueError(
                f"quality_mode must be one of {sorted(_VALID_QUALITY_MODES)}, "
                f"got {quality_mode!r}."
            )

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

    # --- Resolve quality_map (YAML takes precedence over param) ---
    resolved_quality_map: dict | None = None
    if yaml_rules is not None and yaml_rules.get("quality_map"):
        resolved_quality_map = yaml_rules["quality_map"]
    elif quality_map is not None:
        resolved_quality_map = quality_map
    if external_quality_col is not None and quality_mode != "none" and resolved_quality_map is None:
        raise ValueError(
            f"external_quality_col={external_quality_col!r} requires a quality_map "
            f"when quality_mode={quality_mode!r}. "
            "Provide one via YAML rules file or the quality_map= parameter."
        )
    if resolved_quality_map is not None:
        _validate_quality_map(resolved_quality_map)

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

    # Determine whether to run internal rules and/or external quality
    run_internal = quality_mode != "exclusive"
    run_external = (
        external_quality_col is not None
        and quality_mode != "none"
        and resolved_quality_map is not None
    )

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

        # --- Internal rules ---
        if run_internal:
            if yaml_rules is not None:
                from tsqc.config.yaml_parser import get_rules_for_tag

                tag_rules = get_rules_for_tag(yaml_rules, tag)
                if not tag_rules:
                    tag_rules = _build_default_rules(tag_series)
            elif rules is not None:
                tag_rules = list(rules)
            else:
                tag_rules = _build_default_rules(tag_series)

            internal_q, internal_r = _apply_rules_to_tag(tag_series, tag_rules)
        else:
            internal_q = internal_r = None

        # --- External quality ---
        if run_external:
            ext_vals = valid_df_indexed[external_quality_col]
            external_q, external_r = _apply_external_quality_map(ext_vals, resolved_quality_map)  # type: ignore[arg-type]
        else:
            external_q = external_r = None

        # --- Combine ---
        if external_q is not None and internal_q is not None:
            # combined mode
            q, r = _merge_external_internal(internal_q, internal_r, external_q, external_r)  # type: ignore[arg-type]
        elif external_q is not None:
            # exclusive mode
            q, r = external_q, external_r  # type: ignore[union-attr]
        else:
            # internal-only mode
            q, r = internal_q, internal_r  # type: ignore[union-attr]

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

    # --- Handle column conflict: use temp names for output if needed ---
    _output_qc = quality_col
    _output_rc = reasons_col
    if external_quality_col is not None and quality_col == external_quality_col:
        _output_qc = f"_{quality_col}_qc_temp"
        _output_rc = f"_{reasons_col}_qc_temp"

    out[_output_qc] = pd.concat(quality_parts)
    out[_output_rc] = pd.concat(reasons_parts)

    # Drop internal tag column if we added it
    if _tag_col == "_tag_internal":
        out = out.drop(columns=["_tag_internal"])

    # --- Auto-rename output quality columns if they conflict with input ---
    if _output_qc != quality_col:
        new_qc = f"qc_{quality_col}"
        new_rc = f"qc_{reasons_col}"
        _warnings.warn(
            f"Input column {external_quality_col!r} conflicts with output column "
            f"{quality_col!r}. Renaming output to {new_qc!r} / {new_rc!r}.",
            UserWarning,
            stacklevel=2,
        )
        out = out.rename(columns={_output_qc: new_qc, _output_rc: new_rc})
        quality_col = new_qc
        reasons_col = new_rc

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
