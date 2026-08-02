---
title: Architecture — timeseries-qc Internal Design
description: How timeseries-qc is structured internally — package organization, data flow, rule execution pipeline, and design decisions.
og_title: Architecture — timeseries-qc Internal Design
og_description: How timeseries-qc is structured internally — package organization, data flow, rule execution pipeline, and design decisions.
---

# Architecture

!!! abstract "TL;DR"
    `tsqc.check()` validates input, resolves rules (YAML, list, or defaults), applies them per tag with vectorized operations, and returns a `QCResult` with summary, plot, timestamp, and report methods. Design favors pandas-native, offline-first workflows.

## How is the package organized?

Public entry points live in `tsqc/__init__.py`; checking, results, YAML parsing, rules, timestamp health, and viz are separate modules.

```
tsqc/
  __init__.py        # Public API: check(), QCResult, rule classes
  checker.py          # Core check() function and rule application
  result.py           # QCResult class with all downstream methods

  config/
    yaml_parser.py    # Parse YAML rule files into Rule objects

  rules/
    base.py           # Abstract Rule base class
    builtins.py       # NullRule, FlatlineRule, DeltaRule, RangeRule, OutlierRule, CustomRule

  time_health/
    checker.py        # Timestamp validation (gaps, duplicates, drift, DST)

  viz/
    rle.py            # Run-length encoding for quality segments
    timeline.py       # Plotly Gantt-style timeline figure builder
```

## How does data flow through a check?

Input DataFrame → validation/UTC normalize → rule resolution → per-tag vectorized rules → quality columns → `QCResult`.

1. **Input**: User provides a pandas DataFrame with timestamp, tag_name, and value columns
2. **Validation**: Column presence is checked, timestamps are normalized to UTC
3. **Rule Resolution**: Rules come from YAML file, programmatic list, or auto-configured defaults
4. **Per-Tag Processing**: Each tag's data is sorted by time, rules are applied vectorized
5. **Quality Assignment**: Each row gets quality (good/sus/bad) and quality_reasons columns
6. **QCResult**: Returned with the annotated DataFrame and downstream methods

## Why were these design decisions made?

The library prioritizes pandas integration, vectorized performance, three-level quality, worst-wins severity, and offline HTML reports.

### Pandas-Native

The library uses pandas DataFrames throughout, making it easy to integrate into existing data pipelines that already use pandas.

### Vectorized Rule Application

Rules are applied using vectorized numpy operations, not Python loops, for performance at scale.

### Three-Level Classification

Unlike binary pass/fail systems (Pecos, Great Expectations), `timeseries-qc` uses three levels: good, suspect, and bad. This gives more nuanced insight into data quality.

### Worst-Level Wins

When multiple rules fire for the same row, the worst classification wins. This ensures that any serious issue takes precedence over minor warnings.

### Offline-First

The HTML report export embeds all JavaScript and styling, making it viewable without internet access.

## FAQ

### Where is the public API defined?

`tsqc/__init__.py` exports `check()`, `QCResult`, and the rule classes.

### Where do YAML rules get parsed?

In `tsqc/config/yaml_parser.py`, which turns YAML into Rule objects.

### Why three quality levels instead of pass/fail?

`good` / `sus` / `bad` separates confirmed failures from values that need review, which is more useful for industrial sensor data.

### What does worst-wins mean in the pipeline?

If multiple rules flag a row, the worse level is kept (**bad > sus > good**).

### Are HTML reports offline-capable by design?

Yes. `export_report()` embeds Plotly JS and styles so reports work without a network.

## Next Steps

- [Rule Engine](rules.md) — how rules work
- [API Reference](api-reference.md) — complete method documentation
- [Contributing](contributing.md) — how to contribute to the library
