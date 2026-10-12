# Project summary: main problems as of 2026-10-12

Problems are ranked by how much they limit what the repository can honestly claim. Each entry
gives the problem, the evidence (file and line, or the number), what it blocks, and the next
action or the owner decision needed. No numbers here are new; each is quoted from the file cited.
Line numbers refer to the working tree on 2026-10-12 (README line numbers are after the
navigation index was added).

| Rank | Problem | Blocks | Needs |
|---|---|---|---|
| 1 | Volunteer feed has no ground truth; agreement with the official feed declined | Any accuracy, completeness or "level" claim | Independent source (owner decision) |
| 2 | No model beats the baseline; interval coverage missed | Any forecast-skill or calibrated-uncertainty claim | Owner decision on Gate 5 scope |
| 3 | Official feed changed granularity and ended 2026-09-07 | Oblast-level comparison in 2026; any cross-check after 2026-09-07 | Accept as a permanent limit or find a source |
| 4 | Volunteer data licence unconfirmed | Clear redistribution and reuse statements | Read the dataset's licence statement |
| 5 | Telegram-derived figures remain in public git history | The statement that the project does not publish Telegram-derived data | Owner decision on history rewrite |
| 6 | Real-time monitoring descoped; needs a token | Any "live" or latency claim (criterion 3) | alerts.in.ua token |
| 7 | Inconsistencies between documents | Reader trust; a reader can quote the stale version | Edit the listed files |
| 8 | Chapter review has no written record; Chapter 7 has a gap | Calling Chapters 6 and 7 independently reviewed | Review record and fix |
| 9 | Root clutter, historical logs, personal data in a public log | Navigation; privacy | Owner decision on archive moves |

---

## 1. The volunteer feed has no ground truth, and its agreement with the official feed declined

