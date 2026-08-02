---
title: Industry Use Cases — timeseries-qc
description: Timeseries data quality control applications across solar, wind, battery, manufacturing, utilities, and oil & gas with timeseries-qc.
---

# Industry Use Cases

!!! abstract "TL;DR"
    The same `tsqc.check` pattern works across industries: long-format `timestamp` / `tag_name` / `value`, YAML rules for physical limits, then `summary()` / `plot()` / `export_report()`. Tune `tag_rules` to each asset class — inverter MW, wind speed, SOC, pipeline pressure — rather than rewriting QC code per sector.

`timeseries-qc` is sector-agnostic: you bring sensor semantics in YAML (ranges, flatline windows, deltas), and the library classifies every sample as good, suspect, or bad.

## Solar Energy

- **Irradiance sensors**: Detect shading, soiling, or sensor drift
- **Inverter power output**: Identify curtailment, derating, or inverter faults
- **String-level monitoring**: Compare current/voltage across parallel strings

Walk through a full CSV example in the [Solar Farm tutorial](tutorials/solar-farm-csv.md).

## Wind Energy

- **Wind speed/direction**: Detect icing on anemometers
- **Power curve validation**: Compare actual vs. expected power output
- **Vibration monitoring**: Flag abnormal turbine vibration patterns

Use shorter flatline windows on anemometers during expected variability, and range rules on nacelle temperature and rotor speed.

## Battery Storage

- **State of charge (SOC)**: Detect drift or recalibration events
- **Temperature monitoring**: Flag thermal runaway precursors
- **Cycle counting**: Validate charge/discharge cycles

Delta rules on temperature and current catch sudden faults; outlier rules on SOC help surface sensor recalibrations.

## Manufacturing

- **Process sensors**: Detect stuck sensors in continuous processes
- **Quality control**: Monitor production line measurements for drift
- **Predictive maintenance**: Flag abnormal sensor behavior before failures

Gate fixture exports in CI with `pct_bad` thresholds — see [CI Gate on Data Quality](tutorials/ci-gate-data-quality.md).

## Environmental Monitoring

- **Weather stations**: Validate temperature, humidity, pressure readings
- **Air quality**: Detect sensor degradation over time
- **Water quality**: Flag out-of-range pH, turbidity, or conductivity

## Utilities

- **Substation monitoring**: Validate voltage, current, frequency measurements
- **Meter data**: Detect anomalous consumption patterns
- **Transformer health**: Flag abnormal temperature or load patterns

Historian status columns map cleanly via `external_quality_col` — see [SCADA Integration](scada-integration.md).

## Oil & Gas

- **Pipeline monitoring**: Detect pressure anomalies and flow irregularities
- **Wellhead sensors**: Validate temperature, pressure, and flow rate measurements
- **Tank level monitoring**: Flag abnormal fill/draw patterns

## Shared pattern

Regardless of industry, getting started follows the same flow:

```python
import pandas as pd
import tsqc

df = pd.read_csv("sensor_data.csv", parse_dates=["timestamp"])
result = tsqc.check(df, rules="plant_rules.yaml", assume_tz="UTC")
print(result.summary())
result.plot().show()
result.export_report("qc_report.html")
```

Put physical limits under `tag_rules` (often with globs like `"WELL_*.PRESSURE"`), keep null/flatline defaults shared, and pass `assume_tz` for tz-naive historian CSVs.

## Next Steps

- [SCADA Integration](scada-integration.md) — working with SCADA data
- [Tutorials](tutorials/index.md) — end-to-end walkthroughs
- [YAML Configuration](yaml-configuration.md) — configure rules per tag
- [Quickstart](quickstart.md) — five-line intro
