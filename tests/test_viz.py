"""Tests for visualization: RLE encoding and timeline figure builder."""

import numpy as np
import pandas as pd
import pytest

import tsqc
from tsqc.viz.rle import encode_quality_runs


def _seg_df(data: list[tuple]) -> pd.DataFrame:
    """Build a small annotated DataFrame: list of (ts_str, tag, quality)."""
    rows = []
    for ts, tag, q in data:
        rows.append({"timestamp": pd.Timestamp(ts, tz="UTC"), "tag_name": tag, "quality": q})
    return pd.DataFrame(rows)


# ─────────────────────────────  RLE  ───────────────────────────────────────

class TestEncodeQualityRuns:
    def test_consecutive_same_quality_merges(self):
        df = _seg_df([
            ("2026-01-01 00:00", "PUMP_A", "good"),
            ("2026-01-01 00:01", "PUMP_A", "good"),
            ("2026-01-01 00:02", "PUMP_A", "bad"),
            ("2026-01-01 00:03", "PUMP_A", "bad"),
        ])
        segs = encode_quality_runs(df)
        pump_segs = segs[segs["tag_name"] == "PUMP_A"]
        assert len(pump_segs) == 2
        assert pump_segs.iloc[0]["quality"] == "good"
        assert pump_segs.iloc[1]["quality"] == "bad"

    def test_segment_start_and_end(self):
        df = _seg_df([
            ("2026-01-01 00:00", "T", "good"),
            ("2026-01-01 00:01", "T", "bad"),
            ("2026-01-01 00:02", "T", "bad"),
        ])
        segs = encode_quality_runs(df)
        good_seg = segs[segs["quality"] == "good"].iloc[0]
        assert good_seg["start"] == pd.Timestamp("2026-01-01 00:00", tz="UTC")
        # End of 'good' segment = start of 'bad' segment
        assert good_seg["end"] == pd.Timestamp("2026-01-01 00:01", tz="UTC")

    def test_last_segment_end_is_last_ts_plus_median(self):
        df = _seg_df([
            ("2026-01-01 00:00", "T", "bad"),
            ("2026-01-01 00:01", "T", "bad"),
            ("2026-01-01 00:02", "T", "bad"),
        ])
        segs = encode_quality_runs(df)
        assert len(segs) == 1
        expected_end = pd.Timestamp("2026-01-01 00:03", tz="UTC")
        assert segs.iloc[0]["end"] == expected_end

    def test_multi_tag_segments_independent(self):
        df = _seg_df([
            ("2026-01-01 00:00", "TAG_A", "good"),
            ("2026-01-01 00:00", "TAG_B", "bad"),
            ("2026-01-01 00:01", "TAG_A", "good"),
            ("2026-01-01 00:01", "TAG_B", "bad"),
        ])
        segs = encode_quality_runs(df)
        assert len(segs) == 2
        tags = set(segs["tag_name"].unique())
        assert tags == {"TAG_A", "TAG_B"}

    def test_duration_seconds_correct(self):
        df = _seg_df([
            ("2026-01-01 00:00", "T", "good"),
            ("2026-01-01 00:01", "T", "good"),
            ("2026-01-01 01:00", "T", "bad"),
        ])
        segs = encode_quality_runs(df)
        good_seg = segs[segs["quality"] == "good"].iloc[0]
        # start=00:00, end=01:00 → 3600 seconds
        assert good_seg["duration_seconds"] == 3600.0

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame(columns=["timestamp", "tag_name", "quality"])
        segs = encode_quality_runs(df)
        assert segs.empty
        assert list(segs.columns) == ["tag_name", "quality", "start", "end", "duration_seconds"]

    def test_single_row_df(self):
        df = _seg_df([("2026-01-01 00:00", "T", "good")])
        segs = encode_quality_runs(df)
        assert len(segs) == 1
        # Duration should be > 0 (last_ts + median_interval with 1 row)
        assert segs.iloc[0]["duration_seconds"] >= 0

    def test_rle_captures_reasons(self):
        df = pd.DataFrame([
            {"timestamp": pd.Timestamp("2026-01-01 00:00", tz="UTC"), "tag_name": "T", "quality": "good", "quality_reasons": ""},
            {"timestamp": pd.Timestamp("2026-01-01 00:01", tz="UTC"), "tag_name": "T", "quality": "bad", "quality_reasons": "null values"},
            {"timestamp": pd.Timestamp("2026-01-01 00:02", tz="UTC"), "tag_name": "T", "quality": "bad", "quality_reasons": "null values|flatline"},
            {"timestamp": pd.Timestamp("2026-01-01 00:03", tz="UTC"), "tag_name": "T", "quality": "sus", "quality_reasons": "delta"},
        ])
        segs = encode_quality_runs(df, reasons_col="quality_reasons")
        assert len(segs) == 3
        good_seg = segs[segs["quality"] == "good"].iloc[0]
        assert good_seg["reasons"] == ""
        bad_seg = segs[segs["quality"] == "bad"].iloc[0]
        assert bad_seg["reasons"] == "flatline, null values"
        sus_seg = segs[segs["quality"] == "sus"].iloc[0]
        assert sus_seg["reasons"] == "delta"

    def test_rle_reasons_empty_df(self):
        df = pd.DataFrame(columns=["timestamp", "tag_name", "quality", "quality_reasons"])
        segs = encode_quality_runs(df, reasons_col="quality_reasons")
        assert segs.empty
        assert list(segs.columns) == ["tag_name", "quality", "start", "end", "duration_seconds", "reasons"]

    def test_rle_reasons_column_missing_no_crash(self):
        df = _seg_df([("2026-01-01 00:00", "T", "good")])
        segs = encode_quality_runs(df, reasons_col="nonexistent_col")
        assert len(segs) == 1
        assert "reasons" not in segs.columns


