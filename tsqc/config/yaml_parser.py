"""Parse a YAML rule config file into Rule objects."""

from __future__ import annotations

import difflib
import fnmatch
from pathlib import Path
from typing import Any

import yaml

from tsqc.rules.base import Rule
from tsqc.rules.builtins import (
    DeltaRule,
    FlatlineRule,
    NullRule,
    OutlierRule,
    RangeRule,
)

_KNOWN_CHECKS = {"null", "flatline", "delta", "range", "outlier"}
_VALID_QUALITY_LEVELS = {"good", "sus", "bad"}
_ALLOWED_TOP_LEVEL_KEYS = {"default_rules", "tag_rules", "quality_map"}
_KNOWN_CHECK_PARAMS: dict[str, set[str]] = {
    "null": {"check", "level"},
    "flatline": {"check", "window", "min_delta", "min_duration", "level"},
    "delta": {"check", "min_delta", "max_delta", "level"},
    "range": {"check", "min", "max", "level"},
    "outlier": {"check", "method", "threshold", "window", "min_periods", "level"},
}
_RULE_REQUIRED_PARAMS: dict[str, set[str]] = {
    "flatline": {"window"},
}


def _fuzzy_hint(bad_key: str, known_keys: set[str]) -> str:
    """Return a 'Did you mean X?' hint, or empty string."""
    matches = difflib.get_close_matches(bad_key, known_keys, n=1, cutoff=0.6)
    return f" Did you mean {matches[0]!r}?" if matches else ""


def _validate_yaml_structure(raw: dict, path: str) -> list[str]:
    """Collect ALL structural errors in the parsed YAML before rule construction.

    Returns a list of human-readable error messages (empty = valid).
    """
    errors: list[str] = []

    # --- 1. Unknown top-level keys ---
    given_keys = set(raw.keys())
    unknown = given_keys - _ALLOWED_TOP_LEVEL_KEYS
    for key in sorted(unknown):
        hint = _fuzzy_hint(key, _ALLOWED_TOP_LEVEL_KEYS)
        errors.append(
            f"Unknown top-level key {key!r}.{hint} "
            f"Allowed keys: {sorted(_ALLOWED_TOP_LEVEL_KEYS)}"
        )

    # --- 2. default_rules ---
    default_specs = raw.get("default_rules", [])
    if "default_rules" in raw and not isinstance(default_specs, list):
        errors.append(
            f"'default_rules' must be a list. Got {type(default_specs).__name__}."
        )
    elif isinstance(default_specs, list):
        for i, spec in enumerate(default_specs):
            context = f"default_rules[{i}]"
            errors.extend(_validate_rule_spec(spec, context))

    # --- 3. tag_rules ---
    tag_specs = raw.get("tag_rules", {})
    if "tag_rules" in raw and not isinstance(tag_specs, dict):
        errors.append(
            f"'tag_rules' must be a mapping. Got {type(tag_specs).__name__}."
        )
    elif isinstance(tag_specs, dict):
        for tag_pattern, rule_list in tag_specs.items():
            if not isinstance(rule_list, list):
                errors.append(
                    f"tag_rules[{tag_pattern!r}] must be a list of rule specs. "
                    f"Got {type(rule_list).__name__}."
                )
                continue
            for i, spec in enumerate(rule_list):
                context = f"tag_rules[{tag_pattern!r}][{i}]"
                errors.extend(_validate_rule_spec(spec, context))

    # --- 4. quality_map ---
    if "quality_map" in raw:
        raw_qm = raw["quality_map"]
        if not isinstance(raw_qm, dict):
            errors.append(
                f"'quality_map' must be a mapping. Got {type(raw_qm).__name__}."
            )
        else:
            for key, val in raw_qm.items():
                if val not in _VALID_QUALITY_LEVELS:
                    errors.append(
                        f"quality_map value for key {key!r} is {val!r}. "
                        f"Must be one of {sorted(_VALID_QUALITY_LEVELS)}."
                    )

    return errors


