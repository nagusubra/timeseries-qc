# `timeseries-qc` — Product Requirements Document

**Version:** 0.1 Draft  
**Owner:** Solo maintainer  
**Cadence:** Nights & weekends, ~15 hrs/month  
**Target:** v0.1.0 on PyPI in ~6 months  

---

## How to use this document with agentic coding tools

Each phase is a self-contained coding session scope. Start a new Claude Code / Cursor session per phase. Paste the **Session Brief** from that phase as your first prompt. Every function signature, file path, and acceptance criterion is explicit so the agent doesn't have to guess.

---

## 1. Project Identity

| Key | Value |
|-----|-------|
| PyPI package name | `timeseries-qc` |
| Python import name | `tsqc` |
| GitHub org/repo | `timeseries-qc/timeseries-qc` |
| License | MIT |
| Python support | 3.9, 3.10, 3.11, 3.12 |
| Primary DataFrame engine | pandas (v0.1); PySpark and Polars deferred |

---

## 2. Problem Statement

Every SCADA system, IoT pipeline, power generation historian, and API monitoring dataset has the same unsolved workflow:

> "I have a DataFrame with `timestamp`, `tag_name`, and `value` columns. I need to know *where* my data is bad, *why* it's bad, and I need to show that to an engineer or manager without writing 200 lines of custom code."

**What exists today and why it falls short:**

- **Pecos (Sandia Labs):** Binary pass/fail, maintenance mode since 2021, no timeline chart.
- **SaQC (Helmholtz UFZ):** Rich flagging engine but environmental-science API, no timeline chart, LGPL license.
- **EnviroDataQC:** Correct Good/Sus/Bad taxonomy but unmaintained, no visualization.
- **Great Expectations:** Not timeseries-native, no visualization, heavy install.

**The specific gap confirmed missing from the entire Python ecosystem as of June 2026:**  
A single `pip install` that (1) classifies rows as Good / Sus / Bad, (2) renders a multi-tag horizontal status timeline bar chart, and (3) accepts rules from a YAML file. Nothing outputs this chart (`plot_quality_timeline`) anywhere in open-source Python.

---

## 3. Goals and Non-Goals

### Goals for v0.1.0

- `tsqc.check(df)` adds a `quality` column (`"good"`, `"sus"`, `"bad"`) to any timeseries DataFrame in ≤5 lines.
- Four built-in rules cover ≥80% of real-world bad data: null, flatline, big delta, out-of-range.
- `result.plot()` renders a Plotly multi-tag horizontal status bar chart (Green/Yellow/Red).
- `result.summary()` returns a DataFrame of `%good`, `%sus`, `%bad` per tag.
- YAML config file lets non-coders set thresholds without writing Python.
- Timestamp health check: gaps, duplicates, non-monotonic index, DST ambiguity.
- Self-contained HTML export: `result.export_report("report.html")`.
- Test coverage ≥ 80%.
- `pip install timeseries-qc` works cleanly in under 10 seconds.

### Explicit Non-Goals for v0.1.0 (do not add these)

- PySpark or Polars support (deferred to v0.2 / v0.3)
- ML / anomaly detection (out of scope entirely until v1.0)
- A Streamlit or Dash web dashboard
- Real-time / streaming support
- Database connectors (InfluxDB, TimescaleDB — use existing drivers)
- LLM rule suggestion feature (deferred to v1.0)
- CLI tool (deferred to v0.2)

---

## 4. Core Data Contract

### Input DataFrame

The library accepts a pandas DataFrame with three columns. Column names are configurable but these are the defaults:

| Column | Default name | Type | Notes |
|--------|-------------|------|-------|
| Timestamp | `timestamp` | `datetime64[ns, UTC]`, tz-aware (any zone), or parseable string | **Tz-naive inputs raise `ValueError` unless `assume_tz` is passed to `check()`.** All timestamps are converted to UTC internally. The `.df` output always has UTC timestamps. |
| Tag name | `tag_name` | `str` | Identifies the sensor/signal. |
| Value | `value` | `float` or `int` | The sensor reading |

**Multi-tag input (long format — preferred):**
```
timestamp                  tag_name       value
2026-01-01 00:00:00+00:00  SENSOR1A.TNT    42.1
2026-01-01 00:00:00+00:00  SENSOR2A.TNT    87.3
2026-01-01 00:01:00+00:00  SENSOR1A.TNT    42.0
```

If your source data is tz-naive (e.g. a CSV exported from a local-time historian), pass `assume_tz` to `check()`:
```python
result = tsqc.check(df, assume_tz="America/Chicago")  # localize then convert to UTC
```

When `tag_name` column is absent, the library internally assigns the tag name `"default"`.

### Output DataFrame

The `check()` function returns a `QCResult` object. Its `.df` property is the original DataFrame with two columns added:

| Column | Type | Values |
|--------|------|--------|
| `quality` | `str` | `"good"`, `"sus"`, `"bad"` |
| `quality_reasons` | `str` | Pipe-delimited list of triggered rules, e.g. `"flatline\|range"`. Empty string for `"good"`. |

### Quality precedence rule

When multiple rules fire on the same row, the worst-level label wins:
```
"bad" > "sus" > "good"
```

---

## 5. Rule System Specification

