# News and official sources for alert-wave reconciliation: research spike (2026-10-12)

Question: can news or official dispatches explain why an alert wave happened (threat type, drones
vs missiles) and help audit anomalies: the low-match oblasts and the long waves?

Method: each source's own terms page was fetched and quoted. Search summaries were not used as
evidence. Terms are for the owner's review, not legal advice.

## 1. Source evaluation matrix

| Source | Access | Update | Legal and provenance | Effort |
|---|---|---|---|---|
| **GDELT Project** (gdeltproject.org) | Bulk CSV event and mention exports, plus daily files | Every 15 min (per GDELT docs); "daily updates" on the about page | **Strongest.** "unlimited and unrestricted use" for academic, commercial and government use. Citation and link required. | Medium: large files, machine-coded events |
| **Suspilne** (suspilne.media) | HTML only; no RSS or API documented | Continuous | Copyright held by NSTU. Partial use only with a search-indexable hyperlink, no lower than paragraph 2. **Full reprint prohibited without written permission.** Commercial use prohibited. | High: scraping not addressed, legal risk |
| **Ukrainska Pravda** (pravda.com.ua) | HTML; RSS page has no feed URL | Continuous | "© 2000-2026, УП Медіа Плюс. Усі права захищені." Use only with a link, no lower than paragraph 3. Interfax-Ukraine content prohibited to redistribute. | High |
| **LIGA.net** | HTML; an RSS page is linked but its terms are not in the page | Continuous | Copyright notice present. Reuse rules on a linked page not read. | High |
| **RBC-Ukraine** (rbc.ua) | HTML; no RSS | Continuous | Copyright "© LLC «UBT MEDIA»". Photos CC BY 4.0 (journalist photos only). No text reuse terms. | High |
| **Air Force (@kpszsu)** | Telegram only | Several per day | **Blocked.** Telegram API terms bar aggregating Telegram data for ML; fake channels exist. Already recorded in `candidates_review.md`. | Not pursued |
| **State Emergency Service (DSNS)** (dsns.gov.ua) | Site blocks automated access (HTTP 403) | Unknown | Not verified: no terms could be read. | Not pursued |

## 2. Top recommendation for the PoC

**GDELT.** It is the only source with a clear, defensible licence, it is timestamped (15-minute
updates, so it can be aligned with waves), and it stores article URLs and metadata rather than
article text, which keeps the project clear of outlet copyright.

Limits to state up front:
- GDELT event codes are coarse (CAMEO). They do not reliably name the threat type (MiG-31K,
  Shahed, ballistic). Threat-type labels would need a text step, which is not in scope yet.
- Precision is unknown. Every match must be checked by hand before any claim.
- The news outlets above can be cited as links, but their text should not be stored or republished.

## 3. PoC workflow (20 anomalous waves)

1. **Select 20 anomalies.** Pick 10 waves over 24 h (from `output/analysis/waves_gap30.csv`) and
   10 volunteer alerts from the lowest-match oblasts (Sumska, Donetska) in the overlap window.
   Record the selection rule and the seed before looking at any news.
2. **Match within a window.** For each anomaly, take GDELT events for Ukraine within
   [start − 60 min, end + 60 min] whose event code is an attack or aerial-weapon code. Record the
   count of matches and the nearest match time. Use a regex on the GDELT source URL for oblast
   names as a secondary check.
3. **Judge by hand.** A person reads each matched GDELT URL and records: match, partial, or no
   match. Report the agreement rate and the number of anomalies that gain an explanation. Only
   then decide whether to scale.

## 4. Corrections to the research brief

- The brief says "14 waves lasting >24 h." The data does not show that. At 5–30 min gaps there are
  10 to 11 waves over 24 h. At a 60-min gap there are 54. "14" was a row-level count (14 volunteer
  rows over 24 h), not a wave count.
- The 39% Sumska figure in the brief is a different measure: it came from matching official alerts
  to volunteer alerts within ±10 minutes (recall), not volunteer alerts to official ones within
  5 minutes (precision). Our precision figures in `docs/analysis/feed_integrity.md` are Sumska
  50.1% before December 2025 and 46.5% after (overlap window). Quote the measure with its number.

## 5. Sample test: GDELT, 2026-10-09 (2026-10-12)

