---
title: Installation — timeseries-qc
description: Install timeseries-qc via pip. Python 3.9+ required. Dependencies include pandas, plotly, and pyyaml.
---

# Installation

## Quick Install

```bash
pip install timeseries-qc
```

## Requirements

- **Python** 3.9 or later
- **pandas** >= 1.5
- **plotly** >= 5.0
- **pyyaml** >= 6.0

## Development Setup

```bash
git clone https://github.com/nagusubra/timeseries-qc.git
cd timeseries-qc
pip install -e ".[dev]"
```

This installs extra dependencies for testing and linting: `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, and `twine`.

## Verify Installation

```python
import tsqc
print(tsqc.__version__)
```

## Troubleshooting

If you encounter installation issues, see the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

- [Quickstart](quickstart.md) — run your first quality check in 5 lines
- [User Guide](user-guide.md) — full walkthrough with examples