### Abstract Rule interface

Every rule is a class that accepts a pandas Series and returns a boolean mask (`True` = row is flagged).

```python
# tsqc/rules/base.py

from abc import ABC, abstractmethod
import pandas as pd

class Rule(ABC):
    """Base class for all QC rules."""
    
    name: str          # Short identifier used in quality_reasons column
    level: str         # "sus" or "bad" — the quality label applied when rule fires
    
    def __init__(self, level: str = "bad"):
        assert level in ("sus", "bad"), f"level must be 'sus' or 'bad', got {level!r}"
        self.level = level
    
    @abstractmethod
    def check(self, series: pd.Series) -> pd.Series:
        """
        Args:
            series: A pandas Series of float values with a DatetimeIndex.
        Returns:
            Boolean Series. True = this row is flagged by this rule.
        """
        ...
```

### Built-in Rules

#### `NullRule`
```python
# Flags rows where value is NaN, None, or pd.NA.
# Default level: "bad"
# Parameters: none

class NullRule(Rule):
    name = "null"
    def check(self, series: pd.Series) -> pd.Series:
        return series.isna()
```

#### `FlatlineRule`
```python
# Flags rows where the value has not changed by more than min_delta
# within the preceding `window` time window.
# Default level: "sus"
# Parameters:
#   window: str — pandas offset alias, e.g. "1h", "30min", "15min"
#   min_delta: float — minimum required change to NOT be flagged. Default: 0.0

class FlatlineRule(Rule):
    name = "flatline"
    def __init__(self, window: str = "1h", min_delta: float = 0.0, level: str = "sus"):
        ...
    def check(self, series: pd.Series) -> pd.Series:
        # Implementation: rolling(window).std() <= min_delta
        # Handle edge case: window with fewer than 2 points → not flagged
        # Handle NaN: NaN rows should NOT be flagged by this rule (NullRule handles them)
        ...
```

#### `DeltaRule`
```python
# Flags rows where the absolute change from the previous row exceeds threshold.
# Useful for detecting sensor spikes or step changes.
# Default level: "sus"
# Parameters:
#   threshold: float — maximum allowed absolute change between consecutive readings
#   window: str — optional rolling window for computing delta (default: point-to-point diff)

class DeltaRule(Rule):
    name = "delta"
    def __init__(self, threshold: float, level: str = "sus"):
        ...
    def check(self, series: pd.Series) -> pd.Series:
        # Implementation: series.diff().abs() > threshold
        # First row always returns False (no previous row to diff against)
        # NaN rows: return False (NullRule handles them)
        ...
```

#### `RangeRule`
```python
# Flags rows where value is outside [min_val, max_val].
# Either bound can be None (open interval).
# Default level: "bad"
# Parameters:
#   min_val: float | None — lower bound (inclusive). None = no lower bound.
#   max_val: float | None — upper bound (inclusive). None = no upper bound.

class RangeRule(Rule):
    name = "range"
    def __init__(self, min_val: float | None = None, max_val: float | None = None, level: str = "bad"):
        ...
    def check(self, series: pd.Series) -> pd.Series:
        # NaN rows: return False (NullRule handles them)
        ...
```

#### `CustomRule`
```python
# Wraps an arbitrary user-supplied callable.
# Parameters:
#   fn: callable — accepts pd.Series, returns boolean pd.Series
#   name: str — label shown in quality_reasons column
#   level: str — "sus" or "bad"

class CustomRule(Rule):
    def __init__(self, fn: callable, name: str = "custom", level: str = "sus"):
        ...
    def check(self, series: pd.Series) -> pd.Series:
        return self.fn(series)
```

### Default rule set

When `tsqc.check(df)` is called with no `rules` argument, these defaults apply:
```python
DEFAULT_RULES = [
    NullRule(level="bad"),
    FlatlineRule(window="1h", min_delta=0.0, level="sus"),
    DeltaRule(threshold=3 * series.std(), level="sus"),  # 3-sigma spike
]
```
`DeltaRule` threshold uses 3× the series standard deviation computed at runtime per tag.

---

## 6. Public API Specification

### `tsqc.check()`

```python
def check(
    df: pd.DataFrame,
    *,
    time_col: str = "timestamp",
    tag_col: str | None = "tag_name",
    value_col: str = "value",
    rules: list[Rule] | str | None = None,  # list of Rule objects, path to YAML, or None for defaults
    quality_col: str = "quality",
    reasons_col: str = "quality_reasons",
    assume_tz: str | None = None,  # IANA timezone name, e.g. "UTC", "America/Chicago"
) -> QCResult:
    """
    Run quality checks on a timeseries DataFrame.
    
    Timestamp normalization policy:
      - Tz-aware input (any zone) is converted to UTC internally.
      - Tz-naive input raises ValueError unless assume_tz is provided.
      - When assume_tz is given, timestamps are localized to that zone then
        converted to UTC. Rows that cannot be localized unambiguously
        (e.g. DST fold) raise pytz.exceptions.AmbiguousTimeError with the
        offending timestamp in the message.
      - The .df output always carries UTC-aware timestamps.
    
    Returns a QCResult wrapping the input DataFrame with quality columns added.
    Does not modify the original DataFrame (returns a copy).
    
    Raises:
        ValueError: if required columns are missing
        ValueError: if time_col cannot be parsed as datetime
        ValueError: if time_col is tz-naive and assume_tz is not provided
        ValueError: if assume_tz is not a valid IANA timezone name
        pytz.exceptions.AmbiguousTimeError: if a timestamp falls in a DST fold
            and cannot be resolved (surfaces the source-system ambiguity explicitly)
        pytz.exceptions.NonExistentTimeError: if a timestamp falls in a DST gap
            (spring-forward hour that does not exist in wall-clock time)
        FileNotFoundError: if rules is a string path that does not exist
    """
```

