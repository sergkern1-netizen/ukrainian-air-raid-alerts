# Feed integrity: volunteer vs official alert agreement

Definition: a volunteer alert is matched if an official alert in the same oblast starts within
5 minutes (as in `gate3_results.md`). Recall is the same test for oblast-level official alerts.
Descriptive only. A low match rate means the feeds disagree, not that either is wrong.

Overlap window: volunteer alerts up to the official feed's last start (2026-09-07).
Volunteer alerts after that date (5,119) cannot be matched and are excluded from all rates.
The Gate 3 figure of 44.8% after December 2025 included those alerts as unmatched and is biased low;
the overlap-only figure is reported here.

## Name check

- Volunteer region names not in the official feed: none
- Official oblast names not in the volunteer feed: none

## Precision and lag by period

| Period | Volunteer alerts | Matched share | Median abs lag (s) | p90 abs lag (s) |
|---|---:|---:|---:|---:|
| post-Dec 2025 | 29,089 | 0.527 | 9 | 137 |
| pre-Dec 2025 | 81,781 | 0.690 | 19 | 87 |

## Recall (oblast-level official alerts with a volunteer match)

| Period | Official oblast alerts | Matched share |
|---|---:|---:|
| post-Dec 2025 | 472 | 0.627 |
| pre-Dec 2025 | 64,842 | 0.793 |

## Monthly matched share

Full table: `output/analysis/feed_integrity_monthly.csv`. Months with fewer than 50 volunteer alerts are noisy.

## By oblast

Full table: `output/analysis/feed_integrity_by_oblast.csv`. Oblasts with fewer than 50 alerts in a period are small-sample.
