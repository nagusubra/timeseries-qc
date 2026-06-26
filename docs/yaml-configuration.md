---
title: YAML Configuration — timeseries-qc
description: Configure timeseries-qc rules using YAML files. No Python required. Supports glob patterns for tag matching.
---

# YAML Configuration

You can define quality control rules in a plain YAML file — no Python required.

## Basic Structure

```yaml
# tsqc_rules.yaml
default_rules:
  - check: null
    level: bad
  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus
  - check: delta
    max_delta: 50.0
    level: sus

tag_rules:
  "FOREBAY.LEVEL":
    - check: range
      min: 900
      max: 1100
      level: bad
  "GENERATOR.*":
    - check: range
      min: 0
      max: 200
      level: bad
    - check: flatline
      window: 30min
      min_delta: 0.5
      level: sus
```

## Sections

### `default_rules`

Rules applied to **every** tag in the dataset. Each entry is a rule specification with a `check` type and optional parameters.

### `tag_rules`

Rules applied to **specific** tags only, identified by tag name or glob pattern.

## Supported Check Types

| Check | Parameters | Default Level |
|-------|-----------|---------------|
| `null` | none | `bad` |
| `flatline` | `window` (required), `min_delta`, `min_duration` | `sus` |
| `delta` | `min_delta`, `max_delta` (at least one required) | `sus` |
| `range` | `min`, `max` (at least one required) | `bad` |

## Glob Pattern Matching

Tag patterns support `*` and `?` wildcards via `fnmatch`:

| Pattern | Matches |
|---------|---------|
| `GENERATOR.*` | `GENERATOR.MW`, `GENERATOR.VAR`, etc. |
| `*.TEMP` | `REACTOR.TEMP`, `BOILER.TEMP`, etc. |
| `SENSOR?` | `SENSOR1`, `SENSORA`, etc. |

## Using YAML Rules

```python
result = tsqc.check(df, rules="tsqc_rules.yaml")
```

## Loading Rules

When you pass a YAML file path to `tsqc.check()`, the file is parsed and rules are applied per tag:

1. All `default_rules` are applied to every tag
2. Matching `tag_rules` are appended to the default rules
3. If no rules match a tag, the auto-configured defaults are used

## Next Steps

- [Rule Engine](rules.md) — how rules work
- [User Guide](user-guide.md) — walkthrough with examples