Downloaded with owner approval: `http://data.gdeltproject.org/events/20261009.export.CSV.zip`,
7,315,169 bytes, SHA-256 `680968bc40825ae05c8fe50d6a3032b34f99979d02161b0bd4f441896eabbd68`.
Stored in the session scratch folder, not in the repository. It contains one GDELT 1.0 daily
events file (45,494,980 bytes, 116,062 rows, 58 columns).

Findings:
- **Ukraine events** (ActionGeo country `UP`): 1,863 of 116,062 rows.
- **Attack-like CAMEO codes** (180–195, the "use force / employ weapons" family): 232.
  Code 190 ("use conventional military force") is 161 of the 232. It is broad and does not name
  an air raid. Code 195 ("employ aerial weapons") is only 9.
- **Time resolution: none.** `DATEADDED` and `SQLDATE` are day-level (`YYYYMMDD`) in the 1.0 daily
  file. It cannot be aligned with alert waves, which are timed to the minute. This corrects the
  PoC plan above, which assumed time-stamped events.
- **Source domains** for the attack-like events are mixed (Interfax-Ukraine, The Moscow Times,
  Daily Kos, AOL and others). Each event carries a URL that a person must read to judge.

Next step for timing: GDELT 2.0 publishes 15-minute files
(`http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip`). The existence of two
test files was confirmed by HEAD requests only (65 KB at 12:00 UTC and 148 KB at 00:00 UTC on
2026-10-09). A full day is 96 files. Downloading them needs separate owner approval.

## 6. GDELT 2.0, 96 files for 2026-10-09 (2026-10-12)

Downloaded with owner approval: `http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip`
for every 15 minutes of 2026-10-09 UTC. All 96 files exist, total 7.11 MB, and all extracted.
Files stored in the session scratch folder, not in the repository.

- **Cross-check:** the 2.0 files give 1,863 Ukraine events and 232 attack-coded events, the same
  totals as the 1.0 daily file for the same date.
- **Hourly attack-coded events** are present in 23 of 24 hours (peak 36 at 07:00 UTC).
- **Volunteer alert starts** for the same day: 194 distinct start instants, present in all 24 hours.

**Alignment test (one day, 24 hourly points): inconclusive.** Correlation of hourly counts swings
between +0.48 (volunteer one hour before GDELT) and −0.03 (same hour), with no consistent sign.
With one day this cannot separate a real relation from noise. It is not evidence that GDELT tracks
alerts.

Caveats for the next step:
- `DATEADDED` is when GDELT recorded the article, not when the event happened. Lags of hours are
  expected, so the test needs event time, or a window wide enough to contain the lag.
- Attack-coded events include code 190 ("use conventional military force"), which is broad. A
  match needs the article text (manual reading) or a narrower code set.
- One day is too short. The next test should cover several weeks, including the known volunteer
  wave on 2026-10-09 at 07:00–08:00 UTC (the GDELT peak falls in the same hour, but that is one
  observation).

## 7. GDELT 2.0, four-week test, 2026-09-14 to 2026-10-11 (2026-10-12)

Downloaded with owner approval: 2,688 files, `http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip`,
every 15 minutes, 169.6 MB. None missing. Stored in the session scratch folder, not the repository.

Coverage over 672 hours (28 days):
- Ukraine events (ActionGeo `UP`): 45,515. Attack-coded (180–195 family): 6,529.
- Hours with at least one attack-coded event: 632 of 672. Hours with a volunteer alert start: 646.

Hourly correlation between GDELT counts and volunteer alert starts, offsets −6 to +6 hours:
- Broad family (180–195): highest absolute correlation 0.13 (lag −5). Lag 0: 0.08.
- Narrow code 195 ("employ aerial weapons", 281 events): lag 0: 0.09; highest absolute 0.10 (lag −6).

**Result: no meaningful hourly alignment.** Every value is below 0.15, and the sign changes with the
lag. A news-coded attack count does not track when alerts sounded at hourly resolution.

Interpretation: GDELT counts follow news volume, which is spread through the day, not the timing of
alerts. A reconciliation that matches waves to GDELT would mostly match noise. A link would need
the article text, a person reading each match, and a hit rate far above chance. The sample test
here does not support that.

Recommendation: stop the GDELT timing path for alert-wave reconciliation. It fails the
feasibility test, and it does not identify threat types (code 190 is generic, code 195 is rare).
If the owner still wants a news layer, the next step is a manual reading of 20 anomalous waves
against GDELT source URLs, which the owner must approve as a separate task.
