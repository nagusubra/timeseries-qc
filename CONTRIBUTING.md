# Contributing to timeseries-qc

## Dev Setup

```bash
git clone https://github.com/timeseries-qc/timeseries-qc.git
cd timeseries-qc
pip install -e ".[dev]"
```

## Running Tests

```bash
# All tests with coverage
pytest --cov=tsqc --cov-report=term-missing

# Single module
pytest tests/test_rules.py -v

# Coverage must be ≥ 80%
pytest --cov=tsqc --cov-fail-under=80
```

## Lint

```bash
ruff check tsqc/
```

## Submitting a PR

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Write tests for any new behaviour — coverage must not drop below 80%
3. Ensure `ruff check tsqc/` passes with zero errors
4. Open a PR against `main` with a description of what and why
5. CI (pytest + ruff) must be green before merge

## Adding a New Rule

1. Subclass `Rule` in `tsqc/rules/builtins.py`
2. Set `name` (str) and implement `check(series) -> bool Series`
3. Export from `tsqc/rules/__init__.py` and `tsqc/__init__.py`
4. Add a `check: <name>` handler in `tsqc/config/yaml_parser.py`
5. Write unit tests in `tests/test_rules.py`
