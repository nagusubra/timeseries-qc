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

## Lint & Type Check

```bash
ruff check tsqc/
mypy tsqc/
```

## Synthetic Data Generation

Test data generators live in `synthetic_data_generation/`. These are standalone scripts
that produce CSV files with engineered anomalies for testing the library. They are not
shipped with the PyPI package.

```bash
cd synthetic_data_generation
python generate_solar_data.py
```

## Branch Protection

The `main` branch is protected:
- All changes must go through a pull request
- At least one approving review from @nagusubra is required
- All CI checks must pass
- Branches must be up to date before merging
- Force pushes and branch deletions are blocked
- Linear history is enforced (no merge commits)

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
