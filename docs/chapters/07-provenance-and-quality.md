# Chapter 7: Data provenance and quality

*Where the two files come from, how they were checked, and what is wrong or missing in them.*

This chapter does not say how many alerts there were. It describes the two files every other chapter relies on, so you can judge how far to trust them.

**"Quality" here means whether the files are well formed, internally consistent and has no obvious internal mistakes that this chapter could find.** From this chapter you can learn what each file contains, what was removed or flagged, and where gaps are. You cannot learn whether either file is correct about what happened on the ground.

Source: the *official record* (the list kept by the official feed; the *feed* is the official alert system's data stream) and the *volunteer record* (a list of alerts kept by volunteers). Both are files in one public repository.

Terms used below. A *row* is one line in a file. *Raw rows* are every line in the file, before removing copies. An *oblast* is a region; a *raion* is a district inside an oblast; a *hromada* is a community, smaller still.

More terms. The *median* is the middle value: half are above it, half below. UTC is world clock time; Kyiv is two to three hours ahead. A *recording error* is a value in the file that cannot be right as written, such as an end time before a start time. A *checksum* (here SHA-256) is a fingerprint of the file; if it matches, the file is the same one that was downloaded.

---

## The short version

- **Both files come from one public GitHub repository** and were downloaded together on 12 October 2026, 00:58 UTC. The files are the same ones that were downloaded; this says nothing about whether their contents are accurate.
- **The official file is 38.0% exact copies** (rows identical in every column, so they are the same line repeated). 299,275 raw rows become 185,430 after removing 113,845 exact duplicates. The volunteer file has none.
- **The volunteer file has at least one row for every day**, which does not mean every alert was logged, from 25 February 2022 to 11 October 2026. The official record has 3 empty days in a row (30 August to 1 September 2026). Empty days are reported, not filled.
- **5.0% of volunteer rows are marked in a column named `naive`**, which marks rows whose end time was guessed, not recorded (the repository calls these inferred end times). The official file has no such column.
- **Every timestamp is written in a standard form that a computer can read (it ends in +00:00); this is a format check only.**
- **Luhanska oblast is nearly empty in both files:** 3 volunteer rows and 1 official row.

---

## 1. What the files are

| | Official record | Volunteer record |
|---|---|---|
| File | `official_data_en.csv` | `volunteer_data_en.csv` |
| Repository | Vadimkin/ukrainian-air-raid-sirens-dataset (GitHub) | same |
| Raw rows | 299,275 | 115,989 |
| Rows after removing exact duplicates | 185,430 | 115,989 |
| First start (UTC) | 15 March 2022 | 25 February 2022 |
| Last start (UTC) | 7 September 2026 | 11 October 2026 |
| Size | 31,025,633 bytes | 8,907,112 bytes |
| SHA-256 | `b396f87696243069eec0219880e87dcd642b20beb0a7bae0d0e1f61e1ed20ec4` | `d03747ee8bf056032b2eeef50cdcf964d65fa60a92243e91862db48b31377465` |

The download was recorded in the project manifest on 12 October 2026 at 00:58 UTC. The size and SHA-256 of each file on disk match the manifest. The checksum shows the file is the one that was downloaded. It does not show that its contents are right.

---

## 2. Duplicates and conflicts

The official file contains 113,845 rows that are exact copies of another row: 38.0% of its raw rows. They are removed before any count in this project. The volunteer file has none.


I do not choose between conflicting end times by hand. Where this matters, the later chapters say how they handle it.

---

## 3. Coverage over time

![Records per year in each file (raw, UTC year)](figures/ch07_coverage_by_year.png)

- **Volunteer record:** records on every one of 1,690 days, 25 February 2022 to 11 October 2026. No empty day.
- **Official record:** 1,638 days from 15 March 2022 to 7 September 2026; 1,635 have records. The 3 empty days are one run, 30 August to 1 September 2026. That is also the longest gap.

An empty day means the file has no row for it. It does not show that nothing happened, or that the feed was down; I cannot tell which. Empty days are left as missing and are never replaced with zeros.

Raw rows per UTC year. Years are counted in UTC; a Kyiv-year count would differ slightly.

| UTC year | Official | Volunteer |
|---|---:|---:|
| 2022 | 34,986 | 15,242 |
| 2023 | 34,724 | 19,046 |
| 2024 | 52,270 | 25,304 |
| 2025 | 91,878 | 24,653 |
| 2026 (to the file's end) | 85,417 | 31,744 |

The official raw count includes the duplicates from section 2, and its format changed over the period (see Chapter 6, on how the official list changed format). Do not compare the two columns, or read the official column as a trend in alerts.

---

## 4. Inferred end times

The volunteer file has a column named `naive`, which the repository describes as marking inferred end times. It flags 5,812 rows, 5.0% of the file. By UTC year:

| UTC year | Share of rows flagged `naive` |
|---|---:|
| 2022 | 2.0% |
| 2023 | 6.1% |
| 2024 | 5.6% |
| 2025 | 5.8% |
| 2026 | 4.7% |

Durations from these rows are partly estimated. The official file has no such column, so I cannot say how many of its end times were inferred.

---

## 5. Missing values and durations

**Official record.** Oblast, level, start, end and source are complete. Raion is missing in 43.5% of rows and hromada in 87.7%. This is expected: each row describes one level, so a row at oblast level has no raion or hromada. **Volunteer record.** All four columns (region, start, end, `naive`) are complete.

| | Official | Volunteer |
|---|---:|---:|
| Rows with zero duration | 4 | 6 |
| Rows with negative duration (recording error) | 0 | 0 |
| Median duration | 48.4 minutes | 30.0 minutes |

The two medians differ because the feeds record different things. The official feed writes several rows per event, at several area levels, so it is not a like-for-like list of the same alerts (see Chapter 6, on how the official list changed format). Do not read the gap as one feed being more accurate.

---

## 6. Names and levels

Both files use the same 25 region names, including Kyiv City and Kyivska oblast as separate names. The two files use the same region names, so the names do not clash.

**Luhanska oblast.** The volunteer file has 3 rows for it; the official file has one (24 March 2022). Both files are nearly empty for this oblast, so neither supports any statement about it.

Official rows by level and UTC year, after removing duplicates:

| UTC year | Oblast | Raion | Hromada |
|---|---:|---:|---:|
| 2022 | 13,633 | 884 | 2,976 |
| 2023 | 16,243 | 12 | 1,107 |
| 2024 | 21,635 | 4 | 4,496 |
| 2025 | 13,355 | 25,722 | 6,900 |
| 2026 | 448 | 72,682 | 5,333 |

oblast = region, raion = district, hromada = community. The change from oblast to raion rows is covered in Chapter 6, on how the official list changed format.

---

## 7. Known edges and what is not in the files

- **Time zones.** Every timestamp in both files is UTC-aware and none failed to parse. Local-day counts in this project use Kyiv time, converted from UTC.
- **Official first start:** 15 March 2022. The volunteer file starts about two and a half weeks earlier (18 days), on 25 February 2022.
- **Official last start:** 7 September 2026, 05:28 UTC. **Volunteer last start:** 11 October 2026, 04:36 UTC. Comparisons between the two stop at the official end.
- **Not in either file:** the type of threat, the cause of an alert, whether anything was hit, and any launch or impact time.

---

## What this chapter cannot tell you

- **Whether either file is correct or complete.** This chapter does not check either file against an independent record. Passing these checks shows the files are well formed, not true.
- **Why rows are missing, duplicated or in conflict.** The files do not say.
- **Whether the 3 empty official days were quiet days or a gap in the feed.**
- **Which conflicting end time is right** where the official file gives two for one start.
- **How many official end times were inferred.** The official file has no flag.
- **Anything about threats.** Counts of rows say nothing about danger.
- **A like-for-like comparison of counts.** The official and volunteer feeds differ in what they record (area levels, inferred end times), so their counts are not interchangeable.

---

## Method (technical appendix)

- **Run the script:** `python -m scripts.chapter07_provenance`.
- **Checksums.** Verify a file yourself (run in `data/raw`; compare ignoring case, since PowerShell prints uppercase hex):
  - Linux or macOS: `sha256sum official_data_en.csv volunteer_data_en.csv`
  - Windows PowerShell: `Get-FileHash -Algorithm SHA256 official_data_en.csv, volunteer_data_en.csv`

  The output should equal the hashes in section 1. This checks the files against the project's own manifest (`data/raw/MANIFEST.json`), not against the repository's current version.
- **Exact duplicates:** rows identical in every column. **Conflicts:** groups of rows with the same area name and start but different ends, counted before removing exact duplicates, so the row count includes exact copies.
- **Days:** calendar days in Kyiv time, from the first to the last start in each file. A day is empty if no row starts on it.
- **`naive` share by year:** rows with `naive` true, over all raw rows that start that year (UTC year).
- **Durations:** end minus start, in minutes, on raw rows in both files (before removing duplicates).
- **Script and numbers:** `scripts/chapter07_provenance.py`; summary in `output/analysis/chapter07_numbers.json`; figure `docs/chapters/figures/ch07_coverage_by_year.png`.
- **Computed by the writer, not by the script:** the 38.0% share is 113,845 out of 299,275 raw rows.
