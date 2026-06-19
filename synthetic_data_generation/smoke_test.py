"""Smoke test for hydro integration — run from repo root."""
import pandas as pd
import tsqc

df = pd.read_csv("data/hydro_plant_scada.csv")
n_tags = df["tag_name"].nunique()
print(f"Loaded {len(df):,} rows, {n_tags} tags")

result = tsqc.check(df, rules="data/hydro_rules.yaml", assume_tz="UTC")
print(result)

summary = result.summary()
print()
print(summary.to_string(index=False))

issues = result.check_timestamps(expected_freq="1min")
print(f"\nTimestamp issues: {len(issues)}")
if not issues.empty:
    grouped = issues.groupby(["tag_name", "issue_type", "severity"]).size()
    print(grouped.reset_index(name="count").to_string(index=False))

# Generator quality distribution
gen = result.df[result.df["tag_name"] == "GENERATOR.MW"]
print(f"\nGENERATOR.MW quality distribution:")
print(dict(gen["quality"].value_counts()))
pct_bad = (gen["quality"] == "bad").mean() * 100
pct_good = (gen["quality"] == "good").mean() * 100
print(f"  {pct_good:.1f}% good, {pct_bad:.1f}% bad")
assert pct_bad < 1.0, f"Too many bad rows for GENERATOR.MW: {pct_bad:.1f}%"
print("OK - generator quality looks reasonable")

result.export_report("data/hydro_qc_report.html", title="Hydro Plant QC Report")
import os
sz = os.path.getsize("data/hydro_qc_report.html") / 1024
print(f"HTML report exported: {sz:.0f} KB")
