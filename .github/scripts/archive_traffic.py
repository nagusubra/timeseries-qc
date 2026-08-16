#!/usr/bin/env python3
"""Archive GitHub repository traffic into .metrics/data/*.csv and refresh
doc/metric/badge.svg for timeseries-qc.

GitHub only exposes the last 14 days of traffic data, so this is meant to run
on a schedule (see .github/workflows/traffic.yml). Each run:

  * fetches the full 14-day views/clones window and merges it into the
    persistent CSVs (newer values win),
  * snapshots the top referrers/paths dated with the traffic as-of date
    (the most recent day in the views window, so all datasets share one
    timeline and the dashboard's range filters apply uniformly),
  * snapshots repo-level counters (stars, forks, true watchers/subscribers,
    open issues, contributors, releases),
  * rebuilds full star/fork history (backfillable to repo creation via the
    stargazers/forks endpoints) and weekly commit activity,
  * rebuilds issue/PR open/close/merge history,
  * regenerates an all-time total-views badge.

Environment:
    GH_TOKEN            GitHub token (e.g. github.token in Actions). Optional
                        for the public repo endpoints; required for traffic.
    GITHUB_REPOSITORY   "owner/repo" (set automatically in Actions).

Stdlib only.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone

API = "https://api.github.com"
DEFAULT_REPO = "nagusubra/timeseries-qc"

HERE = os.path.dirname(os.path.abspath(__file__))          # <root>/.github/scripts
ROOT = os.path.dirname(os.path.dirname(HERE))              # <root>
DATA_DIR = os.path.join(ROOT, ".metrics", "data")
DOC_DIR = os.path.join(ROOT, "doc", "metric")

TOKEN = os.environ.get("GH_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPO

VIEWS_FIELDS = ["date", "views", "uniques"]
CLONES_FIELDS = ["date", "clones", "uniques"]
REFERRERS_FIELDS = ["date", "referrer", "count", "uniques"]
PATHS_FIELDS = ["date", "path", "title", "count", "uniques"]
REPO_FIELDS = ["date", "stars", "forks", "watchers", "subscribers", "open_issues", "contributors", "releases"]
STARS_FIELDS = ["date", "stars"]
FORKS_FIELDS = ["date", "forks"]
COMMITS_FIELDS = ["week_start", "total"]
ISSUES_FIELDS = ["date", "issues_opened", "issues_closed", "prs_opened", "prs_closed", "prs_merged"]

BADGE_COLOR = "#2563eb"


def log(*args) -> None:
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}]", *args, flush=True)


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def api_get(path: str, accept: str = "application/vnd.github+json"):
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "repo-traffic-archiver")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body.strip() else None
    except urllib.error.HTTPError as e:
        log(f"[warn] GET {path} -> HTTP {e.code} ({e.reason})")
        return None
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        log(f"[warn] GET {path} -> {e}")
        return None


def api_get_paged(path: str, per_page: int = 100, max_pages: int = 20, accept: str = "application/vnd.github+json") -> list:
    out: list = []
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in path else "?"
        data = api_get(f"{path}{sep}per_page={per_page}&page={page}", accept=accept)
        if not isinstance(data, list):
            break
        out.extend(data)
        if len(data) < per_page:
            break
    return out


def merge_into(path: str, fields: list[str], keys: list[str], new_rows: list[dict]) -> None:
    data: dict[tuple, dict] = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row and all(row.get(k) not in (None, "") for k in keys):
                    data[tuple(row[k] for k in keys)] = row
    for row in new_rows:
        data[tuple(row[k] for k in keys)] = {k: str(row.get(k, "")) for k in fields}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for k in sorted(data):
            writer.writerow(data[k])
    log(f"wrote {path} ({len(data)} rows)")


def read_all(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r]


def cumulative_series(created: str, event_days: list[str]) -> list[dict]:
    """Daily cumulative counts from created-date to today."""
    start = date.fromisoformat(created)
    end = today_utc()
    counts = Counter(d[:10] for d in event_days if d)
    series: list[dict] = []
    running = 0
    cur = start
    while cur <= end:
        running += counts.get(cur.isoformat(), 0)
        series.append({"date": cur.isoformat(), "value": running})
        cur += timedelta(days=1)
    return series


def archive_views() -> str:
    """Merge the 14-day views window; return the as-of date (latest day)."""
    data = api_get(f"/repos/{REPO}/traffic/views?per=day") or {}
    rows = [
        {"date": d["timestamp"][:10], "views": d["count"], "uniques": d["uniques"]}
        for d in data.get("views", [])
    ]
    merge_into(os.path.join(DATA_DIR, "views.csv"), VIEWS_FIELDS, ["date"], rows)
    dates = [d["timestamp"][:10] for d in data.get("views", [])]
    return max(dates) if dates else today_utc()


def archive_clones() -> None:
    data = api_get(f"/repos/{REPO}/traffic/clones?per=day") or {}
    rows = [
        {"date": d["timestamp"][:10], "clones": d["count"], "uniques": d["uniques"]}
        for d in data.get("clones", [])
    ]
    merge_into(os.path.join(DATA_DIR, "clones.csv"), CLONES_FIELDS, ["date"], rows)


def archive_referrers(asof: str) -> None:
    rows = [
        {"date": asof, "referrer": r.get("referrer", ""), "count": r.get("count", 0), "uniques": r.get("uniques", 0)}
        for r in (api_get(f"/repos/{REPO}/traffic/popular/referrers") or [])
    ]
    merge_into(os.path.join(DATA_DIR, "referrers.csv"), REFERRERS_FIELDS, ["date", "referrer"], rows)


def archive_paths(asof: str) -> None:
    rows = [
        {
            "date": asof,
            "path": p.get("path", ""),
            "title": p.get("title", ""),
            "count": p.get("count", 0),
            "uniques": p.get("uniques", 0),
        }
        for p in (api_get(f"/repos/{REPO}/traffic/popular/paths") or [])
    ]
    merge_into(os.path.join(DATA_DIR, "paths.csv"), PATHS_FIELDS, ["date", "path"], rows)


def archive_repo() -> None:
    data = api_get(f"/repos/{REPO}")
    if not data:
        return
    today = today_utc().isoformat()
    contributors = len(api_get_paged(f"/repos/{REPO}/contributors"))
    releases = len(api_get_paged(f"/repos/{REPO}/releases"))
    rows = [
        {
            "date": today,
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "subscribers": data.get("subscribers_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "contributors": contributors,
            "releases": releases,
        }
    ]
    merge_into(os.path.join(DATA_DIR, "repo.csv"), REPO_FIELDS, ["date"], rows)
    created = (data.get("created_at") or "").split("T")[0]
    if created:
        archive_star_history(created)
        archive_fork_history(created)


def archive_star_history(created: str) -> None:
    stars = api_get_paged(f"/repos/{REPO}/stargazers", accept="application/vnd.github.star+json")
    rows = [{"date": r["date"], "stars": r["value"]} for r in cumulative_series(created, [s.get("starred_at", "") for s in stars])]
    merge_into(os.path.join(DATA_DIR, "stars.csv"), STARS_FIELDS, ["date"], rows)


def archive_fork_history(created: str) -> None:
    forks = api_get_paged(f"/repos/{REPO}/forks?sort=oldest")
    rows = [{"date": r["date"], "forks": r["value"]} for r in cumulative_series(created, [f.get("created_at", "") for f in forks])]
    merge_into(os.path.join(DATA_DIR, "forks.csv"), FORKS_FIELDS, ["date"], rows)


def archive_commits() -> None:
    data = api_get(f"/repos/{REPO}/stats/commit_activity")
    if not isinstance(data, list):
        log("[warn] commit_activity not ready (GitHub caches it); skipping")
        return
    rows = [
        {"week_start": datetime.fromtimestamp(int(w["week"]), tz=timezone.utc).date().isoformat(), "total": w.get("total", 0)}
        for w in data if isinstance(w, dict) and w.get("total")
    ]
    merge_into(os.path.join(DATA_DIR, "commits.csv"), COMMITS_FIELDS, ["week_start"], rows)


def archive_issues() -> None:
    issues = api_get_paged(f"/repos/{REPO}/issues?state=all")
    pulls = api_get_paged(f"/repos/{REPO}/pulls?state=all")
    merged_by_day = Counter()
    for p in pulls:
        merged = (p.get("merged_at") or "")[:10]
        if merged:
            merged_by_day[merged] += 1

    opened: Counter = Counter()
    closed: Counter = Counter()
    pr_opened: Counter = Counter()
    pr_closed: Counter = Counter()
    for i in issues:
        created = (i.get("created_at") or "")[:10]
        closed_at = (i.get("closed_at") or "")[:10]
        if i.get("pull_request"):
            if created:
                pr_opened[created] += 1
            if closed_at:
                pr_closed[closed_at] += 1
        else:
            if created:
                opened[created] += 1
            if closed_at:
                closed[closed_at] += 1

    all_days = set(opened) | set(closed) | set(pr_opened) | set(pr_closed) | set(merged_by_day)
    rows = [
        {
            "date": d,
            "issues_opened": opened.get(d, 0),
            "issues_closed": closed.get(d, 0),
            "prs_opened": pr_opened.get(d, 0),
            "prs_closed": pr_closed.get(d, 0),
            "prs_merged": merged_by_day.get(d, 0),
        }
        for d in sorted(all_days)
    ]
    merge_into(os.path.join(DATA_DIR, "issues.csv"), ISSUES_FIELDS, ["date"], rows)


def format_int(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "0"


def render_badge(label: str, value: str, color: str = BADGE_COLOR) -> None:
    # shields.io-style badge, left label on grey, right value in color.
    font = 11
    lw = int(len(label) * 7.1 + 14)
    rw = int(len(value) * 7.6 + 14)
    W, H = lw + rw, 20
    lcx, rcx = lw // 2, lw + rw // 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <clipPath id="r"><rect width="{W}" height="{H}" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{lw}" height="{H}" fill="#555"/>
    <rect x="{lw}" width="{rw}" height="{H}" fill="{color}"/>
    <rect width="{W}" height="{H}" fill="url(#s)"/>
  </g>
  <defs><linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-opacity=".08"/></linearGradient></defs>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{font}">
    <text x="{lcx}" y="14">{label}</text>
    <text x="{rcx}" y="14" font-weight="bold">{value}</text>
  </g>
</svg>
"""
    os.makedirs(DOC_DIR, exist_ok=True)
    path = os.path.join(DOC_DIR, "badge.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    log(f"wrote {path}")


def refresh_badge() -> None:
    total = sum(int(r.get("views", 0) or 0) for r in read_all(os.path.join(DATA_DIR, "views.csv")))
    render_badge("total views", format_int(total))


def main() -> int:
    if not os.environ.get("CI"):
        log(f"local run | repo={REPO} | token={'present' if TOKEN else 'MISSING (traffic endpoints will be skipped)'}")
    log(f"archiving traffic for {REPO}")
    asof = archive_views()
    archive_clones()
    archive_referrers(asof)
    archive_paths(asof)
    archive_repo()
    archive_commits()
    archive_issues()
    refresh_badge()
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