### `QCResult` class

```python
class QCResult:
    @property
    def df(self) -> pd.DataFrame:
        """The original DataFrame with quality and quality_reasons columns appended."""
    
    def plot(
        self,
        tags: list[str] | None = None,      # None = all tags
        start: str | None = None,           # ISO datetime string, e.g. "2026-05-01"
        end: str | None = None,             # ISO datetime string
        title: str = "Data Quality Timeline",
        height: int = 400,                  # Plotly figure height in px
        show_summary_bar: bool = True,      # % good/sus/bad bar below chart
    ) -> plotly.graph_objects.Figure:
        """
        Returns a Plotly Figure object (not displayed — caller does fig.show() or result.plot().show()).
        The chart is a horizontal Gantt-style timeline with one row per tag.
        Color scheme: good=#008000 (green), sus=#FFFF00 (yellow), bad=#FF0000 (red).
        Tooltip on hover: tag name, start time, end time, duration, quality level.
        """
    
    def summary(self) -> pd.DataFrame:
        """
        Returns a DataFrame with one row per tag:
        Columns: tag_name, total_rows, pct_good, pct_sus, pct_bad, n_good, n_sus, n_bad
        Sorted by pct_bad descending.
        """
    
    def check_timestamps(
        self,
        expected_freq: str | None = None,   # e.g. "1min", "5min". None = auto-infer.
        freq_tolerance: float = 0.1,        # fraction of expected freq before flagging drift
    ) -> pd.DataFrame:
        """
        Returns a DataFrame of timestamp anomalies with columns:
        tag_name, issue_type, timestamp, description, severity
        
        issue_type values: "gap", "duplicate", "non_monotonic", "freq_drift", "dst_ambiguous"
        severity values: "warning", "error"
        
        Returns empty DataFrame if no issues found.
        """
    
    def export_report(
        self,
        path: str,                           # File path, e.g. "report.html"
        title: str = "Data Quality Report",
    ) -> None:
        """
        Writes a self-contained HTML file with:
        - Embedded Plotly timeline chart (no external CDN required)
        - Summary table per tag
        - Timestamp health issues table (if any)
        - Metadata: run timestamp, number of tags, number of rows, rule config used
        """
```

### 5-line usage target

The following must work for UTC-stamped data with no additional configuration:

```python
import tsqc
import pandas as pd

df = pd.read_csv("sensor_data.csv")   # columns: timestamp, tag_name, value
result = tsqc.check(df, assume_tz="UTC")  # assume_tz required for tz-naive CSVs
result.plot().show()
```

If the CSV already contains tz-aware timestamps (e.g. ISO 8601 with `+00:00`), `assume_tz` can be omitted.

---

## 7. YAML Config Specification

### File format

```yaml
# tsqc_rules.yaml

# Rules applied to every tag unless overridden
default_rules:
  - check: null
    level: bad

  - check: flatline
    window: 1h
    min_delta: 0.001
    level: sus

  - check: delta
    threshold: 50.0
    level: sus

# Tag-specific rules (merged with / override default_rules per tag)
tag_rules:
  SENSOR1A.TNT:
    - check: range
      min: 0
      max: 500
      level: bad

  "TI*.PNT":           # Glob patterns supported
    - check: range
      min: 50
      max: 250
      level: bad
    - check: flatline
      window: 30min
      level: sus
```

### YAML merge behavior

1. `default_rules` apply to all tags.
2. `tag_rules` entries *add* rules on top of `default_rules` for matching tags.
3. If a tag matches multiple glob patterns, all matching rules are combined.
4. To suppress a default rule for a specific tag, use `override: true` in the tag block (deferred to v0.2 — document as known limitation for v0.1).

### YAML usage

```python
result = tsqc.check(df, rules="tsqc_rules.yaml")
```

### Validation and error messages

The YAML parser must produce actionable error messages. Do not let PyYAML raw errors bubble up.

```
# Good error message:
ValueError: Rule at default_rules[1]: 'window' is required for check: flatline.
  Got keys: ['check', 'level']. 
  Example: {check: flatline, window: 1h, min_delta: 0.001, level: sus}

# Not acceptable:
KeyError: 'window'
```

---

## 8. Visualization Specification

### The run-length encoding transform

This is the intellectual core of the library. It must live in `tsqc/viz/rle.py`.

