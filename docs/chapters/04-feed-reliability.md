# Chapter 4: How far the record can be trusted

*How well the volunteer alert record agrees with the official record, over time and by oblast (a region
of Ukraine, like a province).*

**What "a match" means.** A volunteer alert counts as matched if the official record has an entry for
the same region starting within five minutes.

Source: the volunteer alert record (25 February 2022 to 11 October 2026), kept by volunteers who maintain
the open Vadimkin dataset, and the official record (15 March 2022 to 7 September 2026), the official
feed that the same dataset carries until it stopped. The matched figures use only the window from 15 March 2022 to 7
September 2026, where both records exist; volunteer data after 7 September 2026 is not scored.
Reproduce everything with `python -m scripts.chapter04_reliability`.

**Agreement is not accuracy.** The official record is a cross-check, not ground truth, and nothing in
this project independently checks the volunteer record. A low match rate means the two records disagree.
It does not show which one is right. Where the two agree, that is evidence, not proof. The two records
may also share a source: the volunteer record may draw on the official one, which would raise
agreement without confirming either.

**How matching works.** The five-minute window is the *tolerance*, the time allowed for two alerts to
count as a match. It is the project's standard (see the tolerance table in section 4).

---

## The short version

- **About 65% of volunteer alerts match an official alert** over the whole period. In the
  other direction, 79% of the official record's oblast-level alerts have a volunteer match. After the
  break that second figure rests on only 472 of 65,314 official rows, all of them
  Kyiv City, and is 63%, against 79% before the break. The official-side figure cannot be compared
  across the break.
- **Agreement fell in two main steps plus a gradual slide, not steadily.** Agreement dropped from about 98% to
  83% in November to December 2022, then from about 72% in July 2024 to 51% in November 2024, and has
  been roughly flat through 2025. August 2026 (47%) and the partial September 2026 (37%) are lower, but
  may be affected by the official feed ending on 7 September 2026.
- **There is no step at the December 2025 break.** The six months either side are 53.4% before and 53.7%
  after. An earlier version of this analysis read the break as the cause of a drop. The data does not support that.
- **Some oblasts had much lower agreement after the break than before it.** Lvivska fell from 78% to
  10% and Volynska from 71% to 11%. Donetska (74% to 25%) and Zaporizka also fell sharply. The
  comparison mixes earlier declines with any break effect. The cause is not established; the official
  feed's granularity (how finely it reports locations) changed at the same date.
- **Among pairs already selected as within five minutes, the start times agree closely.** Most matched
  pairs (84%) start within a minute of each other, and the volunteer record is typically about 16 seconds
  later. A match is not proof that both records describe the same event.

---

## 1. Agreement over time

![Monthly agreement with the official record](figures/ch04_monthly_agreement.png)

Agreement was high in the first months of the record and then fell in two main steps plus a gradual
slide. The share of matched volunteer alerts was about 98% in mid-2022, fell to about 83% in November
to December 2022, and was about 76 to 81% in early 2023. It averaged about 64% in 2024, with a fall
during the second half (from about 72% in July 2024 to 51% in November), and was roughly flat in 2025.
August 2026 is 47% and the partial September 2026 is 37%; both may be affected by the official feed
ending on 7 September 2026.

| Measure | Value |
|---|---:|
| Matched alerts, whole period (Mar 2022 to Sep 2026) | 65% |
| Matched, six months before the break (Jun to Nov 2025) | 53.4% |
| Matched, six months after the break (Dec 2025 to May 2026) | 53.7% |
| Linear trend in 2023 to 2025 | about −12 points per year (an average that hides the steps) |

The two six-month windows match each other, so the break itself is not a step in the national figure.
The largest falls came before it.

**Two cautions.** The series is monthly and the last month is partial. The early months are also
affected by the start of the official record in March 2022.

---

## 2. How far apart matched alerts are in time

![How far apart matched start times are](figures/ch04_lag_histogram.png)

For matched pairs, the median gap between the time the volunteer alert was entered and the time the official alert was
entered is **16 seconds**. (This is not warning time; see the note below.)
The middle half (interquartile range) falls between **7 and 36 seconds**. **84%** of matched pairs start
within a minute of each other.

The volunteer record is typically about 16 seconds *later* than the official one. These pairs were
already selected as within five minutes in the same oblast, and a match is not proof of the same
event. One possible reading is that
volunteers record an alert after it is announced; the data does not show this. The lag is computed only
over pairs already within 5 minutes, using the nearest official start, so it cannot describe alerts
that were not matched.

**This is not warning time.** The gap measures how quickly two records were written. It says nothing
about how much warning anyone had before an alert started, and must not be presented that way
(see [SAFETY.md](../SAFETY.md)).

---

## 3. Agreement by oblast

![Agreement by oblast, before and after the break](figures/ch04_agreement_by_oblast.png)

The dumbbell chart shows each oblast's match rate before and after the break. It includes the 24
oblasts with at least 50 alerts in both periods. Kyiv City is included as a region. Luhanska is
excluded because it has too few alerts (two before the break and none after).

Grouped by size of change:

