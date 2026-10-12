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
