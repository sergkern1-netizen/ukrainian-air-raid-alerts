# Defensive alert-record profiles

Purpose: support civil-protection planning, warning-system review and checks on how far the
alert record can be trusted. Descriptive only.

Out of scope: forecasts of when or where attacks will occur, rankings of oblasts as targets,
and links to military units or weapon types (not recorded in the feed).

Limits: no population data (no per-capita figures). The feed does not record threat type.
The official feed ends on 2026-09-07. Duration and night-share use the whole volunteer feed;
match-based sections use the overlap window.

## 1. Alert duration by oblast

Duration = finished_at minus started_at, in minutes. Rows with zero or negative duration are
excluded. Whole feed.

| Oblast | Alerts | Median (min) | p90 (min) | p99 (min) |
|---|---:|---:|---:|---:|
| Dnipropetrovska oblast | 13,724 | 23 | 65 | 266 |
| Kharkivska oblast | 12,980 | 27 | 69 | 181 |
| Zaporizka oblast | 8,969 | 36 | 106 | 269 |
| Sumska oblast | 8,737 | 30 | 93 | 218 |
| Donetska oblast | 8,546 | 43 | 170 | 359 |
| Mykolaivska oblast | 7,883 | 29 | 84 | 235 |
| Poltavska oblast | 6,559 | 32 | 100 | 264 |
| Khersonska oblast | 6,430 | 30 | 92 | 268 |
| Kirovohradska oblast | 6,332 | 31 | 108 | 286 |
| Chernihivska oblast | 5,608 | 33 | 107 | 252 |
| Odeska oblast | 4,586 | 25 | 85 | 213 |
| Kyivska oblast | 4,454 | 30 | 99 | 241 |
| Cherkaska oblast | 3,889 | 33 | 115 | 278 |
| Kyiv City | 2,669 | 31 | 110 | 256 |
| Zhytomyrska oblast | 2,322 | 37 | 135 | 284 |
| Volynska oblast | 2,197 | 40 | 137 | 406 |
| Vinnytska oblast | 2,082 | 36 | 138 | 294 |
| Lvivska oblast | 1,789 | 31 | 103 | 225 |
| Khmelnytska oblast | 1,363 | 41 | 126 | 242 |
| Rivnenska oblast | 1,281 | 38 | 124 | 249 |
| Ternopilska oblast | 1,012 | 43 | 131 | 277 |
| Chernivetska oblast | 914 | 44 | 141 | 304 |
| Ivano-Frankivska oblast | 893 | 39 | 121 | 228 |
| Zakarpatska oblast | 761 | 41 | 127 | 246 |
| Luhanska oblast | 3 | 30 | 30 | 30 |

## 2. Night versus day exposure

Night = 22:00 to 07:00 Europe/Kyiv time. Share of alert starts in the night window.

| Oblast | Alerts | Night share |
|---|---:|---:|
| Dnipropetrovska oblast | 13,728 | 0.304 |
| Kharkivska oblast | 12,980 | 0.325 |
| Zaporizka oblast | 8,969 | 0.317 |
| Sumska oblast | 8,737 | 0.311 |
| Donetska oblast | 8,546 | 0.333 |
| Mykolaivska oblast | 7,883 | 0.328 |
| Poltavska oblast | 6,559 | 0.347 |
| Khersonska oblast | 6,430 | 0.349 |
| Kirovohradska oblast | 6,333 | 0.345 |
| Chernihivska oblast | 5,608 | 0.350 |
| Odeska oblast | 4,586 | 0.384 |
| Kyivska oblast | 4,455 | 0.379 |
| Cherkaska oblast | 3,889 | 0.384 |
| Kyiv City | 2,669 | 0.413 |
| Zhytomyrska oblast | 2,322 | 0.436 |
| Volynska oblast | 2,197 | 0.355 |
| Vinnytska oblast | 2,082 | 0.424 |
| Lvivska oblast | 1,789 | 0.349 |
| Khmelnytska oblast | 1,363 | 0.457 |
| Rivnenska oblast | 1,281 | 0.367 |
| Ternopilska oblast | 1,012 | 0.386 |
| Chernivetska oblast | 914 | 0.373 |
| Ivano-Frankivska oblast | 893 | 0.339 |
| Zakarpatska oblast | 761 | 0.318 |
| Luhanska oblast | 3 | 0.000 (small sample) |

Night share by season (all oblasts): autumn 0.357, spring 0.334, summer 0.358, winter 0.316

## 3. Warning timeliness: volunteer minus official lag

For volunteer alerts matched to an official oblast alert within 5 minutes. Positive lag means the
volunteer record came after the official one. Overlap window up to the official feed's last start.

