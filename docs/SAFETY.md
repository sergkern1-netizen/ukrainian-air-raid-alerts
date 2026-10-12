# Safety boundaries

This project publishes statistics about alert records. It is not a warning system, not an
official source, and not a tool for planning attacks or responding to them. These boundaries
apply to every page, number and chart in the repository.

## What this project will not publish

- **Time before impact.** The alert record has no launch or impact timestamps. Any "time to
  impact" or "warning time" figure would be invented.
- **Warning-lead-time claims.** The lag between the volunteer and official records (seconds to
  minutes) is a recording delay. It is not the time people had to take cover.
- **Shelter advice or shelter-access claims.** The project has no shelter data. Instructions on
  where or when to take cover come from official civil-protection channels only.
- **Threat-type inference.** The feed does not record whether an alert was for missiles, drones or
  aircraft. Do not assign a threat type to any alert, wave or oblast.
- **Targeting language.** No "hotspot", "target", "most attacked" or similar framing. Counts show
  where sirens sounded, not where anything was aimed.
- **Risk scores or rankings presented as danger.** Oblast or city rankings may appear only as
  descriptive statistics, with their sample size and limits beside them.
- **Predictions.** No forecast of when or where alerts will occur. The only forecast in the
  project is the trailing four-week mean baseline, which was not beaten by any model. It is not
  a warning.
- **Real-time claims.** The real-time poller has not been measured against the live source. No
  page may describe the output as live or as real-time.
- **Unvalidated accuracy claims.** The volunteer feed has no ground truth. Do not describe it as
  accurate, complete or authoritative.
- **Data with unresolved provenance or licence.** The Telegram-derived dataset is parked and is
  not used (see `docs/FUTURE_PLANS.md`). Do not publish its figures.

## Requirements for every public number

1. It is produced by a script in `scripts/`, and the script runs from the repository root.
2. Its source file and date range are stated.
3. Its limit is stated next to it, for example the overlap window, the small-sample flag or the
   granularity change.
4. Missing periods are reported as missing. They are never filled with zeros.
5. Small samples are flagged. Rates from fewer than 50 alerts are marked as noisy.

## Official warnings

Safety instructions and live warnings come from official channels: the Air Force of the Armed
Forces of Ukraine, the State Emergency Service, and local authorities. This repository links to
them and does not reproduce or summarise their warnings.

## Reporting a problem

If a figure in this repository could mislead someone about their safety, open an issue or contact
the maintainer. Corrections are made in the same commit as the change that explains them.