```python
def encode_quality_runs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a row-per-observation DataFrame into a segment-per-run DataFrame.
    
    Input columns: timestamp, tag_name, quality
    Output columns: tag_name, quality, start, end, duration_seconds
    
    A "run" is a maximal sequence of consecutive rows for the same tag
    with the same quality label.
    
    Example:
    Input:
        timestamp           tag_name    quality
        2026-01-01 00:00   PUMP_A      good
        2026-01-01 00:01   PUMP_A      good
        2026-01-01 00:02   PUMP_A      bad
        2026-01-01 00:03   PUMP_A      bad
    
    Output:
        tag_name  quality  start               end                 duration_seconds
        PUMP_A    good     2026-01-01 00:00    2026-01-01 00:02    120.0
        PUMP_A    bad      2026-01-01 00:02    2026-01-01 00:04    120.0
    
    Note: `end` of a segment is the start of the next segment, or
    (last_timestamp + median_interval) for the final segment.
    """
```

### Chart specification

The Plotly chart produced by `result.plot()` must meet these requirements:

- **Chart type:** `plotly.express.timeline()` (Gantt mode) with `x_start="start"`, `x_end="end"`, `y="tag_name"`, `color="quality"`
- **Color map:** `{"good": "#008000", "sus": "#FFFF00", "bad": "#FF0000"}`
- **Y-axis:** Tags ordered by `pct_bad` descending (worst tags at top)
- **Hover tooltip:** Shows `tag_name`, `quality`, `start`, `end`, `duration` (human-readable, e.g. "2h 15m")
- **Summary bar (optional, `show_summary_bar=True`):** A stacked horizontal bar below the timeline showing overall % good/sus/bad per tag. Use a second subplot via `plotly.subplots.make_subplots`.
- **Figure height:** `height` parameter (default 400px), adjusted upward by 30px per tag automatically if more than 10 tags.
- **No external resources:** The figure must be renderable offline (use `include_plotlyjs='cdn'` is NOT acceptable; use `include_plotlyjs=True` for the export, or rely on the existing Plotly JS in Jupyter for `.show()`).

---

## 9. Timestamp Health Specification

`result.check_timestamps()` must detect and report these issue types:

| issue_type | Detection logic | severity |
|-----------|-----------------|----------|
| `gap` | Interval between consecutive timestamps for a tag exceeds `2 × expected_freq` | `warning` if < 1 hr, `error` if ≥ 1 hr |
| `duplicate` | Two or more rows share the same timestamp for the same tag | `error` |
| `non_monotonic` | A timestamp is earlier than the preceding timestamp for the same tag | `error` |
| `freq_drift` | Median interval for a sliding window deviates > `freq_tolerance` from `expected_freq` | `warning` |
| `dst_ambiguous` | A UTC-offset shift of exactly ±1 hour is detected in the data | `warning` |

**Auto-infer expected_freq:** When `expected_freq=None`, compute the most common interval between consecutive timestamps per tag using `pd.Series.mode()` on the diff. If mode cannot be computed (e.g. fewer than 3 rows), skip frequency-based checks and note in the output.

**DST detection — localization-error approach (replaces calendar heuristic):**

Because `check()` normalizes all input to UTC, DST ambiguity is surfaced *at ingestion time* rather than inside `check_timestamps()`. The normalization step in `checker.py` calls `pd.DatetimeIndex.tz_localize(assume_tz, ambiguous='raise', nonexistent='raise')` which raises deterministically when a wall-clock time is ambiguous (fall-back fold) or non-existent (spring-forward gap). These are the only reliable signals — a calendar heuristic cannot be globally correct across all IANA zones.

Because all `.df` timestamps are UTC by the time `check_timestamps()` runs, this method does **not** need to re-detect DST. Instead it reports `dst_ambiguous` rows that were flagged and stored in the QCResult metadata during the normalization step. If `assume_tz` was not provided (input was already tz-aware or UTC), no DST flags are possible and the column will be empty.

Consequently, the legacy calendar-Sunday heuristic and the `tz-canary` optional integration are **removed**. The `tz` optional dependency group in §11 is retired.

**Normalization error handling in `check()`:**
- `AmbiguousTimeError` → store the offending timestamp(s) in QCResult metadata with `issue_type="dst_ambiguous"`, `severity="warning"`. Continue processing remaining rows using `ambiguous='NaT'` on the second pass, then flag those NaT timestamps via `NullRule`.
- `NonExistentTimeError` → store as `issue_type="gap"`, `severity="warning"` (the wall-clock gap is real — that hour never existed). Use `nonexistent='NaT'` on second pass, same NullRule treatment.

---

## 10. Package Structure

```
timeseries-qc/                  ← GitHub repo root
├── tsqc/
│   ├── __init__.py             ← Public exports: check, QCResult, NullRule, FlatlineRule,
│   │                              DeltaRule, RangeRule, CustomRule
│   ├── checker.py              ← check() function implementation
│   ├── result.py               ← QCResult class
│   ├── rules/
│   │   ├── __init__.py         ← exports all Rule classes
│   │   ├── base.py             ← abstract Rule class
│   │   └── builtins.py         ← NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule
│   ├── config/
│   │   ├── __init__.py
│   │   └── yaml_parser.py      ← YAML file → list[Rule]
│   ├── viz/
│   │   ├── __init__.py
│   │   ├── rle.py              ← encode_quality_runs() function
│   │   └── timeline.py         ← build_timeline_figure() function
│   └── time_health/
│       ├── __init__.py
│       └── checker.py          ← timestamp issue detection
├── tests/
│   ├── conftest.py             ← pytest fixtures (sample DataFrames)
│   ├── test_rules.py
│   ├── test_checker.py
│   ├── test_yaml_parser.py
│   ├── test_viz.py
│   ├── test_time_health.py
│   └── fixtures/
│       ├── sample_single_tag.csv
│       ├── sample_multi_tag.csv
│       └── sample_rules.yaml
├── examples/
│   ├── power_generation.ipynb
│   ├── scada_tags.ipynb
│   └── api_uptime.ipynb
├── docs/                       ← MkDocs site (configured but content deferred to v0.1 release)
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
└── .github/
    └── workflows/
        └── ci.yml              ← pytest + ruff + mypy on push
```

