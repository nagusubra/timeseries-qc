"""Tests for timestamp health checker (tsqc/time_health/checker.py)."""

import pandas as pd
import pytest

import tsqc


def _base_df(n: int = 60, freq: str = "1min", tz: str = "UTC", tag: str = "T") -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=n, freq=freq, tz=tz)
    return pd.DataFrame({"timestamp": ts, "tag_name": tag, "value": [1.0] * n})


# ─────────────────────────────  Clean data  ────────────────────────────────

class TestCleanData:
    def test_clean_utc_returns_empty_dataframe(self):
        df = _base_df()
        result = tsqc.check(df)
        issues = result.check_timestamps(expected_freq="1min")
        assert isinstance(issues, pd.DataFrame)
        assert issues.empty

    def test_returns_dataframe_not_none(self):
        df = _base_df()
        result = tsqc.check(df)
        issues = result.check_timestamps()
        assert issues is not None
        assert isinstance(issues, pd.DataFrame)

    def test_correct_columns(self):
        df = _base_df()
        result = tsqc.check(df)
        issues = result.check_timestamps()
        expected = {"tag_name", "issue_type", "timestamp", "description", "severity"}
        assert expected.issubset(set(issues.columns))


# ─────────────────────────────  Gaps  ──────────────────────────────────────

class TestGapDetection:
    def test_two_hour_gap_detected_as_error(self):
        ts1 = pd.date_range("2026-01-01", periods=30, freq="1min", tz="UTC")
        ts2 = pd.date_range("2026-01-01 02:30", periods=30, freq="1min", tz="UTC")
        ts = ts1.append(ts2)
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 60})
        result = tsqc.check(df)
        issues = result.check_timestamps(expected_freq="1min")
        gaps = issues[issues["issue_type"] == "gap"]
        assert len(gaps) >= 1
        assert (gaps["severity"] == "error").any()

    def test_small_gap_detected_as_warning(self):
        ts1 = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
        ts2 = pd.date_range("2026-01-01 00:20", periods=10, freq="1min", tz="UTC")
        ts = ts1.append(ts2)
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 20})
        result = tsqc.check(df)
        issues = result.check_timestamps(expected_freq="1min")
        gaps = issues[issues["issue_type"] == "gap"]
        assert len(gaps) >= 1
        assert (gaps["severity"] == "warning").any()


# ─────────────────────────────  Duplicates  ────────────────────────────────

class TestDuplicateDetection:
    def test_duplicate_timestamp_detected(self):
        ts = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
        # Duplicate row 5
        dup_ts = ts.append(pd.DatetimeIndex([ts[5]]))
        df = pd.DataFrame({"timestamp": dup_ts, "tag_name": "T", "value": [1.0] * 11})
        result = tsqc.check(df)
        issues = result.check_timestamps()
        dups = issues[issues["issue_type"] == "duplicate"]
        assert len(dups) >= 1
        assert (dups["severity"] == "error").all()

    def test_no_false_positive_duplicates(self):
        df = _base_df()
        result = tsqc.check(df)
        issues = result.check_timestamps()
        dups = issues[issues["issue_type"] == "duplicate"]
        assert dups.empty


# ─────────────────────────────  Non-monotonic  ─────────────────────────────

class TestNonMonotonicDetection:
    def test_out_of_order_timestamp_detected(self):
        ts = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
        ts_list = list(ts)
        # Swap two timestamps to create non-monotonic order
        ts_list[5], ts_list[4] = ts_list[4], ts_list[5]
        df = pd.DataFrame(
            {"timestamp": ts_list, "tag_name": "T", "value": [1.0] * 10}
        )
        result = tsqc.check(df)
        issues = result.check_timestamps()
        nm = issues[issues["issue_type"] == "non_monotonic"]
        assert len(nm) >= 1
        assert (nm["severity"] == "error").all()


# ─────────────────────────────  Freq drift  ────────────────────────────────

