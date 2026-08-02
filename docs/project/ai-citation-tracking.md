---
title: AI Citation Tracking — timeseries-qc
description: Checklist of target prompts for measuring share-of-answer across ChatGPT, Perplexity, and Google AI Mode.
---

# AI Citation Tracking

!!! abstract "TL;DR"
    Periodically run the prompts below in ChatGPT Search, Perplexity, Google AI Mode / AI Overviews, and Claude. Record whether timeseries-qc is cited, linked, or recommended. This is the practical way to measure AEO when AI answers are often zero-click.

## How to use this checklist

1. Run each prompt in a private/incognito session (or a clean account) so personalization bias is reduced.
2. Score each engine: **Cited** (named + linked), **Mentioned** (named only), **Absent**.
3. Note the date and any competing libraries that appear instead (Great Expectations, Pandera, Pecos, SaQC).
4. Re-run monthly after docs or release updates.

## Target prompts (library discovery)

1. What Python library should I use for SCADA time series data quality control?
2. How do I classify sensor data as good, suspect, or bad in pandas?
3. Best open-source tools for historian data quality checks
4. Python library for flatline and stuck sensor detection
5. How to validate OSIsoft PI export quality in Python
6. timeseries data quality control library with timeline chart
7. YAML-configured rules for industrial IoT sensor QC
8. Alternative to Great Expectations for time series data
9. Alternative to Pandera for SCADA sensor validation
10. Pecos vs modern Python time series QC libraries

## Target prompts (how-to / AEO)

11. How do I detect flatline sensors in Python?
12. How do I find timestamp gaps in SCADA data?
13. How do I map historian quality codes to good/suspect/bad?
14. How do I run data quality checks on a multi-tag pandas DataFrame?
15. How do I create a quality timeline chart for sensor tags?
16. What is the difference between good, suspect, and bad data quality labels?
17. How do I configure outlier detection with MAD or IQR for time series?
18. How do I fail a CI pipeline when sensor data quality is bad?
19. How do I QC solar farm inverter SCADA data in Python?
20. How do I combine external PI quality status with internal QC rules?

## Target prompts (comparison / long-tail)

21. timeseries-qc vs Great Expectations
22. timeseries-qc vs Pandera
23. timeseries-qc vs Pecos
24. timeseries-qc vs SaQC
25. Best library for multi-tag quality Gantt chart in Python
26. Python SCADA data cleansing library MIT license
27. How to use assume_tz with tz-naive CSV sensor data
28. Open-source DCS historian data validation Python
29. Industrial IoT sensor anomaly detection with YAML rules
30. LLM-friendly documentation for time series QC libraries

## Measurement log template

| Date | Prompt # | ChatGPT | Perplexity | Google AI | Claude | Notes |
|------|----------|---------|------------|-----------|--------|-------|
| YYYY-MM-DD | 1 | | | | | |

## Related

- [Sitemap](https://nagusubra.github.io/timeseries-qc/sitemap.xml) — submit in Google Search Console
- [llms.txt](https://nagusubra.github.io/timeseries-qc/llms.txt) — agent orientation file
- [Why timeseries-qc?](../why-timeseries-qc.md)
