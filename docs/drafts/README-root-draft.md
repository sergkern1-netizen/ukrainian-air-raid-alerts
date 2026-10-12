# Ukrainian air-alert records: an open, checked analysis

This project looks at the public record of air-raid alerts in Ukraine, from February 2022 to
October 2026. It asks what the record can show, how far it can be trusted, and what it cannot show.

It is not a warning system, a forecast you can act on, or a live feed. Nothing here says where an
attack will happen or what anyone should do. For warnings and shelter guidance, use the official
channels of the Air Force of the Armed Forces of Ukraine and the civil-protection authorities.

## Start here

1. Read the **reading guide** in [`1-read/README.md`](1-read/README.md). It takes about two minutes
   and tells you what to read, in what order, and what to skip.
2. Read the **summary** in [`1-read/summary.md`](1-read/summary.md) for everything done, with the key
   numbers and how each was checked.
3. Read the **chapters** in [`1-read/`](1-read/). Each one answers one question and lists what it
   cannot tell you.

## The four parts

| Part | What it holds | Start with |
|---|---|---|
| [`1-read/`](1-read/) | The findings, in order: purpose, summary, the ten chapters, glossary and safety rules | [Reading guide](1-read/README.md) |
| [`2-evidence/`](2-evidence/) | The supporting analyses behind the chapters | Its index |
| [`3-project/`](3-project/) | Where the project stands, the owner's decisions, the direction, and the history | [Status](3-project/status.md) |
| [`4-run-it/`](4-run-it/) | Setup and how to reproduce every number | [Setup guide](4-run-it/README.md) |

## Two things to know before you read the numbers

- **Counts are not danger.** The record counts alerts that were logged. It has no launch times,
  no impact times and no threat types, so it cannot show how much warning anyone had.
- **Agreement is not accuracy.** The volunteer record and the official record can be compared, but
  neither is a verified, complete account of what happened.

## Status in one line

The project shipped its baseline (a four-week average, which no model beat) with documented misses,
and the enterprise track is closed. The analysis now covers timing, regions, waves, feed agreement,
and data quality. See [`3-project/status.md`](3-project/status.md) for the full picture.
