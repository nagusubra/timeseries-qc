---
title: Architecture — timeseries-qc Internal Design
description: How timeseries-qc is structured internally — package organization, data flow, rule execution pipeline, and design decisions.
---

# Architecture

## Package Structure

```
tsqc/
  __init__.py        # Public API: check(), QCResult, rule classes
  checker.py          # Core check() function and rule application
  result.py           # QCResult class with all downstream methods

  config/
    yaml_parser.py    # Parse YAML rule files into Rule objects

  rules/
    base.py           # Abstract Rule base class
    builtins.py       # NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule

  time_health/
    checker.py        # Timestamp validation (gaps, duplicates, drift, DST)

  viz/
    rle.py            # Run-length encoding for quality segments
    timeline.py       # Plotly Gantt-style timeline figure builder
```

## Data Flow

1. **Input**: User provides a pandas DataFrame with timestamp, tag_name, and value columns
2. **Validation**: Column presence is checked, timestamps are normalized to UTC
3. **Rule Resolution**: Rules come from YAML file, programmatic list, or auto-configured defaults
4. **Per-Tag Processing**: Each tag's data is sorted by time, rules are applied vectorized
5. **Quality Assignment**: Each row gets quality (good/sus/bad) and quality_reasons columns
6. **QCResult**: Returned with the annotated DataFrame and downstream methods

## Design Decisions

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

## Next Steps

- [Rule Engine](rules.md) — how rules work
- [API Reference](api-reference.md) — complete method documentation
- [Contributing](contributing.md) — how to contribute to the library