- **Problem.** The forecast target and every chapter rely on the volunteer record
  (`volunteer_data_en.csv`). Nothing independent checks it. The only cross-check is the official
  record, which is not ground truth either, and the two are not independent (the volunteer
  channel's sources include the Air Force channel).
- **Evidence.**
  - `docs/gate3_results.md` lines 153–154: "No ground truth. Neither feed can be verified against
    an independent record." Lines 162–163: the two feeds "are therefore not independent".
  - `docs/chapters/04-feed-reliability.md` line 19: 65% of volunteer alerts match an official
    alert over the whole period. Line 21: agreement "fell by about 12 percentage points a year
    between 2023 and 2025" and has stayed near 54% since. Line 23: no step at the December 2025
    break (six months either side about 53%).
  - Chapter 4 line 83: largest falls Lvivska 78% → 10%, Volynska 71% → 11%, Donetska 74% → 26%.
  - Pre-break rate 70.0% and post-break 52.7% over the overlap window (`docs/gate3_results.md`
    lines 89–100; `docs/analysis/feed_integrity.md` lines 41–44).
  - Alert types (yellow, red, drone) are not in either file (`docs/gate3_results.md` lines 145–150),
    so a change in what volunteers post cannot be separated from a change in events.
- **What it blocks.** Any statement that the volunteer record is accurate or complete
  (`docs/SAFETY.md` lines 26–27 already forbid it). Any explanation of the western divergence. Any
  claim that the 2026 rise in recorded alerts (Chapter 2) reflects events rather than reporting.
- **Next action / owner decision.** Decide whether to seek an independent source. Options named
  in `docs/gate3_results.md` lines 169–171: UkraineAlarm or alerts.in.ua (credentials needed), or
  a dated sample of events verified by hand. Until then, every chapter must keep "agreement is not
  accuracy" wording.

## 2. The MVP forecast is not beaten by any model, and interval coverage is missed

- **Problem.** The deliverable is the trailing four-week mean. No candidate beat it. The approved
  interval-coverage criterion was not met by any candidate, and the deliverable's own intervals
  were never checked against the bands.
- **Evidence.**
  - `docs/gate3_results.md` lines 15–19: baseline weekly WAPE 8.52%; NB 12.40% (worse, p = 0.027);
    ARIMA 8.55% (p = 0.97). Coverage: NB 88.5% / 94.2%, ARIMA 94.2% / 100%, against bands
    77–83% / 93–97% (line 21).
  - `docs/gate4_status.md` lines 4–6: Gate 4 outcome "not passed"; criteria 1 and 2 unmet.
  - `README.md` (Results / What it does, step 6): baseline intervals are quantiles of in-sample
    backtest residuals, "so they are optimistic".
  - Statistical power is weak: 52 origins; the 13-origin window "gives very little power"
    (`docs/gate3_results.md` lines 45–46, 157–158).
  - Short post-break window: 40 weeks (`docs/gate3_results.md` lines 155–156).
- **What it blocks.** Any claim of forecast skill beyond a moving average. Any calibrated
  uncertainty statement for the published forecast. Any 30-day accuracy claim (`CLAUDE.md`,
  "What not to do").
- **Next action / owner decision.** Gate 5 (ship as is, or expand) — see inconsistency 7.2 below on
  whether this was already decided. If work continues: an out-of-sample coverage check for the
  baseline's intervals (a held-out residual window), with no threshold change.

## 3. The official feed changed granularity and stops on 2026-09-07; oblast-level comparison is blind for 2026

- **Problem.** The cross-check record moved from oblast rows to raion rows, gradually through 2025.
  In 2026 its only oblast-level rows are Kyiv City. It ends on 2026-09-07, so there is no
  cross-check after that date.
- **Evidence.**
  - `docs/chapters/06-granularity-and-official-feed.md` line 33: after the change, oblast-level
    rows are only Kyiv City, 472 rows, 448 in 2026. Lines 120: "All 448 oblast-level rows in 2026
    are Kyiv City."
  - Chapter 6 line 133: oblast-level-only match rate 63.7% before, 1.0% after; all-levels 70.0% and
    52.5% (Chapter 6 explains the 52.5% vs Chapter 4's 52.7% as a window difference).
  - Chapter 6 lines 19, 28, 71: the raion share first rose in January 2025 and passed half in
    August 2025; at the 1 December 2025 marker it was already about 89%.
  - Rows per oblast per day 2.92 → 12.82; official rows per volunteer alert 1.23 → 2.96 (Chapter 6,
    section 4).
  - `docs/chapters/07-provenance-and-quality.md` line 131 and `docs/FUTURE_PLANS.md` lines 55–56:
    official last start 2026-09-07; no ground truth after that date.
- **What it blocks.** A like-for-like oblast comparison between the feeds for 2026 (only Kyiv City
  can be matched at oblast level). Any before/after count comparison across 2025. Any cross-check
  of the volunteer record after 2026-09-07, including the last five weeks of the forecast target.
- **Next action / owner decision.** Record this as a permanent limit in every chapter that
  compares feeds (Chapters 4 and 6 already do). Decide whether a raion-to-oblast roll-up rule is
  worth defining; it would be a modelling choice, not a fix, and needs its own limit statement.

## 4. The volunteer data licence is not confirmed

- **Problem.** The repository's root licence is MIT, but whether it covers the data files was not
  confirmed.
- **Evidence.** `docs/gate3_results.md` lines 70–72: "Whether that licence covers the data files
  was not confirmed: `datasets/README.md` returned HTTP 503." `docs/FUTURE_PLANS.md` line 43 lists
  it as blocked. `docs/MASTER_PLAN.md` line 69: Phase 3 item 3. Contrast `README.md` line 132:
  "MIT licence per the dataset" (see inconsistency 7.1).
- **What it blocks.** A clean statement that derived tables and figures can be redistributed under
  MIT. It also bears on `CLAUDE.md`'s "Vadimkin for commercial projects" guidance.
- **Next action.** Re-fetch the dataset's own licence statement (`datasets/README.md` in the
  Vadimkin repository), record the date and text, and update the README data-source row.

## 5. Telegram-derived data remains in public git history

- **Problem.** Figures from the Kaggle "Massive Missile Attacks" dataset, every row of which cites a
  Telegram channel, were committed, then removed. The commits are on the pushed `origin/master`.
- **Evidence.** Commits `7e19df8` (added `docs/enterprise/kaggle_missile_profile.md`) and `1986c03`
  (added `docs/enterprise/kaggle_missile_descriptive.md` with record counts and monthly totals, and
  `scripts/kaggle_missile_descriptive.py`). Removed in `ed74cdd`. `git rev-list --count
  origin/master..master` is 0, so history is public. `docs/FUTURE_PLANS.md` lines 10–13 and 20–22;
  `docs/SAFETY.md` lines 28–29.
- **What it blocks.** An unqualified statement that the project does not publish Telegram-derived
  figures. The current tree complies; the history does not.
- **Owner decision.** Either rewrite history (force-push; breaks existing clones and the
  `mvp-v0.1.0` tag if it is pushed later) or keep it and state in `FUTURE_PLANS.md` that the
  historical commits remain public by decision. Also decide on the local copy in
  `data/raw/kaggle_missile/` (`FUTURE_PLANS.md` lines 18–19).

## 6. Real-time monitoring is descoped and needs a token

- **Problem.** Criterion 3 (latency under 5 minutes) was never measured. The poller, Telegram
  consumer and Docker stack exist in `src/ingestion/` but are not called by `run_pipeline.py`.
- **Evidence.** `docs/gate4_status.md` line 14 (criterion 3 descoped by owner, 2026-10-12) and
  lines 25–26 ("not a measured pass"). Lines 40–44: the live poller test fails with the placeholder
  token. `README.md` line 239. The Telegram path "has not been run end to end" (README, "Components
  not wired into the pipeline").
- **What it blocks.** Any "live" or "real-time" description (`docs/SAFETY.md` lines 24–25). Gate 4
  criterion 6 stays "partly met" because no live-source timestamps exist (`docs/gate4_status.md`
  line 17).
- **Next action.** Obtain the alerts.in.ua token, then run
  `RUN_LOAD_TESTS=1 pytest tests/test_load_alerts_poller.py` and record a latency measurement.
  Also note that Telegram ingestion is blocked by the Telegram API terms
  (`docs/enterprise/STATUS.md` line 11), so the Telegram consumer has no permitted source.

## 7. Inconsistencies between documents

Each item quotes both places. None changes a number; they are wording or status conflicts.

1. **Volunteer licence.** `README.md` line 132: "MIT licence per the dataset." versus
   `docs/gate3_results.md` lines 70–72: "Whether that licence covers the data files was not
   confirmed".
2. **Gate 5 status.** `README.md` line 100: "MVP shipped 2026-10-12 with documented misses." versus
   `docs/gate4_status.md` lines 89–90: "Gate 5 (ship the MVP or expand to the enterprise scope) is
   the next owner decision." `archive/AI_INTERACTION_LOG.txt` (entry "~16:50") records the answer "Gate 5:
   Ship the MVP" and the local tag `mvp-v0.1.0`, so `gate4_status.md` is stale.
3. **RMSE target.** `README.md` line 231: "Replaces the RMSE < 5 target in CLAUDE.md". `CLAUDE.md`
   no longer contains an RMSE < 5 target; its criterion 1 (line 74) is now the weekly WAPE
   criterion, and only the Gate 3 checklist (line 206) still says "RMSE/MAE metrics calculated".
4. **Criterion 1 wording.** `README.md` line 233 ticks "[x] Weekly WAPE is the primary metric; the
   backtest reports it against the baseline" versus `docs/gate4_status.md` line 12: criterion 1
   "Weekly WAPE beats the trailing four-week mean baseline" is **Not met**. Both are true of
   different wordings, but a reader sees a tick in one and a miss in the other. The README list
   also omits criterion 6 ("partly met" in `gate4_status.md` line 17).
5. **Timing of the granularity change.** `README.md` line 133: "Changes to mostly raion level from
   December 2025." and `docs/GLOSSARY.md` lines 41–42: "moved from mostly oblast-level records to
   raion-level records in December 2025" versus `docs/chapters/06-granularity-and-official-feed.md`
   line 19: the district share "first rose in January 2025 and had passed half by August 2025".
6. **Planned items already done.** `docs/FUTURE_PLANS.md` lines 24–28 list `docs/SAFETY.md` and
   `docs/GLOSSARY.md` as "Planned" versus `docs/MASTER_PLAN.md` line 79: "Step 1 (SAFETY.md and
   GLOSSARY.md) is done."
7. **Links to official channels.** `docs/SAFETY.md` lines 43–44: "This repository links to them"
   versus no link to any official warning channel in `SAFETY.md` or the README. The README index
   now names the channels without URLs; real URLs need to be added by someone who verifies them.
8. **"Warning timeliness".** `docs/analysis/defensive_profiles.md` line 80 heading: "Warning
   timeliness: volunteer minus official lag" versus `docs/SAFETY.md` lines 11–12: the lag "is a
   recording delay. It is not the time people had to take cover."
9. **"Every number is reproduced by the chapter's script."** `docs/chapters/README.md` line 4
   versus the chapters' own notes, for example `docs/chapters/07-provenance-and-quality.md` line
   161 ("Computed by the writer, not by the script: the 38.0% share") and Chapter 6 line 171.
10. **Stale headers on historical files.** `archive/UKRAINIAN_AIR_RAID_ALERTS_RESEARCH_v2.0.md` line 3:
    "Status: Authoritative"; `CLAUDE.md` line 5: "Research Complete — Ready for Implementation
    Phase"; `CLAUDE.md` lines 54–55: Vadimkin "299K+ records", "2022-02-24 to 2026-09-07". Chapter 7
    lines 34–37: 299,275 raw official rows of which 113,845 are exact duplicates; the volunteer file
    has 115,989 rows to 11 October 2026; the official record starts 15 March 2022.
11. **Identity.** `CLAUDE.md` lines 14–15: "Real-world defense analysis", target users "defensive
    intelligence professionals" versus `docs/MASTER_PLAN.md` line 8: "Ukrainian air-alert records:
    an open, reproducible analysis" and `docs/SAFETY.md` lines 3–5 (not a tool for planning or
    responding to attacks). The master plan is still marked "draft for owner approval" (line 3).