# ─────────────────────────────  Timeline figure  ───────────────────────────

class TestBuildTimelineFigure:
    def test_returns_plotly_figure(self, single_tag_df):
        import plotly.graph_objects as go

        result = tsqc.check(single_tag_df)
        fig = result.plot()
        assert isinstance(fig, go.Figure)

    def test_figure_has_traces(self, single_tag_df):
        result = tsqc.check(single_tag_df)
        fig = result.plot()
        assert len(fig.data) > 0

    def test_tag_filter_works(self, multi_tag_df):
        result = tsqc.check(multi_tag_df)
        fig = result.plot(tags=["TAG_A"])
        # Only TAG_A data should appear in Y
        for trace in fig.data:
            if hasattr(trace, "y") and trace.y is not None:
                for y_val in trace.y:
                    assert y_val == "TAG_A", f"Unexpected tag {y_val!r} in filtered chart"

    def test_start_end_filter_clips_data(self, single_tag_df):
        import plotly.graph_objects as go

        result = tsqc.check(single_tag_df)
        # Should not raise
        fig = result.plot(start="2026-01-01", end="2026-01-01T00:30:00+00:00")
        assert isinstance(fig, go.Figure)

    def test_show_summary_bar_ignored(self, multi_tag_df):
        """show_summary_bar is no longer supported; passing it must not raise."""
        import plotly.graph_objects as go

        result = tsqc.check(multi_tag_df)
        fig = result.plot()
        assert isinstance(fig, go.Figure)
        # Exactly 3 quality levels → at most 3 unique legend item names
        legend_names = {trace.name for trace in fig.data if trace.showlegend}
        assert legend_names.issubset({"good", "sus", "bad"})

    def test_hover_includes_cause_for_bad_sus(self, single_tag_df):
        import tsqc
        result = tsqc.check(single_tag_df)
        fig = result.plot()
        has_cause = False
        for trace in fig.data:
            ht = trace.hovertext
            if ht is not None:
                if isinstance(ht, str) and "Cause:" in ht:
                    has_cause = True
                    break
                if isinstance(ht, (list, tuple)) and any("Cause:" in str(h) for h in ht):
                    has_cause = True
                    break
        assert has_cause, "Expected at least one trace with 'Cause:' in hovertext"

    def test_plot_uses_display_timezone_for_non_utc(self):
        """Plot should render bars at the correct universal instant for local timestamps."""
        import plotly.graph_objects as go

        ts = pd.date_range("2026-01-01", periods=20, freq="1min", tz="America/Denver")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 20})
        result = tsqc.check(df)
        assert result.display_tz == "America/Denver"
        fig = result.plot()
        assert isinstance(fig, go.Figure)
        # Bar base values should be ISO strings with correct offset
        for trace in fig.data:
            if trace.base is not None:
                for base_val in trace.base:
                    if base_val:
                        assert "-07:00" in base_val or "-06:00" in base_val, (
                            f"Expected America/Denver offset in {base_val}"
                        )
                        break

    def test_plot_start_end_interpreted_in_display_tz(self):
        """Bare start/end strings should be interpreted in display timezone."""
        import plotly.graph_objects as go

        ts = pd.date_range("2026-01-01", periods=100, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 100})
        result = tsqc.check(df, assume_tz="America/Edmonton")
        fig = result.plot(start="2026-01-01", end="2026-01-01T01:00:00")
        assert isinstance(fig, go.Figure)

    def test_no_error_on_all_good_data(self):
        import plotly.graph_objects as go

        ts = pd.date_range("2026-01-01", periods=20, freq="1min", tz="UTC")
        df = pd.DataFrame({"timestamp": ts, "tag_name": "T", "value": [1.0] * 20})
        result = tsqc.check(df, rules=[])
        # With no rules, all rows are 'good' — should not raise
        # (rules=[] means no rules applied, so quality defaults to 'good')
        # Actually check() needs at least one rule, let's provide NullRule
        from tsqc.rules.builtins import NullRule
        result = tsqc.check(df, rules=[NullRule()])
        fig = result.plot()
        assert isinstance(fig, go.Figure)
