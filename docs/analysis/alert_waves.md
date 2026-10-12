# Alert waves: sensitivity to the gap threshold

Source: volunteer feed (`volunteer_data_en.csv`, after exact-duplicate drop). A wave is a
run of national start instants, each at most `gap` minutes after the previous one.
Weeks are counted only where a wave was observed. Missing weeks are not zero-filled.

| Gap (min) | Waves | Waves over 6 h | Median duration (min) | p90 duration (min) | Median start instants | p90 start instants | Weeks with a wave |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 61,588 | 358 | 33.9 | 123.7 | 1 | 3 | 242 |
| 10 | 48,970 | 357 | 39.0 | 138.2 | 1 | 5 | 242 |
| 15 | 39,974 | 371 | 44.6 | 154.2 | 2 | 6 | 242 |
| 30 | 23,681 | 542 | 63.8 | 212.0 | 2 | 11 | 242 |
| 60 | 10,543 | 1,360 | 113.3 | 409.8 | 5 | 24 | 242 |

## Feed integrity: are long alerts real?

Long waves at wider gaps are mostly built from several rows, so the row level is the right test.
Row-level checks on `volunteer_data_en.csv` (115,989 rows):

- Rows longer than 6 h: 370 (0.3%). Longer than 12 h: 28. Longer than 24 h: 14.
- Long-row share by year is steady (2022: 0.22%, 2023: 0.39%, 2024: 0.38%, 2025: 0.45%, 2026: 0.17%).
  An unclosed-record bug would more likely cluster in one period.
- No finish time is shared by more than 5 rows. A default end time would show a large spike.
- None of the rows longer than 6 h has the `naive` (inferred end) flag set. The overall rate is 5%.
  Recorded end times look like genuine end times.

Conclusion: the row-level evidence points to real long alerts, not an unclosed-record artefact.
The 14 rows longer than 24 h should still be checked by hand before any report cites them.

Per-wave CSVs are written to `output/analysis/` (gitignored). `region_alerts` counts
region-alert pairs in a wave, not distinct regions.
