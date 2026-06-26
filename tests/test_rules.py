"""Unit tests for individual QC rules (tsqc/rules/builtins.py)."""

import numpy as np
import pandas as pd
import pytest

from tsqc.rules.builtins import CustomRule, DeltaRule, FlatlineRule, NullRule, RangeRule


def _make_series(values, freq="1min", tz="UTC"):
    idx = pd.date_range("2026-01-01", periods=len(values), freq=freq, tz=tz)
    return pd.Series(values, index=idx, dtype=float)


# ─────────────────────────────  NullRule  ──────────────────────────────────

class TestNullRule:
    def test_flags_nan_rows(self):
        s = _make_series([1.0, float("nan"), 3.0, None])
        result = NullRule().check(s)
        assert result.iloc[0] is False or result.iloc[0] == False
        assert result.iloc[1] == True
        assert result.iloc[3] == True

    def test_does_not_flag_valid_rows(self):
        s = _make_series([1.0, 2.0, 3.0])
        result = NullRule().check(s)
        assert result.sum() == 0

    def test_default_level_is_bad(self):
        assert NullRule().level == "bad"

    def test_all_nan_series(self):
        s = _make_series([float("nan")] * 5)
        result = NullRule().check(s)
        assert result.all()

    def test_level_sus_accepted(self):
        rule = NullRule(level="sus")
        assert rule.level == "sus"

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="level must be"):
            NullRule(level="unknown")


# ────────────────────────────  FlatlineRule  ───────────────────────────────

class TestFlatlineRule:
    def test_flags_constant_window(self):
        # 10 identical values should trigger flatline after the window fills
        s = _make_series([42.0] * 10 + [43.0, 44.0, 45.0])
        rule = FlatlineRule(window="5min", min_delta=0.0)
        flagged = rule.check(s)
        # At least some of the constant block should be flagged
        assert flagged.iloc[4:10].any(), "Expected flatline flags in constant block"

    def test_does_not_flag_varying_rows(self):
        s = _make_series([float(i) for i in range(60)])
        rule = FlatlineRule(window="10min", min_delta=0.0)
        flagged = rule.check(s)
        assert flagged.sum() == 0

    def test_does_not_flag_nan_rows(self):
        values = [float("nan")] * 10
        s = _make_series(values)
        rule = FlatlineRule(window="5min", min_delta=0.0)
        flagged = rule.check(s)
        assert flagged.sum() == 0, "FlatlineRule must not flag NaN rows"

    def test_default_level_is_sus(self):
        assert FlatlineRule().level == "sus"

    def test_min_delta_suppresses_small_variation(self):
        # Vary by only 0.001 — below min_delta of 0.5, should still flag
        s = _make_series([42.0 + 0.0001 * i for i in range(20)])
        rule = FlatlineRule(window="10min", min_delta=0.5)
        flagged = rule.check(s)
        assert flagged.iloc[5:].any()

    def test_min_delta_allows_sufficient_variation(self):
        # Vary by 1.0 per step — above min_delta of 0.5
        s = _make_series([float(i) for i in range(20)])
        rule = FlatlineRule(window="5min", min_delta=0.5)
        flagged = rule.check(s)
        assert flagged.sum() == 0

    # ── min_duration ────────────────────────────────────────────────────

    def test_min_duration_suppresses_short_flatline(self):
        # 10 min of flat data at 1-min freq; min_duration=30min → should suppress
        s = _make_series([42.0] * 10 + [float(i) for i in range(50)], freq="1min")
        rule = FlatlineRule(window="5min", min_delta=0.0, min_duration="30min")
        flagged = rule.check(s)
        assert flagged.sum() == 0, "Short flat run should be suppressed"

    def test_min_duration_allows_long_flatline(self):
        # 35 min of flat data at 1-min freq; min_duration=30min → should flag
        s = _make_series([42.0] * 35 + [float(i) for i in range(25)], freq="1min")
        rule = FlatlineRule(window="5min", min_delta=0.0, min_duration="30min")
        flagged = rule.check(s)
        assert flagged.iloc[30:35].any(), "Long flat run should survive filter"

    def test_min_duration_does_not_affect_varying_data(self):
        s = _make_series([float(i) for i in range(60)], freq="1min")
        rule = FlatlineRule(window="10min", min_delta=0.0, min_duration="30min")
        flagged = rule.check(s)
        assert flagged.sum() == 0

    def test_min_duration_none_is_noop(self):
        # Same as default behaviour — no filtering
        s = _make_series([42.0] * 10 + [float(i) for i in range(50)], freq="1min")
        rule = FlatlineRule(window="5min", min_delta=0.0, min_duration=None)
        flagged = rule.check(s)
        assert flagged.iloc[4:10].any(), "None min_duration should not filter"


