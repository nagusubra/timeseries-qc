"""
Generate 1 month of synthetic hydro power plant SCADA data.

Tags:
  FOREBAY.LEVEL   — forebay water level (ft)
  TAILRACE.LEVEL  — tailrace water level (ft)
  GENERATOR.MW    — generator output (MW)
  INFLOW.CFS      — inflow to reservoir (CFS)

Anomalies engineered to exercise all four tsqc QC rules:
  NullRule       — sensor dropout bursts (NaN)
  FlatlineRule   — comm-freeze flatlines
  DeltaRule      — lightning transient spikes
  RangeRule      — out-of-range calibration errors

Output: data/hydro_plant_scada.csv (long format)
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd


def generate_forebay(ts: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    """Forebay level: slow drawdown / refill cycle + daily pattern + noise.
    Normal range: 950–1050 ft.
    """
    n = len(ts)
    t_days = np.arange(n) / (60 * 24)  # fractional days

    # Seasonal trend: draw down mid-month, refill at end
    seasonal = -15 * np.sin(2 * np.pi * t_days / 31)

    # Diurnal: small daily drawdown during peak generation hours (6am–10pm)
    hour = np.array([t.hour for t in ts])
    diurnal = -2.0 * ((hour >= 6) & (hour <= 22)).astype(float)

    noise = rng.normal(0, 0.05, n)
    values = 1000.0 + seasonal + diurnal + noise

    # ── Anomaly 1: NaN burst day 8 (comm dropout, ~50 rows) ──────────────
    day8_start = 60 * 24 * 7   # minute index for start of day 8
    values[day8_start : day8_start + 52] = np.nan

    # ── Anomaly 2: 2-hour gap on day 10 (delete rows in place → NaN) ─────
    # We'll mark these NaN here; the generator will drop them from timestamps
    day10_gap_start = 60 * 24 * 9 + 180   # 3h into day 10
    values[day10_gap_start : day10_gap_start + 120] = np.nan

    return values


def generate_tailrace(ts: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    """Tailrace level: responds to discharge + noise. Normal range: 820–870 ft."""
    n = len(ts)
    t_days = np.arange(n) / (60 * 24)

    # Base level with slight rising trend (high water season)
    base = 845.0 + 5.0 * np.sin(2 * np.pi * t_days / 31) + 0.3 * t_days / 31

    # Noisier than forebay (discharge turbulence)
    noise = rng.normal(0, 0.15, n)
    values = base + noise

    # ── Anomaly 3: Flatline (comm freeze) — day 12, 90 minutes ──────────
    day12_start = 60 * 24 * 11 + 240
    flat_val = values[day12_start - 1]  # last good value
    values[day12_start : day12_start + 90] = flat_val

    # ── Anomaly 4: Out-of-range calibration error — day 18, 20 rows ─────
    day18_start = 60 * 24 * 17 + 60
    values[day18_start : day18_start + 20] = 905.0   # >> max of 870 ft

    return values


def generate_generator_mw(ts: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    """Generator MW: step changes on/off; correlated with inflow.
    Normal operating range: 0–150 MW.
    """
    n = len(ts)
    values = np.zeros(n, dtype=float)

    # Unit runs from day 1 to day 19, day 24 to end — 100–130 MW with noise
    # Step changes at hour boundaries
    for i in range(n):
        t = ts[i]
        day_num = (t - ts[0]).days
        hour = t.hour

        if day_num < 19:
            # Running — power varies by hour (load following)
            base_mw = 110.0 + 15.0 * np.sin(2 * np.pi * hour / 24)
            values[i] = base_mw + rng.normal(0, 1.0)
        elif 19 <= day_num < 23:
            # Offline for maintenance — legitimate 0 MW flatline
            values[i] = 0.0
        else:
            # Back online
            base_mw = 105.0 + 12.0 * np.sin(2 * np.pi * hour / 24)
            values[i] = base_mw + rng.normal(0, 1.0)

    values = np.clip(values, 0.0, 150.0)

    # ── Anomaly 5: NaN burst — day 15, 30 rows (instrument fault) ───────
    day15_start = 60 * 24 * 14 + 300
    values[day15_start : day15_start + 32] = np.nan

    return values


def generate_inflow(ts: pd.DatetimeIndex, rng: np.random.Generator) -> np.ndarray:
    """Inflow: log-normal base with storm pulses and daily cycle.
    Normal range: 500–5000 CFS.
    """
    n = len(ts)
    t_days = np.arange(n) / (60 * 24)

    # Base log-normal (geometric mean ~1800 CFS)
    log_base = np.log(1800) + 0.2 * np.sin(2 * np.pi * t_days / 31)
    base = np.exp(log_base + rng.normal(0, 0.05, n))

    # Daily cycle (snowmelt peak mid-afternoon)
    hour = np.array([t.hour for t in ts])
    diurnal_factor = 1.0 + 0.15 * np.sin(2 * np.pi * (hour - 14) / 24)
    values = base * diurnal_factor

    # ── Storm pulses: days 7, 16, 25 ─────────────────────────────────────
    for storm_day in [6, 15, 24]:
        storm_start = 60 * 24 * storm_day + 120
        storm_len = 180
        if storm_start + storm_len <= n:
            # Triangular pulse
            pulse = np.zeros(storm_len)
            mid = storm_len // 2
            pulse[:mid] = np.linspace(0, 2500, mid)
            pulse[mid:] = np.linspace(2500, 0, storm_len - mid)
            values[storm_start : storm_start + storm_len] += pulse

    # ── Anomaly 6: Spike (lightning transient) — day 5, 2 rows ─────────
    day5_start = 60 * 24 * 4 + 90
    values[day5_start] = 18_500.0    # >> max of 5000
    values[day5_start + 1] = 17_200.0

    # ── Anomaly 7: Duplicate timestamps injected ─── done post-hoc ──────
    # (handled separately in data assembly)

    return values


def build_scada_csv(output_path: str = "data/hydro_plant_scada.csv") -> pd.DataFrame:
    """Build the full 4-tag long-format DataFrame and save to CSV."""
    rng = np.random.default_rng(2026)

    # 1-min intervals, January 2026 UTC
    ts = pd.date_range(
        start="2026-01-01T00:00:00+00:00",
        end="2026-01-31T23:59:00+00:00",
        freq="1min",
        tz="UTC",
    )
    n = len(ts)
    print(f"Base timestamps: {n:,} rows per tag")

    generators = {
        "FOREBAY.LEVEL": generate_forebay,
        "TAILRACE.LEVEL": generate_tailrace,
        "GENERATOR.MW": generate_generator_mw,
        "INFLOW.CFS": generate_inflow,
    }

    dfs: list[pd.DataFrame] = []
    for tag, fn in generators.items():
        values = fn(ts, rng)
        df_tag = pd.DataFrame(
            {
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "tag_name": tag,
                "value": values,
            }
        )

        # ── Anomaly for FOREBAY.LEVEL: inject a true gap (remove rows) ──
        # Rows marked NaN above will be kept as NaN (sensor dropout = NullRule).
        # The 2-hour gap is separate — we simulate it by removing those rows.
        if tag == "FOREBAY.LEVEL":
            gap_start_idx = 60 * 24 * 9 + 180
            gap_end_idx = gap_start_idx + 120
            # Replace NaN gap marker with a dropped-row gap (keep only non-gap)
            # We inserted NaN above; now remove those rows to create a true gap
            gap_mask = pd.Series(False, index=df_tag.index)
            gap_mask.iloc[gap_start_idx:gap_end_idx] = True
            df_tag = df_tag[~gap_mask].copy()

        # ── Anomaly for INFLOW.CFS: duplicate timestamp injection ────────
        if tag == "INFLOW.CFS":
            dup_day = 25
            dup_idx = 60 * 24 * dup_day + 45
            dup_row = df_tag.iloc[[dup_idx]].copy()
            # Insert duplicate right after the original row
            before = df_tag.iloc[: dup_idx + 1]
            after = df_tag.iloc[dup_idx + 1 :]
            df_tag = pd.concat([before, dup_row, after], ignore_index=True)

        dfs.append(df_tag)

    combined = pd.concat(dfs, ignore_index=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.to_csv(output_path, index=False)
    print(f"Saved {len(combined):,} rows → {output_path}")

    # Print summary per tag
    for tag, grp in combined.groupby("tag_name"):
        n_nan = grp["value"].isna().sum()
        n_rows = len(grp)
        val_range = (
            f"{grp['value'].min():.1f}–{grp['value'].max():.1f}"
            if grp["value"].notna().any()
            else "all-NaN"
        )
        print(f"  {tag:<20} {n_rows:>6,} rows  NaN={n_nan:>4}  range={val_range}")

    return combined


if __name__ == "__main__":
    build_scada_csv()