- **Largest falls:** Lvivska (78% to 10%), Volynska (71% to 11%), Donetska (74% to 25%) and Zaporizka
  (84% to 38%). These fall far more than the national average. Lvivska and Volynska are in the west,
  so a western location did not make the records agree more.
- **Other larger falls (12 to 31 points):** Kyiv City (83% to 52%), Odeska (82% to 58%), Zhytomyrska
  (80% to 58%), Rivnenska (90% to 70%), Ternopilska (93% to 75%), Chernihivska (71% to 56%) and
  Dnipropetrovska (59% to 47%).
- **Moderate fall:** Ivano-Frankivska (90% to 80%, a 10-point fall; 86 alerts after the break).
- **Small fall:** Cherkaska (85% to 79%).
- **Little change:** Zakarpatska (97% before, 96% after; 74 alerts after the break) and Chernivetska
  (95% before, 91% after; 100 alerts after the break). These far-western oblasts have small post-break
  samples, so their rates are imprecise.
- **Rises:** Kirovohradska rose about 20 points (65% to 84%) and Mykolaivska rose from 58% to 67%.
- Other scored oblasts are in the full table below.

Twenty-one of the 24 scored oblasts fell after the break; 20 of them by more than one point, 2 rose by
more than one point, and 2 changed by one point or less. "Before" here is the whole pooled (combined)
pre-break period, which is dominated by the 2022 months when agreement was highest, so this comparison mixes the
earlier decline with any effect of the break. The six-month comparison in section 1 is the cleaner test.

The full table is in `output/analysis/chapter04_by_oblast.csv` (gitignored).

---

## 4. How the result depends on the tolerance

| Tolerance | Volunteer alerts matched | Official oblast alerts matched |
|---|---:|---:|
| 1 minute | 55% | 67% |
| **5 minutes (standard)** | **65%** | **79%** |
| 10 minutes | 69% | 82% |
| 30 minutes | 77% | 87% |

Widening the window from one minute to thirty adds about 22 points to the volunteer match rate. Some
unmatched alerts have an official alert in the same oblast within 30 minutes, so some of the gap may be
timing or other alerts nearby in time. The 5-minute standard is a choice; reporting any match rate
without its tolerance would overstate how well the records agree.

---

## 5. Corrections to earlier figures

This chapter corrects two statements made earlier in this project:

1. **The pre-break figure.** The earlier value of 69.0% counted 1,149 volunteer alerts from before the
   official record starts (25 February to 14 March 2022) as unmatched. Restricted to the official
   record's coverage, the pre-break match rate is **70.0%**. The post-break figure of 52.7% is unchanged.
   Caveat: the official record changed format at the break, so the two pools are not directly comparable.
2. **The cause of the drop.** Earlier analysis presented the December 2025 break as the point where
   agreement fell. The six-month comparison above shows no step at that date (53.4% before, 53.7% after).
   The largest falls came earlier, in late 2022 and in mid to late 2024. The pooled 70.0% versus 52.7%
   comparison should not be read as a break effect: the official record changed format at the break, so
   the pools are not directly comparable, and the pre-break pool is dominated by earlier, higher months.
   The break coincides with that change in the official record's granularity, which matters for
   comparisons (see Chapter 6), but agreement did not change at the same time.

The corrections are noted in `docs/gate3_results.md` and `docs/analysis/feed_integrity.md`.

---

## What this chapter cannot tell you

- **Which record is right.** Agreement shows where the two records line up, not which one is correct.
- **Why agreement fell.** The decline could reflect changes in how volunteers report, in what the
  official record includes, or in the events themselves. The data cannot separate these.
- **The reliability of the record after 7 September 2026.** The official record ends there, so no
  cross-check exists for the last five weeks.
- **Whether matched alerts are the same event.** A match is a timing match in the same oblast, not an
  identity match.

---

## Method

- **Window:** from the official record's first start (15 March 2022) to its last start (7 September 2026).
- **Match rate, volunteer side** (called precision in the scripts): share of volunteer alerts with any
  official alert (any level) in the same oblast within the tolerance. 65.4% overall; 70.0% before the
  break and 52.7% after, with the caveat that the official record changed format at the break, so the
  pools are not directly comparable.
- **Match rate, official side** (called recall in the scripts): share of official oblast-level alerts
  with a volunteer alert in the same oblast within the tolerance. 79.2% overall. After the break the
  official record has only 472 of 65,314 rows, all of them Kyiv City, so the
  post-break figure (62.7%, against 79.3% before) is a small, single-city sample and cannot be compared
  across the break.
- **Shared source:** the two records may share a source; the volunteer record may draw on the
  official one.
- **Step test:** a comparison of the six months either side of the break (1 December 2025), 53.4% and 53.7%.
- **Trend:** a linear fit to monthly agreement from January 2023 to November 2025 (about −11.9 points a
  year). It is an average that hides the steps.
- **Lag:** volunteer start minus the nearest official start in the same oblast, computed only over
  pairs already within 5 minutes.
- **Small samples:** oblasts with fewer than 50 alerts in a period are excluded.
- **Script:** `scripts/chapter04_reliability.py`. It reuses the matcher in `scripts/feed_integrity.py`.
