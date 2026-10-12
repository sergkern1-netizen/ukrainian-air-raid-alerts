# Glossary

Plain definitions for the terms used across this repository.

**Alert record.** One row in the volunteer feed: an oblast, a start time and an end time. It
records that a siren was reported for that oblast over that period. It does not record the threat
type, the cause, or whether anything was hit.

**Start instant.** A distinct start time across all oblasts. Several oblasts can share one start
instant.

**Wave.** A run of start instants in which each start is no more than a set gap after the
previous one. The project uses gaps of 5, 10, 15, 30 and 60 minutes. A wave is a grouping for
analysis, not an event with a known cause.

**Duration.** The time from an alert's start to its recorded end, in minutes. It is how long a
siren was reported, not how long people had to take cover.

**Naive end time.** An end time that was inferred rather than recorded. About 5% of volunteer rows
carry this flag.

**Official record.** The alert record from the official feed, used as a cross-check. It ends on
2026-09-07, so comparisons stop there.

**Volunteer record.** The alert record kept by volunteers. It is the project's main target series,
and it has no ground truth to check it against.

**Match.** A volunteer alert is matched when an official alert in the same oblast starts within
5 minutes. A match shows that both feeds recorded an alert at about the same time. It does not show
that the alert was correct.

**Match rate.** The share of volunteer alerts that are matched. It is a measure of agreement between
the two feeds, not of accuracy.

**Lag.** The difference between a volunteer start and the nearest matched official start. Lags of
seconds to minutes describe recording delay. They are not warning time.

**Overlap window.** The period when both feeds have data, up to the official feed's last record
(2026-09-07). Match-based figures use only this window.

**Oblast, raion, hromada.** Administrative levels in Ukraine, from largest to smallest. The official
feed moved from mostly oblast-level records to raion-level records in December 2025, so counts
before and after that date are not directly comparable.

**Co-occurrence and Jaccard.** Two oblasts co-occur when both appear in the same wave. The Jaccard
index is the number of waves they share divided by the number of waves either appears in. It
describes association, not cause.

**Baseline.** The trailing four-week mean of weekly alert counts. It is the project's forecast
benchmark, and no model beat it in the backtest.

**WAPE.** Weighted absolute percentage error: the total absolute error divided by the total actual.
It is the project's primary accuracy measure for weekly counts.

**Backtest.** Testing a method on past data, refitting only on data before each forecast point.
