# Gate 3, Day 1: volunteer checks (R3) and source review

Context: `docs/gate2_decisions.md` (rulings R1–R4, triggers T1–T5). Data: Vadimkin
`official_data_en.csv` (after the exact-duplicate ingest rule) and `volunteer_data_en.csv`.
Run date 2026-10-12, times UTC.

## R3 results

| Check | Result | Status |
|---|---|---|
| `naive` share within 3 points of 2023–2025 level | 6.1%, 5.6%, 5.8%; 2026: 4.7% | Passed |
| Missing region explained | Luhanska oblast: 3 volunteer alerts, all on 2022-04-04; none after. Matches the README note that a permanent siren there is not in the datasets | Explained |
| Other regional mix shifts | Donetsk −5.2 pts, Kharkiv +3.5, Odesa +2.7, Chernihiv +2.6 (share of alerts). Consistent with front-line movement, not a dropout | Plausible |
| Official–volunteer overlap within 5 min, same period | Pre-Dec-2025: **69.0%**. Post-Dec-2025: **44.8%**. Drop of **24 points** | **Fails (limit 10 points) → T4 triggered** |

Overlap matches a volunteer alert to any official alert in the same oblast within 5 minutes,
at any official level. The overlap is not limited to oblast-level rows; an earlier version that
was limited to oblast rows was not meaningful after December 2025, because the official feed
has only 472 oblast rows after that date.

## Diagnosis of the overlap drop

- **Widespread, not local.** 13 of 24 regions drop by more than 20 points; median drop 24.
- **Strongest in the west.** Lviv 74% → 8%, Volyn 68% → 9%, Rivne 86% → 47%. Donetsk 74% → 23%.
- **Not explained by resolution alone.** Official raion rows still carry the oblast name, so
  matching by oblast should not drop because of the raion change. The drop means the two feeds
  disagree more after December 2025, not that the match is harder.
- **Consistent with the forecasting project's note** (`vladysalvkrutii/kse-air-alerts`): volunteer
  data is much busier than official in Lviv and Volyn.

Two explanations remain. Either the volunteer feed over-reports in the west, or the official
feed under-reports there after the change. The data cannot decide which.

## Source review

- **Official feed ended.** The public official Telegram feed (@air_alert_ua) ended on
  2026-09-07, the same date the official dataset ends. After that the volunteer feed is the only
  ongoing source. This settles the operational side of R2: any model used after September 2026
  must use volunteer data.
- **The volunteer feed is not independent.** eTryvoga's channel (t.me/UkraineAlarmSignal) is
  posted manually by about 30 volunteers, and its sources include the Air Force channel and
  regional administrations. Coverage depends on who is on shift, which makes a level change
  plausible.
- **The channel publishes more alert types than the dataset may record.** A preview of the
  channel shows yellow alerts, red alerts, drone threats and all-clears at district level.
  Whether the dataset counts drone threats and yellow alerts is unverified. It is a definitional
  question that could explain part of the level difference.
- **Other GitHub projects are not independent.** The time-series project and the forecasting
  project both build on the same Vadimkin files. They are useful as references, not as
  cross-checks.
- **Independent sources need credentials.** The UkraineAlarm API (api.ukrainealarm.com, needs an
  API key) and alerts.in.ua (needs a token, already planned in CLAUDE.md) are the only candidates
  with separate provenance. Neither is in `.env`, and history depth is unknown for both.
- **Discrepancy noted.** The forecasting project reports about 10% of volunteer alerts as `naive`.
  We measure 5.0% over the full file. Their figure may refer to a different cut; not resolved.

## Trigger status

**Update:** the project owner accepted the volunteer series as the target with its documented
caveats (see `docs/gate2_decisions.md`). That is an explicit override of T4 for the target choice.
The overlap drop is still documented in `docs/gate3_results.md`, and the model results were
produced under that override.

- **T4 (overlap differs by more than 10 points across the break): triggered.** Per R3, the
  target stays frozen and modeling is paused until the source is audited.
- Days 2–3 (harness) and Days 4–6 (model fits) are on hold. Fitting models to a series the
  pipeline cannot yet validate would produce numbers that cannot be trusted.

## Decisions needed

1. **Which feed is closer to the truth after December 2025?** The available data does not
   answer this. The usual way to answer it is an independent source, such as UkraineAlarm or
   alerts.in.ua, checked against a sample of known events. Either needs a credential from you.
2. **Definition of "alert".** Should yellow alerts and drone threats count? This changes the
   series level and needs deciding before any target is fixed.
3. **Alternatively**, accept that the volunteer feed is the target as-is, document the western
   over-reporting as a known bias, and proceed with the coverage indicator from R2. This would
   be a deviation from R3 and needs your explicit approval.