| Oblast | Matched alerts | Median lag (s) | p90 absolute lag (s) |
|---|---:|---:|---:|
| Zaporizka oblast | 5,676 | 18 | 74 |
| Donetska oblast | 5,282 | 21 | 68 |
| Kharkivska oblast | 4,111 | 22 | 124 |
| Dnipropetrovska oblast | 3,692 | 20 | 79 |
| Poltavska oblast | 3,516 | 18 | 60 |
| Mykolaivska oblast | 3,060 | 16 | 67 |
| Kirovohradska oblast | 3,033 | 14 | 64 |
| Khersonska oblast | 2,667 | 19 | 72 |
| Sumska oblast | 2,483 | 17 | 94 |
| Cherkaska oblast | 2,262 | 18 | 61 |
| Odeska oblast | 2,031 | 17 | 109 |
| Chernihivska oblast | 1,987 | 19 | 86 |
| Kyiv City | 1,829 | 15 | 85 |
| Kyivska oblast | 1,546 | 18 | 84 |
| Vinnytska oblast | 1,368 | 17 | 70 |
| Zhytomyrska oblast | 1,196 | 23 | 85 |
| Khmelnytska oblast | 846 | 25 | 99 |
| Rivnenska oblast | 814 | 22 | 116 |
| Ternopilska oblast | 794 | 25 | 105 |
| Volynska oblast | 747 | 29 | 103 |
| Chernivetska oblast | 716 | 26 | 104 |
| Ivano-Frankivska oblast | 686 | 30 | 114 |
| Lvivska oblast | 685 | 31 | 126 |
| Zakarpatska oblast | 651 | 32 | 117 |
| Luhanska oblast | 1 (small sample) | 47 | 47 |

## 4. Feed reliability: match rate by oblast

Share of volunteer alerts matched to an official oblast alert within 5 minutes. Overlap window.
Small samples (fewer than 50 alerts in a period) are flagged.

| Oblast | Match before Dec 2025 | n | Match from Dec 2025 | n |
|---|---:|---:|---:|---:|
| Cherkaska oblast | 0.760 | 2,978 | 0.000 | 749 |
| Chernihivska oblast | 0.599 | 3,316 | 0.000 | 2,113 |
| Chernivetska oblast | 0.918 | 780 | 0.000 | 100 |
| Dnipropetrovska oblast | 0.396 | 9,331 | 0.000 | 3,699 |
| Donetska oblast | 0.725 | 7,288 | 0.000 | 1,131 |
| Ivano-Frankivska oblast | 0.860 | 798 | 0.000 | 86 |
| Kharkivska oblast | 0.496 | 8,296 | 0.000 | 4,034 |
| Khersonska oblast | 0.578 | 4,616 | 0.000 | 1,681 |
| Khmelnytska oblast | 0.744 | 1,137 | 0.000 | 159 |
| Kirovohradska oblast | 0.603 | 5,029 | 0.000 | 1,063 |
| Kyiv City | 0.785 | 1,953 | 0.523 | 564 |
| Kyivska oblast | 0.538 | 2,872 | 0.000 | 1,155 |
| Luhanska oblast | 0.333* | 3 | n/a | 0 |
| Lvivska oblast | 0.729 | 939 | 0.000 | 718 |
| Mykolaivska oblast | 0.559 | 5,470 | 0.000 | 1,941 |
| Odeska oblast | 0.783 | 2,594 | 0.000 | 1,701 |
| Poltavska oblast | 0.748 | 4,698 | 0.000 | 1,627 |
| Rivnenska oblast | 0.831 | 979 | 0.000 | 202 |
| Sumska oblast | 0.434 | 5,727 | 0.000 | 2,719 |
| Ternopilska oblast | 0.888 | 894 | 0.000 | 95 |
| Vinnytska oblast | 0.827 | 1,654 | 0.000 | 284 |
| Volynska oblast | 0.674 | 1,109 | 0.000 | 948 |
| Zakarpatska oblast | 0.948 | 687 | 0.000 | 74 |
| Zaporizka oblast | 0.812 | 6,986 | 0.000 | 1,757 |
| Zhytomyrska oblast | 0.726 | 1,647 | 0.000 | 489 |

`*` = small sample.

## 5. Long-alert register (longer than 6 hours)

370 volunteer alerts exceed 6 hours. Full list in `output/analysis/long_alerts.csv`
(gitignored). The `naive` flag (inferred end time) is False for all of these rows (checked 2026-10-12: 0 of them).

| Oblast | Long alerts |
|---|---:|
| Donetska oblast | 84 |
| Dnipropetrovska oblast | 68 |
| Zaporizka oblast | 30 |
| Volynska oblast | 29 |
| Kirovohradska oblast | 24 |
| Mykolaivska oblast | 19 |
| Khersonska oblast | 17 |
| Kharkivska oblast | 13 |
| Poltavska oblast | 12 |
| Cherkaska oblast | 10 |
| Kyivska oblast | 10 |
| Chernihivska oblast | 10 |
| Zhytomyrska oblast | 9 |
| Sumska oblast | 5 |
| Ternopilska oblast | 5 |
| Chernivetska oblast | 5 |
| Kyiv City | 4 |
| Vinnytska oblast | 4 |
| Lvivska oblast | 4 |
| Khmelnytska oblast | 3 |
| Rivnenska oblast | 2 |
| Zakarpatska oblast | 2 |
| Odeska oblast | 1 |

## 6. Granularity change in the official feed

Official records by level, and distinct oblast names, before and after the December 2025 break.

| Period | Records by level | Distinct oblast names |
|---|---|---:|
| before Dec 2025 | hromada 14,787, oblast 64,842, raion 19,324 | 25 |
| from Dec 2025 | hromada 6,025, oblast 472, raion 79,980 | 24 |

Records from the raion level can be several per oblast event, so counts are not comparable
across the break (see `docs/gate3_results.md`).