# ─────────────────────────────  DeltaRule  ─────────────────────────────────

class TestDeltaRule:
    # ── max_delta (replaces old `threshold`) ────────────────────────────

    def test_max_delta_flags_spike(self):
        values = [1.0] * 10 + [500.0] + [1.0] * 10
        s = _make_series(values)
        rule = DeltaRule(max_delta=100.0)
        flagged = rule.check(s)
        # Row at index 10 (the spike) and row 11 (return) should be flagged
        assert flagged.iloc[10] == True

    def test_max_delta_does_not_flag_gradual_changes(self):
        s = _make_series([float(i) for i in range(20)])
        rule = DeltaRule(max_delta=5.0)
        flagged = rule.check(s)
        assert flagged.sum() == 0

    def test_first_row_not_flagged_max_delta(self):
        s = _make_series([1000.0, 1.0, 1.0])
        rule = DeltaRule(max_delta=0.5)
        flagged = rule.check(s)
        assert flagged.iloc[0] == False

    # ── min_delta (new — flags too-small changes) ───────────────────────

    def test_min_delta_flags_stuck_sensor(self):
        # Three identical readings — change of 0.0 is below min_delta
        s = _make_series([42.0, 42.0, 42.0, 50.0])
        rule = DeltaRule(min_delta=1.0)
        flagged = rule.check(s)
        # Row 1 and 2 have zero change — should be flagged
        assert flagged.iloc[1] == True
        assert flagged.iloc[2] == True

    def test_min_delta_first_row_not_flagged(self):
        s = _make_series([1000.0, 1000.0, 1000.0])
        rule = DeltaRule(min_delta=0.5)
        flagged = rule.check(s)
        assert flagged.iloc[0] == False, "First row must never be flagged"

    def test_min_delta_does_not_flag_nan_rows(self):
        values = [1.0, float("nan"), 2.0]
        s = _make_series(values)
        rule = DeltaRule(min_delta=0.5)
        flagged = rule.check(s)
        assert flagged.iloc[1] == False

    # ── both bounds ─────────────────────────────────────────────────────

    def test_both_bounds_independent(self):
        """min_delta and max_delta work independently — flag both edges."""
        values = [1.0, 1.0, 50.0, 500.0, 501.0]
        s = _make_series(values)
        rule = DeltaRule(min_delta=1.0, max_delta=100.0)
        flagged = rule.check(s)
        # Row 1: diff=0   → flagged by min (change too small)
        # Row 2: diff=49  → not flagged (1 <= 49 <= 100)
        # Row 3: diff=450 → flagged by max (change too large)
        # Row 4: diff=1   → not flagged (1 <= 1 <= 100) ... actually 1 < 1 is False, 1 == 1 is not < 1, so not flagged by min
        #                   and 1 <= 100, so not flagged by max
        assert flagged.iloc[1] == True, "zero change flagged by min_delta"
        assert flagged.iloc[2] == False, "moderate change not flagged"
        assert flagged.iloc[3] == True, "large change flagged by max_delta"
        assert flagged.iloc[4] == False, "return change within bounds"

    def test_min_and_max_both_none_raises(self):
        with pytest.raises(ValueError, match="At least one of min_delta or max_delta"):
            DeltaRule()

    def test_only_min_delta_works(self):
        s = _make_series([1.0, 1.0, 100.0])
        rule = DeltaRule(min_delta=0.1)
        flagged = rule.check(s)
        assert flagged.iloc[1] == True
        assert flagged.iloc[2] == False  # large change is irrelevant without max_delta

    def test_only_max_delta_works(self):
        s = _make_series([1.0, 1.0, 500.0])
        rule = DeltaRule(max_delta=100.0)
        flagged = rule.check(s)
        assert flagged.iloc[1] == False  # zero change is irrelevant without min_delta
        assert flagged.iloc[2] == True

    # ── shared ──────────────────────────────────────────────────────────

    def test_default_level_is_sus(self):
        assert DeltaRule(max_delta=10.0).level == "sus"

    def test_does_not_flag_nan_rows(self):
        values = [1.0, float("nan"), 3.0]
        s = _make_series(values)
        rule = DeltaRule(max_delta=0.5)
        flagged = rule.check(s)
        assert flagged.iloc[1] == False


