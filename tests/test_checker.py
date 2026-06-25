"""End-to-end tests for tsqc.check() (tsqc/checker.py)."""

import numpy as np
import pandas as pd
import pytest

import tsqc
from tsqc.rules.builtins import CustomRule, NullRule, RangeRule


def _utc_df(n=50, tag="SENSOR_A", with_nan=True, with_spike=True):
    ts = pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC")
    rng = np.random.default_rng(0)
    vals = 10.0 + rng.normal(0, 0.5, n)
    if with_nan:
        vals[5] = float("nan")
    if with_spike:
        vals[20] = 999.0
    df = pd.DataFrame({"timestamp": ts, "tag_name": tag, "value": vals})
    return df


# ─────────────────────────────  Basic  ─────────────────────────────────────

class TestCheckBasic:
    def test_returns_qcresult(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        assert isinstance(result, tsqc.QCResult)

    def test_output_has_quality_columns(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        assert "quality" in result.df.columns
        assert "quality_reasons" in result.df.columns

    def test_quality_values_valid(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        assert set(result.df["quality"].unique()).issubset({"good", "sus", "bad"})

    def test_does_not_modify_original(self, single_tag_df):
        original_cols = list(single_tag_df.columns)
        tsqc.check(single_tag_df)
        assert list(single_tag_df.columns) == original_cols

    def test_row_count_preserved(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        assert len(result.df) == len(single_tag_df)


# ─────────────────────────────  Multi-tag  ─────────────────────────────────

class TestCheckMultiTag:
    def test_multi_tag_all_tags_present(self, multi_tag_df):
        result = tsqc.check(multi_tag_df)
        assert set(result.df["tag_name"].unique()) == {"TAG_A", "TAG_B", "TAG_C"}

    def test_multi_tag_quality_column_populated(self, multi_tag_df):
        result = tsqc.check(multi_tag_df)
        assert result.df["quality"].notna().all()


# ─────────────────────────────  quality_reasons  ───────────────────────────

class TestQualityReasons:
    def test_null_reason_set(self):
        df = _utc_df(with_nan=True, with_spike=False)
        result = tsqc.check(df, rules=[NullRule()])
        nan_row = result.df[result.df["value"].isna()]
        assert "null values" in nan_row["quality_reasons"].iloc[0]

    def test_pipe_delimited_multiple_reasons(self):
        df = _utc_df(with_nan=True, with_spike=False)
        rules = [
            NullRule(level="bad"),
            CustomRule(fn=lambda s: s.isna(), name="also_null", level="sus"),
        ]
        result = tsqc.check(df, rules=rules)
        nan_row = result.df[result.df["value"].isna()]
        reasons = nan_row["quality_reasons"].iloc[0]
        assert "|" in reasons
        assert "null values" in reasons
        assert "also_null" in reasons

    def test_good_rows_have_empty_reasons(self):
        df = _utc_df(with_nan=False, with_spike=False, n=10)
        result = tsqc.check(df, rules=[NullRule()])
        assert (result.df["quality_reasons"] == "").all()


# ─────────────────────────────  Custom rules  ──────────────────────────────

class TestCheckCustomRules:
    def test_custom_rule_list_applied(self):
        df = _utc_df(with_nan=False, with_spike=True)
        rules = [RangeRule(min_val=0.0, max_val=100.0, level="bad")]
        result = tsqc.check(df, rules=rules)
        bad_rows = result.df[result.df["quality"] == "bad"]
        # Spike at value=999 should be flagged
        assert len(bad_rows) >= 1


# ─────────────────────────────  Error handling  ────────────────────────────

class TestCheckErrors:
    def test_missing_value_column_raises(self):
        df = pd.DataFrame(
            {"timestamp": pd.date_range("2026-01-01", periods=3, freq="1min", tz="UTC")}
        )
        with pytest.raises(ValueError, match="value"):
            tsqc.check(df)

    def test_missing_timestamp_column_raises(self):
        df = pd.DataFrame({"value": [1.0, 2.0]})
        with pytest.raises(ValueError, match="timestamp"):
            tsqc.check(df)

    def test_tz_naive_without_assume_tz_raises(self):
        ts = pd.date_range("2026-01-01", periods=5, freq="1min")  # tz-naive
        df = pd.DataFrame(
            {"timestamp": ts, "tag_name": "T", "value": [1.0] * 5}
        )
        with pytest.raises(ValueError, match="assume_tz"):
            tsqc.check(df)

    def test_tz_naive_with_assume_tz_utc_succeeds(self):
        ts = pd.date_range("2026-01-01", periods=5, freq="1min")  # tz-naive
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 5})
        result = tsqc.check(df, assume_tz="UTC")
        assert result.df["timestamp"].dt.tz is not None
        assert str(result.df["timestamp"].dt.tz) == "UTC"

    def test_invalid_assume_tz_raises(self):
        ts = pd.date_range("2026-01-01", periods=3, freq="1min")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 3})
        with pytest.raises(ValueError, match="IANA"):
            tsqc.check(df, assume_tz="NotATimezone/Bogus")

    def test_tz_aware_preserves_display_timezone(self):
        ts = pd.date_range("2026-01-01", periods=5, freq="1min", tz="America/Chicago")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 5})
        result = tsqc.check(df)
        assert str(result.df["timestamp"].dt.tz) == "America/Chicago"
        assert result.display_tz == "America/Chicago"

    def test_display_tz_property(self):
        ts = pd.date_range("2026-01-01", periods=5, freq="1min")  # tz-naive
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 5})
        result = tsqc.check(df, assume_tz="America/Edmonton")
        assert result.display_tz == "America/Edmonton"
        assert str(result.df["timestamp"].dt.tz) == "America/Edmonton"

    def test_assume_tz_non_utc_keeps_local_timestamps(self):
        """Timestamps in result.df are in assume_tz, not UTC."""
        ts = pd.date_range("2026-01-01", periods=5, freq="1min")  # tz-naive
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 5})
        result = tsqc.check(df, assume_tz="America/Edmonton")
        # The displayed timestamps should show local wall-clock time
        display_ts = result.df["timestamp"]
        assert display_ts.dt.tz is not None
        assert str(display_ts.dt.tz) == "America/Edmonton"
        # The hour should match the original naive input (local time)
        assert display_ts.iloc[0].hour == 0  # midnight local


