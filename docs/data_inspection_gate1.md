# Gate 1 data inspection: Vadimkin siren datasets

Reproduce with `python scripts/inspect_vadimkin.py`. Raw files and their SHA-256 are in
`data/raw/MANIFEST.json` (git-ignored). Inspection run: 2026-10-12, times in UTC.

## Sources

| File | Rows | Coverage | Level | Notes |
|---|---|---|---|---|
| `official_data_en.csv` | 299,275 raw / 185,430 after dedupe | 2022-03-15 .. 2026-09-07 | oblast, raion, hromada | Since Dec 2025 mostly raion level (README) |
| `volunteer_data_en.csv` | 115,989 | 2022-02-25 .. 2026-10-11 | oblast only | `naive=True` means end time inferred as start + 30 min (5.0% of rows) |

Vadimkin's README also says the permanent sirens in Luhansk (from 4 Apr) and Crimea
(from 10 Dec) are **not** in the datasets and must be added manually if needed.

## Ingest rule: exact duplicates

Rows identical in every column are dropped by `src/ingestion/alert_dedupe.py`
(`drop_exact_duplicates`). Each run logs the number dropped. The raw file is never modified.

**Why this is a copy artifact, not repeated signals:**

- Every duplicate group is exactly two rows. No triples, and no pairs that differ in any field.
- For oblast-level alerts in 2022 to 2025, the raw count is exactly twice the deduplicated
  count (2022: 27,266 raw, 13,633 unique).
- The volunteer feed has no duplicates, and its counts match the deduplicated official
  counts more closely than the raw counts (2022: volunteer 15,242, official unique 13,633,
  official raw 27,266).
- The pairs are spread across 2022 to 2026. They are not tied to one event or one snapshot.

The rule is conservative: rows that differ in any column are kept. The evidence is strong but
indirect, because the feed's own logs are not available.

## Data-quality scorecard (after the ingest rule)

| Check | Official | Volunteer | Action |
|---|---|---|---|
| Exact duplicate rows | 113,845 dropped (38% of raw) | 0 | Dropped by the ingest rule |
| Alerts longer than 24 h | 897 (13 longer than 7 d) | n/a | Plausibly real long alerts or missing end times; check before using duration |
| Max duration | ~604 days (one row) | 10,696 min (~7.4 d) | Likely a missing end time; exclude from duration analysis |
| Zero-length alerts | 2 | 6 | Keep; check after dedupe |
| Rows sorted by `started_at` | No | No | Sort before any time-series work |
| Timezone | UTC (`+00:00`) | UTC | None needed |
| Inferred end times | None flagged | 5.0% (`naive`) | Carry `naive` through as `inferred_flag` |

Level counts after dedupe (official): raion 99,304, oblast 65,314, hromada 20,812.

## Source overlap

Only 44.6% of volunteer alerts have an official oblast alert for the same region within
5 minutes (computed on the deduplicated official file). The sources overlap but are not
interchangeable. Using both would double-count, and using one alone would miss alerts. This
needs an explicit decision before modeling.

## Open decisions

1. **Which source is the target series?** Official is the official record but changes
   resolution in Dec 2025. Volunteer is oblast-level throughout and covers 2 more days.
2. **Resolution:** aggregate everything to oblast level so the December 2025 change does not
   break comparisons. Raion-level counts before and after the change are not comparable.
3. **Near-duplicates across sources** are not handled by the ingest rule and need the rule
   chosen in (1).

## Still open for Gate 1

- ACLED freshness: checked on the monitor page, which lists weekly updates through
  26 Sep to 2 Oct 2026. Data access still needs an API key that is not in `.env`.
- alerts.in.ua API token: not in `.env`, so not verified here.
