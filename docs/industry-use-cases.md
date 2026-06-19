---
title: Industry Use Cases — timeseries-qc
description: Timeseries data quality control applications across solar, wind, battery, and industrial sectors.
---

# Industry Use Cases

## Solar Energy

- **Irradiance sensors**: Detect shading, soiling, or sensor drift
- **Inverter power output**: Identify curtailment, derating, or inverter faults
- **String-level monitoring**: Compare current/voltage across parallel strings

## Wind Energy

- **Wind speed/direction**: Detect icing on anemometers
- **Power curve validation**: Compare actual vs. expected power output
- **Vibration monitoring**: Flag abnormal turbine vibration patterns

## Battery Storage

- **State of charge (SOC)**: Detect drift or recalibration events
- **Temperature monitoring**: Flag thermal runaway precursors
- **Cycle counting**: Validate charge/discharge cycles

## Manufacturing

- **Process sensors**: Detect stuck sensors in continuous processes
- **Quality control**: Monitor production line measurements for drift
- **Predictive maintenance**: Flag abnormal sensor behavior before failures

## Environmental Monitoring

- **Weather stations**: Validate temperature, humidity, pressure readings
- **Air quality**: Detect sensor degradation over time
- **Water quality**: Flag out-of-range pH, turbidity, or conductivity

## Utilities

- **Substation monitoring**: Validate voltage, current, frequency measurements
- **Meter data**: Detect anomalous consumption patterns
- **Transformer health**: Flag abnormal temperature or load patterns

## Oil & Gas

- **Pipeline monitoring**: Detect pressure anomalies and flow irregularities
- **Wellhead sensors**: Validate temperature, pressure, and flow rate measurements
- **Tank level monitoring**: Flag abnormal fill/draw patterns

## Getting Started

Regardless of industry, getting started with `timeseries-qc` follows the same pattern:

```python
import pandas as pd
import tsqc

df = pd.read_csv("sensor_data.csv")
result = tsqc.check(df, assume_tz="UTC")
result.plot().show()
```

See the [Quickstart](quickstart.md) guide for a complete example.

## Next Steps

- [SCADA Integration](scada-integration.md) — working with SCADA data
- [YAML Configuration](yaml-configuration.md) — configure rules per tag
- [User Guide](user-guide.md) — walkthrough with examples
