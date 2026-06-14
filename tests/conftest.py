"""Pytest fixtures shared across all test modules."""

import numpy as np
import pandas as pd
import pytest


def _make_tag_df(
    tag_name: str,
    n: int = 100,
    start: str = "2026-01-01",
    freq: str = "1min",
    seed: int = 42,
) -> pd.DataFrame:
    """Build a single-tag DataFrame with known anomalies injected."""
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start=start, periods=n, freq=freq, tz="UTC")
    # Sinusoidal base + small noise
    values = 50 + 20 * np.sin(np.linspace(0, 4 * np.pi, n)) + rng.normal(0, 1, n)

    # Inject 5 NaNs at rows 20-24
    values[20:25] = np.nan

    # Inject 10 flatline rows at rows 40-49 (constant value)
    values[40:50] = 42.0

    # Inject 2 spike rows at rows 70-71
    values[70] = 500.0
    values[71] = 501.0

    df = pd.DataFrame({"timestamp": timestamps, "tag_name": tag_name, "value": values})
    return df


@pytest.fixture
def single_tag_df() -> pd.DataFrame:
    """100-row single-tag DataFrame with injected NaNs, flatlines, and spikes."""
    return _make_tag_df("TAG_A")


@pytest.fixture
def multi_tag_df() -> pd.DataFrame:
    """300-row multi-tag DataFrame (TAG_A, TAG_B, TAG_C), 100 rows each."""
    dfs = [
        _make_tag_df("TAG_A", seed=42),
        _make_tag_df("TAG_B", seed=43),
        _make_tag_df("TAG_C", seed=44),
    ]
    return pd.concat(dfs, ignore_index=True)