# ─────────────────────────────  RangeRule  ─────────────────────────────────

class TestRangeRule:
    def test_flags_below_min(self):
        s = _make_series([-1.0, 0.0, 10.0])
        rule = RangeRule(min_val=0.0)
        flagged = rule.check(s)
        assert flagged.iloc[0] == True
        assert flagged.iloc[1] == False

    def test_flags_above_max(self):
        s = _make_series([10.0, 50.0, 200.0])
        rule = RangeRule(max_val=100.0)
        flagged = rule.check(s)
        assert flagged.iloc[2] == True
        assert flagged.iloc[0] == False

    def test_does_not_flag_in_range(self):
        s = _make_series([10.0, 50.0, 90.0])
        rule = RangeRule(min_val=0.0, max_val=100.0)
        flagged = rule.check(s)
        assert flagged.sum() == 0

    def test_open_upper_bound(self):
        s = _make_series([1.0, 1_000_000.0])
        rule = RangeRule(min_val=0.0)  # no max
        flagged = rule.check(s)
        assert flagged.sum() == 0

    def test_does_not_flag_nan(self):
        s = _make_series([float("nan"), -999.0])
        rule = RangeRule(min_val=0.0, max_val=100.0)
        flagged = rule.check(s)
        assert flagged.iloc[0] == False

    def test_default_level_is_bad(self):
        assert RangeRule(min_val=0.0, max_val=100.0).level == "bad"


# ───────────────────────────  CustomRule  ──────────────────────────────────

class TestCustomRule:
    def test_custom_fn_applied(self):
        s = _make_series([1.0, 2.0, 99.0, 4.0])

        def my_fn(series):
            return series > 50

        rule = CustomRule(fn=my_fn, name="high_value", level="sus")
        flagged = rule.check(s)
        assert flagged.iloc[2] == True
        assert flagged.sum() == 1

    def test_name_stored(self):
        rule = CustomRule(fn=lambda s: s > 0, name="positive_check")
        assert rule.name == "positive_check"

    def test_default_level_is_sus(self):
        rule = CustomRule(fn=lambda s: s > 0)
        assert rule.level == "sus"


# ─────────────────────────  Precedence  ────────────────────────────────────

class TestQualityPrecedence:
    """bad > sus > good when multiple rules fire."""

    def test_bad_beats_sus(self):
        """A row flagged by both a 'sus' and a 'bad' rule should be 'bad'."""
        import tsqc

        values = [float("nan")]  # NullRule(bad) fires; if we add a sus rule it stays bad
        ts = pd.date_range("2026-01-01", periods=1, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": values})

        from tsqc.rules.builtins import CustomRule, NullRule

        rules = [
            NullRule(level="bad"),
            CustomRule(fn=lambda s: s.isna(), name="also_bad", level="sus"),
        ]
        result = tsqc.check(df, rules=rules)
        assert result.df["quality"].iloc[0] == "bad"
        assert "null values" in result.df["quality_reasons"].iloc[0]
        assert "also_bad" in result.df["quality_reasons"].iloc[0]