# ─────────────────────────────  No tag column  ─────────────────────────────

class TestCheckNoTagCol:
    def test_single_tag_no_tag_col(self):
        ts = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "value": list(range(10))})
        result = tsqc.check(df, tag_col=None)
        assert "quality" in result.df.columns

    def test_summary_with_no_tag_col(self):
        ts = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "value": list(range(10))})
        result = tsqc.check(df, tag_col=None)
        summary = result.summary()
        assert "tag_name" in summary.columns
        assert len(summary) == 1


# ─────────────────────────────  summary()  ─────────────────────────────────

class TestSummary:
    def test_summary_columns(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        summary = result.summary()
        expected_cols = {"tag_name", "total_rows", "pct_good", "pct_sus", "pct_bad",
                         "n_good", "n_sus", "n_bad"}
        assert expected_cols.issubset(set(summary.columns))

    def test_summary_pcts_sum_to_100(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        summary = result.summary()
        for _, row in summary.iterrows():
            total = row["pct_good"] + row["pct_sus"] + row["pct_bad"]
            assert abs(total - 100.0) < 0.5, f"Percentages don't sum to 100 for {row['tag_name']}"

    def test_summary_sorted_by_pct_bad(self, multi_tag_df):
        result = tsqc.check(multi_tag_df)
        summary = result.summary()
        pct_bad_values = list(summary["pct_bad"])
        assert pct_bad_values == sorted(pct_bad_values, reverse=True)
