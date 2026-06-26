"""Built-in QC rule implementations."""

from __future__ import annotations

from typing import Callable

import pandas as pd

from tsqc.rules.base import Rule


class NullRule(Rule):
    """Flag rows where value is NaN, None, or pd.NA.

    Default level: "bad"
    """

    name = "null values"

    def __init__(self, level: str = "bad") -> None:
        super().__init__(level=level)

    def check(self, series: pd.Series) -> pd.Series:
        return series.isna()


class FlatlineRule(Rule):
    """Flag rows where the value has not changed by more than min_delta
    within the preceding *window* time window.

    An optional *min_duration* filter suppresses flags for flat runs
    that are shorter than the given duration — useful when short-lived
    flat periods are normal (e.g. pump starts, cloud edges).

    Default level: "sus"

    Parameters:
        window: pandas offset alias, e.g. "1h", "30min".
        min_delta: minimum required change to NOT be flagged. Default 0.0.
        min_duration: minimum duration a continuous flat run must last
            before rows are flagged. pandas offset string or None.
            None = no filter (current behaviour). Example: "30min", "2h".
    """

    name = "flatline"

    def __init__(
        self,
        window: str = "1h",
        min_delta: float = 0.0,
        min_duration: str | None = None,
        level: str = "sus",
    ) -> None:
        super().__init__(level=level)
        self.window = window
        self.min_delta = min_delta
        self.min_duration = min_duration

    def check(self, series: pd.Series) -> pd.Series:
        # NaN rows must NOT be flagged — NullRule handles them.
        # rolling().std() requires a DatetimeIndex with the window offset.
        not_nan = series.notna()

        # Fill NaN temporarily so rolling std doesn't propagate NaN further
        filled = series.ffill().bfill()

        # rolling std over a time-based window; min_periods=2 so we need ≥2 pts
        rolling_std = filled.rolling(window=self.window, min_periods=2).std()

        # Flag where std is at or below min_delta (i.e. flat)
        flagged = rolling_std <= self.min_delta

        # Only flag non-NaN rows
        flagged = flagged & not_nan

        # Optional: suppress short flatline runs
        if self.min_duration is not None:
            flagged = self._filter_short_flatlines(flagged)

        return flagged

    def _filter_short_flatlines(self, flagged: pd.Series) -> pd.Series:
        """Remove flagged runs whose total time span < min_duration."""
        min_dur = pd.Timedelta(self.min_duration)
        result = flagged.copy()
        vals = flagged.to_numpy()
        idx = flagged.index  # monotonic DatetimeIndex

        i = 0
        n = len(vals)
        while i < n:
            if not vals[i]:
                i += 1
                continue
            # Start of a flagged run
            run_start = i
            while i < n and vals[i]:
                i += 1
            run_end = i - 1
            span = idx[run_end] - idx[run_start]
            if span < min_dur:
                result.iloc[run_start : i] = False

        return result

    def __repr__(self) -> str:
        parts = [
            f"window={self.window!r}",
            f"min_delta={self.min_delta}",
        ]
        if self.min_duration is not None:
            parts.append(f"min_duration={self.min_duration!r}")
        parts.append(f"level={self.level!r}")
        return f"FlatlineRule({', '.join(parts)})"


class DeltaRule(Rule):
    """Flag rows based on the absolute change from the previous reading.

    Supports two independent thresholds:
        - *max_delta*: flags when the absolute change is **too large**
          (sensor spike / step change).
        - *min_delta*: flags when the absolute change is **too small**
          (stuck / frozen sensor).

    At least one of *min_delta* or *max_delta* must be provided.
    Default level: "sus"

    Parameters:
        min_delta: minimum required absolute change. Changes below this
            are flagged. None = no lower bound.
        max_delta: maximum allowed absolute change. Changes above this
            are flagged. None = no upper bound.
    """

    name = "delta"

    def __init__(
        self,
        min_delta: float | None = None,
        max_delta: float | None = None,
        level: str = "sus",
    ) -> None:
        super().__init__(level=level)
        if min_delta is None and max_delta is None:
            raise ValueError(
                "At least one of min_delta or max_delta is required."
            )
        self.min_delta = min_delta
        self.max_delta = max_delta

    def check(self, series: pd.Series) -> pd.Series:
        # First row always False (no previous row)
        # NaN rows: return False — NullRule handles them
        diff = series.diff().abs()
        not_nan = series.notna()

        flagged = pd.Series(False, index=series.index, dtype=bool)

        if self.max_delta is not None:
            flagged = flagged | (diff > self.max_delta)
        if self.min_delta is not None:
            # NaN (first row) comparison returns False, so first row is safe
            flagged = flagged | (diff < self.min_delta)

        # Mask out rows where the value itself is NaN
        flagged = flagged & not_nan
        return flagged.fillna(False)

    def __repr__(self) -> str:
        parts = []
        if self.min_delta is not None:
            parts.append(f"min_delta={self.min_delta}")
        if self.max_delta is not None:
            parts.append(f"max_delta={self.max_delta}")
        parts.append(f"level={self.level!r}")
        return f"DeltaRule({', '.join(parts)})"


class RangeRule(Rule):
    """Flag rows where value is outside [min_val, max_val].

    Either bound can be None (open interval).
    Default level: "bad"

    Parameters:
        min_val: lower bound (inclusive). None = no lower bound.
        max_val: upper bound (inclusive). None = no upper bound.
    """

    name = "range"

    def __init__(
        self,
        min_val: float | None = None,
        max_val: float | None = None,
        level: str = "bad",
    ) -> None:
        super().__init__(level=level)
        self.min_val = min_val
        self.max_val = max_val

    def check(self, series: pd.Series) -> pd.Series:
        # NaN rows: return False — NullRule handles them
        not_nan = series.notna()
        flagged = pd.Series(False, index=series.index)

        if self.min_val is not None:
            flagged = flagged | (series < self.min_val)
        if self.max_val is not None:
            flagged = flagged | (series > self.max_val)

        return flagged & not_nan

    def __repr__(self) -> str:
        return (
            f"RangeRule(min_val={self.min_val}, max_val={self.max_val}, "
            f"level={self.level!r})"
        )


class CustomRule(Rule):
    """Wrap an arbitrary user-supplied callable as a QC rule.

    Parameters:
        fn: callable that accepts pd.Series and returns a boolean pd.Series.
        name: label shown in quality_reasons column. Default "custom".
        level: "sus" or "bad". Default "sus".
    """

    def __init__(
        self,
        fn: Callable[[pd.Series], pd.Series],
        name: str = "custom",
        level: str = "sus",
    ) -> None:
        super().__init__(level=level)
        self.fn = fn
        self.name = name

    def check(self, series: pd.Series) -> pd.Series:
        result = self.fn(series)
        return result.fillna(False)

    def __repr__(self) -> str:
        return f"CustomRule(name={self.name!r}, level={self.level!r})"