---

## 11. Dependencies

### Production (required)

```toml
[project]
dependencies = [
  "pandas>=1.5",
  "plotly>=5.0",
  "pyyaml>=6.0",
]
```

### Optional

```toml
[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "black", "ruff", "mypy"]
```

**Constraint:** Never add scipy, sklearn, numpy (it comes with pandas anyway), or any ML library to production dependencies. Four production deps maximum at v0.1.

**Note:** The `tz-canary` optional dependency originally planned for DST detection has been removed. DST ambiguity is now handled deterministically via `pd.DatetimeIndex.tz_localize()` during timestamp normalization in `check()`. `pytz` is already bundled with pandas; no additional dependency is needed. On Python 3.9+ the stdlib `zoneinfo` module is available as an alternative backend but pandas uses `pytz` by default — no action required.

---

## 12. Phased Build Plan

### Phase 0 — Core Rules Engine  
**Target:** Month 1–2 (~25 hrs)  
**Done when:** `tsqc.check(df)` runs on real SCADA data and returns a DataFrame with a correct `quality` column.

**Agentic session brief:**
```
Build the timeseries-qc Python package Phase 0.
Repo: timeseries-qc. Python import name: tsqc.

Tasks:
1. Create pyproject.toml with name=timeseries-qc, version=0.0.1, requires-python=">=3.9",
   dependencies=["pandas>=1.5", "plotly>=5.0"]. No build system except setuptools.
2. Create package structure: tsqc/__init__.py, tsqc/rules/base.py, 
   tsqc/rules/builtins.py, tsqc/checker.py, tsqc/result.py
3. Implement Rule abstract base class in tsqc/rules/base.py per PRD §5.
4. Implement NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule in 
   tsqc/rules/builtins.py per PRD §5.
5. Implement check() in tsqc/checker.py per PRD §6, including the assume_tz
   normalization logic:
   a. If time_col is already tz-aware, convert to UTC with .dt.tz_convert("UTC").
   b. If time_col is tz-naive and assume_tz is None, raise ValueError with message:
      "Column '{time_col}' has no timezone info. Pass assume_tz='UTC' if your data
      is UTC, or assume_tz='America/Chicago' for local time."
   c. If assume_tz is provided, attempt tz_localize(assume_tz, ambiguous='raise',
      nonexistent='raise'). On AmbiguousTimeError or NonExistentTimeError, re-run
      with ambiguous='NaT' / nonexistent='NaT', store the NaT rows in QCResult
      metadata for check_timestamps() to surface later, then convert to UTC.
   d. Validate that assume_tz is a recognized IANA zone; raise ValueError otherwise.
6. Implement QCResult with .df property and .summary() method in tsqc/result.py per PRD §6.
7. Export check, QCResult, NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule 
   from tsqc/__init__.py.
8. Create tests/conftest.py with two pytest fixtures:
   - single_tag_df: 100-row DataFrame with timestamp (1-min intervals, UTC-aware),
     value (sin wave + noise) with 5 injected NaNs, 10 flatline rows, 2 spike rows.
   - multi_tag_df: same structure but 3 tags: "TAG_A", "TAG_B", "TAG_C"
   - All fixture timestamps must be UTC-aware (use pd.date_range(..., tz="UTC")).
9. Create tests/test_rules.py testing each rule in isolation:
   - NullRule: flags NaN rows, does not flag valid rows
   - FlatlineRule: flags flatline window, does not flag normally varying rows
   - DeltaRule: flags spike rows, does not flag gradual changes
   - RangeRule: flags out-of-range rows, does not flag in-range rows
   - Test precedence: "bad" beats "sus" beats "good"
10. Create tests/test_checker.py testing check() end-to-end:
    - Multi-tag input
    - quality_reasons column contains pipe-delimited rule names
    - Custom rules list passed to check()
    - Missing required columns raise ValueError with clear message
    - Tz-naive input without assume_tz raises ValueError
    - Tz-naive input with assume_tz="UTC" succeeds and output is UTC-aware
    - Tz-aware non-UTC input is converted to UTC in output
    - Invalid assume_tz string raises ValueError
11. Create .github/workflows/ci.yml: pytest + ruff check on push to main and PRs.
12. Create a basic README.md with the 5-line example.

Quality bar: all tests pass, ruff passes, coverage ≥ 75% on tsqc/ directory.
```

