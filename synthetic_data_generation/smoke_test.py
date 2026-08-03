"""Smoke test for hydro integration — run from repo root."""
import os

import pandas as pd

import tsqc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

df = pd.read_csv(os.path.join(ROOT, "data", "hydro_plant_scada.csv"))
n_tags = df["tag_name"].nunique()
print(f"Loaded {len(df):,} rows, {n_tags} tags")

result = tsqc.check(df, rules=os.path.join(HERE, "hydro_rules.yaml"), assume_tz="UTC")
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
print("\nGENERATOR.MW quality distribution:")
print(dict(gen["quality"].value_counts()))
pct_bad = (gen["quality"] == "bad").mean() * 100
pct_good = (gen["quality"] == "good").mean() * 100
print(f"  {pct_good:.1f}% good, {pct_bad:.1f}% bad")
assert pct_bad < 1.0, f"Too many bad rows for GENERATOR.MW: {pct_bad:.1f}%"
print("OK - generator quality looks reasonable")

report_path = os.path.join(ROOT, "data", "hydro_qc_report.html")
result.export_report(report_path, title="Hydro Plant QC Report")
sz = os.path.getsize(report_path) / 1024
print(f"HTML report exported: {sz:.0f} KB")
