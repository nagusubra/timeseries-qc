"""Parse a YAML rule config file into Rule objects."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

from tsqc.rules.base import Rule
from tsqc.rules.builtins import DeltaRule, FlatlineRule, NullRule, RangeRule

_KNOWN_CHECKS = {"null", "flatline", "delta", "range"}


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
        return FlatlineRule(window=str(window), min_delta=min_delta, level=level)

    if check_name == "delta":
        threshold = spec.get("threshold")
        if threshold is None:
            raise ValueError(
                f"{context}: 'threshold' is required for check: delta.\n"
                f"  Got keys: {list(spec.keys())}.\n"
                f"  Example: {{check: delta, threshold: 50.0, level: sus}}"
            )
        return DeltaRule(threshold=float(threshold), level=level)

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

    result: dict[str, Any] = {"default": [], "tags": {}}

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
