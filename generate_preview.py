"""Generate a preview plot with reasons in hover tooltip."""
import numpy as np
import pandas as pd
import tsqc

rng = np.random.default_rng(42)
n = 100
timestamps = pd.date_range(start="2026-01-01", periods=n, freq="1min", tz="UTC")
values = 50 + 20 * np.sin(np.linspace(0, 4 * np.pi, n)) + rng.normal(0, 1, n)

values[20:25] = np.nan           # Null (bad)
values[40:50] = 42.0              # Flatline (sus)
values[70] = 500.0                # Spike (sus - delta)
values[71] = 501.0                # Spike (sus - delta)

df = pd.DataFrame({"timestamp": timestamps, "tag_name": "TAG_A", "value": values})

result = tsqc.check(df, assume_tz="UTC")
fig = result.plot(title="Quality Timeline with Cause Tooltip Preview")

fig.write_html("preview_plot.html", auto_open=False)
print("Plot saved to preview_plot.html")
print()
print("Sample quality_reasons from the data:")
print(result.df["quality_reasons"].value_counts().head(10))
