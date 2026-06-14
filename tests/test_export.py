"""Tests for result.export_report() HTML output."""

from pathlib import Path

import pandas as pd
import pytest

import tsqc


@pytest.fixture
def sample_result(single_tag_df):
    return tsqc.check(single_tag_df)


class TestExportReport:
    def test_creates_file(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        assert Path(out).exists()

    def test_file_is_non_empty(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        assert Path(out).stat().st_size > 1000

    def test_file_contains_doctype(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_file_contains_quality_keyword(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        assert "quality" in content.lower()

    def test_file_contains_tag_name(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        assert "TAG_A" in content

    def test_custom_title_in_file(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out, title="My Custom Report")
        content = Path(out).read_text(encoding="utf-8")
        assert "My Custom Report" in content

    def test_multi_tag_report_contains_all_tags(self, multi_tag_df, tmp_path):
        result = tsqc.check(multi_tag_df)
        out = str(tmp_path / "multi_report.html")
        result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        for tag in ["TAG_A", "TAG_B", "TAG_C"]:
            assert tag in content, f"Tag {tag!r} missing from report"

    def test_report_contains_summary_section(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        assert "Summary" in content

    def test_report_contains_plotly_javascript(self, sample_result, tmp_path):
        out = str(tmp_path / "report.html")
        sample_result.export_report(out)
        content = Path(out).read_text(encoding="utf-8")
        # Plotly embeds JavaScript inline
        assert "plotly" in content.lower()
