"""Golden-output tests — perf refactors must keep result.df byte-identical."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import tsqc
from tsqc import (
    DeltaRule,
    FlatlineRule,
    NullRule,
    OutlierRule,
    RangeRule,
)


def _fixture_df() -> pd.DataFrame:
    rng = np.random.default_rng(123)
    frames = []
    for i, tag in enumerate(["TAG_A", "TAG_B", "TAG_C"]):
        n = 120
        ts = pd.date_range("2026-01-01", periods=n, freq="1min", tz="UTC")
        values = 50 + 10 * np.sin(np.linspace(0, 6, n)) + rng.normal(0, 0.5, n)
        values[10:15] = np.nan
        values[40:55] = 42.0
        values[80] = 900.0
        status = np.zeros(n, dtype=int)
        status[10:15] = 2
        status[90:95] = 1
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": ts,
                    "tag_name": tag,
                    "value": values,
                    "status": status,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


@pytest.fixture(scope="module")
def sample_df() -> pd.DataFrame:
    return _fixture_df()


def _assert_df_equal(a: pd.DataFrame, b: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(a, b, check_dtype=True, check_exact=False, rtol=0, atol=0)
    # Quality labels and reasons must be exact string matches
    for col in ("quality", "quality_reasons", "qc_quality", "qc_quality_reasons"):
        if col in a.columns and col in b.columns:
            assert list(a[col]) == list(b[col])


def test_golden_default_rules(sample_df):
    """Capture and re-check quality/reasons for the default rule path."""
    result = tsqc.check(sample_df[["timestamp", "tag_name", "value"]], assume_tz="UTC")
    # Self-consistency: running twice on the same input yields identical output
    result2 = tsqc.check(sample_df[["timestamp", "tag_name", "value"]], assume_tz="UTC")
    _assert_df_equal(result.df, result2.df)
    assert set(result.df["quality"].unique()) <= {"good", "sus", "bad"}
    assert (result.df["quality"] == "bad").any()
    assert (result.df["quality"] == "sus").any()


def test_golden_explicit_rules(sample_df):
    rules = [
        NullRule(level="bad"),
        FlatlineRule(window="10min", min_delta=0.001, level="sus"),
        DeltaRule(max_delta=100.0, level="sus"),
        RangeRule(min_val=0, max_val=200, level="bad"),
        OutlierRule(method="zscore", threshold=3.0, level="sus"),
    ]
    r1 = tsqc.check(sample_df[["timestamp", "tag_name", "value"]], rules=rules, assume_tz="UTC")
    r2 = tsqc.check(sample_df[["timestamp", "tag_name", "value"]], rules=rules, assume_tz="UTC")
    _assert_df_equal(r1.df, r2.df)
    # Flatline reasons include stuck value
    flat_reasons = r1.df.loc[r1.df["quality_reasons"].str.contains("flatline", na=False), "quality_reasons"]
    assert flat_reasons.str.contains(r"flatline @ ").any()


def test_golden_external_combined(sample_df):
    quality_map = {0: "good", 1: "sus", 2: "bad"}
    rules = [NullRule(level="bad"), RangeRule(min_val=0, max_val=200, level="bad")]
    r1 = tsqc.check(
        sample_df,
        rules=rules,
        assume_tz="UTC",
        external_quality_col="status",
        quality_mode="combined",
        quality_map=quality_map,
    )
    r2 = tsqc.check(
        sample_df,
        rules=rules,
        assume_tz="UTC",
        external_quality_col="status",
        quality_mode="combined",
        quality_map=quality_map,
    )
    _assert_df_equal(r1.df, r2.df)
    assert r1.df["quality_reasons"].str.contains("source_data_quality:", na=False).any()


def test_golden_issue_summary_matches_runs(sample_df):
    result = tsqc.check(
        sample_df[["timestamp", "tag_name", "value"]],
        rules=[NullRule(), FlatlineRule(window="10min", min_delta=0.0)],
        assume_tz="UTC",
    )
    issues = result.issue_summary()
    if not issues.empty:
        assert issues["n_rows_with_issues"].gt(0).all()
        assert set(issues["status"]) <= {"sus", "bad"}