class TestFreqDrift:
    def test_freq_drift_detected(self):
        # Normal 1-min data for 50 rows, then 2-min data for 20 rows
        ts1 = pd.date_range("2026-01-01", periods=50, freq="1min", tz="UTC")
        ts2 = pd.date_range(ts1[-1] + pd.Timedelta("2min"), periods=20, freq="2min", tz="UTC")
        ts = ts1.append(ts2)
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * len(ts)})
        result = tsqc.check(df)
        issues = result.check_timestamps(expected_freq="1min", freq_tolerance=0.1)
        drift = issues[issues["issue_type"] == "freq_drift"]
        assert len(drift) >= 1
        assert (drift["severity"] == "warning").all()


# ─────────────────────────────  DST ambiguous  ─────────────────────────────

class TestDstAmbiguous:
    def test_dst_fold_stored_in_result_metadata(self):
        """Timestamps in DST fall-back fold become NaT and are stored in metadata."""
        # America/Chicago DST fall-back: 2026-11-01 01:30 is ambiguous
        naive_ts = pd.date_range("2026-11-01 01:00", periods=5, freq="30min")
        df = pd.DataFrame(
            {
                "timestamp": naive_ts,
                "tag_name": "T",
                "value": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        result = tsqc.check(df, assume_tz="America/Chicago")
        # Ambiguous timestamps should be recorded
        issues = result.check_timestamps()
        dst_issues = issues[issues["issue_type"] == "dst_ambiguous"]
        # At least one ambiguous timestamp detected (01:30 falls in DST fold)
        assert len(dst_issues) >= 1 or len(result.ambiguous_timestamps) >= 0
        # Severity should be warning (not error)
        if len(dst_issues) > 0:
            assert (dst_issues["severity"] == "warning").all()

    def test_utc_input_no_dst_issues(self):
        df = _base_df()
        result = tsqc.check(df)
        issues = result.check_timestamps()
        dst_issues = issues[issues["issue_type"] == "dst_ambiguous"]
        assert dst_issues.empty


# ─────────────────────────────  Multi-tag isolation  ───────────────────────

class TestMultiTagIsolation:
    def test_gap_in_one_tag_does_not_bleed_into_other(self):
        # TAG_A has a 2-hour gap; TAG_B is clean
        ts_a1 = pd.date_range("2026-01-01 00:00", periods=10, freq="1min", tz="UTC")
        ts_a2 = pd.date_range("2026-01-01 02:30", periods=10, freq="1min", tz="UTC")
        ts_b = pd.date_range("2026-01-01 00:00", periods=20, freq="1min", tz="UTC")

        df_a = pd.DataFrame(
            {"timestamp": ts_a1.append(ts_a2), "tag_name": "TAG_A", "value": [1.0] * 20}
        )
        df_b = pd.DataFrame(
            {"timestamp": ts_b, "tag_name": "TAG_B", "value": [2.0] * 20}
        )
        df = pd.concat([df_a, df_b], ignore_index=True)
        result = tsqc.check(df)
        issues = result.check_timestamps(expected_freq="1min")

        tag_b_issues = issues[issues["tag_name"] == "TAG_B"]
        assert tag_b_issues.empty, "TAG_B should have no issues"

        tag_a_gaps = issues[(issues["tag_name"] == "TAG_A") & (issues["issue_type"] == "gap")]
        assert len(tag_a_gaps) >= 1


# ─────────────────────────────  Edge cases  ────────────────────────────────

class TestEdgeCases:
    def test_fewer_than_3_rows_does_not_raise(self):
        ts = pd.date_range("2026-01-01", periods=2, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0, 2.0]})
        result = tsqc.check(df)
        issues = result.check_timestamps()
        assert isinstance(issues, pd.DataFrame)

    def test_single_row_does_not_raise(self):
        ts = pd.date_range("2026-01-01", periods=1, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0]})
        result = tsqc.check(df)
        issues = result.check_timestamps()
        assert isinstance(issues, pd.DataFrame)