def _validate_rule_spec(spec: Any, context: str) -> list[str]:
    """Validate a single rule spec dict and return a list of errors."""
    errors: list[str] = []

    if not isinstance(spec, dict):
        errors.append(f"{context}: Expected a mapping (dict), got {type(spec).__name__}.")
        return errors

    # --- check key ---
    if "check" not in spec:
        errors.append(
            f"{context}: 'check' key is required.\n"
            f"  Got keys: {list(spec.keys())}.\n"
            f"  Example: {{check: null, level: bad}}"
        )
        return errors  # can't validate further without check

    raw_check = spec["check"]
    check_name = "null" if raw_check is None else str(raw_check)

    if check_name not in _KNOWN_CHECKS:
        hint = _fuzzy_hint(check_name, _KNOWN_CHECKS)
        errors.append(
            f"{context}: Unknown check name {check_name!r}.{hint}\n"
            f"  Supported checks: {sorted(_KNOWN_CHECKS)}."
        )
        return errors  # can't validate params without known check

    # --- level ---
    level = spec.get("level", "bad" if check_name in ("null", "range") else "sus")
    if level not in ("sus", "bad"):
        errors.append(
            f"{context}: 'level' must be 'sus' or 'bad', got {level!r}."
        )

    # --- unknown params for this check type ---
    known_params = _KNOWN_CHECK_PARAMS.get(check_name, set())
    given_params = set(spec.keys())
    extra = given_params - known_params
    for param in sorted(extra):
        hint = _fuzzy_hint(param, known_params)
        errors.append(
            f"{context}: Unknown parameter {param!r} for check: {check_name}.{hint}"
            f"  Allowed params: {sorted(known_params)}"
        )

    # --- required params for this check type ---
    required = _RULE_REQUIRED_PARAMS.get(check_name, set())
    for req in required:
        if req not in spec or spec[req] is None:
            errors.append(
                f"{context}: '{req}' is required for check: {check_name}.\n"
                f"  Got keys: {list(spec.keys())}."
            )

    # --- delta: at least one of min_delta / max_delta ---
    if check_name == "delta":
        if spec.get("min_delta") is None and spec.get("max_delta") is None:
            errors.append(
                f"{context}: At least one of 'min_delta' or 'max_delta' "
                f"is required for check: delta.\n"
                f"  Got keys: {list(spec.keys())}."
            )

    # --- range: at least one of min / max ---
    if check_name == "range":
        if spec.get("min") is None and spec.get("max") is None:
            errors.append(
                f"{context}: At least one of 'min' or 'max' "
                f"is required for check: range.\n"
                f"  Got keys: {list(spec.keys())}."
            )

    return errors


def _build_rule(spec: dict[str, Any], context: str) -> Rule:
    """Build a Rule from a parsed YAML dict.  *context* is used in error messages."""
    if "check" not in spec:
        raise ValueError(
            f"{context}: 'check' key is required.\n"
            f"  Got keys: {list(spec.keys())}.\n"
            f"  Example: {{check: null, level: bad}}"
        )

    raw_check = spec["check"]
    # YAML parses `check: null` as Python None — map it back to the string "null"
    if raw_check is None:
        check_name = "null"
    else:
        check_name = str(raw_check)

    if check_name not in _KNOWN_CHECKS:
        raise ValueError(
            f"{context}: Unknown check name {check_name!r}.\n"
            f"  Supported checks: {sorted(_KNOWN_CHECKS)}.\n"
            f"  Example: {{check: flatline, window: 1h, min_delta: 0.001, level: sus}}"
        )

    level = spec.get("level", "bad" if check_name in ("null", "range") else "sus")
    if level not in ("sus", "bad"):
        raise ValueError(
            f"{context}: 'level' must be 'sus' or 'bad', got {level!r}."
        )

    if check_name == "null":
        return NullRule(level=level)

    if check_name == "flatline":
        window = spec.get("window")
        if window is None:
            raise ValueError(
                f"{context}: 'window' is required for check: flatline.\n"
                f"  Got keys: {list(spec.keys())}.\n"
                f"  Example: {{check: flatline, window: 1h, min_delta: 0.001, level: sus}}"
            )
        min_delta = float(spec.get("min_delta", 0.0))
        min_duration = spec.get("min_duration")
        return FlatlineRule(
            window=str(window),
            min_delta=min_delta,
            min_duration=str(min_duration) if min_duration is not None else None,
            level=level,
        )

    if check_name == "delta":
        min_delta = spec.get("min_delta")
        max_delta = spec.get("max_delta")
        if min_delta is None and max_delta is None:
            raise ValueError(
                f"{context}: At least one of 'min_delta' or 'max_delta' "
                f"is required for check: delta.\n"
                f"  Got keys: {list(spec.keys())}.\n"
                f"  Example: {{check: delta, min_delta: 0.5, max_delta: 100.0, level: sus}}"
            )
        return DeltaRule(
            min_delta=float(min_delta) if min_delta is not None else None,
            max_delta=float(max_delta) if max_delta is not None else None,
            level=level,
        )

    if check_name == "range":
        min_val = spec.get("min")
        max_val = spec.get("max")
        if min_val is None and max_val is None:
            raise ValueError(
                f"{context}: At least one of 'min' or 'max' is required for check: range.\n"
                f"  Got keys: {list(spec.keys())}.\n"
                f"  Example: {{check: range, min: 0, max: 500, level: bad}}"
            )
        return RangeRule(
            min_val=float(min_val) if min_val is not None else None,
            max_val=float(max_val) if max_val is not None else None,
            level=level,
        )

    if check_name == "outlier":
        method = str(spec.get("method", "zscore"))
        if method not in ("zscore", "mad", "iqr"):
            raise ValueError(
                f"{context}: 'method' for check: outlier must be one of "
                f"'zscore', 'mad', 'iqr', got {method!r}."
            )
        threshold = spec.get("threshold")
        threshold_f = float(threshold) if threshold is not None else None
        window_str = spec.get("window")
        window = str(window_str) if window_str is not None else None
        min_periods = int(spec.get("min_periods", 10))
        return OutlierRule(
            method=method,
            threshold=threshold_f,
            window=window,
            min_periods=min_periods,
            level=level,
        )

    # Should never reach here due to check above
    raise ValueError(f"{context}: Unhandled check {check_name!r}")  # pragma: no cover


