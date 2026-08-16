# Traffic Metrics

Raw traffic and repo-metrics data for timeseries-qc, collected hourly by
[`.github/workflows/traffic.yml`](../.github/workflows/traffic.yml) via
[`.github/scripts/archive_traffic.py`](../.github/scripts/archive_traffic.py).

## Branches

* `main` — dashboard app and badge live at `doc/metric/` (published to GitHub
  Pages by the mkdocs deploy workflow; `docs/hooks.py` copies `doc/metric`
  into the built site).
* `traffic-data` — this directory's `data/*.csv` files are force-pushed here
  by the hourly workflow and served to the dashboard via raw GitHub URLs.

## Layout

| File | Contents |
|------|----------|
| `data/views.csv` | daily views + unique visitors (14-day window merged, newer wins) |
| `data/clones.csv` | daily clones + uniques |
| `data/referrers.csv` | daily top-referrer snapshot |
| `data/paths.csv` | daily top-path snapshot |
| `data/repo.csv` | daily repo counters (stars, forks, watchers, subscribers, open issues, contributors, releases) |
| `data/stars.csv` | full star history (backfilled to repo creation) |
| `data/forks.csv` | full fork history (backfilled to repo creation) |
| `data/commits.csv` | weekly commit totals |
| `data/issues.csv` | daily issues/PRs opened, closed, merged |

## Notes

* GitHub only exposes the last 14 days of traffic, so `views.csv`/`clones.csv`
  grow a 14-day window per run rather than full history. The repo was created
  2026-06-13; star/fork/issue/commit history backfills to that date.
* `watchers` in `repo.csv` is GitHub's `watchers_count` (== stars on modern
  GitHub); `subscribers` is the true "watch" count.
* Views/clones and top referrers/paths require a token with read access to
  traffic. The workflow runs with `github.token` which has that access.
