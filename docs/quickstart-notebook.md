---
title: Quickstart Notebook
description: A runnable Jupyter notebook covering the full timeseries-qc workflow — synthetic SCADA data with injected range violations, a flatline, nulls, and a timestamp gap, run through YAML rules, classification, and the Plotly quality timeline.
---

# Quickstart Notebook

Run the [5-minute quickstart end-to-end](https://github.com/nagusubra/timeseries-qc/blob/main/examples/quickstart.ipynb) — synthetic SCADA data with injected problems, YAML rules, and the quality timeline, all in one notebook.

[Open on GitHub](https://github.com/nagusubra/timeseries-qc/blob/main/examples/quickstart.ipynb){ .md-button }

## What it covers

1. Generates a week of synthetic hourly data for three tags (`FEEDWATER.FLOW_GPM`, `BOILER.PRESSURE_PSI`, `STACK.TEMP_F`) with a range violation, a flatline, null values, and a timestamp gap deliberately injected
2. Defines thresholds in a YAML rule config
3. Runs `tsqc.check()` to classify every row good / sus / bad
4. Walks through `summary()`, `issue_summary()`, and `check_timestamps()`
5. Renders the Plotly quality timeline
6. Exports a self-contained HTML report

To run it locally:

```bash
git clone https://github.com/nagusubra/timeseries-qc.git
cd timeseries-qc
pip install -e ".[dev]"
jupyter notebook examples/quickstart.ipynb
```
