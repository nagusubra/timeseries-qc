"""Built-in QC rule implementations."""

from __future__ import annotations

from typing import Callable

import numpy as np
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

        # Fill NaN temporarily so rolling std doesn't propagate NaN further.
        # Intentional: ffill/bfill bridges NaN gaps so a sensor that returns to
        # the same value after a null stretch can still be scored as flat across
        # that gap. Changing this would alter output — keep for compatibility.
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
        vals = flagged.to_numpy(dtype=bool, copy=True)
        idx = flagged.index  # monotonic DatetimeIndex

        padded = np.concatenate([[False], vals, [False]])
        edges = np.diff(padded.astype(np.int8))
        starts = np.flatnonzero(edges == 1)
        ends = np.flatnonzero(edges == -1)  # exclusive
        for s, e in zip(starts, ends):
            if idx[e - 1] - idx[s] < min_dur:
                vals[s:e] = False

        return pd.Series(vals, index=idx)

    def __repr__(self) -> str:
        parts = [
            f"window={self.window!r}",
            f"min_delta={self.min_delta}",
        ]
        if self.min_duration is not None:
            parts.append(f"min_duration={self.min_duration!r}")
        parts.append(f"level={self.level!r}")
        return f"FlatlineRule({', '.join(parts)})"

    def get_reason(self, series: pd.Series, idx: int) -> str:
        """Return reason string with the flatline value included.

        Format: "flatline @ <value>" with 4 decimal places.
        Handles special values: nan, inf, -inf.
        """
        return self._format_flatline_value(series.iloc[idx])

    def get_reasons_vectorized(self, series: pd.Series, mask: np.ndarray) -> np.ndarray:
        """Vectorised flatline reasons for flagged rows."""
        out = np.full(len(series), "", dtype=object)
        if not mask.any():
            return out
        vals = series.to_numpy(copy=False)
        out[mask] = [self._format_flatline_value(v) for v in vals[mask]]
        return out

    @staticmethod
    def _format_flatline_value(value) -> str:
        if pd.isna(value):
            return "flatline @ nan"
        if value == float("inf"):
            return "flatline @ inf"
        if value == float("-inf"):
            return "flatline @ -inf"
        return f"flatline @ {value:.4f}"


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

        flagged = np.zeros(len(series), dtype=bool)
        if self.max_delta is not None:
            flagged |= (diff > self.max_delta).fillna(False).to_numpy(dtype=bool)
        if self.min_delta is not None:
            # NaN (first row) comparison returns False, so first row is safe
            flagged |= (diff < self.min_delta).fillna(False).to_numpy(dtype=bool)

        flagged &= not_nan.to_numpy(dtype=bool)
        return pd.Series(flagged, index=series.index)

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
        not_nan = series.notna().to_numpy(dtype=bool)
        flagged = np.zeros(len(series), dtype=bool)

        if self.min_val is not None:
            flagged |= (series < self.min_val).fillna(False).to_numpy(dtype=bool)
        if self.max_val is not None:
            flagged |= (series > self.max_val).fillna(False).to_numpy(dtype=bool)

        return pd.Series(flagged & not_nan, index=series.index)

    def __repr__(self) -> str:
        return (
            f"RangeRule(min_val={self.min_val}, max_val={self.max_val}, "
            f"level={self.level!r})"
        )


class OutlierRule(Rule):
    """Flag rows that are statistical outliers using Z-score, IQR, or MAD methods.

    Supports both global (full-series) and rolling (time-windowed) computation
    modes. NaN values are excluded from statistics and never flagged (NullRule
    handles them).

    Default level: "sus"

    Parameters:
        method:
            - "zscore": (value - mean) / std. Classic method; assumes normality.
            - "mad": 0.6745 * (value - median) / MAD. Robust variant, less
              sensitive to outliers in the baseline statistics.
            - "iqr": value outside [Q1 - k*IQR, Q3 + k*IQR]. Distribution-free.
        threshold: Sensitivity threshold.
            - For "zscore" / "mad": |score| > threshold is flagged. Default 3.0.
            - For "iqr": multiplier k. Default 1.5 (Tukey's fences).
        window: pandas offset alias (e.g. "24h", "7d") or None.
            If set, statistics are computed over a rolling window of this size.
            Requires a monotonic DatetimeIndex. None = global mode.
            Default None.
        min_periods: Minimum non-NaN observations needed in the (rolling) window
            to compute statistics. Below this, the row is not flagged. Default 10.
        level: "sus" or "bad". Default "sus".
    """

    def __init__(
        self,
        method: str = "zscore",
        threshold: float | None = None,
        window: str | None = None,
        min_periods: int = 10,
        level: str = "sus",
    ) -> None:
        super().__init__(level=level)
        if method not in ("zscore", "mad", "iqr"):
            raise ValueError(
                f"method must be one of 'zscore', 'mad', 'iqr', got {method!r}."
            )
        self.method = method

        if threshold is None:
            self.threshold = 3.0 if method in ("zscore", "mad") else 1.5
        else:
            self.threshold = threshold

        self.window = window
        self.min_periods = min_periods

    @property
    def name(self) -> str:
        return f"outlier-{self.method}"

    def check(self, series: pd.Series) -> pd.Series:
        not_nan = series.notna()
        valid = series[not_nan]

        if len(valid) < self.min_periods:
            return pd.Series(False, index=series.index)

        if self.window is not None:
            flagged_valid = self._check_rolling(valid)
        else:
            flagged_valid = self._check_global(valid)

        result = pd.Series(False, index=series.index)
        result.loc[flagged_valid.index] = flagged_valid
        return result & not_nan

    def _check_global(self, valid: pd.Series) -> pd.Series:
        if self.method == "zscore":
            mean, std = valid.mean(), valid.std()
            if std == 0 or pd.isna(std):
                return pd.Series(False, index=valid.index)
            scores = (valid - mean) / std
            return scores.abs() > self.threshold

        elif self.method == "mad":
            median = valid.median()
            mad = (valid - median).abs().median()
            if mad == 0:
                return pd.Series(False, index=valid.index)
            scores = 0.6745 * (valid - median) / mad
            return scores.abs() > self.threshold

        elif self.method == "iqr":
            q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - self.threshold * iqr
            upper = q3 + self.threshold * iqr
            return (valid < lower) | (valid > upper)

    def _check_rolling(self, valid: pd.Series) -> pd.Series:
        roller = valid.rolling(self.window, min_periods=self.min_periods)
        if self.method == "zscore":
            mean = roller.mean()
            std = roller.std()
            scores = (valid - mean) / std.replace(0, float("nan"))
            return scores.abs() > self.threshold

        elif self.method == "mad":
            median = roller.median()
            abs_dev = (valid - median).abs()
            # Second rolling pass needed for MAD of absolute deviations
            mad = abs_dev.rolling(self.window, min_periods=self.min_periods).median()
            scores = 0.6745 * (valid - median) / mad.replace(0, float("nan"))
            return scores.abs() > self.threshold

        elif self.method == "iqr":
            # Reuse one Rolling object; quantile still requires two kernel passes
            q1 = roller.quantile(0.25)
            q3 = roller.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - self.threshold * iqr
            upper = q3 + self.threshold * iqr
            return (valid < lower) | (valid > upper)

    def __repr__(self) -> str:
        parts = [
            f"method={self.method!r}",
            f"threshold={self.threshold}",
        ]
        if self.window is not None:
            parts.append(f"window={self.window!r}")
        parts.append(f"min_periods={self.min_periods}")
        parts.append(f"level={self.level!r}")
        return f"OutlierRule({', '.join(parts)})"


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
