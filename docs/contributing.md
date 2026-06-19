---
title: Contributing — timeseries-qc
description: How to contribute to the timeseries-qc library — development setup, testing, and pull request guidelines.
---

# Contributing

## Development Setup

```bash
git clone https://github.com/your-org/timeseries-qc.git
cd timeseries-qc
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/
```

## Adding a New Rule

1. Create a class in `tsqc/rules/` that extends `Rule`
2. Implement `apply(tag_df: pd.DataFrame) -> RuleResult`
3. Register in `tsqc/rules/__init__.py`
4. Add tests in `tests/test_rules.py`

## Code Style

- Follow PEP 8
- Type hints for all public functions
- Docstrings for all public classes and methods

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## Reporting Issues

Report bugs and feature requests at:

[https://github.com/nagusubra/timeseries-qc/issues](https://github.com/nagusubra/timeseries-qc/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Next Steps

- [Roadmap](roadmap.md) — planned features
- [Architecture](architecture.md) — internal design
- [Changelog](changelog.md) — version history
