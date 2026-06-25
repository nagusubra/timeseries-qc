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

    Default level: "sus"

    Parameters:
        window: pandas offset alias, e.g. "1h", "30min".
        min_delta: minimum required change to NOT be flagged. Default 0.0.
    """

    name = "flatline"

    def __init__(
        self,
        window: str = "1h",
        min_delta: float = 0.0,
        level: str = "sus",
    ) -> None:
        super().__init__(level=level)
        self.window = window
        self.min_delta = min_delta

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
        return flagged & not_nan

    def __repr__(self) -> str:
        return (
            f"FlatlineRule(window={self.window!r}, "
            f"min_delta={self.min_delta}, level={self.level!r})"
        )


class DeltaRule(Rule):
    """Flag rows where the absolute change from the previous row exceeds threshold.

    Useful for detecting sensor spikes or step changes.
    Default level: "sus"

    Parameters:
        threshold: maximum allowed absolute change between consecutive readings.
    """

    name = "delta"

    def __init__(self, threshold: float, level: str = "sus") -> None:
        super().__init__(level=level)
        self.threshold = threshold

    def check(self, series: pd.Series) -> pd.Series:
        # First row always False (no previous row)
        # NaN rows: return False — NullRule handles them
        diff = series.diff().abs()
        flagged = diff > self.threshold
        # Mask out rows where the value itself is NaN
        flagged = flagged & series.notna()
        return flagged.fillna(False)

    def __repr__(self) -> str:
        return f"DeltaRule(threshold={self.threshold}, level={self.level!r})"


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