def parse_yaml_rules(path: str) -> dict[str, Any]:
    """Parse a YAML config file into a dict of Rule lists.

    Returns:
        {
            "default": list[Rule],           # rules for every tag
            "tags": {pattern: list[Rule]},   # tag-specific rules (may use globs)
        }

    Raises:
        FileNotFoundError: if *path* does not exist.
        ValueError: if the YAML structure is invalid, with an actionable message.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Rule config file not found: {path!r}.\n"
            "Pass a valid path to a YAML file, or omit 'rules' to use defaults."
        )

    with p.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if raw is None:
        raise ValueError(
            f"YAML file {path!r} is empty. "
            "Expected at least a 'default_rules' or 'tag_rules' section."
        )

    if not isinstance(raw, dict):
        raise ValueError(
            f"YAML file {path!r} must be a mapping at the top level. "
            f"Got {type(raw).__name__}."
        )

    # --- Batch structural validation (collect ALL errors) ---
    errors = _validate_yaml_structure(raw, str(p))
    if errors:
        raise ValueError(
            f"Rule config file {str(p)!r} has {len(errors)} error(s):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    result: dict[str, Any] = {"default": [], "tags": {}, "quality_map": {}}

    # --- quality_map (optional) ---
    raw_qm = raw.get("quality_map", {})
    if not isinstance(raw_qm, dict):
        raise ValueError(
            f"'quality_map' must be a mapping. Got {type(raw_qm).__name__}."
        )
    qm: dict = {}
    for key, val in raw_qm.items():
        if val not in _VALID_QUALITY_LEVELS:
            raise ValueError(
                f"quality_map value {val!r} is invalid. "
                f"Must be one of {sorted(_VALID_QUALITY_LEVELS)}."
            )
        qm[key] = str(val)
    result["quality_map"] = qm

    # --- default_rules ---
    default_specs = raw.get("default_rules", [])
    if not isinstance(default_specs, list):
        raise ValueError(
            f"'default_rules' must be a list. Got {type(default_specs).__name__}."
        )
    for i, spec in enumerate(default_specs):
        context = f"default_rules[{i}]"
        result["default"].append(_build_rule(spec, context))

    # --- tag_rules ---
    tag_specs = raw.get("tag_rules", {})
    if not isinstance(tag_specs, dict):
        raise ValueError(
            f"'tag_rules' must be a mapping. Got {type(tag_specs).__name__}."
        )
    for tag_pattern, rule_list in tag_specs.items():
        if not isinstance(rule_list, list):
            raise ValueError(
                f"tag_rules[{tag_pattern!r}] must be a list of rule specs. "
                f"Got {type(rule_list).__name__}."
            )
        built: list[Rule] = []
        for i, spec in enumerate(rule_list):
            context = f"tag_rules[{tag_pattern!r}][{i}]"
            built.append(_build_rule(spec, context))
        result["tags"][tag_pattern] = built

    return result


def get_rules_for_tag(parsed: dict[str, Any], tag: str) -> list[Rule]:
    """Resolve the combined rule list for a given tag name."""
    rules = list(parsed.get("default", []))
    for pattern, pattern_rules in parsed.get("tags", {}).items():
        if fnmatch.fnmatch(tag, pattern):
            rules.extend(pattern_rules)
    return rules
