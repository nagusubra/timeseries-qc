"""Tests for tsqc/config/yaml_parser.py."""

import textwrap
from pathlib import Path

import pytest

from tsqc.config.yaml_parser import get_rules_for_tag, parse_yaml_rules
from tsqc.rules.builtins import DeltaRule, FlatlineRule, NullRule, RangeRule


@pytest.fixture
def rules_yaml(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
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
          SENSOR_A:
            - check: range
              min: 0
              max: 500
              level: bad

          "TI*.PNT":
            - check: range
              min: 50
              max: 250
              level: bad
            - check: flatline
              window: 30min
              level: sus
    """)
    p = tmp_path / "rules.yaml"
    p.write_text(content)
    return p


# ─────────────────────────────  Parsing  ───────────────────────────────────

class TestParseYamlRules:
    def test_parses_default_rules(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        assert len(parsed["default"]) == 3
        assert isinstance(parsed["default"][0], NullRule)
        assert isinstance(parsed["default"][1], FlatlineRule)
        assert isinstance(parsed["default"][2], DeltaRule)

    def test_flatline_window_parsed(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        flatline = parsed["default"][1]
        assert isinstance(flatline, FlatlineRule)
        assert flatline.window == "1h"
        assert flatline.min_delta == 0.001

    def test_delta_max_delta_parsed(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        delta = parsed["default"][2]
        assert isinstance(delta, DeltaRule)
        assert delta.max_delta == 50.0
        assert delta.min_delta is None

    def test_tag_specific_rules_parsed(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        assert "SENSOR_A" in parsed["tags"]
        assert isinstance(parsed["tags"]["SENSOR_A"][0], RangeRule)

    def test_range_bounds_parsed(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        rr = parsed["tags"]["SENSOR_A"][0]
        assert isinstance(rr, RangeRule)
        assert rr.min_val == 0.0
        assert rr.max_val == 500.0

    def test_levels_parsed_correctly(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        assert parsed["default"][0].level == "bad"
        assert parsed["default"][1].level == "sus"


# ─────────────────────────────  Glob matching  ─────────────────────────────

class TestGlobMatching:
    def test_glob_matches_ti_pnt(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        rules = get_rules_for_tag(parsed, "TI101.PNT")
        rule_types = [type(r).__name__ for r in rules]
        assert "RangeRule" in rule_types

    def test_glob_does_not_match_unrelated_tag(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        rules = get_rules_for_tag(parsed, "SENSOR_A")
        # SENSOR_A doesn't match "TI*.PNT" but does match "SENSOR_A" exactly
        ti_ranges = [r for r in rules if isinstance(r, RangeRule) and r.max_val == 250.0]
        assert len(ti_ranges) == 0

    def test_default_rules_always_included(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        rules = get_rules_for_tag(parsed, "UNMATCHED_TAG")
        assert len(rules) == 3  # only default rules
        assert isinstance(rules[0], NullRule)

    def test_tag_rules_added_on_top_of_defaults(self, rules_yaml):
        parsed = parse_yaml_rules(str(rules_yaml))
        rules = get_rules_for_tag(parsed, "SENSOR_A")
        assert len(rules) == 4  # 3 default + 1 tag-specific


# ─────────────────────────────  Error cases  ───────────────────────────────

class TestYamlErrors:
    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            parse_yaml_rules(str(tmp_path / "nonexistent.yaml"))

    def test_empty_file_raises(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("")
        with pytest.raises(ValueError, match="empty"):
            parse_yaml_rules(str(p))

    def test_missing_check_key_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("default_rules:\n  - level: bad\n")
        with pytest.raises(ValueError, match="'check' key is required"):
            parse_yaml_rules(str(p))

    def test_unknown_check_name_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("default_rules:\n  - check: magic_rule\n    level: bad\n")
        with pytest.raises(ValueError, match="Unknown check name"):
            parse_yaml_rules(str(p))

    def test_flatline_missing_window_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("default_rules:\n  - check: flatline\n    level: sus\n")
        with pytest.raises(ValueError, match="'window' is required"):
            parse_yaml_rules(str(p))

    def test_delta_missing_both_bounds_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("default_rules:\n  - check: delta\n    level: sus\n")
        with pytest.raises(ValueError, match="At least one of 'min_delta' or 'max_delta'"):
            parse_yaml_rules(str(p))

    def test_range_missing_bounds_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("default_rules:\n  - check: range\n    level: bad\n")
        with pytest.raises(ValueError, match="At least one of 'min' or 'max'"):
            parse_yaml_rules(str(p))

    def test_delta_min_delta_parsed(self, tmp_path):
        p = tmp_path / "r.yaml"
        p.write_text("default_rules:\n  - check: delta\n    min_delta: 0.5\n    level: sus\n")
        parsed = parse_yaml_rules(str(p))
        delta = parsed["default"][0]
        assert delta.min_delta == 0.5
        assert delta.max_delta is None

    def test_delta_both_bounds_parsed(self, tmp_path):
        p = tmp_path / "r.yaml"
        p.write_text(
            "default_rules:\n"
            "  - check: delta\n"
            "    min_delta: 0.5\n"
            "    max_delta: 100.0\n"
            "    level: sus\n"
        )
        parsed = parse_yaml_rules(str(p))
        delta = parsed["default"][0]
        assert delta.min_delta == 0.5
        assert delta.max_delta == 100.0

    def test_flatline_min_duration_parsed(self, tmp_path):
        p = tmp_path / "r.yaml"
        p.write_text(
            "default_rules:\n"
            "  - check: flatline\n"
            "    window: 1h\n"
            "    min_duration: 30min\n"
            "    level: sus\n"
        )
        parsed = parse_yaml_rules(str(p))
        fl = parsed["default"][0]
        assert fl.min_duration == "30min"
        assert fl.window == "1h"

    def test_error_message_includes_rule_index(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(
            "default_rules:\n"
            "  - check: null\n    level: bad\n"
            "  - check: flatline\n    level: sus\n"  # missing window at index 1
        )
        with pytest.raises(ValueError, match=r"default_rules\[1\]"):
            parse_yaml_rules(str(p))


# ─────────────────────────────  End-to-end  ────────────────────────────────

class TestYamlEndToEnd:
    def test_check_with_yaml_path(self, rules_yaml, multi_tag_df):
        import tsqc

        result = tsqc.check(multi_tag_df, rules=str(rules_yaml))
        assert "quality" in result.df.columns
        assert set(result.df["quality"].unique()).issubset({"good", "sus", "bad"})

    def test_check_with_yaml_applies_range_to_correct_tag(self, tmp_path, multi_tag_df):
        """TAG_A gets RangeRule(max=100); values > 100 should be 'bad'."""
        import tsqc

        p = tmp_path / "r.yaml"
        p.write_text(
            "default_rules:\n  - check: null\n    level: bad\n"
            "tag_rules:\n  TAG_A:\n    - check: range\n      min: 0\n      max: 100\n      level: bad\n"
        )
        result = tsqc.check(multi_tag_df, rules=str(p))
        tag_a = result.df[result.df["tag_name"] == "TAG_A"]
        # Spike rows (value ~500) should be bad
        bad_a = tag_a[tag_a["quality"] == "bad"]
        assert len(bad_a) > 0
