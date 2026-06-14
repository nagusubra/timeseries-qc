"""
Generate one month of synthetic hourly SCADA data for an oil and gas well pad
with three sensor tags:

  WHP.PSIG        — Wellhead Pressure (psig)
  FMRATE.MSCFD    — Gas Flow Rate at the meter (Mscfd, thousand standard ft³/day)
  OHT.TEMP_F      — Heater-Treater outlet temperature (°F)

Data covers 2026-04-01 to 2026-04-30 (UTC), 1-hour interval → 720 rows per tag.

Engineered anomalies (designed to stress-test every built-in rule):
  1. NaN burst (NullRule)              WHP.PSIG      rows 200-219  (20 h missing)
  2. Comm-freeze flatline              FMRATE.MSCFD  rows 60-79    (20 h frozen)
  3. Out-of-range high pressure        WHP.PSIG      row  340      (reads 1500 psig — above MAWP)
  4. Out-of-range low  pressure        WHP.PSIG      rows 500-504  (reads 5 psig — below atmospheric)
  5. Large delta spike                 FMRATE.MSCFD  row  415      (sudden -2000 Mscfd)
  6. Duplicate timestamp               OHT.TEMP_F    row  600      (duplicate injected)
  7. Stale / flatline temperature      OHT.TEMP_F    rows 650-670  (heater stuck 21 h)
  8. Excessive temp drop               OHT.TEMP_F    row  720      (temp drops 50°F in 1 h)
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

# ── reproducibility ──────────────────────────────────────────────────────────
SEED = 1729
rng = np.random.default_rng(SEED)

# ── time axis ────────────────────────────────────────────────────────────────
START = pd.Timestamp("2026-04-01 00:00:00", tz="UTC")
END   = pd.Timestamp("2026-04-30 23:00:00", tz="UTC")
ts    = pd.date_range(START, END, freq="1h")
N     = len(ts)  # 720

def _iso(series: pd.DatetimeIndex) -> list[str]:
    return [t.isoformat() for t in series]


# ── WHP.PSIG — Wellhead Pressure (psig) ─────────────────────────────────────
# Normal operating range: 400-900 psig. Diurnal fluctuation from pump cycles.
# Base pressure ~650 psig + slow diurnal component + small noise.
hours = np.arange(N, dtype=float)
diurnal = 25.0 * np.sin(2 * np.pi * hours / 24.0 - np.pi / 2)
whp_clean = 650.0 + diurnal + rng.normal(0, 4.0, N)
whp_clean = np.clip(whp_clean, 400, 900)

whp_values = whp_clean.copy()

# Anomaly 1: NaN burst (rows 200-219, 20 h dropout)
whp_values[200:220] = np.nan

# Anomaly 3: out-of-range HIGH (row 340, mid-month) — above 1100 psig MAWP
whp_values[340] = 1500.0

# Anomaly 4: out-of-range LOW (rows 500-504) — below atmospheric (~14.7 psig)
# 5 psig is physically impossible → triggers RangeRule → bad
whp_values[500:505] = 5.0

whp_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "WHP.PSIG",
    "value": np.round(whp_values, 2),
})


# ── FMRATE.MSCFD — Gas flow rate (Mscfd) ─────────────────────────────────────
# Normal range: 1500-4500 Mscfd. Follows wellhead pressure with noise.
fmrate_clean = 2800.0 + 4.0 * diurnal + rng.normal(0, 80, N)
fmrate_clean = np.clip(fmrate_clean, 1500, 4500)

fmrate_values = fmrate_clean.copy()

# Anomaly 2: comm-freeze flatline (rows 60-79, 20 h)
frozen_val = round(float(fmrate_clean[59]), 1)
fmrate_values[60:80] = frozen_val

# Anomaly 5: large negative delta spike (row 415) — sudden 2000 Mscfd drop
fmrate_values[415] = fmrate_values[414] - 2000.0

fmrate_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "FMRATE.MSCFD",
    "value": np.round(fmrate_values, 1),
})


# ── OHT.TEMP_F — Heater-treater outlet temperature (°F) ─────────────────────
# Normal range: 100-180 °F. Slowly varying; no strong diurnal pattern.
# Note: -1 in size to leave room for last anomaly (delta spike needs 2 points)
oht_clean = 145.0 + 6.0 * np.sin(2 * np.pi * hours / 48.0) + rng.normal(0, 1.5, N)
oht_clean = np.clip(oht_clean, 100, 180)

oht_values = oht_clean.copy()

# Anomaly 7: heater stuck (flatline) at 142°F (rows 650-670, 21 h)
oht_values[650:671] = 142.0

# Anomaly 8: excessive temp drop at last row (50°F in 1 h)
oht_values[N - 1] = oht_values[N - 2] - 50.0

oht_df = pd.DataFrame({
    "timestamp": _iso(ts),
    "tag_name": "OHT.TEMP_F",
    "value": np.round(oht_values, 2),
})

# Anomaly 6: duplicate timestamp in OHT.TEMP_F (row 600)
dup_row = oht_df.iloc[[600]].copy()
oht_df = pd.concat(
    [oht_df.iloc[:601], dup_row, oht_df.iloc[601:]],
    ignore_index=True,
)


# ── Combine and save ─────────────────────────────────────────────────────────
combined = pd.concat([whp_df, fmrate_df, oht_df], ignore_index=True)

out_path = os.path.join(os.path.dirname(__file__), "oilfield_scada.csv")
combined.to_csv(out_path, index=False)

print(f"Written {len(combined):,} rows -> {out_path}")
print(combined.groupby("tag_name").agg(
    rows=("value", "count"),
    nulls=("value", lambda s: s.isna().sum()),
).to_string())
print("\nEngineered anomalies summary:")
print("  WHP.PSIG      rows 200-219: NaN burst (NullRule -> bad)")
print("  WHP.PSIG      row  340    : 1500 psig over-range (RangeRule -> bad)")
print("  WHP.PSIG      rows 500-504: 5 psig sub-atmospheric (RangeRule -> bad)")
print("  FMRATE.MSCFD  rows 60-79  : 20 h comm-freeze flatline (FlatlineRule -> sus)")
print("  FMRATE.MSCFD  row  415    : -2000 Mscfd delta spike (DeltaRule -> sus/bad)")
print("  OHT.TEMP_F    row  600    : duplicate timestamp (check_timestamps)")
print("  OHT.TEMP_F    rows 650-670: heater stuck 21 h (FlatlineRule -> sus)")
print("  OHT.TEMP_F    row  719    : 50 degF drop in 1 h (DeltaRule -> sus/bad)")
