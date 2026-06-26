"""QCResult — wraps an annotated DataFrame and exposes the public API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import plotly.graph_objects as go


class QCResult:
    """Result object returned by tsqc.check().

    Attributes:
        df: Original DataFrame with quality and quality_reasons columns appended.
        display_tz: IANA timezone in which timestamps are displayed.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        time_col: str = "timestamp",
        tag_col: str | None = "tag_name",
        value_col: str = "value",
        quality_col: str = "quality",
        reasons_col: str = "quality_reasons",
        ambiguous_timestamps: list[pd.Timestamp] | None = None,
        display_tz: str = "UTC",
    ) -> None:
        self._df = df
        self.time_col = time_col
        self.tag_col = tag_col
        self.value_col = value_col
        self.quality_col = quality_col
        self.reasons_col = reasons_col
        self.ambiguous_timestamps: list[pd.Timestamp] = ambiguous_timestamps or []
        self._display_tz = display_tz

    @property
    def display_tz(self) -> str:
        """IANA timezone used for all timestamp display (plot, summaries, etc.)."""
        return self._display_tz

    @property
    def df(self) -> pd.DataFrame:
        """The annotated DataFrame (original columns + quality + quality_reasons)."""
        return self._df

    # ------------------------------------------------------------------ #
    #  summary()
    # ------------------------------------------------------------------ #

    def summary(self) -> pd.DataFrame:
        """Return per-tag quality summary sorted by pct_bad descending.

        Columns: tag_name, total_rows, pct_good, pct_sus, pct_bad,
                 n_good, n_sus, n_bad
        """
        df = self._df

        if self.tag_col is not None and self.tag_col in df.columns:
            groups = df.groupby(self.tag_col)
        else:
            groups = [("default", df)]

        records = []
        for tag, group in groups:
            total = len(group)
            n_good = (group[self.quality_col] == "good").sum()
            n_sus = (group[self.quality_col] == "sus").sum()
            n_bad = (group[self.quality_col] == "bad").sum()
            records.append(
                {
                    "tag_name": tag,
                    "total_rows": total,
                    "n_good": int(n_good),
                    "n_sus": int(n_sus),
                    "n_bad": int(n_bad),
                    "pct_good": round(100 * n_good / total, 2) if total else 0.0,
                    "pct_sus": round(100 * n_sus / total, 2) if total else 0.0,
                    "pct_bad": round(100 * n_bad / total, 2) if total else 0.0,
                }
            )

        summary_df = pd.DataFrame(records)
        return summary_df.sort_values("pct_bad", ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------ #
    #  plot()
    # ------------------------------------------------------------------ #

    def plot(
        self,
        tags: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        title: str = "Data Quality Timeline",
        height: int = 400,
    ) -> "go.Figure":
        """Return a Plotly multi-tag horizontal quality timeline figure.

        Args:
            tags: Subset of tag names to display. None = all tags.
            start: ISO datetime string to clip the left edge.
            end: ISO datetime string to clip the right edge.
            title: Chart title.
            height: Base figure height in pixels.

        Returns:
            plotly.graph_objects.Figure (call .show() to display).
        """
        from tsqc.viz.rle import encode_quality_runs
        from tsqc.viz.timeline import build_timeline_figure

        df = self._df.copy()

        # Apply tag filter
        if tags is not None and self.tag_col in df.columns:
            df = df[df[self.tag_col].isin(tags)]

        # Apply time filter — bare strings are interpreted in the display timezone
        if start is not None:
            start_ts = pd.Timestamp(start, tz=self._display_tz) if "+" not in start and "Z" not in start else pd.Timestamp(start)
            df = df[df[self.time_col] >= start_ts]
        if end is not None:
            end_ts = pd.Timestamp(end, tz=self._display_tz) if "+" not in end and "Z" not in end else pd.Timestamp(end)
            df = df[df[self.time_col] <= end_ts]

        segments = encode_quality_runs(
            df,
            time_col=self.time_col,
            tag_col=self.tag_col,
            quality_col=self.quality_col,
            reasons_col=self.reasons_col,
        )

        summary = self.summary()
        if tags is not None:
            summary = summary[summary["tag_name"].isin(tags)]

        return build_timeline_figure(
            segments=segments,
            summary=summary,
            title=title,
            height=height,
            display_tz=self._display_tz,
        )

    # ------------------------------------------------------------------ #
    #  check_timestamps()
    # ------------------------------------------------------------------ #

    def check_timestamps(
        self,
        expected_freq: str | None = None,
        freq_tolerance: float = 0.1,
    ) -> pd.DataFrame:
        """Return a DataFrame of timestamp anomalies.

        Columns: tag_name, issue_type, timestamp, description, severity

        issue_type values: gap, duplicate, non_monotonic, freq_drift, dst_ambiguous
        severity values: warning, error
        Returns empty DataFrame if no issues found.
        """
        from tsqc.time_health.checker import check_timestamps

        return check_timestamps(
            result=self,
            expected_freq=expected_freq,
            freq_tolerance=freq_tolerance,
            display_tz=self._display_tz,
        )

    # ------------------------------------------------------------------ #
    #  issue_summary()
    # ------------------------------------------------------------------ #

    def issue_summary(self) -> pd.DataFrame:
        """Return a per-issue summary of non-good quality runs.

        Each row represents a contiguous segment (run) of 'bad' or 'sus'
        quality for a given tag, with start/end timestamps, row count,
        total duration in hours, and the rule names that triggered.

        Columns: tag_name, issue_start_time, issue_end_time,
                 n_rows_with_issues, status, totalDuration_hours, reasons
        """
        from tsqc.viz.rle import encode_quality_runs

        segments = encode_quality_runs(
            self._df,
            time_col=self.time_col,
            tag_col=self.tag_col,
            quality_col=self.quality_col,
            reasons_col=self.reasons_col,
        )

        segments = segments[segments["quality"] != "good"].copy()
        _has_reasons = "reasons" in segments.columns

        if segments.empty:
            cols = [
                "tag_name", "issue_start_time", "issue_end_time",
                "n_rows_with_issues", "status", "totalDuration_hours",
            ]
            if _has_reasons:
                cols.append("reasons")
            return pd.DataFrame(columns=cols)

        # Count actual rows per tag/start/end segment
        df = self._df.copy()
        if self.tag_col is not None and self.tag_col in df.columns:
            grouped = df.groupby(self.tag_col)
        else:
            grouped = [("default", df)]

        row_counts: dict[tuple, int] = {}
        for tag, group in grouped:
            group = group.sort_values(self.time_col)
            qualities = group[self.quality_col].to_list()
            timestamps = group[self.time_col].to_list()

            n = len(group)
            run_starts = [0]
            for i in range(1, n):
                if qualities[i] != qualities[i - 1]:
                    run_starts.append(i)
            run_starts.append(n)

            for j in range(len(run_starts) - 1):
                s_idx = run_starts[j]
                e_idx = run_starts[j + 1]
                start_ts = timestamps[s_idx]
                quality = qualities[s_idx]
                end_ts = timestamps[e_idx - 1] if e_idx <= n else timestamps[-1]
                key = (tag, start_ts, end_ts, quality)
                row_counts[key] = e_idx - s_idx

        records = []
        for _, seg in segments.iterrows():
            tag = seg["tag_name"]
            start = seg["start"]
            end = seg["end"]
            quality = seg["quality"]
            if self.tag_col is not None and self.tag_col in df.columns:
                mask = (
                    (df[self.tag_col] == tag)
                    & (df[self.time_col] >= start)
                    & (df[self.time_col] < end)
                    & (df[self.quality_col] == quality)
                )
            else:
                mask = (
                    (df[self.time_col] >= start)
                    & (df[self.time_col] < end)
                    & (df[self.quality_col] == quality)
                )
            n_rows = mask.sum()
            duration_hours = round(seg["duration_seconds"] / 3600, 1)
            record = {
                "tag_name": tag,
                "issue_start_time": start.isoformat(),
                "issue_end_time": end.isoformat(),
                "n_rows_with_issues": int(n_rows),
                "status": quality,
                "totalDuration_hours": duration_hours,
            }
            if _has_reasons:
                record["reasons"] = seg.get("reasons", "")
            records.append(record)

        result_df = pd.DataFrame(records)
        if not result_df.empty:
            result_df = result_df.sort_values(
                ["tag_name", "issue_start_time"]
            ).reset_index(drop=True)
        return result_df

    # ------------------------------------------------------------------ #
    #  export_report()
    # ------------------------------------------------------------------ #

    def export_report(
        self,
        path: str,
        title: str = "Data Quality Report",
    ) -> None:
        """Write a self-contained HTML quality report to *path*.

        The file contains an embedded Plotly chart, per-tag summary table,
        per-issue summary table, timestamp health table, and run metadata.
        No external CDN required.
        """
        import datetime

        import plotly.io as pio

        fig = self.plot(title=title)
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=True)

        summary_df = self.summary()
        ts_issues = self.check_timestamps()
        issue_df = self.issue_summary()

        n_tags = len(summary_df)
        n_rows = len(self._df)
        run_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        def _df_to_html_table(df: pd.DataFrame, table_id: str = "") -> str:
            if df.empty:
                return "<p><em>No issues found.</em></p>"
            rows = "".join(
                "<tr>" + "".join(f"<td style='padding:4px 8px;border:1px solid #ddd'>{v}</td>" for v in row) + "</tr>"
                for row in df.itertuples(index=False)
            )
            headers = "".join(
                f"<th style='padding:4px 8px;border:1px solid #ddd;background:#f5f5f5'>{c}</th>"
                for c in df.columns
            )
            return (
                f"<table id='{table_id}' style='border-collapse:collapse;width:100%;font-size:13px'>"
                f"<thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>"
            )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 0; padding: 20px; background: #fafafa; color: #333; }}
  h1 {{ color: #2c3e50; margin-bottom: 4px; }}
  h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 6px; }}
  .meta {{ color: #7f8c8d; font-size: 13px; margin-bottom: 24px; }}
  .section {{ background: #fff; border-radius: 8px; padding: 20px;
              box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 24px; }}
</style>
</head>
<body>
<div class="section">
  <h1>{title}</h1>
  <p class="meta">
    Generated: {run_ts} &nbsp;|&nbsp;
    Tags: {n_tags} &nbsp;|&nbsp;
    Total rows: {n_rows:,}
  </p>
</div>

<div class="section">
  <h2>Quality Timeline</h2>
  {chart_html}
</div>

<div class="section">
  <h2>Summary per Tag</h2>
  {_df_to_html_table(summary_df, 'summary-table')}
</div>

<div class="section">
  <h2>Issue Summary (by Tag Issue)</h2>
  {_df_to_html_table(issue_df, 'issue-summary-table')}
</div>

<div class="section">
  <h2>Timestamp Health Issues</h2>
  {_df_to_html_table(ts_issues, 'ts-issues-table')}
</div>
</body>
</html>
"""

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)

    def __repr__(self) -> str:
        n = len(self._df)
        tags = (
            self._df[self.tag_col].nunique()
            if self.tag_col and self.tag_col in self._df.columns
            else 1
        )
        return f"QCResult(rows={n}, tags={tags})"