**Acceptance criteria:**
- [ ] `pip install -e .` succeeds in a fresh virtualenv
- [ ] `import tsqc; result = tsqc.check(df); result.df.columns` includes `quality` and `quality_reasons`
- [ ] `quality` values are only `"good"`, `"sus"`, `"bad"`
- [ ] All `test_rules.py` and `test_checker.py` tests pass
- [ ] `ruff check tsqc/` passes with zero errors
- [ ] `pytest --cov=tsqc` shows ≥ 75% coverage

---

### Phase 1 — YAML Config Layer  
**Target:** Month 3 (~20 hrs)  
**Done when:** An SME can edit `rules.yaml` and run checks without writing Python.

**Agentic session brief:**
```
Add YAML config support to timeseries-qc.

Prerequisite: Phase 0 is complete and all tests pass.

Tasks:
1. Add pyyaml>=6.0 to pyproject.toml dependencies.
2. Create tsqc/config/yaml_parser.py implementing parse_yaml_rules(path: str) -> list[Rule].
   - Validate YAML structure; raise ValueError with actionable messages (see PRD §7).
   - Support default_rules and tag_rules sections.
   - Support glob patterns in tag_rules keys (use fnmatch.fnmatch).
   - Return a dict: {"default": list[Rule], "tags": dict[str, list[Rule]]}
3. Update tsqc/checker.py: when rules is a str, call parse_yaml_rules(rules).
   When applying rules to multi-tag data, merge default rules + tag-specific rules per tag.
4. Create tests/fixtures/sample_rules.yaml with a realistic multi-tag config.
5. Create tests/test_yaml_parser.py:
   - Valid YAML parses to correct Rule objects
   - Glob pattern matching works ("TI*.PNT" matches "SENSOR2A.TNT", not "SENSOR1A.TNT")
   - Missing required field raises ValueError with rule index and helpful hint
   - Unknown check name raises ValueError naming the bad check
   - Empty YAML file raises ValueError
   - rules="rules.yaml" path passed to check() triggers YAML parsing end-to-end
6. Create tests/fixtures/sample_rules.yaml and tests/fixtures/sample_multi_tag.csv.

Quality bar: all tests pass, coverage ≥ 80%.
```

**Acceptance criteria:**
- [ ] `tsqc.check(df, rules="rules.yaml")` works end-to-end
- [ ] Bad YAML produces a `ValueError` with the field name, rule index, and a fix hint
- [ ] Glob patterns match correctly against tag names
- [ ] All tests pass with ≥ 80% coverage

---

### Phase 2 — Timeline Visualization  
**Target:** Month 4 (~20 hrs)  
**Done when:** `result.plot().show()` renders the multi-tag status bar chart.

**Agentic session brief:**
```
Add the Plotly quality timeline chart to timeseries-qc.

Prerequisite: Phases 0 and 1 complete.

Tasks:
1. Create tsqc/viz/rle.py implementing encode_quality_runs() per PRD §8.
   - Handles multi-tag DataFrames.
   - Computes end timestamp as start of next segment, or last_timestamp + median_interval for final row.
   - Computes duration_seconds column.
2. Create tsqc/viz/timeline.py implementing build_timeline_figure(segments_df, ...) per PRD §8.
   - Uses plotly.express.timeline() with color_discrete_map.
   - Tags ordered by pct_bad descending on Y-axis.
   - Hover tooltip shows tag_name, quality, start, end, duration (human-readable).
   - When show_summary_bar=True, add a stacked bar subplot below timeline.
   - Figure height auto-scales with number of tags.
3. Add .plot() method to QCResult in tsqc/result.py.
   - Calls encode_quality_runs() then build_timeline_figure().
   - Returns a plotly.graph_objects.Figure (not .show() — caller decides).
4. Create tests/test_viz.py:
   - encode_quality_runs() produces correct segments for a known input
   - Consecutive same-quality rows merge into one segment
   - Multi-tag segments are independent (TAG_A and TAG_B runs don't merge)
   - Duration is correctly computed for last segment
   - build_timeline_figure() returns a plotly Figure without raising
   - Tags filtered by tags= parameter appear/disappear correctly
5. Create examples/power_generation.ipynb demonstrating the chart on synthetic power gen data.

Quality bar: all tests pass. Running result.plot().show() in Jupyter renders the chart visually.
```

