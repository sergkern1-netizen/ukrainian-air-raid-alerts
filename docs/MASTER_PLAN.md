# Master plan

Status: draft for owner approval. Companion to `docs/SAFETY.md`, `docs/GLOSSARY.md` and
`docs/FUTURE_PLANS.md`.

## Repository identity

**Ukrainian air-alert records: an open, reproducible analysis.** This describes what the repository
contains. Words such as "civic intelligence", "production-grade" or "gold standard" are not used,
because the data cannot support them (see the Pessimist's notes below).

## Triad deliberation (summary)

**Optimist.** The alert record can help residents see typical alert lengths, night-time share and
how sirens cluster in time. It can help schools and employers see how often a day is interrupted.
Clear charts, plain-language summaries and a glossary would make it usable by people with no
research background.

**Pessimist.**
- The record has no launch or impact times, so no warning-time figure is possible.
- The volunteer feed has no ground truth. Its western over-reporting and batching are documented.
- "Disruption" figures for businesses would look operational but rest on an unvalidated feed. That
  is the main false-security risk.
- The official feed ends on 2026-09-07, so recent periods have no cross-check.
- Per-capita figures need population data, which the project does not have.

**Judge.**
- Keep the Optimist's aims: plain language, clear charts, reproducible methods.
- Phase the usefulness work. Documentation and reproducibility come first.
- Disruption metrics for schools or employers may be published only as descriptive counts of time
  under alert, with explicit "not for operational decisions" wording and the feed's limits.
- Shelter and warning-time content stays excluded (SAFETY.md).
- "Production-grade" and "gold standard" are not claims this project can support. The repository
  says what it contains and what it cannot show.

## Phases

### Phase 0: done
- MVP baseline (8.52% weekly WAPE; no model beat it). Gate 4 closed with documented misses.
- Analyses: alert waves, feed integrity, wave anatomy, Western cluster check, pair investigation,
  defensive profiles.
- Corrections to earlier overstatements (Gate 3 overlap figures, README, research brief).
- Public-safety foundations: `SAFETY.md`, `GLOSSARY.md`.
- Telegram-derived Kaggle figures removed from current docs (history still holds them; see
  `FUTURE_PLANS.md`).

### Phase 1: documentation polish (no new data)
1. Rewrite the README top layer: what the repository is and is not, five plain facts with their
   numbers, how to read a number, and links to official warning channels.
2. One figure per finding, produced by a script in `scripts/`: duration distribution, night share
   by season, match rate by oblast, wave-size distribution. Each figure states its source, date
   range and limit.
3. A `docs/HOW_TO_READ.md` for residents and a `docs/METHODS.md` index for analysts.

Exit check: every public number traces to a script and a limit (Judge's checklist).

### Phase 2: guarded usefulness
1. Per-oblast summary cards: median and p90 duration, night share, match rate, small-sample flag.
2. Time-under-alert profiles by hour and weekday, for schools and employers, labelled descriptive
   and not for operational decisions.
3. A municipal view: the same profiles for one oblast, with its reliability rating shown beside
   them.

Exit check: the Pessimist reviews each card for misreadings before release.

### Phase 3: rigour and reproducibility
1. Tests for the analysis scripts (pytest), with the golden-file pattern used for the demo.
2. A data manifest: file names, sizes, SHA-256 and access dates for every input.
3. Confirm the volunteer data licence from the dataset's own statement.
4. Population source (open, licence checked) for per-capita figures, if the owner approves it.

### Phase 4: blocked (needs an external decision)
- Real-time monitoring: needs an alerts.in.ua token, then a latency measurement.
- Any external source: needs written permission or a changed account type (see
  `docs/FUTURE_PLANS.md`).

## Immediate next step

Step 1 (SAFETY.md and GLOSSARY.md) is done. Step 2 is the README top-layer rewrite in Phase 1. It
needs your approval of the wording before I publish it, because it is the page most people will read.

## Decisions for the owner

1. Approve the repository name and description above.
2. Approve Phase 2's disruption profiles, with their descriptive wording, or keep them out.
3. Approve the population-data source in Phase 3, if per-capita figures are wanted.