- **Next action.** Edit items 1, 2, 3, 5, 6 and 8 (wording only). Items 7, 10 and 11 need an owner
  decision. Item 9: change the chapter-list sentence to "Every number is reproduced by the
  chapter's script or by a stated calculation from its output."

## 8. Chapter review: no written record, and a gap in Chapter 7

- **Update.** A written review log now exists: `docs/chapters/REVIEW_LOG.md`. Chapters 1 to 4 have
  no independent Skeptic pass. The text below describes the state before that log was written.
- **Problem.** Chapters 6 and 7 are marked "Done" in `docs/chapters/README.md` (lines 14–15) and
  "reviewed" in their commit messages (`fd8877b`, `e9bb742`), but there is no review record in the
  repository: who reviewed, against what checklist (`docs/MASTER_PLAN.md` line 55: "every public
  number traces to a script and a limit"), and what was changed. Chapter 7 was committed at 21:54
  on 2026-10-12, while this summary was being written.
- **Evidence of an open gap.** `docs/chapters/07-provenance-and-quality.md` section 2 is titled
  "Duplicates and conflicts" (line 45) and its "cannot tell you" list refers to conflicting end
  times (line 141), but the section gives no conflict count; there is an empty paragraph at lines
  48–49. The script computes one (`scripts/chapter07_provenance.py` lines 93–99,
  `rows_same_name_and_start_diff_finish`).
- **What it blocks.** Describing Chapters 6 and 7 as independently reviewed. Chapter 7 as the
  reference for "how duplicates were handled".
- **Next action.** Add a short review record (date, reviewer, checklist, outcome) for each chapter,
  for example a "Review" line in each chapter's method section or a `docs/chapters/REVIEWS.md`.
  Owner to decide whether Chapter 7 states the conflict count from the script or drops the
  conflict wording.

## 9. Root clutter, historical logs and personal data

- **Problem.** 17 of the 30 root-level files are research-phase plans or session logs (11
  historical, 6 internal logs; see the tables in `docs/NAVIGATION.md`).
  Several carry headers that read as current ("Authoritative", "Ready for Implementation",
  "Final & Binding").
- **Evidence.** `docs/NAVIGATION.md`, "Root-level files, one by one". `archive/AI_INTERACTION_LOG.txt`
  line 10 names the owner's personal email address and is on the pushed `origin/master`.
  `DATA_SOURCES_REFERENCE.json` is listed in `CLAUDE.md` "References" but ignored by
  `.gitignore` line 29 (`*.json`), so public readers cannot see it.
- **What it blocks.** Easy navigation for new readers; a reader may cite a superseded plan.
- **Owner decision.** Approve the archive moves proposed in `docs/NAVIGATION.md`; decide whether
  the interaction log stays public and whether to remove the email address from it (history would
  still hold it); decide whether to track or drop `DATA_SOURCES_REFERENCE.json`.

---

## Not re-checked in this summary

- The test count in `docs/gate4_status.md` line 35 (106 passed, 3 skipped) was not re-run.
- The download path of `run_pipeline.py` (without `--offline`) was not re-run
  (`docs/gate4_status.md` line 15).