**Acceptance criteria:**
- [ ] `result.plot()` returns a `plotly.graph_objects.Figure`
- [ ] Chart has one horizontal row per tag
- [ ] Colors are green (#008000), yellow (#FFFF00), red (#FF0000)
- [ ] Tags are ordered worst-first (highest `pct_bad` at top)
- [ ] Hover tooltip shows tag, quality level, start, end, duration
- [ ] `result.plot(tags=["TAG_A"])` shows only TAG_A
- [ ] `result.plot(start="2026-01-01", end="2026-01-02")` clips the time range
- [ ] All tests pass

---

### Phase 3 — Timestamp Health Check  
**Target:** Month 5 (~15 hrs)  
**Done when:** `result.check_timestamps()` returns a structured anomaly report.

**Agentic session brief:**
```
Add timestamp health checking to timeseries-qc.

Prerequisite: Phases 0–2 complete.

Tasks:
1. Create tsqc/time_health/checker.py implementing check_timestamps() per PRD §9.
   - Detects: gap, duplicate, non_monotonic, freq_drift, dst_ambiguous
   - Auto-infers expected_freq from data when not provided
   - DST detection: reads dst_ambiguous rows from QCResult metadata populated
     during check() normalization (no calendar heuristic, no tz-canary).
     If input was already UTC-aware, no DST rows are possible.
   - Returns DataFrame with: tag_name, issue_type, timestamp, description, severity
   - Returns empty DataFrame (not None) when no issues found
2. Wire check_timestamps() into QCResult.check_timestamps() method.
3. Create tests/test_time_health.py:
   - Gap detection: inject a 2-hour gap (UTC), verify it appears with severity "error"
   - Duplicate detection: inject duplicate row, verify flagged
   - Non-monotonic: inject out-of-order timestamp, verify flagged
   - Freq drift: inject section with 2x normal interval, verify flagged
   - DST ambiguous: call check() with assume_tz="America/Chicago" and a DataFrame
     containing 2026-11-01 01:30 (falls in DST fold); verify dst_ambiguous rows
     appear in check_timestamps() output with severity "warning"
   - DST spring-forward: call check() with a timestamp in the spring-forward gap
     (2026-03-08 02:30 US/Eastern); verify issue_type="gap" with severity "warning"
   - Clean UTC data: returns empty DataFrame
   - Multi-tag: gaps in TAG_A do not bleed into TAG_B results
4. Add check_timestamps() output to the examples notebook.

Quality bar: all tests pass. Real SCADA data with a known DST spring-forward gap correctly flagged.
```

**Acceptance criteria:**
- [ ] `result.check_timestamps()` returns a DataFrame with the correct columns
- [ ] Each issue type has at least one passing test
- [ ] Clean data returns empty DataFrame (not empty list, not None)
- [ ] The function does not raise on DataFrames with fewer than 3 rows per tag
- [ ] All tests pass

---

### Phase 4 — HTML Export and v0.1.0 Release  
**Target:** Month 6 (~20 hrs)  
**Done when:** `pip install timeseries-qc` works from PyPI and `result.export_report()` produces a working HTML file.

**Agentic session brief:**
```
Finalize timeseries-qc for v0.1.0 PyPI release.

Prerequisite: Phases 0–3 complete, all tests passing.

Tasks:
1. Implement result.export_report(path, title) in tsqc/result.py:
   - Writes a self-contained HTML file (no external CDN calls at render time)
   - Sections: header with title + metadata, embedded Plotly chart, summary table, 
     timestamp health issues table (if any)
   - Use plotly.io.to_html(fig, full_html=False, include_plotlyjs=True) for embedding
   - Summary and issues tables: plain HTML tables with basic inline CSS (no external CSS)
2. Bump version to 0.1.0 in pyproject.toml.
3. Add classifiers and metadata to pyproject.toml:
   - Programming Language :: Python :: 3
   - License :: OSI Approved :: MIT License
   - Topic :: Scientific/Engineering :: Information Analysis
   - keywords = ["timeseries", "data quality", "QC", "SCADA", "IoT", "pandas"]
4. Write complete README.md:
   - One-paragraph description
   - Feature list (5–7 bullets)
   - Installation: pip install timeseries-qc
   - 5-line quickstart
   - YAML config example (10 lines)
   - Link to examples/ notebooks
   - Comparison table (vs Pecos, SaQC, GE) — one paragraph not a full table
   - License badge + PyPI badge
5. Write CONTRIBUTING.md: how to set up dev environment, run tests, submit a PR.
6. Write tests/test_export.py: export_report() creates a file, file is valid HTML, 
   file contains the word "quality" and at least one tag name.
7. Run full test suite, ensure ≥ 80% coverage.
8. Build with: python -m build; check dist/ contains .whl and .tar.gz.
9. Publish to TestPyPI first: twine upload --repository testpypi dist/*
   Verify: pip install --index-url https://test.pypi.org/simple/ timeseries-qc
10. If TestPyPI passes, publish to PyPI: twine upload dist/*

Quality bar: pip install timeseries-qc && python -c "import tsqc; print(tsqc.__version__)" 
prints "0.1.0" from a fresh environment.
```

**Acceptance criteria:**
- [ ] `result.export_report("report.html")` writes a valid HTML file
- [ ] HTML file opens in browser and shows chart and summary table
- [ ] `pip install timeseries-qc` works from PyPI
- [ ] `import tsqc; tsqc.__version__` returns `"0.1.0"`
- [ ] GitHub Actions CI is green on main
- [ ] Test coverage ≥ 80%
- [ ] README renders correctly on PyPI and GitHub

---

## 13. Testing Strategy

### Test data fixtures

Create these as CSV files in `tests/fixtures/`:

**`sample_single_tag.csv`** — 200 rows, 1-minute intervals, single tag:
- Rows 0–49: normal sinusoidal data
- Rows 50–54: NaN values (null)
- Rows 55–74: flatlined at 42.0 (flatline)
- Rows 75–76: spike (value jumps to 500 then back)
- Rows 77–199: normal data
- Timestamps must be UTC-aware ISO 8601 strings (e.g. `2026-01-01T00:00:00+00:00`) so that `tsqc.check(df)` can be called without `assume_tz`.

**`sample_multi_tag.csv`** — 200 rows × 3 tags (long format), same patterns per tag. Same UTC timestamp requirement.

### Coverage targets

| Module | Target |
|--------|--------|
| `tsqc/rules/builtins.py` | 95% |
| `tsqc/checker.py` | 90% |
| `tsqc/config/yaml_parser.py` | 90% |
| `tsqc/viz/rle.py` | 90% |
| `tsqc/viz/timeline.py` | 70% (Plotly internals hard to unit test) |
| `tsqc/time_health/checker.py` | 85% |
| Overall | ≥ 80% |

### Test naming convention

```python
def test_<rule_or_function>_<scenario>():
    # e.g.:
    def test_flatline_rule_flags_constant_window():
    def test_flatline_rule_does_not_flag_nan_rows():
    def test_check_single_tag_no_tag_col():
    def test_yaml_parser_missing_window_raises_valueerror():
```

---

## 14. Known Limitations for v0.1.0

Document these explicitly in the README so users don't file bugs:

1. **Pandas only.** PySpark and Polars support are deferred to v0.2 and v0.3 respectively.
2. **No YAML override of default rules.** Tag-specific rules add to, not replace, default rules. Full override deferred to v0.2.
3. **Visualization requires Plotly ≥ 5.0.** Matplotlib output not supported.
4. **`DeltaRule` is point-to-point diff only.** Rolling-window delta deferred to v0.2.
5. **No CLI.** Command-line tool deferred to v0.2.
6. **Memory bound.** Tested up to ~5M rows in pandas on a 16GB machine. Larger datasets need chunking (user responsibility in v0.1).
7. **No DST repair.** The timestamp checker detects and surfaces DST ambiguity and spring-forward gaps (as NaT rows flagged by NullRule), but does not attempt to resolve them. The caller must decide the correct interpretation.
8. **Tz-naive input requires `assume_tz`.** Passing a DataFrame with tz-naive timestamps without `assume_tz` raises `ValueError`. This is intentional — silent UTC assumption was rejected to avoid masking DST bugs in source data.

---

## 15. Deferred Features Log

Track these for future phases. Do not implement in v0.1.

| Feature | Target version | Notes |
|---------|----------------|-------|
| PySpark adapter | v0.2 | Abstract via DataFrame Protocol |
| Polars adapter | v0.3 | After PySpark is proven |
| CLI (`tsqc check data.csv`) | v0.2 | Use Click or Typer |
| YAML tag rule override (not just add) | v0.2 | Needs `override: true` syntax |
| Rolling-window delta rule | v0.2 | Current is point-to-point only |
| LLM rule suggestion (`tsqc.suggest_rules()`) | v1.0 | Requires Anthropic/OpenAI API key |
| ML anomaly detection layer | v1.0 | Would use Merlion or Prophet |
| Bokeh/matplotlib output | v1.0 | Only Plotly in v0.1 |
| Real-time / streaming | not planned | Different architecture entirely |

---

## 16. Open Questions

These need decisions before Phase 1 or Phase 2 starts:

| # | Question | Decision needed by |
|---|----------|-------------------|
| 1 | Should `check()` raise on NaN timestamps, or silently drop those rows with a warning? | Before Phase 0 |
| 2 | Should the YAML `default_rules` section be optional (so a minimal YAML with only `tag_rules` is valid)? | Before Phase 1 |
| 3 | For `FlatlineRule`, should the first N rows in the window (where the window isn't full yet) be flagged or skipped? | Before Phase 0 |
| 4 | Should `result.plot()` call `.show()` automatically (like pandas `.plot()`) or return the Figure silently? PRD currently says return silently. | Before Phase 2 |
| 5 | What is the PyPI package owner email / GitHub org URL? (Needed for pyproject.toml) | Before Phase 4 |
| 6 | ~~Should the input timestamp be UTC-only or should local time be accepted?~~ **Resolved — see §17.** | Resolved |

---

## 17. Recommended Decision for Q3, Q4, and Q6 (from Open Questions)

- **Q3 (FlatlineRule warm-up):** Skip (return `False`) for rows where the rolling window is not yet full. This avoids false positives at the start of a dataset and is the behavior engineers expect.
- **Q4 (`result.plot()`):** Return the Figure silently. Callers who want auto-display can do `result.plot().show()`. This is consistent with Plotly's own API and works better in non-Jupyter contexts.
- **Q6 (Timestamp timezone policy):** Reject tz-naive input unless `assume_tz` is explicitly provided. All internal processing and output uses UTC. Rationale:
  - Silent UTC assumption was considered and rejected. Real-world SCADA historians export in local wall-clock time; silently treating that as UTC would corrupt delta and gap calculations by a DST offset.
  - Forcing the caller to name the timezone makes the data's provenance explicit and auditable.
  - tz-aware non-UTC inputs (e.g. `America/Chicago`) are accepted and converted to UTC internally. The caller sees UTC in `.df` and does not need to think about offsets after that point.
  - DST ambiguity and spring-forward gaps are detected deterministically via `pd.DatetimeIndex.tz_localize()` during normalization — no calendar heuristics, no third-party library required.
  - The `tz-canary` optional dependency is retired. The `[tz]` extras group is removed from `pyproject.toml`.

---

*End of PRD v0.1 Draft*
