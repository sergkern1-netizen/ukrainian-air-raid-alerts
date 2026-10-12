# Chapter 1: When sirens sound, and how long they last

*How long alerts last and when they start.*

Everything in this chapter comes from the volunteer alert record, from 25 February 2022 to 11
October 2026. It counts **what was recorded**, not what happened. The record has no launch times,
no impact times and no threat types, so it cannot tell you how much notice people had before an
alert or what caused an alert. Read it as a picture of the rhythm of alerts, not a measure of danger.

Reproduce every number and chart with `python -m scripts.chapter01_timing`.

---

## The short version

- **A typical alert lasts about 30 to 31 minutes.** This is the median, the middle value: half of
  all alerts end within about that time.
- **Most of the rest end within two hours, but about 1 in 13 alerts runs for more than two hours.**
- **Alerts are grouped into waves, and there are many each day.** A wave is a group of alerts that
  follow one another closely. On a typical day there are 14 separate waves across the country.
- **Most nights had at least one alert.** Of 1,689 complete nights since 2022, all but one had at
  least one alert start somewhere in Ukraine.

---

## 1. How long alerts last

![How long alerts lasted](figures/ch01_duration_bands.png)

| How long | Share of alerts |
|---|---:|
| Under 15 minutes | 19% |
| 15 to 30 minutes | 27% |
| 30 to 60 minutes | 32% |
| 1 to 2 hours | 15% |
| 2 to 4 hours | 6% |
| Over 4 hours | 1% |

- **Median:** 30 minutes. **90% of alerts end within about 104 minutes.**
- **Under 30 minutes:** 45% of alerts.
- **Over an hour:** 22% of alerts.
- **Over three hours:** 3% of alerts.

**In plain terms.** The typical recorded alert lasted about 30 to 31 minutes. More than one in
five lasted over an hour, and about 1 in 13 ran past two hours.

**Caveat.** About 5% of end times in the record were inferred, meaning the dataset's maintainers
estimated them because nobody recorded them. If those alerts are excluded, the median moves from
30.0 to 31.1 minutes and the share over an hour from 22% to 23%. The difference is small, but it
is in the direction of longer alerts. The spike at exactly 30.0 minutes comes from the estimated
alert records: all 5,812 of them last exactly 30.0 minutes, while only 43 recorded alerts do.
Because the estimated end time sits on the median, the "about 30 to 31 minutes" statement is
partly affected by it.

---

## 2. When alerts start

![When alerts start, by hour](figures/ch01_hour_of_day.png)

Alerts start at every hour, but not evenly. The busiest hours are late morning and early afternoon
(about 10:00 to 13:00, Kyiv time). The quietest is about 06:00. The 34% below and the hour
shares count distinct start times, not alert records.

**Night** here means 22:00 to 07:00. Night holds **34%** of alert starts, counted on distinct
start times (113,142 distinct start times among 115,989 alert records). If alerts were spread evenly across the day,
night would hold 37.5%, because it covers 9 of 24 hours. So night holds slightly less than an even
spread would give: alerts start a little less often per night hour than per daytime hour.

---

## 3. Nights

![Nights with an alert, by year](figures/ch01_nights_by_year.png)

Across the country, 1,688 of 1,689 complete nights (99.9%) since February 2022 had at least one
alert start between 22:00 and 07:00. The night beginning 22:00 on 11 October 2026 is not yet
complete, so it is excluded. The one untouched complete night is 2022-12-25. No
start was recorded; the record cannot show whether the night was quiet or unrecorded.

**Read this carefully.** This counts whether *any* oblast (a region of Ukraine) had an alert in the
night window. It does not mean that every household had an alert every night. A single alert in a distant oblast counts
the same as one over a whole region. A per-region view of night alerts is planned for a later
chapter, with the same caveats.

---

## 4. How many alerts in a day

![Separate alert waves per day](figures/ch01_waves_per_day.png)

This analysis groups alerts into **waves**: groups of alerts that follow one another closely,
where each alert starts within 30 minutes of the previous one (see [the glossary](../GLOSSARY.md)).

- **Typical day:** 14 separate waves (median). The 90th percentile is 18 waves: 9 days in 10 had
  18 waves or fewer. About 1 day in 7 had 18 or more.
- **Almost every day has many waves.** Every complete day had at least three waves; the final
  partial day (11 October) is not in that count.
- **Wave pairs.** A wave pair is two waves that follow each other in time. Two waves are
  *non-overlapping* when the first has fully ended before the second starts. For example, if one
  wave runs from 10:00 to 10:40 and the next starts at 11:00, there is a 20-minute gap with no
  alert active anywhere. If the next wave starts at 10:30, the two overlap and there is no gap.
- **Overlap.** In 38% of wave pairs the waves overlapped, so there was no gap at all.
- **Gap length.** Gaps are computed only between non-overlapping waves (14,747 of 23,680 pairs,
  62%). Their median is **38 minutes**, and one in ten is 8 minutes or less. For comparison, the
  median start-to-start interval between waves is 81 minutes. Estimated end times affect where
  some waves end, so these gaps carry that caveat.

**In plain terms.** Waves are national groupings of alerts, not one event in one
place. Among non-overlapping waves, the median gap between waves is 38 minutes.

---

## What this chapter cannot tell you

- **How much notice people had before an alert.** The record has no times of launches or of what
  was hit.
- **What kind of threat caused an alert.** The record does not say.
- **What any one person experienced.** The figures count oblast-level alerts across the country.
- **Risk by place.** This is not a measure of risk by place.
- **Whether the record is complete.** It is a volunteer record with no ground truth to check it
  against.

For warnings and shelter guidance, use official channels of the Air Force and the civil-protection
authorities.

---

## Method

- **Data:** the volunteer alert record, 115,989 alert records after removing exact duplicates.
- **Durations:** end time minus start time, in minutes. Alert records with zero or negative duration are
  excluded (6 records).
- **Local time:** Kyiv time, for hours and nights.
- **Nights:** a night starts at 22:00 on one date and ends at 07:00 the next. It counts as touched
  if any oblast starts an alert inside that window.
- **Waves:** a 30-minute gap rule on the start times across all oblasts (see
  `scripts/alert_waves.py`).
- **Script:** `scripts/chapter01_timing.py`. The numbers are reproduced by the script and saved to
  `output/analysis/` (gitignored); the chapter text is written by hand.
