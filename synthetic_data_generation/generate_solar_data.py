"""
Generate one week of synthetic hourly SCADA data for a solar farm with 3 tags:

  INVERTER.MW         — AC output of the inverter string array (MW)
  MET.IRRADIANCE      — Pyranometer GHI reading (W/m²)
  TRACKER.ANGLE       — Single-axis tracker tilt angle (degrees from horizontal)

Data covers 2026-06-01 to 2026-06-07 (UTC), 1-hour interval → 168 rows per tag.

Engineered anomalies (designed to stress-test every built-in rule):
  1. NaN burst (NullRule)        INVERTER.MW    rows 50-54  (5 hours missing)
  2. Comm-freeze flatline        MET.IRRADIANCE rows 30-39  (10 h frozen at 642 W/m²)
  3. Night-time irradiance spike MET.IRRADIANCE row  72     (reads 980 at 00:00 — impossible)
  4. Out-of-range angle          TRACKER.ANGLE  rows 60-62  (jumps to 110° — beyond ±90°)
  5. Large delta spike           INVERTER.MW    row  96     (sudden +25 MW in one hour)
  6. Duplicate timestamp         TRACKER.ANGLE  row 100     (duplicate injected)
  7. Stale / flatline angle      TRACKER.ANGLE  rows 120-134 (tracker stuck at 30° for 15h)

All anomalies are intentional so that the tsqc library flags every one.
"""

from __future__ import annotations

import os
import random

import numpy as np
import pandas as pd

# ── reproducibility ──────────────────────────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

# ── time axis ────────────────────────────────────────────────────────────────
START = pd.Timestamp("2026-06-01 00:00:00", tz="UTC")
END   = pd.Timestamp("2026-06-07 23:00:00", tz="UTC")
ts    = pd.date_range(START, END, freq="1h")
N     = len(ts)  # 168

def _iso(series: pd.DatetimeIndex) -> list[str]:
    return [t.isoformat() for t in series]


# ── helpers ──────────────────────────────────────────────────────────────────

def solar_elevation_factor(timestamps: pd.DatetimeIndex) -> np.ndarray:
    """Approximate sin(elevation) curve for a mid-latitude site (lat≈37°N).
    Returns values in [0, 1]; negative hours (night) clamped to 0.
    """
    # hour-of-day in solar time (simplified: UTC ≈ local solar for 0° longitude site)
    hour = np.array(timestamps.hour) + np.array(timestamps.minute) / 60.0
    # sunrise ~5 h, solar noon ~12 h, sunset ~19 h  (June, ~14h day)
    elev = np.sin(np.pi * (hour - 5) / 14)
    return np.clip(elev, 0, 1)


# ── INVERTER.MW ──────────────────────────────────────────────────────────────
# Rated capacity 10 MW.  Output follows irradiance curve + small noise.
elev = solar_elevation_factor(ts)
mw_clean = 10.0 * elev + rng.normal(0, 0.15, N)
mw_clean = np.clip(mw_clean, 0, 10.5)

# Anomaly 1: NaN burst (rows 50-54)
mw_values = mw_clean.copy().astype(float)
mw_values[50:55] = np.nan

# Anomaly 5: large delta spike at row 96 (midnight spike — impossible physics)
mw_values[96] = mw_values[95] + 25.0  # 25 MW jump in 1 hour on a 10 MW plant

inv_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "INVERTER.MW",
    "value": np.round(mw_values, 4),
})

# ── MET.IRRADIANCE ───────────────────────────────────────────────────────────
# GHI W/m².  Peak ~950 W/m² at noon.  Night = 0.
irr_clean = 950.0 * elev + rng.normal(0, 12, N)
irr_clean = np.clip(irr_clean, 0, 1000)

irr_values = irr_clean.copy()

# Anomaly 2: comm-freeze flatline (rows 30-39: ~06:00–15:00 on day 2)
frozen_val = round(float(irr_clean[29]), 2)
irr_values[30:40] = frozen_val

# Anomaly 3: nighttime irradiance spike above physical max (row 72 = 00:00 on day 4)
# 1100 W/m² exceeds the theoretical clear-sky limit (1050) → triggers RangeRule → bad
irr_values[72] = 1100.0

met_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "MET.IRRADIANCE",
    "value": np.round(irr_values, 2),
})

# ── TRACKER.ANGLE ────────────────────────────────────────────────────────────
# Single-axis E-W tracker.  Angle in degrees: -60° at sunrise → 0° at noon → +60° at sunset.
# Night: parked at 0° (horizontal, dew-shedding position).
angle_clean = np.where(elev > 0, -60 + 120 * (ts.hour - 5) / 14, 0.0)
angle_clean = np.clip(angle_clean, -65, 65)
angle_values = angle_clean + rng.normal(0, 0.3, N)

# Anomaly 4: out-of-range angle (rows 60-62)
angle_values[60:63] = 110.0  # beyond ±90° — physically impossible

# Anomaly 7: tracker stuck / flatline (rows 120-134, 15 consecutive hours)
angle_values[120:135] = 30.0

angle_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "TRACKER.ANGLE",
    "value": np.round(angle_values, 3),
})

# ── Anomaly 6: duplicate timestamp in TRACKER.ANGLE ─────────────────────────
dup_row = angle_df.iloc[[100]].copy()
angle_df = pd.concat(
    [angle_df.iloc[:101], dup_row, angle_df.iloc[101:]],
    ignore_index=True,
)

# ── Combine and save ─────────────────────────────────────────────────────────
combined = pd.concat([inv_df, met_df, angle_df], ignore_index=True)

out_path = os.path.join(os.path.dirname(__file__), "solar_farm_scada.csv")
combined.to_csv(out_path, index=False)

print(f"Written {len(combined):,} rows → {out_path}")
print(combined.groupby("tag_name").agg(
    rows=("value", "count"),
    nulls=("value", lambda s: s.isna().sum()),
).to_string())
print("\nEngineered anomalies summary:")
print("  INVERTER.MW   rows 50-54  : NaN burst (NullRule → bad)")
print("  INVERTER.MW   row  96     : +25 MW delta spike (DeltaRule → sus/bad)")
print("  MET.IRRADIANCE rows 30-39 : comm-freeze flatline (FlatlineRule → sus)")
print("  MET.IRRADIANCE row  72    : nighttime irradiance 1100 W/m\u00b2 (RangeRule \u2192 bad)")
print("  TRACKER.ANGLE rows 60-62  : 110° out-of-range (RangeRule → bad)")
print("  TRACKER.ANGLE row  100    : duplicate timestamp (check_timestamps)")
print("  TRACKER.ANGLE rows 120-134: tracker stuck 15h (FlatlineRule → sus)")
